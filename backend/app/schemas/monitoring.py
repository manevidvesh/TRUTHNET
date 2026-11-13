"""
Pydantic schemas for Live Monitoring & Event Pipeline.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class InvestigationEventResponse(BaseModel):
    id: str
    investigation_id: str
    event_type: str
    severity: str
    summary: str
    details_json: Dict[str, Any]
    originating_entity_id: Optional[str] = None
    originating_entity_type: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvestigationEventsListResponse(BaseModel):
    investigation_id: str
    events: List[InvestigationEventResponse]
    total_events: int
    last_event_timestamp: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
