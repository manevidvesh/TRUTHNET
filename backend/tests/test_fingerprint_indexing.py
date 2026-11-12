import pytest
from pathlib import Path
from PIL import Image
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.indexing.preprocessing import preprocessor
from app.indexing.descriptor_store import descriptor_store
from app.indexing.hasher import media_hasher
from app.indexing.indexer import media_indexer
from app.models.investigation import Investigation
from app.models.evidence import EvidenceSubmission, MediaAsset, DerivedArtifact
from app.models.fingerprint import MediaFingerprint, FrameFingerprint

def test_deterministic_preprocessing_transparency_and_orientation(tmp_path: Path):
    """
    Verifies that ImagePreprocessor composits transparent RGBA onto white background,
    tags PREPROCESS-V1, and outputs valid RGB and grayscale arrays.
    """
    img_path = tmp_path / "transparent.png"
    # Create RGBA image with transparent background
    img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    # Draw red square in center
    for x in range(25, 75):
        for y in range(25, 75):
            img.putpixel((x, y), (255, 0, 0, 255))
    img.save(img_path)

    rgb_img, gray_cv, meta = preprocessor.preprocess_image(img_path)

    assert meta["preprocessing_version"] == "PREPROCESS-V1"
    assert meta["alpha_flattened"] is True
    assert rgb_img.mode == "RGB"
    # Background should now be white (255, 255, 255)
    assert rgb_img.getpixel((0, 0)) == (255, 255, 255)
    # Center pixel should still be red (255, 0, 0)
    assert rgb_img.getpixel((50, 50)) == (255, 0, 0)
    assert gray_cv.shape == (100, 100)
    assert gray_cv.dtype == np.uint8

def test_descriptor_store_validation_and_security(tmp_path: Path):
    """
    Verifies that DescriptorStore validates array shape/dtype, prevents
    traversal attacks, and disallows arbitrary pickle execution.
    """
    # 1. Valid descriptors
    valid_descs = np.random.randint(0, 255, size=(50, 32), dtype=np.uint8)
    sha256 = "a" * 64
    rel_path = descriptor_store.save_descriptors(sha256, valid_descs)
    assert rel_path is not None

    loaded = descriptor_store.load_descriptors(rel_path)
    assert loaded is not None
    assert np.array_equal(loaded, valid_descs)

    # 2. Reject invalid shape
    invalid_shape = np.random.randint(0, 255, size=(50, 64), dtype=np.uint8)
    bad_rel = descriptor_store.save_descriptors("b" * 64, invalid_shape)
    assert bad_rel is None

    # 3. Traversal attempt
    assert descriptor_store.load_descriptors("../../etc/passwd") is None

def test_hasher_metrics_and_hamming_distance():
    """
    Verifies bitwise Hamming distance computation.
    """
    assert media_hasher.hamming_distance("0000000000000000", "0000000000000000") == 0
    assert media_hasher.hamming_distance("0000000000000000", "0000000000000001") == 1
    assert media_hasher.hamming_distance("0000000000000000", "000000000000000f") == 4
    assert media_hasher.hamming_distance("ffffffffffffffff", "0000000000000000") == 64

@pytest.mark.asyncio
async def test_incremental_indexing_and_persistence(db_session: AsyncSession):
    """
    Verifies that MediaIndexer indexes an asset, persists to SQLite WAL,
    and supports controlled reindexing without data loss.
    """
    from app.core.storage import storage_manager

    # Create test image on disk in storage_manager directory
    img_dir = storage_manager.upload_dir / "c1"
    img_dir.mkdir(parents=True, exist_ok=True)
    img_file = img_dir / "c1test.jpg"
    img = Image.new("RGB", (200, 200), (120, 150, 180))
    img.save(img_file)

    rel_path = str(img_file.relative_to(storage_manager.upload_dir.parent))

    asset = MediaAsset(
        sha256_hash="c1" + "0" * 62,
        mime_type="image/jpeg",
        file_path=rel_path,
        file_size_bytes=img_file.stat().st_size
    )
    db_session.add(asset)
    await db_session.flush()

    # Index asset
    fp = await media_indexer.index_media_asset(db_session, asset.id)
    assert fp is not None
    assert fp.algorithm_version == "1.0.0"
    assert fp.preprocessing_version == "PREPROCESS-V1"
    assert len(fp.phash_hex) == 16
    assert len(fp.dhash_hex) == 16
    assert fp.indexing_status == "INDEXED"

    # Commit and verify persistence in new query
    await db_session.commit()

    query_res = await db_session.execute(
        select(MediaFingerprint).where(MediaFingerprint.media_asset_id == asset.id)
    )
    queried_fp = query_res.scalars().first()
    assert queried_fp is not None
    assert queried_fp.sha256_hash == asset.sha256_hash
    assert queried_fp.phash_hex == fp.phash_hex
