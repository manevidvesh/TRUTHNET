import io
import pytest
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.storage import storage_manager
from app.models.investigation import Investigation
from app.models.evidence import EvidenceSubmission, MediaAsset
from app.models.fingerprint import MediaFingerprint, MediaMatchRecord
from app.indexing.indexer import media_indexer
from app.matching.engine import match_engine
from app.matching.candidate_retrieval import candidate_retrieval

def _create_textured_test_image(base_seed: int = 42) -> Image.Image:
    """Generates a rich, highly-textured image with shapes and text for ORB feature matching."""
    np.random.seed(base_seed)
    arr = np.random.randint(50, 200, size=(300, 300, 3), dtype=np.uint8)
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)
    # Draw geometric shapes and text
    draw.rectangle([40, 40, 160, 160], outline=(255, 255, 0), width=4)
    draw.ellipse([100, 100, 220, 220], outline=(0, 255, 255), width=4)
    draw.text((50, 50), "TRUTHNET EVIDENCE SIGNATURE 2026", fill=(255, 255, 255))
    return img

@pytest.mark.asyncio
async def test_exact_file_match_classification(db_session: AsyncSession):
    """
    Verifies that SHA-256 exact binary identity yields EXACT_FILE_MATCH.
    """
    img = _create_textured_test_image(100)
    img_dir = storage_manager.upload_dir / "ex"
    img_dir.mkdir(parents=True, exist_ok=True)
    img_path = img_dir / "exact1.jpg"
    img.save(img_path)

    rel_path = str(img_path.relative_to(storage_manager.upload_dir.parent))
    sha256 = "ex" + "1" * 62

    # Deduplicated MediaAsset
    asset = MediaAsset(sha256_hash=sha256, mime_type="image/jpeg", file_path=rel_path, file_size_bytes=100)
    db_session.add(asset)
    await db_session.flush()
    await media_indexer.index_media_asset(db_session, asset.id)

    # Submission 1 (Investigation 1)
    inv1 = Investigation(title="Investigation 1", priority="MEDIUM")
    db_session.add(inv1)
    await db_session.flush()

    sub1 = EvidenceSubmission(investigation_id=inv1.id, media_asset_id=asset.id, submission_type="IMAGE", sha256_hash=sha256)
    db_session.add(sub1)

    # Submission 2 (Investigation 2 - Reusing exact same MediaAsset)
    inv2 = Investigation(title="Investigation 2", priority="HIGH")
    db_session.add(inv2)
    await db_session.flush()

    sub2 = EvidenceSubmission(investigation_id=inv2.id, media_asset_id=asset.id, submission_type="IMAGE", sha256_hash=sha256)
    db_session.add(sub2)
    await db_session.commit()

    matches = await match_engine.match_evidence(db_session, sub2.id)
    assert len(matches) >= 1
    assert matches[0].classification == "EXACT_FILE_MATCH"
    assert "SHA256" in matches[0].method
    assert matches[0].raw_metrics["distance"] == 0

@pytest.mark.asyncio
async def test_same_photograph_modified_classification(db_session: AsyncSession):
    """
    Verifies that a 25% crop + 5 deg rotation of the same textured image is confirmed
    as SAME_PHOTOGRAPH_MODIFIED via RANSAC homography.
    """
    # 1. Base textured image (Historical Asset)
    base_img = _create_textured_test_image(200)
    img_dir = storage_manager.upload_dir / "sp"
    img_dir.mkdir(parents=True, exist_ok=True)
    base_path = img_dir / "base.jpg"
    base_img.save(base_path)

    rel_base = str(base_path.relative_to(storage_manager.upload_dir.parent))
    asset1 = MediaAsset(sha256_hash="sp" + "1" * 62, mime_type="image/jpeg", file_path=rel_base, file_size_bytes=base_path.stat().st_size)
    db_session.add(asset1)
    await db_session.flush()
    await media_indexer.index_media_asset(db_session, asset1.id)

    # 2. Transformed image: rotate 5 deg and crop
    transformed_img = base_img.rotate(5).crop((20, 20, 260, 260))
    trans_path = img_dir / "trans.jpg"
    transformed_img.save(trans_path)

    rel_trans = str(trans_path.relative_to(storage_manager.upload_dir.parent))
    asset2 = MediaAsset(sha256_hash="sp" + "2" * 62, mime_type="image/jpeg", file_path=rel_trans, file_size_bytes=trans_path.stat().st_size)
    db_session.add(asset2)
    await db_session.flush()
    await media_indexer.index_media_asset(db_session, asset2.id)

    inv = Investigation(title="RANSAC Homography Test", priority="HIGH")
    db_session.add(inv)
    await db_session.flush()

    sub = EvidenceSubmission(investigation_id=inv.id, media_asset_id=asset2.id, submission_type="IMAGE", sha256_hash=asset2.sha256_hash)
    db_session.add(sub)
    await db_session.commit()

    matches = await match_engine.match_evidence(db_session, sub.id, max_hamming=25)
    assert len(matches) >= 1
    match = next((m for m in matches if m.matched_media_asset_id == asset1.id), matches[0])
    assert match.classification == "SAME_PHOTOGRAPH_MODIFIED"
    assert match.raw_metrics["geometric_verification"]["is_geometric_match"] is True
    assert match.raw_metrics["geometric_verification"]["inlier_count"] >= 12
    assert "homography" in match.classification_rationale.lower()

@pytest.mark.asyncio
async def test_insufficient_features_textureless_image(db_session: AsyncSession):
    """
    Verifies that blank or low-texture images with < 10 keypoints are classified
    as INSUFFICIENT_MATCH_EVIDENCE rather than false positive or negative.
    """
    # Create solid white image (zero texture)
    blank_img = Image.new("RGB", (200, 200), (255, 255, 255))
    img_dir = storage_manager.upload_dir / "tf"
    img_dir.mkdir(parents=True, exist_ok=True)
    b_path = img_dir / "blank.jpg"
    blank_img.save(b_path)

    rel_b = str(b_path.relative_to(storage_manager.upload_dir.parent))
    asset = MediaAsset(sha256_hash="tf" + "1" * 62, mime_type="image/jpeg", file_path=rel_b, file_size_bytes=b_path.stat().st_size)
    db_session.add(asset)
    await db_session.flush()

    # Index it: keypoint count will be < 10
    fp = await media_indexer.index_media_asset(db_session, asset.id)
    assert fp.orb_keypoints_count < 10

    inv = Investigation(title="Textureless Test", priority="LOW")
    db_session.add(inv)
    await db_session.flush()
    sub = EvidenceSubmission(investigation_id=inv.id, media_asset_id=asset.id, submission_type="IMAGE")
    db_session.add(sub)
    await db_session.commit()

    # Create dummy candidate with similar hash to trigger candidate retrieval
    cand_asset = MediaAsset(sha256_hash="tf" + "2" * 62, mime_type="image/jpeg", file_path=rel_b, file_size_bytes=b_path.stat().st_size)
    db_session.add(cand_asset)
    await db_session.flush()

    cand_fp = MediaFingerprint(
        media_asset_id=cand_asset.id,
        sha256_hash=cand_asset.sha256_hash,
        phash_hex=fp.phash_hex,
        dhash_hex=fp.dhash_hex,
        orb_keypoints_count=0
    )
    db_session.add(cand_fp)
    await db_session.commit()

    matches = await match_engine.match_evidence(db_session, sub.id)
    assert len(matches) >= 1
    assert matches[0].classification == "INSUFFICIENT_MATCH_EVIDENCE"
    assert "fewer than 10 distinctive keypoints" in matches[0].classification_rationale

@pytest.mark.asyncio
async def test_no_local_match_found_with_bounded_disclaimer(db_session: AsyncSession):
    """
    Verifies that when no candidates pass Hamming threshold,
    NO_LOCAL_MATCH_FOUND is returned with explicit repository-bound disclaimer.
    """
    img_dir = storage_manager.upload_dir / "nl"
    img_dir.mkdir(parents=True, exist_ok=True)
    nl_path = img_dir / "unrelated.jpg"
    # Pure green image
    Image.new("RGB", (150, 150), (0, 255, 0)).save(nl_path)

    rel_nl = str(nl_path.relative_to(storage_manager.upload_dir.parent))
    asset = MediaAsset(sha256_hash="nl" + "1" * 62, mime_type="image/jpeg", file_path=rel_nl, file_size_bytes=nl_path.stat().st_size)
    db_session.add(asset)
    inv = Investigation(title="No Match Test", priority="LOW")
    db_session.add(inv)
    await db_session.flush()

    sub = EvidenceSubmission(investigation_id=inv.id, media_asset_id=asset.id, submission_type="IMAGE")
    db_session.add(sub)
    await db_session.commit()

    matches = await match_engine.match_evidence(db_session, sub.id, max_hamming=1)
    assert len(matches) == 1
    assert matches[0].classification == "NO_LOCAL_MATCH_FOUND"
    assert "search bounded to" in matches[0].disclaimer
    assert "does not constitute proof" in matches[0].disclaimer
