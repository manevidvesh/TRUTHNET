import hashlib
import io
import pytest
from httpx import AsyncClient
from app.services.pipeline import pipeline_service

TINY_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

# Simulated audio header bytes (WAV RIFF format)
SAMPLE_WAV_BYTES = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"

@pytest.mark.asyncio
async def test_complete_phase1_vertical_slice(async_client: AsyncClient):
    """
    End-to-End Vertical Slice Verification:
    1. Create Investigation ('Suspected Regional Election Rumor')
    2. Submit Image with claimed context
    3. Submit Audio note with caption
    4. Submit Text claim describing purported incident
    5. Submit identical Image again with conflicting historical context
    6. Verify SHA-256 deduplication (shared MediaAsset, separate EvidenceSubmissions)
    7. Verify background pipeline processing
    8. Verify parent investigation reflects accurate counts and remains healthy
    """
    # 1. Create Investigation
    inv_res = await async_client.post("/api/v1/investigations/", json={
        "title": "Suspected Regional Election Rumor",
        "description": "Investigating coordinated claims of polling station disruptions",
        "priority": "HIGH"
    })
    assert inv_res.status_code == 201
    inv_id = inv_res.json()["id"]

    # 2. Submit Image
    img_hash = hashlib.sha256(TINY_PNG_BYTES).hexdigest()
    img_res1 = await async_client.post(
        f"/api/v1/investigations/{inv_id}/evidence/upload",
        files={"file": ("polling_clash.png", io.BytesIO(TINY_PNG_BYTES), "image/png")},
        data={
            "caption": "Purported clash outside Booth 42 earlier today",
            "claimed_event": "Election Day Disturbance",
            "claimed_date": "2026-11-13",
            "claimed_location": "Secunderabad",
            "language": "en"
        }
    )
    assert img_res1.status_code == 201
    img_data1 = img_res1.json()
    assert img_data1["sha256_hash"] == img_hash
    assert img_data1["submission_type"] == "IMAGE"
    asset1_id = img_data1["media_asset"]["id"]
    sub1_id = img_data1["id"]

    # 3. Submit Audio
    wav_hash = hashlib.sha256(SAMPLE_WAV_BYTES).hexdigest()
    audio_res = await async_client.post(
        f"/api/v1/investigations/{inv_id}/evidence/upload",
        files={"file": ("police_dispatch_audio.wav", io.BytesIO(SAMPLE_WAV_BYTES), "audio/x-wav")},
        data={
            "caption": "Purported leaked audio of police control room",
            "claimed_event": "Emergency Dispatch",
            "claimed_date": "2026-11-13",
            "language": "te"
        }
    )
    assert audio_res.status_code == 201
    audio_data = audio_res.json()
    assert audio_data["submission_type"] == "AUDIO"
    assert audio_data["sha256_hash"] == wav_hash
    sub_audio_id = audio_data["id"]

    # 4. Submit Text Claim
    text_res = await async_client.post(
        f"/api/v1/investigations/{inv_id}/evidence/claim",
        json={
            "raw_text": "Section 144 reportedly imposed across three polling wards following skirmish.",
            "caption": "Anonymous Telegram broadcast forward",
            "claimed_location": "Secunderabad District",
            "language": "en"
        }
    )
    assert text_res.status_code == 201
    text_data = text_res.json()
    assert text_data["submission_type"] == "TEXT"
    sub_text_id = text_data["id"]

    # 5. Submit the identical Image again with conflicting historical context
    img_res2 = await async_client.post(
        f"/api/v1/investigations/{inv_id}/evidence/upload",
        files={"file": ("archival_photo.png", io.BytesIO(TINY_PNG_BYTES), "image/png")},
        data={
            "caption": "Fact-checker submission: this photo is from a 2019 sports event queue",
            "claimed_event": "2019 Sports Ticket Queue",
            "claimed_date": "2019-05-10",
            "claimed_location": "Gachibowli Stadium",
            "language": "en"
        }
    )
    assert img_res2.status_code == 201
    img_data2 = img_res2.json()
    sub2_id = img_data2["id"]
    asset2_id = img_data2["media_asset"]["id"]

    # 6. Verify Deduplication and Context Decoupling
    assert sub1_id != sub2_id, "Submissions must have unique IDs"
    assert asset1_id == asset2_id, "Both submissions must link to the exact same MediaAsset"
    assert img_data1["caption"] != img_data2["caption"], "Distinct captions must be preserved"
    assert img_data1["claimed_date"] == "2026-11-13"
    assert img_data2["claimed_date"] == "2019-05-10"

    # 7. Run background pipeline validation
    for item_id in [sub1_id, sub_audio_id, sub_text_id, sub2_id]:
        await pipeline_service.process_evidence_item(item_id)

    # 8. Verify all submissions have COMPLETED status
    list_res = await async_client.get(f"/api/v1/investigations/{inv_id}/evidence/")
    assert list_res.status_code == 200
    all_subs = list_res.json()
    assert len(all_subs) == 4
    for sub in all_subs:
        assert sub["processing_status"] == "COMPLETED"

    # 9. Verify Investigation detail reflects evidence count
    inv_check = await async_client.get(f"/api/v1/investigations/{inv_id}")
    assert inv_check.status_code == 200
    assert inv_check.json()["evidence_count"] == 4
    assert inv_check.json()["status"] == "ACTIVE"
