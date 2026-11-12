import hashlib
import io
import pytest
from httpx import AsyncClient

# Minimal 1x1 PNG image bytes with valid PNG header
TINY_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

@pytest.mark.asyncio
async def test_evidence_file_upload_and_deduplication(async_client: AsyncClient):
    # 1. Create investigation
    inv_res = await async_client.post("/api/v1/investigations/", json={
        "title": "Viral Flood Footage Investigation",
        "description": "Verifying origin of bridge collapse video clip",
        "priority": "HIGH"
    })
    assert inv_res.status_code == 201
    inv_id = inv_res.json()["id"]

    # 2. Upload image file with contextual metadata
    expected_hash = hashlib.sha256(TINY_PNG_BYTES).hexdigest()
    
    upload_1 = await async_client.post(
        f"/api/v1/investigations/{inv_id}/evidence/upload",
        files={"file": ("bridge_collapse.png", io.BytesIO(TINY_PNG_BYTES), "image/png")},
        data={
            "caption": "Breaking: Bridge collapsed in Coastal City today!",
            "claimed_event": "Coastal City Bridge Collapse",
            "claimed_date": "2026-11-12",
            "claimed_location": "Coastal City, Andhra Pradesh",
            "language": "en"
        }
    )
    assert upload_1.status_code == 201
    data_1 = upload_1.json()
    assert data_1["sha256_hash"] == expected_hash
    assert data_1["mime_type"] == "image/png"
    assert data_1["submission_type"] == "IMAGE"
    assert data_1["caption"] == "Breaking: Bridge collapsed in Coastal City today!"
    assert data_1["claimed_location"] == "Coastal City, Andhra Pradesh"
    assert data_1["media_asset"] is not None
    assert data_1["media_asset"]["sha256_hash"] == expected_hash
    sub_1_id = data_1["id"]
    asset_1_id = data_1["media_asset"]["id"]

    # 3. Submit the EXACT SAME file again with a conflicting context (e.g. second user claiming different event/location)
    upload_2 = await async_client.post(
        f"/api/v1/investigations/{inv_id}/evidence/upload",
        files={"file": ("same_image_repost.png", io.BytesIO(TINY_PNG_BYTES), "image/png")},
        data={
            "caption": "Old footage from 2021 flooding being shared as new",
            "claimed_event": "2021 Archival Dam Overflow",
            "claimed_date": "2021-08-15",
            "claimed_location": "Godavari Basin",
            "language": "en"
        }
    )
    assert upload_2.status_code == 201
    data_2 = upload_2.json()
    sub_2_id = data_2["id"]
    asset_2_id = data_2["media_asset"]["id"]

    # Critical Assertion: Decoupling and deduplication
    assert sub_1_id != sub_2_id, "Submissions must be distinct records"
    assert asset_1_id == asset_2_id, "Both submissions must reuse the identical underlying MediaAsset"
    assert data_1["caption"] != data_2["caption"], "Contexts must remain distinct"
    assert data_1["claimed_date"] == "2026-11-12"
    assert data_2["claimed_date"] == "2021-08-15"

    # 4. List evidence for investigation
    list_res = await async_client.get(f"/api/v1/investigations/{inv_id}/evidence/")
    assert list_res.status_code == 200
    evidence_list = list_res.json()
    assert len(evidence_list) == 2

@pytest.mark.asyncio
async def test_evidence_text_and_url_claims(async_client: AsyncClient):
    inv_res = await async_client.post("/api/v1/investigations/", json={
        "title": "Text Claim Investigation",
        "priority": "MEDIUM"
    })
    inv_id = inv_res.json()["id"]

    # 1. Submit text claim
    text_claim = await async_client.post(
        f"/api/v1/investigations/{inv_id}/evidence/claim",
        json={
            "raw_text": "Government announces sudden shutdown of regional power grid.",
            "caption": "Viral WhatsApp forward circulating in Hyderabad",
            "claimed_location": "Hyderabad",
            "claimed_event": "Power Outage Rumor",
            "language": "te"
        }
    )
    assert text_claim.status_code == 201
    text_data = text_claim.json()
    assert text_data["submission_type"] == "TEXT"
    assert text_data["language"] == "te"
    assert text_data["raw_text"] == "Government announces sudden shutdown of regional power grid."
    assert text_data["media_asset"] is not None

    # 2. Submit URL claim
    url_claim = await async_client.post(
        f"/api/v1/investigations/{inv_id}/evidence/claim",
        json={
            "source_url": "https://example.org/news/rumor-debunk",
            "caption": "External fact check reporting on the rumor",
            "language": "en"
        }
    )
    assert url_claim.status_code == 201
    url_data = url_claim.json()
    assert url_data["submission_type"] == "URL"
    assert url_data["source_url"] == "https://example.org/news/rumor-debunk"
