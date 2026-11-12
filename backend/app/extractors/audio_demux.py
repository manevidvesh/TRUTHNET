import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import av
from app.core.config import settings

logger = logging.getLogger("truthnet.extractors.audio_demux")

class AudioDemuxer:
    """
    Detects and demuxes audio streams from video containers using PyAV.
    Resamples extracted audio to 16kHz mono PCM WAV suitable for speech transcription.
    Computes SHA-256 for the derived audio artifact.
    Fault-tolerant: failures in audio extraction do not affect video decoding.
    """

    def __init__(self, derived_dir: Path | None = None):
        self.derived_dir = derived_dir or (settings.DATA_DIR / "derived")

    def extract_audio_from_video(
        self,
        video_path: Path,
        evidence_id: str
    ) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "status": "COMPLETED",
            "has_audio": False,
            "artifact": None,
            "stream_metadata": None,
            "error": None
        }

        if not video_path.exists():
            result["status"] = "FAILED"
            result["error"] = "Video file does not exist"
            return result

        try:
            with av.open(str(video_path)) as in_container:
                if not in_container.streams.audio:
                    result["status"] = "NO_AUDIO_STREAM"
                    result["has_audio"] = False
                    return result

                in_stream = in_container.streams.audio[0]
                result["has_audio"] = True
                result["stream_metadata"] = {
                    "index": in_stream.index,
                    "codec_name": in_stream.codec_context.name if in_stream.codec_context else None,
                    "channels": in_stream.codec_context.channels if in_stream.codec_context else None,
                    "sample_rate": in_stream.codec_context.sample_rate if in_stream.codec_context else None
                }

                out_dir = self.derived_dir / evidence_id / "audio"
                out_dir.mkdir(parents=True, exist_ok=True)
                out_path = out_dir / "extracted_audio.wav"

                resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)

                with av.open(str(out_path), mode="w", format="wav") as out_container:
                    out_stream = out_container.add_stream("pcm_s16le", rate=16000, layout="mono")
                    
                    frames_processed = 0
                    for frame in in_container.decode(in_stream):
                        resampled = resampler.resample(frame)
                        for r_frame in resampled:
                            for packet in out_stream.encode(r_frame):
                                out_container.mux(packet)
                                frames_processed += 1

                    # Flush resampler
                    resampled_flush = resampler.resample(None)
                    for r_frame in resampled_flush:
                        for packet in out_stream.encode(r_frame):
                            out_container.mux(packet)
                            frames_processed += 1

                    # Flush encoder
                    for packet in out_stream.encode():
                        out_container.mux(packet)

                if not out_path.exists() or out_path.stat().st_size == 0:
                    result["status"] = "FAILED"
                    result["error"] = "Extracted audio file is empty"
                    return result

                audio_bytes = out_path.read_bytes()
                sha256_hash = hashlib.sha256(audio_bytes).hexdigest()
                base_data_dir = self.derived_dir.parent
                try:
                    rel_path = str(out_path.relative_to(base_data_dir))
                except ValueError:
                    rel_path = f"derived/{evidence_id}/audio/{out_path.name}"

                result["artifact"] = {
                    "artifact_type": "EXTRACTED_AUDIO",
                    "sha256_hash": sha256_hash,
                    "relative_path": rel_path,
                    "file_size_bytes": len(audio_bytes),
                    "mime_type": "audio/wav",
                    "artifact_metadata": {
                        "sample_rate": 16000,
                        "channels": 1,
                        "format": "pcm_s16le",
                        "frames_processed": frames_processed,
                        "source_stream_index": in_stream.index
                    }
                }

        except Exception as e:
            logger.error(f"Audio demuxing failed for {video_path}: {e}")
            result["status"] = "FAILED"
            result["error"] = str(e)

        return result

audio_demuxer = AudioDemuxer()
