"""
API Endpoints for Live Monitoring & Event Pipeline.
"""

import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.monitoring import (
    InvestigationEventResponse,
    InvestigationEventsListResponse
)
from app.monitoring.events import event_bus

logger = logging.getLogger("truthnet.api.monitoring")

router = APIRouter(prefix="/investigations/{investigation_id}/events", tags=["Live Monitoring"])


@router.get("", response_model=InvestigationEventsListResponse)
async def get_investigation_events(
    investigation_id: str,
    since: Optional[datetime] = Query(None, description="Filter events created after timestamp"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
) -> InvestigationEventsListResponse:
    """
    Returns chronologically logged events for live investigation monitoring.
    """
    events = await event_bus.get_events(db, investigation_id, since=since, limit=limit)
    event_responses = [InvestigationEventResponse.model_validate(e) for e in events]
    last_ts = events[0].created_at if events else None

    return InvestigationEventsListResponse(
        investigation_id=investigation_id,
        events=event_responses,
        total_events=len(event_responses),
        last_event_timestamp=last_ts
    )


@router.get("/poll", response_model=List[InvestigationEventResponse])
async def poll_investigation_events(
    investigation_id: str,
    since: Optional[datetime] = Query(None, description="Filter events created after timestamp"),
    db: AsyncSession = Depends(get_db)
) -> List[InvestigationEventResponse]:
    """
    Fast lightweight polling endpoint returning only new events since timestamp.
    """
    events = await event_bus.get_events(db, investigation_id, since=since, limit=30)
    return [InvestigationEventResponse.model_validate(e) for e in events]
