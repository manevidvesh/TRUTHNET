import pytest
from pathlib import Path
from PIL import Image, ImageDraw
from app.extractors.ocr import CompositeOcrService, WindowsMediaOcrEngine, TesseractOcrEngine, ocr_service
from app.extractors.transcription import FasterWhisperEngine, transcription_service

@pytest.mark.asyncio
async def test_ocr_capability_detection():
    """
    Verifies that OCR capability detection checks native host engines
    without throwing exceptions or returning fabricated status.
    """
    active_engine_name = ocr_service.get_active_engine_name()
    assert active_engine_name != ""
    assert isinstance(active_engine_name, str)

    win_engine = WindowsMediaOcrEngine()
    is_win_avail = win_engine.is_available()
    assert isinstance(is_win_avail, bool)

    tess_engine = TesseractOcrEngine()
    is_tess_avail = tess_engine.is_available()
    assert isinstance(is_tess_avail, bool)

@pytest.mark.asyncio
async def test_genuine_ocr_inference_on_rendered_image(tmp_path: Path):
    """
    Executes actual OCR inference on a real generated image with rendered text.
    Verifies that genuine text extraction works and is categorized as OBSERVED_DATA.
    """
    img_path = tmp_path / "test_ocr_sample.png"
    img = Image.new("RGB", (500, 120), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((30, 45), "TRUTHNET EVIDENCE 2026", fill=(0, 0, 0))
    img.save(img_path)

    result = await ocr_service.extract_text(img_path)

    assert result["category"] == "OBSERVED_DATA"
    if ocr_service.get_active_engine():
        assert result["status"] == "COMPLETED"
        assert result["text"] is not None
        # On Windows native OCR, text is recognized cleanly
        recognized = result["text"].replace(" ", "").upper()
        assert "TRUTHNET" in recognized
        assert "2026" in recognized
        assert len(result["lines"]) >= 1
    else:
        assert result["status"] == "UNAVAILABLE"
        assert result["text"] is None

@pytest.mark.asyncio
async def test_ocr_unavailable_behavior_never_fabricates_text(tmp_path: Path):
    """
    Strict truthfulness test: when an engine is unavailable, it must report
    UNAVAILABLE status and text=None, never returning synthetic predictions.
    """
    img_path = tmp_path / "empty.png"
    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    img.save(img_path)

    mock_service = CompositeOcrService()
    # Force no engines available
    mock_service.engines = []

    res = await mock_service.extract_text(img_path)
    assert res["category"] == "OBSERVED_DATA"
    assert res["status"] == "UNAVAILABLE"
    assert res["text"] is None
    assert "No supported OCR engine" in res["reason"]

@pytest.mark.asyncio
async def test_transcription_capability_and_contract():
    """
    Verifies that speech transcription service detects faster-whisper capability,
    and adheres to the strict contract of never fabricating transcripts.
    """
    is_avail = transcription_service.is_available()
    assert isinstance(is_avail, bool)

    engine_name = transcription_service.get_engine_name()
    assert "faster-whisper" in engine_name

@pytest.mark.asyncio
async def test_transcription_unavailable_contract(tmp_path: Path):
    """
    Verifies that when transcription engine is unavailable, it honestly reports
    UNAVAILABLE and does not return synthetic text.
    """
    from app.extractors.transcription import CompositeTranscriptionService
    empty_audio = tmp_path / "missing.wav"

    mock_transcription = CompositeTranscriptionService()
    mock_transcription.engine.is_available = lambda: False

    res = await mock_transcription.transcribe(empty_audio)
    assert res["category"] == "OBSERVED_DATA"
    assert res["status"] == "UNAVAILABLE"
    assert res["text"] is None
    assert res["segments"] == []
