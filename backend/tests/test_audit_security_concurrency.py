import io
import hashlib
import pytest
from httpx import AsyncClient
from sqlalchemy import text
from app.core.security import is_safe_url
from app.core.storage import storage_manager
from app.services.pipeline import pipeline_service
from fastapi import HTTPException

TINY_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

@pytest.mark.asyncio
async def test_ssrf_guards(async_client: AsyncClient):
    """Verify SSRF defense blocks loopback, private IPs, metadata IP, and invalid schemes."""
    blocked_urls = [
        "http://localhost:8000/api/v1/investigations",
        "http://127.0.0.1:8000/",
        "http://127.0.0.1",
        "http://169.254.169.254/latest/meta-data/",
        "http://192.168.1.1/admin",
        "http://10.0.0.5:8080/metrics",
        "http://172.16.0.1/",
        "ftp://example.com/file.txt",
        "file:///etc/passwd",
        "gopher://example.com/",
    ]
    for url in blocked_urls:
        safe, reason = is_safe_url(url)
        assert safe is False, f"Expected {url} to be blocked by SSRF guard, but passed! Reason: {reason}"
        assert len(reason) > 0

    # Integration test through evidence claim endpoint
    inv_res = await async_client.post("/api/v1/investigations/", json={"title": "SSRF Test Case"})
    inv_id = inv_res.json()["id"]

    claim_res = await async_client.post(
        f"/api/v1/investigations/{inv_id}/evidence/claim",
        json={"source_url": "http://169.254.169.254/latest/meta-data/"}
    )
    assert claim_res.status_code == 201
    evidence_id = claim_res.json()["id"]

    # Run processing
    res = await pipeline_service.process_evidence_item(evidence_id)
    assert res is False

    # Check status
    status_res = await async_client.get(f"/api/v1/investigations/{inv_id}/evidence/{evidence_id}/status")
    assert status_res.status_code == 200
    data = status_res.json()
    assert data["processing_status"] == "FAILED"
    assert "SSRF Guard" in data["error_message"]

@pytest.mark.asyncio
async def test_cross_investigation_isolation(async_client: AsyncClient):
    """Verify cross-investigation deduplication does NOT leak submission context or access."""
    # Create Investigation A
    inv_a = await async_client.post("/api/v1/investigations/", json={"title": "Investigation A (Confidential)"})
    id_a = inv_a.json()["id"]

    # Create Investigation B
    inv_b = await async_client.post("/api/v1/investigations/", json={"title": "Investigation B (Public)"})
    id_b = inv_b.json()["id"]

    # Upload same PNG to A
    res_a = await async_client.post(
        f"/api/v1/investigations/{id_a}/evidence/upload",
        files={"file": ("classified.png", io.BytesIO(TINY_PNG_BYTES), "image/png")},
        data={"caption": "TOP SECRET: Classified Military Movement", "claimed_location": "Base Alpha"}
    )
    assert res_a.status_code == 201
    data_a = res_a.json()
    sub_a_id = data_a["id"]
    asset_a_id = data_a["media_asset"]["id"]

    # Upload same PNG to B
    res_b = await async_client.post(
        f"/api/v1/investigations/{id_b}/evidence/upload",
        files={"file": ("public.png", io.BytesIO(TINY_PNG_BYTES), "image/png")},
        data={"caption": "Public News Clip", "claimed_location": "Downtown"}
    )
    assert res_b.status_code == 201
    data_b = res_b.json()
    sub_b_id = data_b["id"]
    asset_b_id = data_b["media_asset"]["id"]

    # 1. Deduplication confirmed
    assert asset_a_id == asset_b_id, "Both investigations must share the same physical MediaAsset"

    # 2. Querying A's evidence list returns ONLY A's data
    list_a = await async_client.get(f"/api/v1/investigations/{id_a}/evidence/")
    items_a = list_a.json()
    assert len(items_a) == 1
    assert items_a[0]["caption"] == "TOP SECRET: Classified Military Movement"
    assert items_a[0]["id"] == sub_a_id
    assert "Public News Clip" not in str(items_a)

    # 3. Querying B's evidence list returns ONLY B's data
    list_b = await async_client.get(f"/api/v1/investigations/{id_b}/evidence/")
    items_b = list_b.json()
    assert len(items_b) == 1
    assert items_b[0]["caption"] == "Public News Clip"
    assert items_b[0]["id"] == sub_b_id
    assert "TOP SECRET" not in str(items_b)

    # 4. Access control: Querying B's submission ID via A's URL must return 404
    cross_res = await async_client.get(f"/api/v1/investigations/{id_a}/evidence/{sub_b_id}")
    assert cross_res.status_code == 404

    cross_res_reverse = await async_client.get(f"/api/v1/investigations/{id_b}/evidence/{sub_a_id}")
    assert cross_res_reverse.status_code == 404

@pytest.mark.asyncio
async def test_path_traversal_and_file_safety():
    """Verify directory traversal attempts are rejected."""
    traversal_paths = [
        "../../etc/passwd",
        "../../../secret.txt",
        "..\\..\\windows\\system32\\cmd.exe",
        "/etc/shadow"
    ]
    for p in traversal_paths:
        with pytest.raises(HTTPException) as exc:
            storage_manager.resolve_safe_path(p)
        assert exc.value.status_code == 400

@pytest.mark.asyncio
async def test_zero_byte_file_rejection(async_client: AsyncClient):
    """Verify 0-byte uploaded files are rejected immediately."""
    inv_res = await async_client.post("/api/v1/investigations/", json={"title": "Zero Byte Test"})
    inv_id = inv_res.json()["id"]

    res = await async_client.post(
        f"/api/v1/investigations/{inv_id}/evidence/upload",
        files={"file": ("empty.png", io.BytesIO(b""), "image/png")}
    )
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()

@pytest.mark.asyncio
async def test_job_recovery_across_restarts(async_client: AsyncClient, test_db_engine):
    """Verify stranded jobs in PENDING or PROCESSING status are recovered and processed."""
    inv_res = await async_client.post("/api/v1/investigations/", json={"title": "Restart Recovery Test"})
    inv_id = inv_res.json()["id"]

    # Submit valid text claim
    res = await async_client.post(
        f"/api/v1/investigations/{inv_id}/evidence/claim",
        json={"raw_text": "Unprocessed claim before restart simulation"}
    )
    assert res.status_code == 201
    eid = res.json()["id"]

    # Simulate crash mid-flight by resetting status to PENDING in the DB
    async with test_db_engine.connect() as conn:
        await conn.execute(
            text("UPDATE evidence_submissions SET processing_status = 'PENDING' WHERE id = :eid"),
            {"eid": eid}
        )
        await conn.commit()

    # Verify status is currently PENDING
    status_before = await async_client.get(f"/api/v1/investigations/{inv_id}/evidence/{eid}/status")
    assert status_before.json()["processing_status"] == "PENDING"

    # Simulate backend restart: call recover_pending_jobs()
    recovered_count = await pipeline_service.recover_pending_jobs()
    assert recovered_count >= 1

    # Verify status is now COMPLETED
    status_res = await async_client.get(f"/api/v1/investigations/{inv_id}/evidence/{eid}/status")
    assert status_res.status_code == 200
    assert status_res.json()["processing_status"] == "COMPLETED"

@pytest.mark.asyncio
async def test_sqlite_pragmas(test_db_engine):
    """Verify SQLite WAL mode, foreign keys, and busy timeout pragmas are active on connections."""
    async with test_db_engine.connect() as conn:
        wal_res = await conn.execute(text("PRAGMA journal_mode;"))
        mode = wal_res.scalar()
        assert mode.lower() == "wal"

        fk_res = await conn.execute(text("PRAGMA foreign_keys;"))
        fk = fk_res.scalar()
        assert fk == 1

        timeout_res = await conn.execute(text("PRAGMA busy_timeout;"))
        timeout = timeout_res.scalar()
        assert timeout == 5000
