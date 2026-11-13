"""
Live Investigation Event Pipeline & Monitoring Engine.

Provides persistent, chronologically ordered event logging for real-time investigation monitoring:
- Tracks evidence ingestion, processing status, claim extraction, media matches,
  source retrieval, authenticity audits, coordination findings, and contextual verdicts.
- Supports lightweight HTTP polling and real-time event streaming.
- Fault-tolerant: event failures never crash the underlying investigation pipeline.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.monitoring import InvestigationEventRecord

logger = logging.getLogger("truthnet.monitoring.events")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EventBus:
    """
    Central event dispatcher and persistence coordinator.
    """

    def __init__(self, max_cached_per_case: int = 100):
        self._recent_events: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_cached_per_case))

    async def emit(
        self,
        session: AsyncSession,
        investigation_id: str,
        event_type: str,
        severity: str,
        summary: str,
        details_json: Optional[Dict[str, Any]] = None,
        originating_entity_id: Optional[str] = None,
        originating_entity_type: Optional[str] = None
    ) -> Optional[InvestigationEventRecord]:
        """
        Emits and persists a monitoring event into the database and live cache.
        """
        try:
            event = InvestigationEventRecord(
                investigation_id=investigation_id,
                event_type=event_type,
                severity=severity,
                summary=summary,
                details_json=details_json or {},
                originating_entity_id=originating_entity_id,
                originating_entity_type=originating_entity_type,
                created_at=utc_now()
            )
            session.add(event)
            await session.commit()
            await session.refresh(event)

            # Add to fast in-memory cache for live polling
            self._recent_events[investigation_id].append(event)
            logger.info(f"Event emitted [{severity}] {event_type} for case {investigation_id}: {summary}")
            return event
        except Exception as e:
            logger.warning(f"Non-fatal failure emitting event {event_type} for case {investigation_id}: {e}")
            return None

    async def get_events(
        self,
        session: AsyncSession,
        investigation_id: str,
        since: Optional[datetime] = None,
        limit: int = 50
    ) -> List[InvestigationEventRecord]:
        """
        Queries persistent events for an investigation ordered chronologically.
        """
        stmt = select(InvestigationEventRecord).where(
            InvestigationEventRecord.investigation_id == investigation_id
        )
        if since:
            stmt = stmt.where(InvestigationEventRecord.created_at > since)
        stmt = stmt.order_by(InvestigationEventRecord.created_at.desc()).limit(limit)

        res = await session.execute(stmt)
        return list(res.scalars().all())


event_bus = EventBus()
