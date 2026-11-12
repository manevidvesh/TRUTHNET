import asyncio
import logging
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional
from PIL import Image

logger = logging.getLogger("truthnet.extractors.ocr")

class BaseOcrEngine(ABC):
    """Abstract base class for Optical Character Recognition adapters."""

    @abstractmethod
    def engine_name(self) -> str:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Determines if the underlying binary or runtime is genuinely available on the host."""
        pass

    @abstractmethod
    async def extract_text(self, image_path: Path) -> Dict[str, Any]:
        """
        Executes genuine OCR inference on the target image.
        Returns:
            {
                "status": "COMPLETED" | "FAILED" | "UNAVAILABLE",
                "text": str | None,
                "engine": str,
                "lines": List[Dict[str, Any]],
                "confidence": float | None,
                "error": str | None
            }
        """
        pass

class WindowsMediaOcrEngine(BaseOcrEngine):
    """
    Native Windows 10/11 OCR adapter using Windows.Media.Ocr.OcrEngine via winocr.
    Provides hardware-accelerated local OCR without external binary installations.
    """

    def __init__(self):
        self._available: Optional[bool] = None

    def engine_name(self) -> str:
        return "Windows.Media.Ocr (winocr)"

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            import winocr
            self._available = True
        except ImportError:
            self._available = False
        except Exception:
            self._available = False
        return self._available

    async def extract_text(self, image_path: Path) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "status": "COMPLETED",
            "text": None,
            "engine": self.engine_name(),
            "lines": [],
            "confidence": None,
            "error": None
        }

        if not self.is_available():
            result["status"] = "UNAVAILABLE"
            result["error"] = "winocr module is not installed or Windows OCR runtime is inaccessible."
            return result

        if not image_path.exists():
            result["status"] = "FAILED"
            result["error"] = f"Image file not found: {image_path}"
            return result

        try:
            import winocr
            with Image.open(image_path) as pil_img:
                ocr_out = await winocr.recognize_pil(pil_img, "en")

            recognized_text = ocr_out.text.strip() if ocr_out.text else ""
            lines_data: List[Dict[str, Any]] = []

            for line in getattr(ocr_out, "lines", []):
                line_text = getattr(line, "text", "")
                words = [getattr(w, "text", "") for w in getattr(line, "words", [])]
                lines_data.append({
                    "text": line_text,
                    "word_count": len(words)
                })

            result["text"] = recognized_text if recognized_text else None
            result["lines"] = lines_data
            result["confidence"] = 1.0 if recognized_text else None

        except Exception as e:
            logger.error(f"Windows OCR inference failed on {image_path}: {e}")
            result["status"] = "FAILED"
            result["error"] = str(e)

        return result

class TesseractOcrEngine(BaseOcrEngine):
    """
    Tesseract OCR adapter using pytesseract.
    Requires tesseract.exe on PATH.
    """

    def __init__(self):
        self._available: Optional[bool] = None

    def engine_name(self) -> str:
        return "Tesseract-OCR"

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        has_binary = shutil.which("tesseract") is not None
        try:
            import pytesseract
            has_module = True
        except ImportError:
            has_module = False
        self._available = has_binary and has_module
        return self._available

    async def extract_text(self, image_path: Path) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "status": "COMPLETED",
            "text": None,
            "engine": self.engine_name(),
            "lines": [],
            "confidence": None,
            "error": None
        }

        if not self.is_available():
            result["status"] = "UNAVAILABLE"
            result["error"] = "tesseract binary or pytesseract library is not available on host."
            return result

        try:
            import pytesseract
            with Image.open(image_path) as pil_img:
                loop = asyncio.get_running_loop()
                text = await loop.run_in_executor(None, pytesseract.image_to_string, pil_img)
            
            clean_text = text.strip() if text else ""
            result["text"] = clean_text if clean_text else None
            result["lines"] = [{"text": l} for l in clean_text.splitlines() if l.strip()]
        except Exception as e:
            logger.error(f"Tesseract OCR inference failed on {image_path}: {e}")
            result["status"] = "FAILED"
            result["error"] = str(e)

        return result

class CompositeOcrService:
    """
    Orchestrates OCR engines with strict prioritization and honest capability reporting.
    Never returns synthetic or hardcoded text.
    """

    def __init__(self):
        self.engines: List[BaseOcrEngine] = [
            WindowsMediaOcrEngine(),
            TesseractOcrEngine()
        ]

    def get_active_engine(self) -> Optional[BaseOcrEngine]:
        for engine in self.engines:
            if engine.is_available():
                return engine
        return None

    def get_active_engine_name(self) -> str:
        active = self.get_active_engine()
        return active.engine_name() if active else "NONE_AVAILABLE"

    async def extract_text(self, image_path: Path) -> Dict[str, Any]:
        active = self.get_active_engine()
        if not active:
            return {
                "category": "OBSERVED_DATA",
                "status": "UNAVAILABLE",
                "text": None,
                "engine": None,
                "lines": [],
                "confidence": None,
                "reason": "No supported OCR engine (Windows.Media.Ocr or Tesseract) is currently available on the host system."
            }

        res = await active.extract_text(image_path)
        res["category"] = "OBSERVED_DATA"
        return res

ocr_service = CompositeOcrService()
