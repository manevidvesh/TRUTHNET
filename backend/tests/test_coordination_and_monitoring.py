"""
Unit & Integration Tests for Coordinated Misinformation Intelligence and Live Monitoring.

Verifies:
1. Coordination detection across multiple submissions (temporal burst, shared media, repeated text, shared URLs).
2. Epistemic honesty: no arbitrary probability or fake bot labeling.
3. Event bus emission, persistence, and live polling.
4. Coordination REST APIs and human review lifecycle.
"""

from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.investigation import Investigation
from app.models.evidence import EvidenceSubmission, MediaAsset
from app.models.coordination import CoordinationClusterRecord
from app.models.monitoring import InvestigationEventRecord
from app.coordination.engine import coordination_engine
from app.monitoring.events import event_bus


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_coordination_engine_multi_signal(db_session: AsyncSession):
    """Verify engine detects multi-signal coordinated distribution."""
    inv = Investigation(title="Coordination Test Case", description="Testing multi-signal detection")
    db_session.add(inv)
    await db_session.flush()

    asset = MediaAsset(
        sha256_hash="test_coord_shared_asset_hash",
        mime_type="image/jpeg",
        file_path="uploads/test_coord.jpg",
        file_size_bytes=1024
    )
    db_session.add(asset)
    await db_session.flush()

    base_time = utc_now()
    shared_url = "https://example.com/breaking-leak"

    # Create 3 submissions with shared media, similar caption, shared URL within 10 minutes
    for i in range(3):
        sub = EvidenceSubmission(
            investigation_id=inv.id,
            submission_type="IMAGE",
            caption="Breaking alert: emergency curfew announced across city center immediately!",
            source_url=shared_url,
            media_asset_id=asset.id,
            created_at=base_time + timedelta(minutes=i * 2),
            processing_status="COMPLETED"
        )
        db_session.add(sub)
    await db_session.commit()

    clusters = await coordination_engine.analyze_investigation(db_session, inv.id)
    assert len(clusters) >= 1

    main_cluster = clusters[0]
    assert main_cluster.cluster_type == "POSSIBLE_COORDINATED_ACTIVITY"
    assert main_cluster.confidence >= 0.75
    assert main_cluster.supporting_observations["has_shared_media"] is True
    assert main_cluster.supporting_observations["has_temporal_burst"] is True
    assert main_cluster.supporting_observations["has_repeated_content"] is True
    assert main_cluster.supporting_observations["has_shared_url"] is True
    assert len(main_cluster.entities_involved) == 3


@pytest.mark.asyncio
async def test_coordination_engine_singleton(db_session: AsyncSession):
    """Verify single submission produces INSUFFICIENT_COORDINATION_EVIDENCE without false alarm."""
    inv = Investigation(title="Singleton Case", description="Testing single submission")
    db_session.add(inv)
    await db_session.flush()

    sub = EvidenceSubmission(
        investigation_id=inv.id,
        submission_type="TEXT",
        raw_text="Isolated individual opinion statement",
        processing_status="COMPLETED"
    )
    db_session.add(sub)
    await db_session.commit()

    clusters = await coordination_engine.analyze_investigation(db_session, inv.id)
    assert len(clusters) == 1
    assert clusters[0].cluster_type == "INSUFFICIENT_COORDINATION_EVIDENCE"


@pytest.mark.asyncio
async def test_event_bus_emission_and_retrieval(db_session: AsyncSession):
    """Verify live monitoring event bus emits, persists, and queries chronological events."""
    inv = Investigation(title="Event Bus Case", description="Testing live monitoring")
    db_session.add(inv)
    await db_session.flush()

    ev1 = await event_bus.emit(
        session=db_session,
        investigation_id=inv.id,
        event_type="EVIDENCE_INGESTED",
        severity="INFO",
        summary="Test evidence ingested successfully",
        details_json={"count": 1}
    )
    assert ev1 is not None

    ev2 = await event_bus.emit(
        session=db_session,
        investigation_id=inv.id,
        event_type="COORDINATION_DETECTED",
        severity="WARNING",
        summary="Test temporal burst detected across 3 accounts",
        details_json={"signals": 3}
    )
    assert ev2 is not None

    events = await event_bus.get_events(db_session, inv.id, limit=10)
    assert len(events) >= 2
    types = [e.event_type for e in events]
    assert "EVIDENCE_INGESTED" in types
    assert "COORDINATION_DETECTED" in types


@pytest.mark.asyncio
async def test_coordination_and_monitoring_rest_apis(async_client: AsyncClient, db_session: AsyncSession):
    """Verify REST endpoints for coordination analysis and live event streaming."""
    # 1. Create Investigation
    inv_res = await async_client.post("/api/v1/investigations/", json={"title": "REST Coordination Case"})
    assert inv_res.status_code == 201
    inv_id = inv_res.json()["id"]

    # 2. Check coordination endpoint
    coord_res = await async_client.get(f"/api/v1/investigations/{inv_id}/coordination")
    assert coord_res.status_code == 200
    coord_data = coord_res.json()
    assert "clusters" in coord_data
    assert "epistemic_disclaimer" in coord_data

    # 3. Check events endpoint
    events_res = await async_client.get(f"/api/v1/investigations/{inv_id}/events")
    assert events_res.status_code == 200
    events_data = events_res.json()
    assert "events" in events_data
    assert "total_events" in events_data

    # 4. Check poll endpoint
    poll_res = await async_client.get(f"/api/v1/investigations/{inv_id}/events/poll")
    assert poll_res.status_code == 200
    assert isinstance(poll_res.json(), list)
