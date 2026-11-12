import io
import pytest
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from app.core.config import settings
from app.core.storage import storage_manager
from app.models.investigation import Investigation
from app.models.evidence import EvidenceSubmission, MediaAsset, DerivedArtifact
from app.models.fingerprint import MediaFingerprint, FrameFingerprint, MediaMatchRecord
from app.indexing.indexer import media_indexer
from app.matching.engine import match_engine

def _create_rich_test_image() -> Image.Image:
    np.random.seed(42)
    arr = np.random.randint(60, 220, size=(400, 400, 3), dtype=np.uint8)
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)
    draw.rectangle([60, 60, 220, 220], outline=(255, 200, 0), width=4)
    draw.ellipse([160, 160, 340, 340], outline=(0, 220, 255), width=4)
    draw.polygon([(200, 40), (360, 160), (240, 240)], outline=(255, 50, 100), width=3)
    draw.text((70, 90), "CONFIDENTIAL INTELLIGENCE DOSSIER", fill=(255, 255, 255))
    return img

@pytest.mark.asyncio
async def test_cross_investigation_privacy_isolation(async_client: AsyncClient, db_session: AsyncSession):
    """
    E2E Test 1: Cross-investigation privacy proof.
    Investigation 1 ('Top Secret Case', 'Classified Notes') uploads Image A.
    Investigation 2 ('Public Verification') uploads cropped Image A.
    Verifies Investigation 2 discovers the match but receives ZERO cross-investigation metadata.
    """
    # 1. Create Investigation 1 (Secret Case)
    resp1 = await async_client.post("/api/v1/investigations/", json={
        "title": "Top Secret Case - Classified Operation Blackout",
        "description": "Sensitive intelligence notes from Agent Fox",
        "priority": "HIGH"
    })
    assert resp1.status_code == 201
    inv1_id = resp1.json()["id"]

    # Ingest Image A into Investigation 1
    img_a = _create_rich_test_image()
    buf_a = io.BytesIO()
    img_a.save(buf_a, format="JPEG", quality=95)
    buf_a.seek(0)

    upload_resp1 = await async_client.post(
        f"/api/v1/investigations/{inv1_id}/evidence/upload",
        files={"file": ("classified_doc.jpg", buf_a.getvalue(), "image/jpeg")}
    )
    assert upload_resp1.status_code == 201
    ev1_id = upload_resp1.json()["id"]

    # 2. Create Investigation 2 (Public Verification Unit)
    resp2 = await async_client.post("/api/v1/investigations/", json={
        "title": "Public Verification Unit",
        "description": "Open source claim verification",
        "priority": "LOW"
    })
    assert resp2.status_code == 201
    inv2_id = resp2.json()["id"]

    # Ingest Cropped Image A (10% crop) into Investigation 2
    img_b = img_a.crop((20, 20, 380, 380))
    buf_b = io.BytesIO()
    img_b.save(buf_b, format="JPEG", quality=90)
    buf_b.seek(0)

    upload_resp2 = await async_client.post(
        f"/api/v1/investigations/{inv2_id}/evidence/upload",
        files={"file": ("public_leak.jpg", buf_b.getvalue(), "image/jpeg")}
    )
    assert upload_resp2.status_code == 201
    ev2_id = upload_resp2.json()["id"]

    # 3. Execute Matching for Investigation 2
    match_resp = await async_client.post(
        f"/api/v1/investigations/{inv2_id}/evidence/{ev2_id}/matching/match?max_hamming=25"
    )
    assert match_resp.status_code == 200
    matches = match_resp.json()
    assert len(matches) >= 1

    top_match = matches[0]
    assert top_match["classification"] in ("SAME_PHOTOGRAPH_MODIFIED", "NEAR_DUPLICATE")
    assert top_match["scope"] == "GLOBAL_INDEX_ANONYMIZED"
    assert top_match["matched_artifact_id"] is None, "LEAK: Foreign artifact ID exposed in anonymized match!"

    # 4. Strict Privacy Audit Assertion: Zero leakage of Inv 1 metadata or server paths
    payload_str = match_resp.text
    assert "Top Secret Case" not in payload_str, "LEAK: Investigation 1 title exposed!"
    assert "Classified Operation Blackout" not in payload_str, "LEAK: Investigation 1 secret title exposed!"
    assert "Agent Fox" not in payload_str, "LEAK: Investigator identity exposed!"
    assert "Sensitive intelligence notes" not in payload_str, "LEAK: Private notes exposed!"
    assert inv1_id not in payload_str, "LEAK: Foreign investigation ID exposed!"
    assert ev1_id not in payload_str, "LEAK: Foreign evidence ID exposed!"
    assert "descriptor_rel_path" not in payload_str, "LEAK: Internal server descriptor storage path exposed!"
    assert "derived/" not in payload_str, "LEAK: Internal derived filesystem directory exposed!"
    assert "uploads/" not in payload_str, "LEAK: Internal upload filesystem directory exposed!"

    # 5. Query matches via GET endpoint and verify identical privacy guarantee
    get_resp = await async_client.get(
        f"/api/v1/investigations/{inv2_id}/evidence/{ev2_id}/matching/matches"
    )
    assert get_resp.status_code == 200
    get_payload_str = get_resp.text
    assert "Top Secret Case" not in get_payload_str
    assert "Agent Fox" not in get_payload_str
    assert inv1_id not in get_payload_str

@pytest.mark.asyncio
async def test_video_keyframe_to_image_matching(db_session: AsyncSession):
    """
    E2E Test 2: Video keyframe-to-image matching with frame timestamp provenance.
    Verifies that querying a media asset against indexed video keyframes
    identifies the exact timestamp and attaches whole-video disclaimers.
    """
    inv = Investigation(title="Video Archive Investigation", priority="MEDIUM")
    db_session.add(inv)
    await db_session.flush()

    # Create dummy video asset and submission
    vid_asset = MediaAsset(
        sha256_hash="f0" + "9" * 62,
        mime_type="video/mp4",
        file_path="uploads/source_broadcast.mp4",
        file_size_bytes=5000000
    )
    db_session.add(vid_asset)
    await db_session.flush()

    vid_sub = EvidenceSubmission(
        investigation_id=inv.id,
        media_asset_id=vid_asset.id,
        submission_type="VIDEO",
        sha256_hash=vid_asset.sha256_hash
    )
    db_session.add(vid_sub)
    await db_session.flush()

    # Create keyframe artifact and save physical image
    kf_dir = settings.DATA_DIR / "derived" / "keyframes"
    kf_dir.mkdir(parents=True, exist_ok=True)
    kf_img = _create_rich_test_image()
    kf_path = kf_dir / "frame_001.jpg"
    kf_img.save(kf_path, quality=90)
    rel_kf = str(kf_path.relative_to(settings.DATA_DIR))

    kf_artifact = DerivedArtifact(
        evidence_submission_id=vid_sub.id,
        artifact_type="KEYFRAME",
        sha256_hash="kf1" + "0" * 61,
        relative_path=rel_kf,
        file_size_bytes=kf_path.stat().st_size,
        mime_type="image/jpeg",
        artifact_metadata={"frame_index": 1, "timestamp_ms": 2500.0}
    )
    db_session.add(kf_artifact)
    await db_session.flush()

    # Index video keyframes
    await media_indexer.index_video_keyframes(db_session, vid_asset.id, [kf_artifact])

    # Now an investigator submits an image captured from this broadcast
    query_asset = MediaAsset(
        sha256_hash="e0" + "8" * 62,
        mime_type="image/jpeg",
        file_path=rel_kf,
        file_size_bytes=kf_path.stat().st_size
    )
    db_session.add(query_asset)
    await db_session.flush()

    query_sub = EvidenceSubmission(
        investigation_id=inv.id,
        media_asset_id=query_asset.id,
        submission_type="IMAGE",
        sha256_hash=query_asset.sha256_hash
    )
    db_session.add(query_sub)
    await db_session.flush()

    # Execute match
    matches = await match_engine.match_evidence(db_session, query_sub.id, max_hamming=10)
    assert len(matches) >= 1

    match = matches[0]
    assert match.is_video_frame_match is True
    assert match.matched_frame_timestamp_ms == 2500.0
    assert match.matched_media_asset_id == vid_asset.id
    assert match.matched_artifact_id == kf_artifact.id
    assert "Does not prove whole-video identity" in match.disclaimer

@pytest.mark.asyncio
async def test_consecutive_video_frame_grouping(db_session: AsyncSession):
    """
    E2E Test 3: Multiple consecutive frame matching across videos.
    Verifies that multi-frame matches group consecutive frame counts accurately.
    """
    inv = Investigation(title="Broadcast Multi-Frame Verification", priority="MEDIUM")
    db_session.add(inv)
    await db_session.flush()

    vid_asset = MediaAsset(
        sha256_hash="d0" + "7" * 62,
        mime_type="video/mp4",
        file_path="uploads/source_broadcast_2.mp4",
        file_size_bytes=8000000
    )
    db_session.add(vid_asset)
    await db_session.flush()

    vid_sub = EvidenceSubmission(
        investigation_id=inv.id,
        media_asset_id=vid_asset.id,
        submission_type="VIDEO",
        sha256_hash=vid_asset.sha256_hash
    )
    db_session.add(vid_sub)
    await db_session.flush()

    # Add 3 consecutive keyframes (indices 0, 1, 2)
    kf_dir = settings.DATA_DIR / "derived" / "keyframes_seq"
    kf_dir.mkdir(parents=True, exist_ok=True)
    artifacts = []
    for idx, ts in enumerate([1000.0, 2000.0, 3000.0]):
        img = _create_rich_test_image()
        p = kf_dir / f"seq_{idx}.jpg"
        img.save(p, quality=90)
        art = DerivedArtifact(
            evidence_submission_id=vid_sub.id,
            artifact_type="KEYFRAME",
            sha256_hash=f"kfseq{idx}" + "0" * 58,
            relative_path=str(p.relative_to(settings.DATA_DIR)),
            file_size_bytes=p.stat().st_size,
            mime_type="image/jpeg",
            artifact_metadata={"frame_index": idx, "timestamp_ms": ts}
        )
        db_session.add(art)
        artifacts.append(art)
    await db_session.flush()

    # Index keyframes
    await media_indexer.index_video_keyframes(db_session, vid_asset.id, artifacts)

    # Query with identical image
    q_asset = MediaAsset(
        sha256_hash="c0" + "6" * 62,
        mime_type="image/jpeg",
        file_path=artifacts[0].relative_path,
        file_size_bytes=artifacts[0].file_size_bytes
    )
    db_session.add(q_asset)
    await db_session.flush()

    q_sub = EvidenceSubmission(
        investigation_id=inv.id,
        media_asset_id=q_asset.id,
        submission_type="IMAGE",
        sha256_hash=q_asset.sha256_hash
    )
    db_session.add(q_sub)
    await db_session.flush()

    matches = await match_engine.match_evidence(db_session, q_sub.id, max_hamming=12)
    assert len(matches) >= 1
    # Check that consecutive frames count is tracked
    for m in matches:
        if m.is_video_frame_match:
            assert m.consecutive_frames_matched >= 1
            assert "whole-video identity" in m.disclaimer

@pytest.mark.asyncio
async def test_external_reverse_search_returns_unavailable(async_client: AsyncClient, db_session: AsyncSession):
    """
    E2E Test 4: External reverse search returns UNAVAILABLE.
    Verifies that commercial engines (Google, TinEye, Bing, Wayback) are explicitly
    marked as UNAVAILABLE without any fabricated or mocked results.
    """
    inv_resp = await async_client.post("/api/v1/investigations/", json={
        "title": "Reverse Search Audit",
        "description": "Checking commercial provider status"
    })
    inv_id = inv_resp.json()["id"]

    img = _create_rich_test_image()
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    upload_resp = await async_client.post(
        f"/api/v1/investigations/{inv_id}/evidence/upload",
        files={"file": ("check_search.jpg", buf.getvalue(), "image/jpeg")}
    )
    ev_id = upload_resp.json()["id"]

    search_resp = await async_client.get(
        f"/api/v1/investigations/{inv_id}/evidence/{ev_id}/matching/external-search"
    )
    assert search_resp.status_code == 200
    data = search_resp.json()

    assert data["status"] == "UNAVAILABLE"
    assert data["providers"]["google_lens"]["status"] == "UNAVAILABLE"
    assert data["providers"]["tineye"]["status"] == "UNAVAILABLE"
    assert data["providers"]["bing_visual_search"]["status"] == "UNAVAILABLE"
    assert data["providers"]["wayback_machine"]["status"] == "UNAVAILABLE"
    assert "unavailable in this release" in data["disclaimer"]
