import asyncio
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.core.config import settings

logger = logging.getLogger("truthnet.extractors.transcription")

class BaseTranscriptionEngine(ABC):
    """Abstract base class for speech transcription engines."""

    @abstractmethod
    def engine_name(self) -> str:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Determines if the speech transcription model runtime and checkpoints are ready."""
        pass

    @abstractmethod
    async def transcribe(self, audio_path: Path) -> Dict[str, Any]:
        """
        Executes genuine speech transcription on an audio file.
        Returns:
            {
                "status": "COMPLETED" | "FAILED" | "UNAVAILABLE",
                "text": str | None,
                "language": str | None,
                "duration_seconds": float | None,
                "segments": List[Dict[str, Any]],
                "engine": str,
                "error": str | None
            }
        """
        pass

class FasterWhisperEngine(BaseTranscriptionEngine):
    """
    Speech transcription engine using faster-whisper (CTranslate2 optimized for CPU).
    Provides real time-aligned transcription segments when model weights are available.
    Reports honest UNAVAILABLE status when model weights or library are not present.
    """

    def __init__(self, model_size_or_path: str = "base"):
        self.model_size_or_path = model_size_or_path
        self._model = None
        self._available: Optional[bool] = None

    def engine_name(self) -> str:
        return f"faster-whisper ({self.model_size_or_path})"

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            import faster_whisper
            self._available = True
        except ImportError:
            self._available = False
        except Exception:
            self._available = False
        return self._available

    def _get_model(self):
        if self._model is None and self.is_available():
            from faster_whisper import WhisperModel
            # Load with int8 CPU compute for low-memory fast local execution
            self._model = WhisperModel(
                self.model_size_or_path,
                device="cpu",
                compute_type="int8",
                download_root=str(settings.DATA_DIR / "models" / "whisper")
            )
        return self._model

    async def transcribe(self, audio_path: Path) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "status": "COMPLETED",
            "text": None,
            "language": None,
            "duration_seconds": None,
            "segments": [],
            "engine": self.engine_name(),
            "error": None
        }

        if not self.is_available():
            result["status"] = "UNAVAILABLE"
            result["error"] = "faster-whisper package is not installed on host."
            return result

        if not audio_path.exists():
            result["status"] = "FAILED"
            result["error"] = f"Audio file not found: {audio_path}"
            return result

        try:
            loop = asyncio.get_running_loop()

            def _inference():
                model = self._get_model()
                segments_iter, info = model.transcribe(str(audio_path), beam_size=3)
                collected_segments = []
                full_text_parts = []
                for seg in segments_iter:
                    collected_segments.append({
                        "start_ms": int(seg.start * 1000),
                        "end_ms": int(seg.end * 1000),
                        "text": seg.text.strip(),
                        "confidence": getattr(seg, "avg_logprob", None)
                    })
                    full_text_parts.append(seg.text.strip())
                return collected_segments, " ".join(full_text_parts), info.language, info.duration

            segments, full_text, detected_lang, duration = await loop.run_in_executor(None, _inference)

            result["text"] = full_text if full_text else None
            result["segments"] = segments
            result["language"] = detected_lang
            result["duration_seconds"] = round(duration, 2) if duration else None

        except Exception as e:
            logger.error(f"Whisper transcription failed on {audio_path}: {e}")
            result["status"] = "FAILED"
            result["error"] = str(e)

        return result

class CompositeTranscriptionService:
    """
    Orchestrates transcription services with strict truthfulness.
    Never fabricates speech transcripts.
    """

    def __init__(self):
        self.engine = FasterWhisperEngine()

    def is_available(self) -> bool:
        return self.engine.is_available()

    def get_engine_name(self) -> str:
        return self.engine.engine_name()

    async def transcribe(self, audio_path: Path) -> Dict[str, Any]:
        if not self.is_available():
            return {
                "category": "OBSERVED_DATA",
                "status": "UNAVAILABLE",
                "text": None,
                "language": None,
                "duration_seconds": None,
                "segments": [],
                "engine": self.get_engine_name(),
                "reason": "Speech transcription engine (faster-whisper) is not available or weights not loaded."
            }

        res = await self.engine.transcribe(audio_path)
        res["category"] = "OBSERVED_DATA"
        return res

transcription_service = CompositeTranscriptionService()
