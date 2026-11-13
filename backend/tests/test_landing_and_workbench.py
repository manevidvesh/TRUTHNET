"""
Integration tests for TRUTHNET AI Public Landing Page and Intelligence Workbench UI.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.investigation import Investigation


@pytest.mark.asyncio
async def test_landing_page_html_render(async_client: AsyncClient):
    """
    Verify GET / returns the public landing page with complete 9-capability showcase,
    epistemic principles, problem breakdown, and forensic visual elements.
    """
    resp = await async_client.get("/", headers={"Accept": "text/html,application/xhtml+xml"})
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    html = resp.text

    # Hero & Identity
    assert "TRUTHNET AI" in html
    assert "MULTIMODAL INVESTIGATIVE INTELLIGENCE" in html
    assert "When digital evidence is manipulated" in html
    assert "context becomes intelligence." in html
    assert "Launch Workbench" in html
    assert "Explore Capabilities" in html

    # Section B: Trust / Capability Strip
    assert "Image & Video Forensics" in html
    assert "Historical Media Discovery" in html
    assert "Claim Verification" in html
    assert "Source Intelligence" in html
    assert "Coordination Analysis" in html

    # Section C: Problem Breakdown
    assert "Manipulated Media" in html
    assert "Misleading Context" in html
    assert "Coordinated Narratives" in html

    # Section D: All 6 Contextual Verification Verdicts
    assert "SUPPORTED" in html
    assert "CONTRADICTED" in html
    assert "MISLEADING_OR_CONTEXT_MISSING" in html
    assert "UNVERIFIED" in html
    assert "INSUFFICIENT_EVIDENCE" in html
    assert "CONFLICTING_EVIDENCE" in html

    # Section E: Workflow
    assert "SUBMIT" in html
    assert "EXTRACT" in html
    assert "DISCOVER" in html
    assert "VERIFY" in html
    assert "CONNECT" in html
    assert "REVIEW" in html

    # Section F: Epistemic Principles
    assert "Media authenticity does not establish claim truth." in html
    assert "Historical reuse does not automatically prove misinformation." in html
    assert "Similar reporting does not equal independent corroboration." in html
    assert "Insufficient evidence is never proof of falsehood." in html

    # Section H: Hackathon attribution
    assert "YUKTIK-2026" in html
    assert "PS-11" in html


@pytest.mark.asyncio
async def test_root_api_json_response(async_client: AsyncClient):
    """
    Verify GET / returns JSON when client explicitly requests application/json without text/html.
    """
    resp = await async_client.get("/", headers={"Accept": "application/json"})
    assert resp.status_code == 200
    assert "application/json" in resp.headers["content-type"]
    data = resp.json()
    assert "TRUTHNET AI API" in data["message"]
    assert data["workbench"] == "/workbench"


@pytest.mark.asyncio
async def test_workbench_ui_render_with_investigation(db_session: AsyncSession, async_client: AsyncClient):
    """
    Verify GET /workbench returns the full investigator intelligence workbench
    with all required tabs, controls, and elements.
    """
    inv = Investigation(title="WB Test Case", priority="HIGH")
    db_session.add(inv)
    await db_session.commit()

    resp = await async_client.get(f"/workbench?investigation_id={inv.id}")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    html = resp.text

    assert "TRUTHNET AI — Intelligence Workbench" in html
    assert "WB Test Case" in html
    assert "+ Upload Evidence" in html
    assert "+ New Case" in html
    assert "Print Dossier" in html

    # Required tabs and elements
    assert "Overview" in html
    assert "Evidence & Submissions" in html
    assert "Media Forensics" in html
    assert "Historical Discovery" in html
    assert "Claims & Sources" in html
    assert "Intelligence Graph" in html
    assert "Timeline" in html
    assert "Assessment Engine" in html
    assert "Case Report" in html

    # Graph canvas & test-critical identifiers
    assert "canvas-container" in html
    assert "graph-svg" in html
    assert "drawer" in html
    assert "toggle-inferred" in html
    assert "stat-nodes" in html
    assert "stat-edges" in html


@pytest.mark.asyncio
async def test_workbench_simulated_banner(db_session: AsyncSession, async_client: AsyncClient):
    """
    Verify that simulated scenario metadata triggers appropriate front-end indicators.
    """
    inv = Investigation(title="INV-999 [SIMULATED]: Benchmark Drill", priority="LOW")
    db_session.add(inv)
    await db_session.commit()

    resp = await async_client.get(f"/workbench?investigation_id={inv.id}")
    assert resp.status_code == 200
    assert "SIMULATED BENCHMARK SCENARIO" in resp.text
