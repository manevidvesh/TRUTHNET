import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "TRUTHNET" in data["app"]

@pytest.mark.asyncio
async def test_investigation_lifecycle(async_client: AsyncClient):
    # 1. Create an investigation
    payload = {
        "title": "Suspected Disaster Misinformation Campaign",
        "description": "Investigating viral flood footage purportedly from 2026",
        "priority": "HIGH"
    }
    create_res = await async_client.post("/api/v1/investigations/", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["title"] == payload["title"]
    assert created_data["priority"] == "HIGH"
    assert created_data["status"] == "ACTIVE"
    inv_id = created_data["id"]

    # 2. List investigations
    list_res = await async_client.get("/api/v1/investigations/")
    assert list_res.status_code == 200
    inv_list = list_res.json()
    assert len(inv_list) >= 1
    assert any(i["id"] == inv_id for i in inv_list)

    # 3. Get single investigation
    get_res = await async_client.get(f"/api/v1/investigations/{inv_id}")
    assert get_res.status_code == 200
    detail = get_res.json()
    assert detail["id"] == inv_id
    assert detail["title"] == payload["title"]

    # 4. Update investigation
    update_payload = {
        "title": "Updated Disaster Misinformation Case",
        "priority": "URGENT",
        "status": "ACTIVE"
    }
    patch_res = await async_client.patch(f"/api/v1/investigations/{inv_id}", json=update_payload)
    assert patch_res.status_code == 200
    updated_data = patch_res.json()
    assert updated_data["title"] == "Updated Disaster Misinformation Case"
    assert updated_data["priority"] == "URGENT"

    # 5. Delete investigation
    del_res = await async_client.delete(f"/api/v1/investigations/{inv_id}")
    assert del_res.status_code == 204

    # 6. Verify 404 after deletion
    not_found_res = await async_client.get(f"/api/v1/investigations/{inv_id}")
    assert not_found_res.status_code == 404


@pytest.mark.asyncio
async def test_investigation_report_endpoint(async_client: AsyncClient):
    # Create investigation
    create_res = await async_client.post("/api/v1/investigations/", json={
        "title": "Report Verification Investigation",
        "description": "Testing automated dossier generation",
        "priority": "MEDIUM"
    })
    assert create_res.status_code == 201
    inv_id = create_res.json()["id"]

    # 1. Test JSON report endpoint
    rep_res = await async_client.get(f"/api/v1/investigations/{inv_id}/report")
    assert rep_res.status_code == 200
    report = rep_res.json()
    assert report["investigation"]["id"] == inv_id
    assert "metrics" in report
    assert "executive_summary" in report
    assert "epistemic_limitations" in report
    assert len(report["epistemic_limitations"]) >= 3
    assert report["is_simulated_scenario"] is False
    assert report["simulation_disclaimer"] is None

    # 2. Test HTML report endpoint
    html_res = await async_client.get(f"/api/v1/investigations/{inv_id}/report/html")
    assert html_res.status_code == 200
    assert "text/html" in html_res.headers["content-type"]
    assert "TRUTHNET AI — Intelligence Investigation Dossier" in html_res.text

    # 3. Test Workbench root
    wb_res = await async_client.get(f"/workbench?investigation_id={inv_id}")
    assert wb_res.status_code == 200
    assert "TRUTHNET AI — Intelligence Workbench" in wb_res.text


@pytest.mark.asyncio
async def test_simulated_investigation_banner_detection(async_client: AsyncClient):
    create_res = await async_client.post("/api/v1/investigations/", json={
        "title": "INV-2026-999 [SIMULATED]: Synthetic Drill Case",
        "description": "Controlled demonstration scenario",
        "priority": "LOW"
    })
    assert create_res.status_code == 201
    inv_id = create_res.json()["id"]

    rep_res = await async_client.get(f"/api/v1/investigations/{inv_id}/report")
    assert rep_res.status_code == 200
    report = rep_res.json()
    assert report["is_simulated_scenario"] is True
    assert "SIMULATED EVIDENCE RECORD" in report["simulation_disclaimer"]
