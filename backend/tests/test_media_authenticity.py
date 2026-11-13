"""
Unit & Integration Tests for Media Authenticity, Deepfake Model Registry & Forensics.

Verifies:
1. Model Registry catalog, hardware reflection, and dependency/checkpoint status tracking.
2. Epistemic truthfulness: never claiming inference executed when unavailable.
3. Execution of real CPU models (Spectral DCT classifier, Noise Residual Consistency).
4. Deterministic technical forensic measurements (ELA, 2D FFT/DCT power spectra, noise residuals).
5. Video frame sampling and cross-frame temporal consistency analysis.
6. Database persistence, active state tracking, and record versioning.
7. Authenticity REST APIs and HTML investigation report integration.
"""

import io
import tempfile
from pathlib import Path
import pytest
from PIL import Image
import numpy as np
import av
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.investigation import Investigation
from app.models.evidence import EvidenceSubmission, MediaAsset
from app.models.authenticity import MediaAuthenticityRecord
from app.authenticity.registry import model_registry, ModelStatus
from app.authenticity.forensics import TechnicalForensicsEngine
from app.authenticity.video_authenticity import video_authenticity_analyzer
from app.services.authenticity_service import authenticity_service
from app.core.config import settings


def create_test_image_bytes(w=128, h=128, color=(70, 130, 180)) -> bytes:
    img = Image.new("RGB", (w, h), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def create_test_video_bytes(num_frames=6, w=160, h=120) -> bytes:
    buf = io.BytesIO()
    container = av.open(buf, mode="w", format="mp4")
    stream = container.add_stream("mpeg4", rate=10)
    stream.width = w
    stream.height = h
    stream.pix_fmt = "yuv420p"
    for i in range(num_frames):
        arr = np.full((h, w, 3), fill_value=int(30 + i * 20), dtype=np.uint8)
        frame = av.VideoFrame.from_ndarray(arr, format="bgr24")
        for packet in stream.encode(frame):
            container.mux(packet)
    for packet in stream.encode():
        container.mux(packet)
    container.close()
    return buf.getvalue()


# ============================================================================
# 1. MODEL REGISTRY TESTS
# ============================================================================

def test_model_registry_inventory():
    """Verify registry catalog has expected models and explicit attributes."""
    models = model_registry.get_registered_models()
    assert len(models) >= 5

    model_ids = [m["model_id"] for m in models]
    assert "spectral_dct_classifier_v1" in model_ids
    assert "noise_residual_consistency_v1" in model_ids
    assert "mesonet4_facial_manipulation" in model_ids
    assert "xception_faceforensics" in model_ids
    assert "cnndetect_resnet50" in model_ids

    # Hardware runtime reflects host CPU
    hw = model_registry.hardware_info
    assert "platform" in hw
    assert "cpu_cores" in hw
    assert "onnxruntime_available" in hw


def test_model_registry_epistemic_truthfulness():
    """Verify registry never claims a model ran when it was only registered."""
    dummy_img = np.zeros((64, 64, 3), dtype=np.uint8)

    # 1. MesoNet: Checkpoint/Dependency unavailable
    meso_res = model_registry.execute_inference(
        model_id="mesonet4_facial_manipulation",
        image_np=dummy_img,
        mime_type="image/jpeg"
    )
    assert meso_res["status"] in (ModelStatus.MODEL_CHECKPOINT_UNAVAILABLE, ModelStatus.DEPENDENCY_UNAVAILABLE)

    # 2. XceptionNet: PyTorch dependency unavailable in host environment
    xcep_res = model_registry.execute_inference(
        model_id="xception_faceforensics",
        image_np=dummy_img,
        mime_type="image/jpeg"
    )
    assert xcep_res["status"] in (ModelStatus.DEPENDENCY_UNAVAILABLE, ModelStatus.MODEL_CHECKPOINT_UNAVAILABLE)

    # 3. Unsupported format
    unsupp_res = model_registry.execute_inference(
        model_id="spectral_dct_classifier_v1",
        image_np=dummy_img,
        mime_type="application/pdf"
    )
    assert unsupp_res["status"] == ModelStatus.UNSUPPORTED_INPUT


def test_spectral_dct_classifier_execution():
    """Verify real CPU execution of Spectral DCT Classifier."""
    # Synthetic image with smooth gradient
    x = np.linspace(0, 255, 128)
    y = np.linspace(0, 255, 128)
    xx, yy = np.meshgrid(x, y)
    grad = np.stack([xx, yy, (xx + yy) / 2], axis=-1).astype(np.uint8)

    res = model_registry.execute_inference(
        model_id="spectral_dct_classifier_v1",
        image_np=grad,
        mime_type="image/jpeg"
    )
    assert res["status"] == ModelStatus.INFERENCE_EXECUTED
    assert res["runtime_device"] == "cpu"
    assert "spectral_decay_slope" in res["raw_metrics"]
    assert "high_frequency_peak_metric" in res["raw_metrics"]
    assert isinstance(res["raw_metrics"]["spectral_decay_slope"], float)
    assert len(res["evaluation_limitations"]) > 0


def test_noise_residual_consistency_execution():
    """Verify real CPU execution of Noise Residual Consistency Model."""
    rng = np.random.RandomState(42)
    noise_img = rng.randint(0, 256, (128, 128, 3), dtype=np.uint8)

    res = model_registry.execute_inference(
        model_id="noise_residual_consistency_v1",
        image_np=noise_img,
        mime_type="image/png"
    )
    assert res["status"] == ModelStatus.INFERENCE_EXECUTED
    assert "channel_divergence_ratio" in res["raw_metrics"]
    assert res["raw_metrics"]["channel_divergence_ratio"] >= 1.0


# ============================================================================
# 2. TECHNICAL FORENSIC ENGINE TESTS
# ============================================================================

def test_technical_forensics_ela():
    """Verify Error Level Analysis returns real mathematical error metrics."""
    img = Image.new("RGB", (64, 64), color=(120, 40, 200))
    res = TechnicalForensicsEngine.compute_ela(img, quality=90)

    assert "mean_error" in res
    assert "max_error" in res
    assert "high_divergence_ratio" in res
    assert res["recompression_quality"] == 90
    assert isinstance(res["mean_error"], float)


def test_technical_forensics_noise_and_spectral():
    """Verify noise residuals and 2D FFT spectral decay."""
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    noise_res = TechnicalForensicsEngine.compute_noise_residuals(arr)
    assert "channel_divergence" in noise_res
    assert "channel_variances" in noise_res
    assert "r" in noise_res["channel_variances"]

    spec_res = TechnicalForensicsEngine.compute_spectral_decay(arr)
    assert "decay_slope" in spec_res
    assert "high_freq_peak_ratio" in spec_res


def test_technical_forensics_full_image():
    """Verify complete image forensics pipeline on disk file."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
        img_p = Path(tf.name)
    try:
        img_p.write_bytes(create_test_image_bytes(96, 96))
        analysis = TechnicalForensicsEngine.analyze_image_forensics(img_p)

        assert "ela_analysis" in analysis
        assert "noise_analysis" in analysis
        assert "spectral_analysis" in analysis
        assert "metadata_anomalies" in analysis
        assert "forensic_summary" in analysis
        assert "epistemic_disclaimer" in analysis
    finally:
        img_p.unlink(missing_ok=True)


# ============================================================================
# 3. VIDEO AUTHENTICITY TESTS
# ============================================================================

def test_video_authenticity_analyzer():
    """Verify video authenticity analysis across keyframes and temporal consistency."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tf:
        vid_p = Path(tf.name)
    try:
        vid_p.write_bytes(create_test_video_bytes(num_frames=6))
        res = video_authenticity_analyzer.analyze_video(
            video_path=vid_p,
            evidence_id="test_vid_ev_1",
            max_frames_to_analyze=4
        )

        assert "video_frame_analyses" in res
        assert "temporal_consistency" in res
        assert "epistemic_disclaimer" in res
        assert "whole-video authenticity" in res["epistemic_disclaimer"]

        # If frames were decoded
        if res["video_frame_analyses"]:
            f0 = res["video_frame_analyses"][0]
            assert "frame_index" in f0
            assert "timestamp_ms" in f0
            assert "ela_mean_error" in f0
            assert "spectral_decay_slope" in f0
    finally:
        vid_p.unlink(missing_ok=True)


# ============================================================================
# 4. DATABASE PERSISTENCE & VERSIONING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_authenticity_service_persistence_and_versioning(db_session: AsyncSession):
    """Verify service persists MediaAuthenticityRecord and manages active versions."""
    inv = Investigation(title="Case Auth Test", description="Testing authenticity persistence")
    db_session.add(inv)
    await db_session.flush()

    # Save a test file under data/uploads/
    upload_dir = settings.BASE_DIR / "data" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    fpath = upload_dir / "test_auth_img.jpg"
    fpath.write_bytes(create_test_image_bytes(64, 64))

    asset = MediaAsset(
        file_path="uploads/test_auth_img.jpg",
        file_size_bytes=fpath.stat().st_size,
        mime_type="image/jpeg",
        sha256_hash="dummy_sha256_auth"
    )
    db_session.add(asset)
    await db_session.flush()

    sub = EvidenceSubmission(
        investigation_id=inv.id,
        submission_type="IMAGE",
        original_filename="test_auth_img.jpg",
        media_asset_id=asset.id,
        processing_status="COMPLETED"
    )
    db_session.add(sub)
    await db_session.commit()

    # 1. First analysis: should create version 1
    rec1 = await authenticity_service.analyze_submission(db_session, sub.id)
    assert rec1 is not None
    assert rec1.version == 1
    assert rec1.is_active is True
    assert rec1.evidence_submission_id == sub.id
    assert len(rec1.executed_model_results) >= 2
    assert len(rec1.unavailable_models) >= 2

    # 2. Re-analysis: should create version 2 and deactivate version 1
    rec2 = await authenticity_service.analyze_submission(db_session, sub.id)
    assert rec2 is not None
    assert rec2.version == 2
    assert rec2.is_active is True

    # Check that rec1 is now inactive
    prior = await db_session.execute(
        select(MediaAuthenticityRecord).where(MediaAuthenticityRecord.id == rec1.id)
    )
    old_rec = prior.scalars().first()
    assert old_rec.is_active is False

    # Fetch active record via helper
    active_rec = await authenticity_service.get_active_record(db_session, sub.id)
    assert active_rec.id == rec2.id


# ============================================================================
# 5. REST API TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_authenticity_rest_endpoints(async_client: AsyncClient, db_session: AsyncSession):
    """Verify REST endpoints for model registry catalog, evidence authenticity, and reanalysis."""
    # 1. Model Catalog
    res_models = await async_client.get("/api/v1/authenticity/models")
    assert res_models.status_code == 200
    data_models = res_models.json()
    assert data_models["total_registered"] >= 5
    assert data_models["total_executable"] >= 2
    assert len(data_models["models"]) >= 5

    # 2. Setup investigation and submission
    inv_res = await async_client.post("/api/v1/investigations/", json={"title": "REST Auth Investigation"})
    assert inv_res.status_code == 201
    inv_id = inv_res.json()["id"]

    # Intake image
    img_bytes = create_test_image_bytes(64, 64)
    files = {"files": ("auth_evidence.jpg", img_bytes, "image/jpeg")}
    data = {"sync_process": "true", "claimed_location": "Hyderabad"}
    intake_res = await async_client.post(f"/api/v1/investigations/{inv_id}/evidence/intake", files=files, data=data)
    assert intake_res.status_code == 201
    items = intake_res.json()["items"]
    assert len(items) > 0
    ev_id = items[0]["submission_id"]

    # 3. Retrieve evidence authenticity
    auth_res = await async_client.get(f"/api/v1/investigations/{inv_id}/evidence/{ev_id}/authenticity")
    assert auth_res.status_code == 200
    auth_data = auth_res.json()
    assert auth_data["evidence_submission_id"] == ev_id
    assert auth_data["version"] >= 1
    assert "ela_analysis" in auth_data["forensic_analysis"]
    assert len(auth_data["executed_model_results"]) >= 2

    # 4. Reanalyze evidence authenticity
    re_res = await async_client.post(f"/api/v1/investigations/{inv_id}/evidence/{ev_id}/authenticity/reanalyze")
    assert re_res.status_code == 200
    re_data = re_res.json()
    assert re_data["version"] == auth_data["version"] + 1

    # 5. List investigation authenticity records
    list_res = await async_client.get(f"/api/v1/investigations/{inv_id}/authenticity")
    assert list_res.status_code == 200
    all_recs = list_res.json()
    assert len(all_recs) >= 1

    # 6. Investigation Report includes authenticity records
    rep_res = await async_client.get(f"/api/v1/investigations/{inv_id}/report")
    assert rep_res.status_code == 200
    rep_data = rep_res.json()
    assert "authenticity_records" in rep_data
    assert len(rep_data["authenticity_records"]) >= 1

    # 7. HTML Report includes Media Authenticity section
    html_res = await async_client.get(f"/api/v1/investigations/{inv_id}/report?format=html")
    assert html_res.status_code == 200
    assert "Media Authenticity & Deepfake Forensic Analysis" in html_res.text
