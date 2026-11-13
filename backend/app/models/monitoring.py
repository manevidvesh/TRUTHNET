"""
Database model for Live Monitoring & Event Pipeline.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class InvestigationEventRecord(Base):
    """
    Chronological investigation event record for real-time monitoring and traceability.
    """
    __tablename__ = "investigation_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Event category: EVIDENCE_INGESTED, PROCESSING_STATUS_CHANGED, CLAIM_EXTRACTED,
    # HISTORICAL_MEDIA_MATCHED, SOURCE_RETRIEVED, SOURCE_DEPENDENCY_DETECTED,
    # AUTHENTICITY_AUDITED, COORDINATION_DETECTED, ASSESSMENT_UPDATED, INVESTIGATION_PRIORITY_UPDATED
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Severity level: INFO, WARNING, CRITICAL
    severity: Mapped[str] = mapped_column(String(20), default="INFO", nullable=False)

    summary: Mapped[str] = mapped_column(String(255), nullable=False)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    originating_entity_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    originating_entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    investigation = relationship("Investigation", backref="events")
