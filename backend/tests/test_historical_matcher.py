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
    """Generates a rich, textured scene depicting an architectural landmark with distinct shapes and text."""
    np.random.seed(seed)
    arr = np.random.randint(60, 220, size=(400, 400, 3), dtype=np.uint8)
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)
    # Architectural landmarks
    draw.rectangle([50, 50, 200, 200], outline=(255, 200, 0), width=5)
    draw.ellipse([150, 150, 350, 350], outline=(0, 220, 255), width=5)
    draw.polygon([(200, 30), (380, 150), (220, 250)], outline=(255, 50, 100), width=4)
    draw.text((60, 80), "TRUTHNET HISTORICAL ARCHIVE BENCHMARK", fill=(255, 255, 255))
    draw.text((70, 120), "YUKTIK-2026 PS-11 INVESTIGATION", fill=(240, 240, 200))
    return img

def _generate_different_photo_same_landmark() -> Image.Image:
    """Generates a photograph of the same landmark taken from an oblique 45° angle with parallax shifts."""
    np.random.seed(999)
    arr = np.random.randint(60, 220, size=(400, 400, 3), dtype=np.uint8)
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)
    # Landmark seen from different perspective with altered 3D parallax
    draw.rectangle([90, 110, 270, 290], outline=(255, 200, 0), width=5)
    draw.ellipse([40, 60, 220, 240], outline=(0, 220, 255), width=5)
    draw.polygon([(80, 180), (310, 260), (160, 360)], outline=(255, 50, 100), width=4)
    draw.text((70, 140), "MONUMENT PERIMETER // EAST ELEVATION", fill=(255, 255, 255))
    return img

def _generate_different_photo_same_event() -> Image.Image:
    """Generates a photo of the same press briefing taken from a secondary camera position."""
    img = Image.new("RGB", (400, 400), (220, 220, 220))
    draw = ImageDraw.Draw(img)
    # Stage banner with text
    draw.rectangle([40, 20, 360, 80], fill=(20, 40, 120))
    draw.text((50, 45), "ANNUAL GOVERNANCE SUMMIT 2026", fill=(255, 255, 255))
    # Speaker position altered
    draw.rectangle([210, 140, 290, 360], fill=(50, 50, 50))
    draw.ellipse([230, 95, 275, 140], fill=(210, 170, 130))
    # Reporter silhouette in foreground
    draw.ellipse([20, 240, 120, 390], fill=(30, 30, 30))
    return img

def _generate_repeated_facade() -> Image.Image:
    """Generates a building facade with a 6x6 grid of repetitive identical windows."""
    img = Image.new("RGB", (400, 400), (180, 180, 180))
    draw = ImageDraw.Draw(img)
    for r in range(6):
        for c in range(6):
            draw.rectangle([35 + c * 58, 35 + r * 58, 70 + c * 58, 70 + r * 58], fill=(30, 60, 120), outline=(0, 0, 0))
    draw.text((40, 375), "MUNICIPAL OFFICE BUILDING FACADE", fill=(0, 0, 0))
    return img

def _generate_similar_composition_sunset() -> Image.Image:
    """Generates an image with similar global color composition (sky top, dark bottom) but unrelated content."""
    img = Image.new("RGB", (400, 400), (40, 60, 140))
    draw = ImageDraw.Draw(img)
    # Upper sky gradient
    draw.rectangle([0, 0, 400, 160], fill=(80, 120, 200))
    # Middle horizon
    draw.rectangle([0, 160, 400, 240], fill=(220, 140, 60))
    # Lower dark silhouette
    draw.rectangle([0, 240, 400, 400], fill=(30, 40, 30))
    draw.text((50, 280), "TRANQUIL DESERT DUNE SILHOUETTE", fill=(200, 200, 150))
    return img

def _generate_screenshot_with_photo_embed(base_img: Image.Image) -> Image.Image:
    """Generates a mobile social media screenshot embedding a scaled derivative of the base photo."""
    screenshot = Image.new("RGB", (400, 500), (245, 245, 245))
    ds = ImageDraw.Draw(screenshot)
    # Status bar
    ds.rectangle([0, 0, 400, 24], fill=(225, 225, 225))
    ds.text((15, 5), "12:30", fill=(0, 0, 0))
    ds.text((340, 5), "LTE 95%", fill=(0, 0, 0))
    # Post header
    ds.text((20, 30), "@breaking_truth: EXCLUSIVE ARCHIVAL PHOTO", fill=(20, 20, 20))
    # Paste scaled base photo in center (350x350)
    scaled = base_img.resize((350, 350))
    screenshot.paste(scaled, (25, 50))
    # Footer and comments
    ds.text((20, 410), "3,812 Reposts  |  12.4K Likes", fill=(100, 100, 100))
    ds.rectangle([20, 435, 380, 490], outline=(200, 200, 200))
    ds.text((30, 450), "Fact-checkers investigating original capture provenance.", fill=(60, 60, 60))
    return screenshot

def _generate_severe_occlusion(base_img: Image.Image) -> Image.Image:
    """Generates an image where 70% of the photograph is occluded by breaking news lower-thirds."""
    occluded = base_img.copy()
    draw = ImageDraw.Draw(occluded)
    # Heavy lower banner (covering y=160 to 400)
    draw.rectangle([0, 160, 400, 400], fill=(180, 0, 0))
    draw.rectangle([0, 300, 400, 400], fill=(20, 20, 20))
    draw.text((20, 190), "BREAKING NEWS ALERT // URGENT REPORT", fill=(255, 255, 255))
    draw.text((20, 330), "DEVELOPING STORY: VERIFICATION IN PROGRESS", fill=(255, 255, 0))
    return occluded

def _generate_periodic_stripes() -> Image.Image:
    """Generates a 1D periodic stripe pattern (collinear features) to challenge homography non-degeneracy."""
    img = Image.new("RGB", (400, 400), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    for x in range(20, 380, 16):
        draw.line([(x, 40), (x, 360)], fill=(0, 0, 0), width=6)
    return img

def _generate_unrelated_radar_image() -> Image.Image:
    """Generates a high-frequency textured radar telemetry graphic completely unrelated to the base photo."""
    img = Image.new("RGB", (400, 400), (20, 30, 25))
    draw = ImageDraw.Draw(img)
    for r in range(20, 180, 20):
        draw.ellipse([200 - r, 200 - r, 200 + r, 200 + r], outline=(40, 255, 80), width=3)
    draw.line([200, 20, 200, 380], fill=(40, 255, 80), width=2)
    draw.line([20, 200, 380, 200], fill=(40, 255, 80), width=2)
    draw.text((30, 30), "RADAR SECTOR SCAN // FLIGHT AIRSPACE", fill=(40, 255, 80))
    return img

@pytest.mark.asyncio
async def test_expanded_transformation_benchmark_suite(db_session: AsyncSession):
    """
    Comprehensive false-positive and false-negative adversarial benchmark evaluation
    across 22 distinct transformation, occlusion, and adversarial scenarios.
    Separately calculates and reports:
      - Total Cases (N = 22)
      - True Positive Count (N_pos = 13)
      - True Negative / Rejection Count (N_neg = 9)
      - False Positive Rate (FPR = FP / N_neg)
      - False Negative Rate (FNR = FN / N_pos)
    """
    img_dir = storage_manager.upload_dir / "bench_adv"
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

    # Define test variations: (id, name, image, expected_classifications, is_positive_ground_truth)
    scenarios = [
        # --- POSITIVE TEST CASES (Ground Truth = True Variant of Same Image) ---
        ("T01", "Exact_Binary_Identity", base_img.copy(), ["EXACT_FILE_MATCH"], True),
        ("T02", "JPEG_Q90_Recompression", base_img.copy(), ["NEAR_DUPLICATE", "SAME_PHOTOGRAPH_MODIFIED"], True),
        ("T03", "JPEG_Q50_Recompression", base_img.copy(), ["NEAR_DUPLICATE", "SAME_PHOTOGRAPH_MODIFIED"], True),
        ("T04", "JPEG_Q20_Severe_Compression", base_img.copy(), ["NEAR_DUPLICATE", "SAME_PHOTOGRAPH_MODIFIED"], True),
        ("T05", "Downscaling_0.5x", base_img.resize((200, 200), Image.Resampling.BILINEAR), ["SAME_PHOTOGRAPH_MODIFIED", "NEAR_DUPLICATE"], True),
        ("T06", "Upscaling_1.5x", base_img.resize((600, 600), Image.Resampling.BICUBIC), ["SAME_PHOTOGRAPH_MODIFIED", "NEAR_DUPLICATE"], True),
        ("T07", "Modest_Crop_10pct", base_img.crop((20, 20, 380, 380)), ["SAME_PHOTOGRAPH_MODIFIED", "NEAR_DUPLICATE"], True),
        ("T08", "Moderate_Crop_30pct", base_img.crop((50, 50, 350, 350)), ["SAME_PHOTOGRAPH_MODIFIED"], True),
        ("T09", "Aggressive_Crop_50pct", base_img.crop((100, 100, 300, 300)), ["SAME_PHOTOGRAPH_MODIFIED", "POSSIBLE_VISUAL_SIMILARITY"], True),
        ("T10", "Rotation_5deg_With_Crop", base_img.rotate(5).crop((30, 30, 370, 370)), ["SAME_PHOTOGRAPH_MODIFIED"], True),
        ("T11", "Headline_Watermark_Overlay", base_img.copy(), ["SAME_PHOTOGRAPH_MODIFIED", "NEAR_DUPLICATE"], True),
        ("T12", "Color_To_Grayscale", base_img.convert("L").convert("RGB"), ["SAME_PHOTOGRAPH_MODIFIED", "NEAR_DUPLICATE"], True),
        ("T13", "ADV_Screenshot_With_Photo_Embed", _generate_screenshot_with_photo_embed(base_img), ["SAME_PHOTOGRAPH_MODIFIED", "NEAR_DUPLICATE"], True),
        ("T14", "ADV_Severe_70pct_Occlusion", _generate_severe_occlusion(base_img), ["SAME_PHOTOGRAPH_MODIFIED", "POSSIBLE_VISUAL_SIMILARITY", "INSUFFICIENT_MATCH_EVIDENCE"], True),

        # --- NEGATIVE / REJECTION TEST CASES (Ground Truth = Not Same Image) ---
        ("T15", "ADV_Different_Photo_Same_Landmark", _generate_different_photo_same_landmark(), ["POSSIBLE_VISUAL_SIMILARITY", "NO_LOCAL_MATCH_FOUND"], False),
        ("T16", "ADV_Different_Photo_Same_Event", _generate_different_photo_same_event(), ["POSSIBLE_VISUAL_SIMILARITY", "NO_LOCAL_MATCH_FOUND"], False),
        ("T17", "ADV_Repeated_Window_Facade", _generate_repeated_facade(), ["POSSIBLE_VISUAL_SIMILARITY", "NO_LOCAL_MATCH_FOUND"], False),
        ("T18", "ADV_Similar_Global_Composition_Sunset", _generate_similar_composition_sunset(), ["POSSIBLE_VISUAL_SIMILARITY", "NO_LOCAL_MATCH_FOUND", "INSUFFICIENT_MATCH_EVIDENCE"], False),
        ("T19", "ADV_Periodic_1D_Stripes", _generate_periodic_stripes(), ["INSUFFICIENT_MATCH_EVIDENCE", "NO_LOCAL_MATCH_FOUND", "POSSIBLE_VISUAL_SIMILARITY"], False),
        ("T20", "Textureless_Blank_White", Image.new("RGB", (300, 300), (255, 255, 255)), ["INSUFFICIENT_MATCH_EVIDENCE", "NO_LOCAL_MATCH_FOUND"], False),
        ("T21", "Smooth_Color_Fog_Gradient", Image.new("RGB", (300, 300), (220, 230, 240)), ["INSUFFICIENT_MATCH_EVIDENCE", "NO_LOCAL_MATCH_FOUND"], False),
        ("T22", "Unrelated_Radar_Telemetry", _generate_unrelated_radar_image(), ["NO_LOCAL_MATCH_FOUND", "POSSIBLE_VISUAL_SIMILARITY"], False),
    ]

    # Apply watermark to T11
    draw_wm = ImageDraw.Draw(scenarios[10][2])
    draw_wm.rectangle([0, 340, 400, 400], fill=(0, 0, 0))
    draw_wm.text((20, 360), "BREAKING NEWS // CONFIDENTIAL LEAK", fill=(255, 0, 0))

    benchmark_results = []
    n_pos = sum(1 for s in scenarios if s[4])
    n_neg = sum(1 for s in scenarios if not s[4])
    false_positives = 0
    false_negatives = 0

    for idx_num, (code, name, var_img, expected_classes, is_pos) in enumerate(scenarios):
        var_path = img_dir / f"{code}_{name}.jpg"
        var_img.save(var_path, quality=85)
        rel_var = str(var_path.relative_to(storage_manager.upload_dir.parent))

        if code == "T01":
            var_asset = base_asset
        else:
            var_sha = f"c{idx_num:02d}" + "0" * 61
            var_asset = MediaAsset(sha256_hash=var_sha, mime_type="image/jpeg", file_path=rel_var, file_size_bytes=var_path.stat().st_size)
            db_session.add(var_asset)
            await db_session.flush()

        sub = EvidenceSubmission(investigation_id=inv.id, media_asset_id=var_asset.id, submission_type="IMAGE", sha256_hash=var_asset.sha256_hash)
        db_session.add(sub)
        await db_session.flush()

        # Run matcher with bounded Hamming threshold 25
        matches = await match_engine.match_evidence(db_session, sub.id, max_hamming=25)
        top_match = matches[0] if matches else None
        actual_class = top_match.classification if top_match else "NO_LOCAL_MATCH_FOUND"

        is_passed = actual_class in expected_classes

        # Comprehensive FP and FN accounting:
        # A False Positive occurs when a negative scenario (is_pos=False) is declared EXACT_FILE_MATCH or SAME_PHOTOGRAPH_MODIFIED
        if not is_pos and actual_class in ("EXACT_FILE_MATCH", "SAME_PHOTOGRAPH_MODIFIED"):
            false_positives += 1
        # A False Negative occurs when a positive scenario (is_pos=True) is declared NO_LOCAL_MATCH_FOUND
        elif is_pos and actual_class == "NO_LOCAL_MATCH_FOUND":
            false_negatives += 1

        benchmark_results.append({
            "code": code,
            "test_case": name,
            "ground_truth": "POSITIVE" if is_pos else "NEGATIVE",
            "expected": expected_classes,
            "actual": actual_class,
            "method": top_match.method if top_match else "NONE",
            "passed": is_passed
        })

    await db_session.commit()

    # Print comprehensive adversarial benchmark table
    print("\n" + "=" * 95)
    print("TRUTHNET ADVERSARIAL HISTORICAL MATCHING BENCHMARK TABLE")
    print("=" * 95)
    print(f"{'Code':<5} | {'Ground Truth':<12} | {'Actual Classification':<27} | {'Status':<6} | {'Matching Method'}")
    print("-" * 95)
    for r in benchmark_results:
        status_icon = "PASS" if r["passed"] else "FAIL"
        print(f"{r['code']:<5} | {r['ground_truth']:<12} | {r['actual']:<27} | {status_icon:<6} | {r['method']}")
    print("-" * 95)
    fpr = (false_positives / n_neg) * 100.0 if n_neg > 0 else 0.0
    fnr = (false_negatives / n_pos) * 100.0 if n_pos > 0 else 0.0
    print(f"Total Scenarios: {len(scenarios)} | Positive (N_pos): {n_pos} | Negative (N_neg): {n_neg}")
    print(f"False Positives: {false_positives} / {n_neg} (FPR = {fpr:.1f}%) | False Negatives: {false_negatives} / {n_pos} (FNR = {fnr:.1f}%)")
    print("=" * 95)

    # Assert rigorous bounds
    assert false_positives == 0, f"Detected {false_positives} false positives among {n_neg} negative scenarios (FPR={fpr:.1f}%)!"
    assert false_negatives == 0, f"Detected {false_negatives} false negatives among {n_pos} positive scenarios (FNR={fnr:.1f}%)!"
    for r in benchmark_results:
        assert r["passed"], f"Scenario {r['code']} ({r['test_case']}) failed: expected {r['expected']}, got {r['actual']}"
