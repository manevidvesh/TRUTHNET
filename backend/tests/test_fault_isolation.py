import io
import pytest
from httpx import AsyncClient
from app.services.pipeline import pipeline_service

TINY_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

@pytest.mark.asyncio
async def test_unreachable_url_fault_isolation(async_client: AsyncClient):
    # 1. Create investigation
    inv_res = await async_client.post("/api/v1/investigations/", json={
        "title": "Fault Isolation URL Test",
        "priority": "LOW"
    })
    inv_id = inv_res.json()["id"]

    # 2. Submit unreachable domain URL
    claim_res = await async_client.post(
        f"/api/v1/investigations/{inv_id}/evidence/claim",
        json={
            "source_url": "http://non-existent-domain-truthnet-99999.invalid/article",
            "caption": "Purported foreign press release"
        }
    )
    assert claim_res.status_code == 201
    evidence_id = claim_res.json()["id"]

    # 3. Process the evidence item directly
    success = await pipeline_service.process_evidence_item(evidence_id)
    assert success is False, "Processing must report failure on invalid URL"

    # 4. Check status endpoint
    status_res = await async_client.get(f"/api/v1/investigations/{inv_id}/evidence/{evidence_id}/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["processing_status"] == "FAILED"
    assert status_data["error_message"] is not None

    # 5. Check parent investigation is still active and healthy
    inv_check = await async_client.get(f"/api/v1/investigations/{inv_id}")
    assert inv_check.status_code == 200
    assert inv_check.json()["status"] == "ACTIVE"

@pytest.mark.asyncio
async def test_mixed_evidence_batch_resilience(async_client: AsyncClient):
    inv_res = await async_client.post("/api/v1/investigations/", json={
        "title": "Mixed Evidence Resilience Test",
        "priority": "HIGH"
    })
    inv_id = inv_res.json()["id"]

    # Item 1: Valid Image
    item1_res = await async_client.post(
        f"/api/v1/investigations/{inv_id}/evidence/upload",
        files={"file": ("valid.png", io.BytesIO(TINY_PNG_BYTES), "image/png")},
        data={"caption": "Valid visual evidence"}
    )
    assert item1_res.status_code == 201
    id1 = item1_res.json()["id"]

    # Item 2: Unreachable URL
    item2_res = await async_client.post(
        f"/api/v1/investigations/{inv_id}/evidence/claim",
        json={"source_url": "http://broken-link-fake-test.invalid"}
    )
    assert item2_res.status_code == 201
    id2 = item2_res.json()["id"]

    # Item 3: Valid Text Claim
    item3_res = await async_client.post(
        f"/api/v1/investigations/{inv_id}/evidence/claim",
        json={"raw_text": "Eyewitness report claiming sudden tremors in district."}
    )
    assert item3_res.status_code == 201
    id3 = item3_res.json()["id"]

    # Process all 3 items
    res1 = await pipeline_service.process_evidence_item(id1)
    res2 = await pipeline_service.process_evidence_item(id2)
    res3 = await pipeline_service.process_evidence_item(id3)

    assert res1 is True, "Valid image should process to COMPLETED"
    assert res2 is False, "Broken URL should process to FAILED"
    assert res3 is True, "Valid text should process to COMPLETED"

    # Verify all 3 appear in investigation evidence list with their individual statuses
    list_res = await async_client.get(f"/api/v1/investigations/{inv_id}/evidence/")
    assert list_res.status_code == 200
    all_evidence = list_res.json()
    assert len(all_evidence) == 3

    status_map = {item["id"]: item["processing_status"] for item in all_evidence}
    assert status_map[id1] == "COMPLETED"
    assert status_map[id2] == "FAILED"
    assert status_map[id3] == "COMPLETED"

    # Parent investigation remains intact
    inv_status = await async_client.get(f"/api/v1/investigations/{inv_id}")
    assert inv_status.status_code == 200
    assert inv_status.json()["status"] == "ACTIVE"
    assert inv_status.json()["evidence_count"] == 3
