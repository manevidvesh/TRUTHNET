import pytest
from pathlib import Path
from PIL import Image
from PIL.TiffImagePlugin import IFDRational
import av
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.extractors.metadata import ImageMetadataExtractor, VideoMetadataExtractor, AudioMetadataExtractor
from app.models.investigation import Investigation
from app.models.evidence import EvidenceSubmission, ExtractionRecord, DerivedArtifact
from app.core.storage import storage_manager

@pytest.mark.asyncio
async def test_image_metadata_extraction_with_exif_and_timezone_discipline(tmp_path: Path):
    """
    Verifies raw EXIF is preserved, normalized values are recorded,
    and timestamps without explicit timezone offsets are flagged with timezone_detected=False.
    """
    img_path = tmp_path / "test_exif.jpg"
    img = Image.new("RGB", (640, 480), color=(100, 150, 200))
    
    # Construct EXIF with DateTimeOriginal (no offset)
    exif = img.getexif()
    exif[0x010F] = "Nikon"           # Make
    exif[0x0110] = "D850"            # Model
    exif[0x9003] = "2024:05:12 14:30:00"  # DateTimeOriginal
    img.save(img_path, exif=exif)

    metadata = ImageMetadataExtractor.extract(img_path)

    assert metadata["category"] == "OBSERVED_DATA"
    assert metadata["dimensions"] == {"width": 640, "height": 480}
    assert metadata["normalized_exif"]["camera_make"] == "Nikon"
    assert metadata["normalized_exif"]["camera_model"] == "D850"
    assert metadata["normalized_exif"]["datetime_original_raw"] == "2024:05:12 14:30:00"

    # Timezone discipline check
    assert metadata["timezone_info"]["timezone_detected"] is False
    assert metadata["timezone_info"]["confidence"] == "UNSPECIFIED_LOCAL"
    assert "Do not assume UTC" in metadata["timezone_info"]["disclaimer"]

@pytest.mark.asyncio
async def test_image_metadata_gps_extraction(tmp_path: Path):
    """
    Verifies GPS IFD coordinates are decoded to decimal degrees with authenticity disclaimer.
    """
    img_path = tmp_path / "test_gps.jpg"
    img = Image.new("RGB", (320, 240), color=(200, 100, 50))
    
    exif = img.getexif()
    gps_ifd = {
        1: "N",
        2: (IFDRational(37, 1), IFDRational(46, 1), IFDRational(2974, 100)),
        3: "W",
        4: (IFDRational(122, 1), IFDRational(25, 1), IFDRational(984, 100))
    }
    exif[0x8825] = gps_ifd
    img.save(img_path, exif=exif)

    metadata = ImageMetadataExtractor.extract(img_path)
    assert metadata["gps"] is not None
    assert metadata["gps"]["status"] == "OBSERVED"
    assert 37.77 < metadata["gps"]["latitude"] < 37.78
    assert -122.42 < metadata["gps"]["longitude"] < -122.41
    assert "disclaimer" in metadata["gps"]

@pytest.mark.asyncio
async def test_video_metadata_extraction_with_and_without_audio(tmp_path: Path):
    """
    Verifies video metadata extractor detects resolution, fps, streams, and audio presence.
    """
    # 1. Video without audio
    v_no_audio = tmp_path / "silent.mp4"
    container = av.open(str(v_no_audio), mode="w", format="mp4")
    v_stream = container.add_stream("mpeg4", rate=30)
    v_stream.width = 320
    v_stream.height = 240
    v_stream.pix_fmt = "yuv420p"
    for frame_i in range(15):
        frame = av.VideoFrame(320, 240, "yuv420p")
        for packet in v_stream.encode(frame):
            container.mux(packet)
    for packet in v_stream.encode():
        container.mux(packet)
    container.close()

    meta_no_audio = VideoMetadataExtractor.extract(v_no_audio)
    assert meta_no_audio["category"] == "OBSERVED_DATA"
    assert meta_no_audio["has_audio"] is False
    assert meta_no_audio["audio_stream_count"] == 0
    assert len(meta_no_audio["video_streams"]) == 1
    assert meta_no_audio["video_streams"][0]["width"] == 320

    # 2. Video with audio
    v_with_audio = tmp_path / "with_audio.mp4"
    container = av.open(str(v_with_audio), mode="w", format="mp4")
    v_stream2 = container.add_stream("mpeg4", rate=30)
    v_stream2.width = 320
    v_stream2.height = 240
    v_stream2.pix_fmt = "yuv420p"
    a_stream = container.add_stream("aac", rate=44100, layout="mono")

    for frame_i in range(15):
        vframe = av.VideoFrame(320, 240, "yuv420p")
        for packet in v_stream2.encode(vframe):
            container.mux(packet)
    for packet in v_stream2.encode():
        container.mux(packet)

    # Encode at least one audio frame
    aframe = av.AudioFrame(format="fltp", layout="mono", samples=1024)
    aframe.rate = 44100
    for packet in a_stream.encode(aframe):
        container.mux(packet)
    for packet in a_stream.encode():
        container.mux(packet)
    container.close()

    meta_with_audio = VideoMetadataExtractor.extract(v_with_audio)
    assert meta_with_audio["has_audio"] is True
    assert meta_with_audio["audio_stream_count"] == 1
    assert len(meta_with_audio["audio_streams"]) == 1
    assert meta_with_audio["audio_streams"][0]["sample_rate"] == 44100

@pytest.mark.asyncio
async def test_audio_metadata_extraction(tmp_path: Path):
    """
    Verifies standalone audio metadata extraction.
    """
    audio_path = tmp_path / "test.wav"
    container = av.open(str(audio_path), mode="w", format="wav")
    a_stream = container.add_stream("pcm_s16le", rate=16000, layout="mono")
    aframe = av.AudioFrame(format="s16", layout="mono", samples=1024)
    aframe.rate = 16000
    for packet in a_stream.encode(aframe):
        container.mux(packet)
    for packet in a_stream.encode():
        container.mux(packet)
    container.close()

    metadata = AudioMetadataExtractor.extract(audio_path)
    assert metadata["category"] == "OBSERVED_DATA"
    assert metadata["metadata_status"] == "COMPLETED"
    assert metadata["sample_rate"] == 16000

@pytest.mark.asyncio
async def test_extracted_endpoints_and_artifact_security(async_client: AsyncClient, db_session: AsyncSession):
    """
    Verifies /extracted and /artifacts endpoints, confirming that
    absolute filesystem paths are not disclosed.
    """
    inv = Investigation(title="Artifact Security Test", description="Testing privacy", priority="HIGH")
    db_session.add(inv)
    await db_session.flush()

    sub = EvidenceSubmission(
        investigation_id=inv.id,
        submission_type="IMAGE",
        processing_status="COMPLETED"
    )
    db_session.add(sub)
    await db_session.flush()

    # Create dummy derived artifact file
    rel_dir = storage_manager.upload_dir.parent / "derived" / sub.id / "frames"
    rel_dir.mkdir(parents=True, exist_ok=True)
    dummy_file = rel_dir / "frame_0.jpg"
    dummy_file.write_bytes(b"\xFF\xD8\xFF\xE0dummy_jpg_content")

    artifact = DerivedArtifact(
        evidence_submission_id=sub.id,
        artifact_type="KEYFRAME",
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        relative_path=f"derived/{sub.id}/frames/frame_0.jpg",
        file_size_bytes=len(dummy_file.read_bytes()),
        mime_type="image/jpeg",
        artifact_metadata={"frame_index": 0, "timestamp_ms": 0}
    )
    db_session.add(artifact)
    await db_session.flush()

    record = ExtractionRecord(
        evidence_submission_id=sub.id,
        version=1,
        is_active=True,
        category="OBSERVED_DATA",
        extractor_name="TruthNetMultimodalExtractor",
        extractor_version="2.0.0",
        status="COMPLETED",
        modality_statuses={"metadata": "COMPLETED", "ocr": "COMPLETED"},
        technical_metadata={"dimensions": {"width": 800, "height": 600}},
        derived_artifact_ids=[artifact.id]
    )
    db_session.add(record)
    await db_session.commit()
    inv_id = inv.id
    sub_id = sub.id
    art_id = artifact.id

    # 1. Test GET /extracted
    ext_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/evidence/{sub_id}/extracted")
    assert ext_resp.status_code == 200
    ext_data = ext_resp.json()
    assert ext_data["category"] == "OBSERVED_DATA"
    assert ext_data["version"] == 1
    assert ext_data["technical_metadata"]["dimensions"]["width"] == 800

    # 2. Test GET /artifacts
    art_resp = await async_client.get(f"/api/v1/investigations/{inv_id}/evidence/{sub_id}/artifacts")
    assert art_resp.status_code == 200
    art_list = art_resp.json()
    assert len(art_list) == 1
    first_art = art_list[0]
    assert first_art["id"] == art_id
    assert first_art["artifact_type"] == "KEYFRAME"
    # Ensure relative_path or absolute paths are NEVER exposed in the JSON schema
    assert "relative_path" not in first_art
    assert "file_path" not in first_art
    assert first_art["download_url"] == f"/api/v1/investigations/{inv_id}/evidence/{sub_id}/artifacts/{art_id}/content"

    # 3. Test GET artifact content download
    dl_resp = await async_client.get(first_art["download_url"])
    assert dl_resp.status_code == 200
    assert dl_resp.content == b"\xFF\xD8\xFF\xE0dummy_jpg_content"
    assert dl_resp.headers["content-type"] == "image/jpeg"
