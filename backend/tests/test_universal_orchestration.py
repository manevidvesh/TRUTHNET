"""
Comprehensive tests for TRUTHNET AI Universal Evidence Input Orchestration.

Verifies:
1. Automatic modality classification for images, video, audio, text, and URLs.
2. Single-file, multi-file, and mixed-modality (files + text claim + URL) batch ingestion.
3. Fault-isolated processing: invalid or unsupported items do not crash valid evidence.
4. Assigned processing route tracking.
5. Integration with investigation reports, lineage graphs, and database storage.
"""

import io
import wave
import struct
import pytest
from PIL import Image
import numpy as np
import av
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.investigation import Investigation
from app.models.evidence import EvidenceSubmission, MediaAsset
from app.services.evidence_orchestrator import evidence_orchestrator


def make_test_png(w=64, h=64, color=(40, 100, 200)) -> bytes:
    img = Image.new("RGB", (w, h), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_test_wav(duration_s=0.2, freq=440, rate=16000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        samples = [int(32767 * 0.3 * np.sin(2 * np.pi * freq * t / rate)) for t in range(int(rate * duration_s))]
        wf.writeframes(struct.pack("<" + ("h" * len(samples)), *samples))
    return buf.getvalue()


def make_test_mp4(num_frames=5, w=160, h=120) -> bytes:
    buf = io.BytesIO()
    container = av.open(buf, mode="w", format="mp4")
    stream = container.add_stream("mpeg4", rate=10)
    stream.width = w
    stream.height = h
    stream.pix_fmt = "yuv420p"
    for _ in range(num_frames):
        frame = av.VideoFrame.from_ndarray(np.zeros((h, w, 3), dtype=np.uint8), format="bgr24")
        for packet in stream.encode(frame):
            container.mux(packet)
    for packet in stream.encode():
        container.mux(packet)
    container.close()
    return buf.getvalue()


def test_modality_detection_accuracy():
    """Verify modality detection and assigned technical routes across formats."""
    # Images
    mod, routes = evidence_orchestrator.detect_file_modality("photo.jpg", "image/jpeg")
    assert mod == "IMAGE"
    assert "Dual-Engine OCR Extraction" in routes
    assert "Perceptual Fingerprinting (pHash/dHash)" in routes

    mod_png, _ = evidence_orchestrator.detect_file_modality("evidence.png", "image/png")
    assert mod_png == "IMAGE"

    # Videos
    mod_vid, v_routes = evidence_orchestrator.detect_file_modality("clip.mp4", "video/mp4")
    assert mod_vid == "VIDEO"
    assert "Boundary Keyframe Sampling" in v_routes
    assert "CTranslate2 Whisper Speech Transcription" in v_routes

    # Audio
    mod_aud, a_routes = evidence_orchestrator.detect_file_modality("dispatch.wav", "audio/wav")
    assert mod_aud == "AUDIO"
    assert "CTranslate2 Whisper Speech Transcription" in a_routes

    # Text document
    mod_txt, t_routes = evidence_orchestrator.detect_file_modality("statement.txt", "text/plain")
    assert mod_txt == "TEXT"
    assert "Multilingual Factual Claim Extraction" in t_routes

    # Unsupported format
    mod_unsupp, unsupp_routes = evidence_orchestrator.detect_file_modality("payload.exe", "application/x-msdownload")
    assert mod_unsupp == "UNSUPPORTED"
    assert len(unsupp_routes) == 0


@pytest.mark.asyncio
async def test_single_file_orchestrated_intake(db_session: AsyncSession, async_client: AsyncClient):
    """Verify single file ingestion via unified orchestrator endpoint."""
    inv = Investigation(title="Single File Intake Test", priority="HIGH")
    db_session.add(inv)
    await db_session.commit()

    png_bytes = make_test_png()
    files = [("files", ("scene.png", io.BytesIO(png_bytes), "image/png"))]
    data = {
        "caption": "Flooded roadway",
        "claimed_location": "Hyderabad",
        "claimed_date": "2026-11-13"
    }

    resp = await async_client.post(f"/api/v1/investigations/{inv.id}/evidence/intake", files=files, data=data)
    assert resp.status_code == 201
    payload = resp.json()

    assert payload["investigation_id"] == inv.id
    assert payload["total_items_received"] == 1
    assert payload["accepted_items_count"] == 1
    assert payload["rejected_items_count"] == 0
    assert len(payload["items"]) == 1

    item = payload["items"][0]
    assert item["item_type"] == "FILE"
    assert item["detected_modality"] == "IMAGE"
    assert item["status"] == "QUEUED"
    assert len(item["sha256_hash"]) == 64
    assert "Dual-Engine OCR Extraction" in item["assigned_routes"]


@pytest.mark.asyncio
async def test_multiple_mixed_files_batch_intake(db_session: AsyncSession, async_client: AsyncClient):
    """Verify batch ingestion of multiple heterogeneous media files (image, audio, video)."""
    inv = Investigation(title="Multi-File Batch Test", priority="HIGH")
    db_session.add(inv)
    await db_session.commit()

    png_bytes = make_test_png(color=(80, 150, 40))
    wav_bytes = make_test_wav()
    mp4_bytes = make_test_mp4()

    files = [
        ("files", ("overview.png", io.BytesIO(png_bytes), "image/png")),
        ("files", ("intercept.wav", io.BytesIO(wav_bytes), "audio/wav")),
        ("files", ("footage.mp4", io.BytesIO(mp4_bytes), "video/mp4")),
    ]
    data = {
        "caption": "Incident multi-angle evidence package",
        "claimed_location": "Secunderabad",
        "claimed_event": "Flash Flooding"
    }

    resp = await async_client.post(f"/api/v1/investigations/{inv.id}/evidence/intake", files=files, data=data)
    assert resp.status_code == 201
    payload = resp.json()

    assert payload["total_items_received"] == 3
    assert payload["accepted_items_count"] == 3
    assert payload["rejected_items_count"] == 0
    assert len(payload["items"]) == 3

    modalities = {item["detected_modality"] for item in payload["items"]}
    assert modalities == {"IMAGE", "AUDIO", "VIDEO"}

    # Verify all submissions persist in database with investigation linkage
    res = await db_session.execute(
        select(EvidenceSubmission).where(EvidenceSubmission.investigation_id == inv.id)
    )
    submissions = res.scalars().all()
    assert len(submissions) == 3


@pytest.mark.asyncio
async def test_mixed_modalities_package_files_text_and_url(db_session: AsyncSession, async_client: AsyncClient):
    """Verify submitting files, text claims, and an external URL together in one unified package."""
    inv = Investigation(title="Mixed Modalities Unified Package", priority="URGENT")
    db_session.add(inv)
    await db_session.commit()

    png_bytes = make_test_png()
    files = [("files", ("suspect_image.png", io.BytesIO(png_bytes), "image/png"))]
    data = {
        "raw_text": "Massive dam collapse reported after unseasonal rainstorms",
        "source_url": "https://example-news.org/breaking/dam-incident-report",
        "caption": "Multi-vector breaking incident claim",
        "claimed_date": "2026-11-13",
        "claimed_location": "Telangana"
    }

    resp = await async_client.post(f"/api/v1/investigations/{inv.id}/evidence/intake", files=files, data=data)
    assert resp.status_code == 201
    payload = resp.json()

    assert payload["total_items_received"] == 3
    assert payload["accepted_items_count"] == 3
    assert payload["rejected_items_count"] == 0

    item_types = [it["item_type"] for it in payload["items"]]
    assert "FILE" in item_types
    assert "TEXT" in item_types
    assert "URL" in item_types

    # Verify text item details
    text_item = next(it for it in payload["items"] if it["item_type"] == "TEXT")
    assert text_item["detected_modality"] == "TEXT"
    assert "Massive dam collapse" in text_item["filename_or_snippet"]

    # Verify url item details
    url_item = next(it for it in payload["items"] if it["item_type"] == "URL")
    assert url_item["detected_modality"] == "URL"
    assert url_item["filename_or_snippet"] == "https://example-news.org/breaking/dam-incident-report"


@pytest.mark.asyncio
async def test_fault_isolation_unsupported_and_corrupt_files(db_session: AsyncSession, async_client: AsyncClient):
    """
    Verify fault isolation: a batch containing valid evidence alongside zero-byte
    and unsupported files accepts the valid evidence and isolates the failures.
    """
    inv = Investigation(title="Fault Isolation Batch Test", priority="MEDIUM")
    db_session.add(inv)
    await db_session.commit()

    valid_png = make_test_png()
    empty_bytes = b""
    unsupported_bytes = b"MZ\x90\x00\x03\x00\x00\x00"

    files = [
        ("files", ("valid_scene.png", io.BytesIO(valid_png), "image/png")),
        ("files", ("corrupt_zero.jpg", io.BytesIO(empty_bytes), "image/jpeg")),
        ("files", ("binary_tool.exe", io.BytesIO(unsupported_bytes), "application/x-msdownload")),
    ]

    resp = await async_client.post(f"/api/v1/investigations/{inv.id}/evidence/intake", files=files)
    assert resp.status_code == 201
    payload = resp.json()

    assert payload["total_items_received"] == 3
    assert payload["accepted_items_count"] == 1
    assert payload["rejected_items_count"] == 2

    valid_item = next(it for it in payload["items"] if it["filename_or_snippet"] == "valid_scene.png")
    assert valid_item["status"] == "QUEUED"
    assert valid_item["submission_id"] is not None

    zero_item = next(it for it in payload["items"] if it["filename_or_snippet"] == "corrupt_zero.jpg")
    assert zero_item["status"] == "FAILED"
    assert "0 bytes" in zero_item["error_message"]

    unsupp_item = next(it for it in payload["items"] if it["filename_or_snippet"] == "binary_tool.exe")
    assert unsupp_item["status"] == "UNSUPPORTED"
    assert "Unsupported file format" in unsupp_item["error_message"]


@pytest.mark.asyncio
async def test_empty_intake_rejected_400(db_session: AsyncSession, async_client: AsyncClient):
    """Verify empty intake request with no files, no text, and no URL is cleanly rejected."""
    inv = Investigation(title="Empty Intake Rejection Test", priority="LOW")
    db_session.add(inv)
    await db_session.commit()

    resp = await async_client.post(f"/api/v1/investigations/{inv.id}/evidence/intake", data={})
    assert resp.status_code == 400
    assert "At least one media file, text claim, or source URL" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_non_existent_investigation_404(async_client: AsyncClient):
    """Verify intake targeted at unknown investigation returns 404."""
    resp = await async_client.post(
        "/api/v1/investigations/non-existent-case-id/evidence/intake",
        data={"raw_text": "Some claim"}
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_orchestrated_evidence_appears_in_investigation_report_and_lineage(
    db_session: AsyncSession,
    async_client: AsyncClient
):
    """Verify that evidence ingested via the orchestrator is immediately indexed in case reports and lineage."""
    inv = Investigation(title="Orchestrated Lineage Integration Case", priority="HIGH")
    db_session.add(inv)
    await db_session.commit()

    png_bytes = make_test_png()
    files = [("files", ("lin_scene.png", io.BytesIO(png_bytes), "image/png"))]
    data = {
        "raw_text": "Bridge structure collapsed following morning torrential deluge",
        "caption": "Viral post with photographic proof",
        "claimed_location": "Mumbai",
        "sync_process": "true"  # Execute pipeline synchronously for immediate verification
    }

    resp = await async_client.post(f"/api/v1/investigations/{inv.id}/evidence/intake", files=files, data=data)
    assert resp.status_code == 201

    # 1. Verify Investigation Report reflects both submissions
    rep_resp = await async_client.get(f"/api/v1/investigations/{inv.id}/report")
    assert rep_resp.status_code == 200
    rep_data = rep_resp.json()
    assert rep_data["metrics"]["submissions_count"] == 2
    assert rep_data["metrics"]["claims_count"] >= 1

    # 2. Verify Lineage Graph connects submissions and claims
    graph_resp = await async_client.get(f"/api/v1/investigations/{inv.id}/lineage/graph")
    assert graph_resp.status_code == 200
    graph_data = graph_resp.json()
    node_types = {n["entity_type"] for n in graph_data["nodes"]}
    assert "INVESTIGATION" in node_types
    assert "EVIDENCE_SUBMISSION" in node_types
    assert "CLAIM" in node_types
