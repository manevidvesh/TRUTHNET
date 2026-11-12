import io
import pytest
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.storage import storage_manager
from app.models.investigation import Investigation
from app.models.evidence import EvidenceSubmission, MediaAsset
from app.indexing.indexer import media_indexer
from app.matching.engine import match_engine

def _generate_rich_scene(seed: int = 101) -> Image.Image:
    """Generates a rich, highly textured scene with distinct shapes, patterns, and text."""
    np.random.seed(seed)
    arr = np.random.randint(60, 220, size=(400, 400, 3), dtype=np.uint8)
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)
    # Draw geometric landmarks
    draw.rectangle([50, 50, 200, 200], outline=(255, 200, 0), width=5)
    draw.ellipse([150, 150, 350, 350], outline=(0, 220, 255), width=5)
    draw.polygon([(200, 30), (380, 150), (220, 250)], outline=(255, 50, 100), width=4)
    draw.text((60, 80), "TRUTHNET HISTORICAL ARCHIVE BENCHMARK", fill=(255, 255, 255))
    draw.text((70, 120), "YUKTIK-2026 PS-11 INVESTIGATION", fill=(240, 240, 200))
    return img

def _generate_different_photo_same_scene() -> Image.Image:
    """Generates a different photograph taken of the same general scene/event from a different vantage point."""
    np.random.seed(999)
    arr = np.random.randint(60, 220, size=(400, 400, 3), dtype=np.uint8)
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)
    # Different perspective / rearranged elements of the venue
    draw.rectangle([80, 120, 250, 300], outline=(255, 200, 0), width=5)
    draw.ellipse([50, 50, 200, 200], outline=(0, 220, 255), width=5)
    draw.polygon([(100, 200), (300, 280), (180, 380)], outline=(255, 50, 100), width=4)
    draw.text((80, 150), "EVENING PROCEEDINGS // PERSPECTIVE 2", fill=(255, 255, 255))
    return img

def _generate_unrelated_image() -> Image.Image:
    """Generates an unrelated, highly textured image (radar telemetry graphics) with high feature count."""
    img = Image.new("RGB", (400, 400), (30, 30, 30))
    draw = ImageDraw.Draw(img)
    for r in range(20, 180, 20):
        draw.ellipse([200 - r, 200 - r, 200 + r, 200 + r], outline=(50, 255, 50), width=3)
    draw.line([200, 20, 200, 380], fill=(50, 255, 50), width=2)
    draw.line([20, 200, 380, 200], fill=(50, 255, 50), width=2)
    draw.text((30, 30), "UNRELATED RADAR TELEMETRY DISPLAY", fill=(50, 255, 50))
    return img

@pytest.mark.asyncio
async def test_expanded_transformation_benchmark_suite(db_session: AsyncSession):
    """
    Comprehensive false-positive and false-negative benchmark evaluation across
    15 distinct transformation and variation scenarios.
    Reports and asserts false positives and false negatives separately.
    """
    img_dir = storage_manager.upload_dir / "bench"
    img_dir.mkdir(parents=True, exist_ok=True)

    # 1. Establish Historical Base Asset and Archival Submission
    archive_inv = Investigation(title="Historical Archive Case", priority="LOW")
    db_session.add(archive_inv)
    await db_session.flush()

    base_img = _generate_rich_scene(seed=101)
    base_path = img_dir / "base_monument.jpg"
    base_img.save(base_path, quality=95)
    rel_base = str(base_path.relative_to(storage_manager.upload_dir.parent))

    base_sha256 = "b0" + "1" * 62
    base_asset = MediaAsset(sha256_hash=base_sha256, mime_type="image/jpeg", file_path=rel_base, file_size_bytes=base_path.stat().st_size)
    db_session.add(base_asset)
    await db_session.flush()
    await media_indexer.index_media_asset(db_session, base_asset.id)

    archival_sub = EvidenceSubmission(
        investigation_id=archive_inv.id,
        media_asset_id=base_asset.id,
        submission_type="IMAGE",
        sha256_hash=base_asset.sha256_hash
    )
    db_session.add(archival_sub)
    await db_session.flush()

    inv = Investigation(title="Benchmark Investigation", priority="HIGH")
    db_session.add(inv)
    await db_session.flush()

    # Define test variations: (name, image, expected_classifications, is_positive_relative)
    transformations = [
        # True Positives (should match base asset)
        ("T01_Exact_Binary", base_img.copy(), ["EXACT_FILE_MATCH"], True),
        ("T02_JPEG_Q90", base_img.copy(), ["NEAR_DUPLICATE", "SAME_PHOTOGRAPH_MODIFIED"], True),
        ("T03_JPEG_Q50", base_img.copy(), ["NEAR_DUPLICATE", "SAME_PHOTOGRAPH_MODIFIED"], True),
        ("T04_JPEG_Q20", base_img.copy(), ["NEAR_DUPLICATE", "SAME_PHOTOGRAPH_MODIFIED"], True),
        ("T05_Resize_0.5x", base_img.resize((200, 200), Image.Resampling.BILINEAR), ["SAME_PHOTOGRAPH_MODIFIED", "NEAR_DUPLICATE"], True),
        ("T06_Resize_1.5x", base_img.resize((600, 600), Image.Resampling.BICUBIC), ["SAME_PHOTOGRAPH_MODIFIED", "NEAR_DUPLICATE"], True),
        ("T07_Crop_10pct", base_img.crop((20, 20, 380, 380)), ["SAME_PHOTOGRAPH_MODIFIED", "NEAR_DUPLICATE"], True),
        ("T08_Crop_30pct", base_img.crop((50, 50, 350, 350)), ["SAME_PHOTOGRAPH_MODIFIED"], True),
        ("T09_Crop_50pct", base_img.crop((100, 100, 300, 300)), ["SAME_PHOTOGRAPH_MODIFIED", "POSSIBLE_VISUAL_SIMILARITY"], True),
        ("T10_Rotate_5deg", base_img.rotate(5).crop((30, 30, 370, 370)), ["SAME_PHOTOGRAPH_MODIFIED"], True),
        ("T11_Text_Watermark", base_img.copy(), ["SAME_PHOTOGRAPH_MODIFIED", "NEAR_DUPLICATE"], True),
        ("T12_Grayscale", base_img.convert("L").convert("RGB"), ["SAME_PHOTOGRAPH_MODIFIED", "NEAR_DUPLICATE"], True),

        # True Negatives / Rejections (must NOT falsely classify as SAME_PHOTOGRAPH_MODIFIED)
        ("T13_Different_Photo_Same_Scene", _generate_different_photo_same_scene(), ["POSSIBLE_VISUAL_SIMILARITY", "NO_LOCAL_MATCH_FOUND"], False),
        ("T14_Textureless_Blank", Image.new("RGB", (300, 300), (255, 255, 255)), ["INSUFFICIENT_MATCH_EVIDENCE", "NO_LOCAL_MATCH_FOUND"], False),
        ("T15_Unrelated_Image", _generate_unrelated_image(), ["NO_LOCAL_MATCH_FOUND", "POSSIBLE_VISUAL_SIMILARITY"], False),
    ]

    # Apply watermark to T11
    draw_wm = ImageDraw.Draw(transformations[10][1])
    draw_wm.rectangle([0, 340, 400, 400], fill=(0, 0, 0))
    draw_wm.text((20, 360), "BREAKING NEWS // CONFIDENTIAL LEAK", fill=(255, 0, 0))

    benchmark_results = []
    false_positives = 0
    false_negatives = 0

    for i, (name, var_img, expected_classes, is_pos) in enumerate(transformations):
        var_path = img_dir / f"{name}.jpg"
        var_img.save(var_path, quality=85)
        rel_var = str(var_path.relative_to(storage_manager.upload_dir.parent))

        if name == "T01_Exact_Binary":
            var_asset = base_asset
        else:
            var_sha = f"b{i:02d}" + "0" * 61
            var_asset = MediaAsset(sha256_hash=var_sha, mime_type="image/jpeg", file_path=rel_var, file_size_bytes=var_path.stat().st_size)
            db_session.add(var_asset)
            await db_session.flush()

        sub = EvidenceSubmission(investigation_id=inv.id, media_asset_id=var_asset.id, submission_type="IMAGE", sha256_hash=var_asset.sha256_hash)
        db_session.add(sub)
        await db_session.flush()

        # Run matcher
        matches = await match_engine.match_evidence(db_session, sub.id, max_hamming=25)
        top_match = matches[0] if matches else None
        actual_class = top_match.classification if top_match else "NO_LOCAL_MATCH_FOUND"

        is_passed = actual_class in expected_classes

        # Count false positives and false negatives
        if not is_pos and actual_class in ("EXACT_FILE_MATCH", "SAME_PHOTOGRAPH_MODIFIED"):
            false_positives += 1
        elif is_pos and actual_class == "NO_LOCAL_MATCH_FOUND":
            false_negatives += 1

        benchmark_results.append({
            "test_case": name,
            "expected": expected_classes,
            "actual": actual_class,
            "method": top_match.method if top_match else "NONE",
            "passed": is_passed
        })

    await db_session.commit()

    # Print summary table in test logs
    print("\n--- BENCHMARK TRANSFORMATION EVALUATION TABLE ---")
    for r in benchmark_results:
        status_icon = "PASS" if r["passed"] else "FAIL"
        print(f"[{status_icon}] {r['test_case']}: Actual={r['actual']} (Expected={r['expected']}) | Method={r['method']}")
    print(f"Total False Positives: {false_positives} | Total False Negatives: {false_negatives}")

    assert false_positives == 0, f"Detected {false_positives} false positives in benchmark!"
    assert false_negatives == 0, f"Detected {false_negatives} false negatives in benchmark!"
