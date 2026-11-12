import pytest
from pathlib import Path
import av
import numpy as np
from app.extractors.video_frames import KeyframeExtractor
from app.extractors.audio_demux import AudioDemuxer

def create_synthetic_video(file_path: Path, with_audio: bool = True, duration_sec: int = 3, fps: int = 30):
    """Generates a synthetic MP4 file with moving colored boxes and optional audio track."""
    container = av.open(str(file_path), mode="w", format="mp4")
    v_stream = container.add_stream("mpeg4", rate=fps)
    v_stream.width = 320
    v_stream.height = 240
    v_stream.pix_fmt = "yuv420p"

    a_stream = None
    if with_audio:
        a_stream = container.add_stream("aac", rate=44100, layout="mono")

    total_frames = duration_sec * fps
    for i in range(total_frames):
        # Create image with varying color
        img = np.zeros((240, 320, 3), dtype=np.uint8)
        img[:, :] = [(i * 5) % 255, (i * 10) % 255, (i * 15) % 255]
        v_frame = av.VideoFrame.from_ndarray(img, format="bgr24")
        for packet in v_stream.encode(v_frame):
            container.mux(packet)

        if a_stream and i % 10 == 0:
            # Generate 0.1s of audio tone
            audio_samples = np.sin(2 * np.pi * 440 * np.linspace(0, 0.1, 4410)).astype(np.float32)
            a_frame = av.AudioFrame.from_ndarray(audio_samples.reshape(1, -1), format="flt", layout="mono")
            a_frame.rate = 44100
            for packet in a_stream.encode(a_frame):
                container.mux(packet)

    for packet in v_stream.encode():
        container.mux(packet)

    if a_stream:
        for packet in a_stream.encode():
            container.mux(packet)

    container.close()

def test_boundary_anchored_keyframe_extraction(tmp_path: Path):
    """
    Verifies that keyframe extraction captures the first decodable frame (0ms),
    last frame, and intermediate frames with exact timestamps and SHA-256 hashes.
    """
    video_path = tmp_path / "sample_video.mp4"
    create_synthetic_video(video_path, with_audio=False, duration_sec=3, fps=30)

    extractor = KeyframeExtractor(derived_dir=tmp_path / "derived")
    frames, summary = extractor.extract_keyframes(
        video_path=video_path,
        evidence_id="ev_test_123",
        max_frames=10,
        target_interval_sec=0.5
    )

    assert summary["status"] == "COMPLETED"
    assert len(frames) > 0
    assert summary["total_frames_extracted"] == len(frames)
    assert "disclaimer" in summary

    # First frame verification (boundary 0 ms)
    first_frame = frames[0]
    assert first_frame["target_timestamp_ms"] == 0.0
    assert first_frame["is_boundary_frame"] is True
    assert len(first_frame["sha256_hash"]) == 64
    assert Path(tmp_path / "derived" / "ev_test_123" / "frames" / f"frame_0_{int(first_frame['actual_timestamp_ms'])}ms.jpg").exists()

    # Last frame verification (boundary end)
    last_frame = frames[-1]
    assert last_frame["is_boundary_frame"] is True
    assert last_frame["actual_timestamp_ms"] > 1000.0

def test_audio_demux_from_video_with_audio(tmp_path: Path):
    """
    Verifies that audio is demuxed from video and resampled to 16kHz mono WAV.
    """
    video_path = tmp_path / "video_with_audio.mp4"
    create_synthetic_video(video_path, with_audio=True, duration_sec=2, fps=30)

    demuxer = AudioDemuxer(derived_dir=tmp_path / "derived")
    result = demuxer.extract_audio_from_video(video_path, evidence_id="ev_audio_123")

    assert result["status"] == "COMPLETED"
    assert result["has_audio"] is True
    artifact = result["artifact"]
    assert artifact is not None
    assert artifact["artifact_type"] == "EXTRACTED_AUDIO"
    assert artifact["mime_type"] == "audio/wav"
    assert artifact["artifact_metadata"]["sample_rate"] == 16000
    assert artifact["artifact_metadata"]["channels"] == 1
    assert len(artifact["sha256_hash"]) == 64

    # Verify physical file
    wav_path = tmp_path / "derived" / "ev_audio_123" / "audio" / "extracted_audio.wav"
    assert wav_path.exists()
    assert wav_path.stat().st_size > 0

def test_audio_demux_video_without_audio(tmp_path: Path):
    """
    Verifies that a video without audio stream reports NO_AUDIO_STREAM without error.
    """
    video_path = tmp_path / "silent_video.mp4"
    create_synthetic_video(video_path, with_audio=False, duration_sec=1, fps=30)

    demuxer = AudioDemuxer(derived_dir=tmp_path / "derived")
    result = demuxer.extract_audio_from_video(video_path, evidence_id="ev_silent_123")

    assert result["status"] == "NO_AUDIO_STREAM"
    assert result["has_audio"] is False
    assert result["artifact"] is None

def test_corrupt_video_fault_isolation(tmp_path: Path):
    """
    Verifies that corrupt video files do not crash the extractor or demuxer.
    """
    corrupt_path = tmp_path / "corrupt.mp4"
    corrupt_path.write_bytes(b"\x00\x00\x00\x18ftypmp42corrupt_bytes_here")

    extractor = KeyframeExtractor(derived_dir=tmp_path / "derived")
    frames, summary = extractor.extract_keyframes(corrupt_path, evidence_id="ev_corrupt_123")
    assert summary["status"] == "FAILED"
    assert len(frames) == 0

    demuxer = AudioDemuxer(derived_dir=tmp_path / "derived")
    result = demuxer.extract_audio_from_video(corrupt_path, evidence_id="ev_corrupt_123")
    assert result["status"] == "FAILED"
