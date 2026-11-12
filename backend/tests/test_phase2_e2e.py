import io
import pytest
from pathlib import Path
from PIL import Image, ImageDraw
import av
import numpy as np
from httpx import AsyncClient
from sqlalchemy import select
from app.models.investigation import Investigation
from app.models.evidence import EvidenceSubmission, ExtractionRecord, DerivedArtifact

def _generate_test_image_bytes(text: str = "TRUTHNET OCR") -> bytes:
    img = Image.new("RGB", (320, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 35), text, fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def _generate_synthetic_mp4(with_audio: bool = True, duration_sec: int = 2) -> bytes:
    buf = io.BytesIO()
    container = av.open(buf, mode="w", format="mp4")
    v_stream = container.add_stream("mpeg4", rate=30)
    v_stream.width = 320
    v_stream.height = 240
    v_stream.pix_fmt = "yuv420p"

    a_stream = None
    if with_audio:
        a_stream = container.add_stream("aac", rate=44100, layout="mono")

    for i in range(duration_sec * 30):
        img = np.zeros((240, 320, 3), dtype=np.uint8)
        img[:, :] = [(i * 4) % 255, (i * 8) % 255, 120]
        v_frame = av.VideoFrame.from_ndarray(img, format="bgr24")
        for packet in v_stream.encode(v_frame):
            container.mux(packet)

        if a_stream and i % 10 == 0:
            samples = np.sin(2 * np.pi * 440 * np.linspace(0, 0.1, 4410)).astype(np.float32)
            a_frame = av.AudioFrame.from_ndarray(samples.reshape(1, -1), format="flt", layout="mono")
            a_frame.rate = 44100
            for packet in a_stream.encode(a_frame):
                container.mux(packet)

    for packet in v_stream.encode():
        container.mux(packet)
    if a_stream:
        for packet in a_stream.encode():
            container.mux(packet)
    container.close()
    return buf.getvalue()

@pytest.mark.asyncio
async def test_e2e_image_upload_and_multimodal_extraction(async_client: AsyncClient):
    """
    E2E Test: Upload image -> background processing executes metadata & OCR
    -> verify /extracted endpoint returns versioned OBSERVED_DATA record.
    """
    # 1. Create investigation
    inv_res = await async_client.post(
        "/api/v1/investigations/",
        json={"title": "E2E Image Investigation", "description": "Phase 2 Verification"}
    )
    assert inv_res.status_code == 201
    inv_id = inv_res.json()["id"]

    # 2. Upload image file with text
    img_bytes = _generate_test_image_bytes("TRUTHNET PS11")
    upload_res = await async_client.post(
        f"/api/v1/investigations/{inv_id}/evidence/upload",
        files={"file": ("evidence_doc.jpg", img_bytes, "image/jpeg")},
        data={"caption": "Purported leaked document"}
    )
    assert upload_res.status_code == 201
    ev_data = upload_res.json()
    ev_id = ev_data["id"]

    # In tests, FastAPI BackgroundTasks execute synchronously before response completes
    # Check extraction record via API
    ext_res = await async_client.get(f"/api/v1/investigations/{inv_id}/evidence/{ev_id}/extracted")
    assert ext_res.status_code == 200
    ext_data = ext_res.json()

    assert ext_data["category"] == "OBSERVED_DATA"
    assert ext_data["version"] == 1
    assert ext_data["is_active"] is True
    assert ext_data["technical_metadata"]["dimensions"]["width"] == 320
    assert ext_data["technical_metadata"]["dimensions"]["height"] == 100
    assert ext_data["technical_metadata"]["timezone_info"]["timezone_detected"] is False

    # Check OCR result
    assert ext_data["ocr_result"] is not None
    assert ext_data["ocr_result"]["category"] == "OBSERVED_DATA"
    assert ext_data["modality_statuses"]["metadata"] == "COMPLETED"

@pytest.mark.asyncio
async def test_e2e_video_upload_keyframes_audio_demux_and_artifact_security(async_client: AsyncClient):
    """
    E2E Test: Upload video with audio -> extract keyframes (boundary anchored)
    -> demux audio -> query artifacts -> download content -> verify path isolation.
    """
    inv_res = await async_client.post(
        "/api/v1/investigations/",
        json={"title": "E2E Video Investigation", "description": "Video with audio"}
    )
    inv_id = inv_res.json()["id"]

    video_bytes = _generate_synthetic_mp4(with_audio=True, duration_sec=2)
    upload_res = await async_client.post(
        f"/api/v1/investigations/{inv_id}/evidence/upload",
        files={"file": ("suspicious_video.mp4", video_bytes, "video/mp4")},
        data={"caption": "Video showing alleged incident"}
    )
    assert upload_res.status_code == 201
    ev_id = upload_res.json()["id"]

    # 1. Query extracted record
    ext_res = await async_client.get(f"/api/v1/investigations/{inv_id}/evidence/{ev_id}/extracted")
    assert ext_res.status_code == 200
    ext_data = ext_res.json()

    assert ext_data["category"] == "OBSERVED_DATA"
    assert ext_data["modality_statuses"]["frames"] == "COMPLETED"
    assert ext_data["modality_statuses"]["audio_demux"] == "COMPLETED"
    assert len(ext_data["video_frames"]) > 0

    # Verify boundary frames
    assert ext_data["video_frames"][0]["target_timestamp_ms"] == 0.0
    assert ext_data["video_frames"][0]["is_boundary_frame"] is True

    # 2. Query derived artifacts
    art_res = await async_client.get(f"/api/v1/investigations/{inv_id}/evidence/{ev_id}/artifacts")
    assert art_res.status_code == 200
    artifacts = art_res.json()
    assert len(artifacts) >= 2  # At least keyframes + extracted audio

    types = [a["artifact_type"] for a in artifacts]
    assert "KEYFRAME" in types
    assert "EXTRACTED_AUDIO" in types

    # Verify strict path privacy (no filesystem path leaked)
    for art in artifacts:
        assert "file_path" not in art
        assert "relative_path" not in art
        assert art["download_url"].startswith(f"/api/v1/investigations/{inv_id}/evidence/{ev_id}/artifacts/")

    # 3. Test downloading a keyframe artifact
    keyframe_art = next(a for a in artifacts if a["artifact_type"] == "KEYFRAME")
    kf_dl = await async_client.get(keyframe_art["download_url"])
    assert kf_dl.status_code == 200
    assert kf_dl.headers["content-type"] == "image/jpeg"
    assert len(kf_dl.content) > 0

    # 4. Test downloading an audio artifact
    audio_art = next(a for a in artifacts if a["artifact_type"] == "EXTRACTED_AUDIO")
    aud_dl = await async_client.get(audio_art["download_url"])
    assert aud_dl.status_code == 200
    assert aud_dl.headers["content-type"] == "audio/wav"
    assert len(aud_dl.content) > 0

@pytest.mark.asyncio
async def test_e2e_video_without_audio_stream(async_client: AsyncClient):
    """
    E2E Test: Upload video with NO audio stream.
    Verifies keyframe extraction succeeds and audio demux gracefully reports NO_AUDIO_STREAM.
    """
    inv_res = await async_client.post(
        "/api/v1/investigations/",
        json={"title": "Silent Video Investigation", "description": "Silent video"}
    )
    inv_id = inv_res.json()["id"]

    video_bytes = _generate_synthetic_mp4(with_audio=False, duration_sec=1)
    upload_res = await async_client.post(
        f"/api/v1/investigations/{inv_id}/evidence/upload",
        files={"file": ("silent_clip.mp4", video_bytes, "video/mp4")}
    )
    assert upload_res.status_code == 201
    ev_id = upload_res.json()["id"]

    ext_res = await async_client.get(f"/api/v1/investigations/{inv_id}/evidence/{ev_id}/extracted")
    assert ext_res.status_code == 200
    ext_data = ext_res.json()

    assert ext_data["modality_statuses"]["frames"] == "COMPLETED"
    assert ext_data["modality_statuses"]["audio_demux"] == "NO_AUDIO_STREAM"
    assert ext_data["modality_statuses"]["transcription"] == "SKIPPED"
    assert ext_data["status"] == "COMPLETED"

@pytest.mark.asyncio
async def test_e2e_reprocessing_version_preservation(async_client: AsyncClient):
    """
    Verifies that re-running extraction preserves history and creates an active version 2 record.
    """
    inv_res = await async_client.post(
        "/api/v1/investigations/",
        json={"title": "Reprocessing Test", "description": "Versioning"}
    )
    inv_id = inv_res.json()["id"]

    img_bytes = _generate_test_image_bytes("VERSION 1")
    upload_res = await async_client.post(
        f"/api/v1/investigations/{inv_id}/evidence/upload",
        files={"file": ("version_test.jpg", img_bytes, "image/jpeg")}
    )
    ev_id = upload_res.json()["id"]

    # Initial extraction is version 1
    ext1_res = await async_client.get(f"/api/v1/investigations/{inv_id}/evidence/{ev_id}/extracted")
    assert ext1_res.status_code == 200
    assert ext1_res.json()["version"] == 1

    # Trigger re-processing via retry endpoint
    retry_res = await async_client.post(f"/api/v1/investigations/{inv_id}/evidence/{ev_id}/retry")
    assert retry_res.status_code == 200

    # Active extraction is now version 2
    ext2_res = await async_client.get(f"/api/v1/investigations/{inv_id}/evidence/{ev_id}/extracted")
    assert ext2_res.status_code == 200
    ext2_data = ext2_res.json()
    assert ext2_data["version"] == 2
    assert ext2_data["is_active"] is True

@pytest.mark.asyncio
async def test_e2e_corrupt_media_fault_isolation(async_client: AsyncClient):
    """
    Verifies that uploading a corrupt media file records failure gracefully
    and does not crash the system or cause unhandled 500 errors.
    """
    inv_res = await async_client.post(
        "/api/v1/investigations/",
        json={"title": "Corrupt Media Investigation", "description": "Fault isolation test"}
    )
    inv_id = inv_res.json()["id"]

    # Upload corrupt bytes with image/jpeg extension
    upload_res = await async_client.post(
        f"/api/v1/investigations/{inv_id}/evidence/upload",
        files={"file": ("corrupt.jpg", b"\xFF\xD8\xFFcorrupt_truncated_bytes", "image/jpeg")}
    )
    assert upload_res.status_code == 201
    ev_id = upload_res.json()["id"]

    # Verify status
    status_res = await async_client.get(f"/api/v1/investigations/{inv_id}/evidence/{ev_id}/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    # It either completed metadata with warnings/fallback or failed gracefully
    assert status_data["processing_status"] in ("COMPLETED", "FAILED")

