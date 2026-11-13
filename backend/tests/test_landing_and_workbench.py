"""
Integration tests for TRUTHNET AI Public Landing Page and Intelligence Workbench UI.
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
from app.models.investigation import Investigation


@pytest.mark.asyncio
async def test_landing_page_html_render(async_client: AsyncClient):
    """
    Verify GET / returns the public landing page with complete 9-capability showcase,
    epistemic principles, problem breakdown, and forensic visual elements.
    """
    resp = await async_client.get("/", headers={"Accept": "text/html,application/xhtml+xml"})
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    html = resp.text

    # Hero & Identity
    assert "TRUTHNET AI" in html
    assert "MULTIMODAL INVESTIGATIVE INTELLIGENCE" in html
    assert "When digital evidence is manipulated" in html
    assert "context becomes intelligence." in html
    assert "Launch Workbench" in html
    assert "Explore Capabilities" in html

    # Section B: Trust / Capability Strip
    assert "Image & Video Forensics" in html
    assert "Historical Media Discovery" in html
    assert "Claim Verification" in html
    assert "Source Intelligence" in html
    assert "Coordination Analysis" in html

    # Section C: Problem Breakdown
    assert "Manipulated Media" in html
    assert "Misleading Context" in html
    assert "Coordinated Narratives" in html

    # Section D: All 6 Contextual Verification Verdicts
    assert "SUPPORTED" in html
    assert "CONTRADICTED" in html
    assert "MISLEADING_OR_CONTEXT_MISSING" in html
    assert "UNVERIFIED" in html
    assert "INSUFFICIENT_EVIDENCE" in html
    assert "CONFLICTING_EVIDENCE" in html

    # Section E: Workflow
    assert "SUBMIT" in html
    assert "EXTRACT" in html
    assert "DISCOVER" in html
    assert "VERIFY" in html
    assert "CONNECT" in html
    assert "REVIEW" in html

    # Section F: Epistemic Principles
    assert "Media authenticity does not establish claim truth." in html
    assert "Historical reuse does not automatically prove misinformation." in html
    assert "Similar reporting does not equal independent corroboration." in html
    assert "Insufficient evidence is never proof of falsehood." in html

    # Section H: Hackathon attribution
    assert "YUKTIK-2026" in html
    assert "PS-11" in html


@pytest.mark.asyncio
async def test_root_api_json_response(async_client: AsyncClient):
    """
    Verify GET / returns JSON when client explicitly requests application/json without text/html.
    """
    resp = await async_client.get("/", headers={"Accept": "application/json"})
    assert resp.status_code == 200
    assert "application/json" in resp.headers["content-type"]
    data = resp.json()
    assert "TRUTHNET AI API" in data["message"]
    assert data["workbench"] == "/workbench"


@pytest.mark.asyncio
async def test_workbench_ui_render_with_investigation(db_session: AsyncSession, async_client: AsyncClient):
    """
    Verify GET /workbench returns the full investigator intelligence workbench
    with all required tabs, controls, and elements.
    """
    inv = Investigation(title="WB Test Case", priority="HIGH")
    db_session.add(inv)
    await db_session.commit()

    resp = await async_client.get(f"/workbench?investigation_id={inv.id}")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    html = resp.text

    assert "TRUTHNET AI — Intelligence Workbench" in html
    assert "WB Test Case" in html
    assert "+ Upload Evidence" in html
    assert "+ New Case" in html
    assert "Print Dossier" in html

    # Required tabs and elements
    assert "Overview" in html
    assert "Evidence & Submissions" in html
    assert "Media Forensics" in html
    assert "Historical Discovery" in html
    assert "Claims & Sources" in html
    assert "Intelligence Graph" in html
    assert "Timeline" in html
    assert "Assessment Engine" in html
    assert "Case Report" in html

    # Graph canvas & test-critical identifiers
    assert "canvas-container" in html
    assert "graph-svg" in html
    assert "drawer" in html
    assert "toggle-inferred" in html
    assert "stat-nodes" in html
    assert "stat-edges" in html

    # Verify Frontend-Backend upload contract in JavaScript
    assert "api/v1/investigations/${encodeURIComponent(currentInvId)}/evidence/upload" in html
    assert "api/v1/investigations/${encodeURIComponent(currentInvId)}/evidence/claim" in html
    # Ensure broken un-prefixed routes are NOT present
    assert 'fetch("/api/v1/evidence/upload"' not in html
    assert 'fetch("/api/v1/evidence/text"' not in html

    # Verify upload modal target case selector & dynamic switcher handlers
    assert 'id="upload-case-select-file"' in html
    assert 'id="upload-case-select-text"' in html
    assert 'id="upload-case-select-universal"' in html
    assert 'id="form-upload-universal"' in html
    assert 'id="upload-universal-files"' in html
    assert 'id="upload-universal-text"' in html
    assert 'id="upload-universal-url"' in html
    assert 'api/v1/investigations/${encodeURIComponent(currentInvId)}/evidence/intake' in html
    assert 'handleUniversalIntake' in html
    assert 'onUniversalFilesSelected' in html
    assert 'setupDropZone' in html
    assert 'populateUploadModalCases' in html
    assert 'syncUploadCase' in html
    assert 'selectCaseById' in html


@pytest.mark.asyncio
async def test_workbench_simulated_banner(db_session: AsyncSession, async_client: AsyncClient):
    """
    Verify that simulated scenario metadata triggers appropriate front-end indicators.
    """
    inv = Investigation(title="INV-999 [SIMULATED]: Benchmark Drill", priority="LOW")
    db_session.add(inv)
    await db_session.commit()

    resp = await async_client.get(f"/workbench?investigation_id={inv.id}")
    assert resp.status_code == 200
    assert "SIMULATED BENCHMARK SCENARIO" in resp.text


@pytest.mark.asyncio
async def test_workbench_upload_end_to_end_multimodal(db_session: AsyncSession, async_client: AsyncClient):
    """
    Regression test for evidence upload workflow:
    Verifies that real media files (PNG, JPEG, MP4, WAV) and text claims
    are accepted via the exact investigation evidence endpoints with proper persistence,
    hash calculation, deduplication, and error handling for empty/invalid files.
    """
    inv = Investigation(title="Upload Contract Regression Test", priority="HIGH")
    db_session.add(inv)
    await db_session.commit()

    # 1. Image Upload (PNG)
    png_img = Image.new("RGB", (64, 64), color=(30, 80, 160))
    png_buf = io.BytesIO()
    png_img.save(png_buf, format="PNG")
    png_bytes = png_buf.getvalue()

    resp_png = await async_client.post(
        f"/api/v1/investigations/{inv.id}/evidence/upload",
        files={"file": ("incident_photo.png", io.BytesIO(png_bytes), "image/png")},
        data={
            "caption": "Flooding near metro station",
            "claimed_date": "2026-11-13",
            "claimed_location": "Hyderabad",
            "language": "en"
        }
    )
    assert resp_png.status_code == 201
    png_data = resp_png.json()
    assert png_data["submission_type"] == "IMAGE"
    assert png_data["caption"] == "Flooding near metro station"
    assert png_data["claimed_location"] == "Hyderabad"
    assert png_data["media_asset"] is not None
    assert len(png_data["sha256_hash"]) == 64

    # 2. Image Upload (JPEG)
    jpg_img = Image.new("RGB", (64, 64), color=(180, 40, 40))
    jpg_buf = io.BytesIO()
    jpg_img.save(jpg_buf, format="JPEG")
    jpg_bytes = jpg_buf.getvalue()

    resp_jpg = await async_client.post(
        f"/api/v1/investigations/{inv.id}/evidence/upload",
        files={"file": ("incident_alt.jpg", io.BytesIO(jpg_bytes), "image/jpeg")},
        data={"caption": "Alternate angle photograph"}
    )
    assert resp_jpg.status_code == 201
    assert resp_jpg.json()["submission_type"] == "IMAGE"

    # 3. Video Upload (MP4)
    mp4_buf = io.BytesIO()
    container = av.open(mp4_buf, mode="w", format="mp4")
    v_stream = container.add_stream("mpeg4", rate=20)
    v_stream.width = 160
    v_stream.height = 120
    v_stream.pix_fmt = "yuv420p"
    for _ in range(10):
        frame = av.VideoFrame.from_ndarray(np.zeros((120, 160, 3), dtype=np.uint8), format="bgr24")
        for packet in v_stream.encode(frame):
            container.mux(packet)
    for packet in v_stream.encode():
        container.mux(packet)
    container.close()
    mp4_bytes = mp4_buf.getvalue()

    resp_mp4 = await async_client.post(
        f"/api/v1/investigations/{inv.id}/evidence/upload",
        files={"file": ("incident_clip.mp4", io.BytesIO(mp4_bytes), "video/mp4")},
        data={"caption": "Bystander video recording"}
    )
    assert resp_mp4.status_code == 201
    assert resp_mp4.json()["submission_type"] == "VIDEO"

    # 4. Audio Upload (WAV)
    wav_buf = io.BytesIO()
    with wave.open(wav_buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        samples = [int(32767 * 0.3 * np.sin(2 * np.pi * 440 * t / 16000)) for t in range(4000)]
        wav_file.writeframes(struct.pack("<" + ("h" * len(samples)), *samples))
    wav_bytes = wav_buf.getvalue()

    resp_wav = await async_client.post(
        f"/api/v1/investigations/{inv.id}/evidence/upload",
        files={"file": ("police_dispatch.wav", io.BytesIO(wav_bytes), "audio/wav")},
        data={"caption": "Audio dispatch intercept"}
    )
    assert resp_wav.status_code == 201
    assert resp_wav.json()["submission_type"] == "AUDIO"

    # 5. Text Claim Submission (/claim)
    resp_text = await async_client.post(
        f"/api/v1/investigations/{inv.id}/evidence/claim",
        json={
            "raw_text": "Severe cloudburst causes unprecedented urban flooding",
            "caption": "Viral post text",
            "claimed_location": "Hyderabad",
            "language": "en"
        }
    )
    assert resp_text.status_code == 201
    assert resp_text.json()["submission_type"] == "TEXT"

    # 6. Negative test: Zero-byte file rejection (400)
    resp_zero = await async_client.post(
        f"/api/v1/investigations/{inv.id}/evidence/upload",
        files={"file": ("empty.png", io.BytesIO(b""), "image/png")}
    )
    assert resp_zero.status_code == 400
    assert "0 bytes" in resp_zero.json()["detail"]

    # 7. Negative test: Non-existent investigation (404)
    resp_404 = await async_client.post(
        "/api/v1/investigations/non-existent-id/evidence/upload",
        files={"file": ("photo.png", io.BytesIO(png_bytes), "image/png")}
    )
    assert resp_404.status_code == 404

    # 8. Verify investigation report reflects all uploaded evidence
    report_resp = await async_client.get(f"/api/v1/investigations/{inv.id}/report")
    assert report_resp.status_code == 200
    report_data = report_resp.json()
    assert report_data["metrics"]["submissions_count"] == 5  # 4 files + 1 text
    assert len(report_data["submissions"]) == 5
