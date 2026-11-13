"""
Claim Lineage & Entity Relationship Model.

Supports persistent and inferred edges between:
- Investigations, Evidence Submissions, Media Assets, Claims,
  Claim Variants, Retrieved Sources, Accounts, and Events.
Each relationship explicitly records edge nature (OBSERVED vs INFERRED),
evidence traceability, detection method, and human review status.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class LineageRelationshipRecord(Base):
    """
    Persistent record representing a verified or inferred relationship
    between two entities in the investigation lineage graph.
    """
    __tablename__ = "lineage_relationships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Polymorphic source entity
    source_entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Polymorphic target entity
    target_entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    target_entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Typed Relationship
    # Claim: SAME_CLAIM, CLAIM_VARIANT, SUPPORTS, CONTRADICTS, MISLEADING_CONTEXT, ATTRIBUTED_TO
    # Media: EXACT_MEDIA_MATCH, NEAR_DUPLICATE_MEDIA, POSSIBLE_REUSED_MEDIA, SAME_PHOTOGRAPH_CANDIDATE, HISTORICAL_CONTEXT_CONFLICT
    # Source: REPEATS_SOURCE, SHARED_URL, SHARED_PRESS_RELEASE, SHARED_WIRE_REPORT, SIMILAR_REPORTING, SOURCE_DEPENDENCY_UNKNOWN
    # Timeline/Event: PUBLISHED_BEFORE, ASSOCIATED_WITH_EVENT, SAME_EVENT_CANDIDATE
    # Distribution: SHARED_CAPTION, SIMILAR_CAPTION, REPEATED_DISTRIBUTION, POSSIBLE_COORDINATION
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Edge Nature: OBSERVED (directly recorded in metadata/artifacts) vs INFERRED (algorithmic/statistical inference)
    edge_nature: Mapped[str] = mapped_column(String(20), default="OBSERVED", nullable=False)
    is_inferred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Evidence Traceability
    evidence_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    evidence_summary: Mapped[str] = mapped_column(Text, nullable=False)
    detection_method: Mapped[str] = mapped_column(String(100), default="DETERMINISTIC_RULES", nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Human Review Lifecycle
    review_status: Mapped[str] = mapped_column(String(50), default="UNREVIEWED", nullable=False)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Structured metadata & timestamps
    timestamps: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    relationship_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Investigation relationship
    investigation = relationship("Investigation")
