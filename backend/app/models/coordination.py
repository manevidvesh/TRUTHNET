"""
Database model for Coordinated Misinformation Intelligence.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CoordinationClusterRecord(Base):
    """
    Evidence-backed cluster of coordinated distribution signals.
    Records shared content, media reuse, temporal bursts, and entity relationships
    with explicit epistemic limitations.
    """
    __tablename__ = "coordination_clusters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Classification: REPEATED_CONTENT_PATTERN, TEMPORAL_BURST, SHARED_MEDIA_PATTERN,
    # SHARED_DISTRIBUTION_PATTERN, SOURCE_DEPENDENCY_PATTERN, POSSIBLE_COORDINATED_ACTIVITY,
    # INSUFFICIENT_COORDINATION_EVIDENCE
    cluster_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    # Entities involved: [{"entity_id": "...", "entity_type": "SUBMISSION|CLAIM|ACCOUNT|MEDIA", "label": "..."}]
    entities_involved: Mapped[list] = mapped_column(JSON, nullable=False)

    # Supporting measurements: time_window_seconds, text_similarity_ratio, shared_url, shared_media_hash, etc.
    supporting_observations: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Detection method: TEMPORAL_SLIDING_WINDOW, JACCARD_TEXT_SIMILARITY, PHASH_COLLISION, GRAPH_CONNECTED_COMPONENTS
    detection_method: Mapped[str] = mapped_column(String(100), nullable=False)

    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)

    # Epistemic limitations & review
    epistemic_limitations: Mapped[str] = mapped_column(Text, nullable=False)
    review_status: Mapped[str] = mapped_column(String(50), default="UNREVIEWED", nullable=False)  # UNREVIEWED, CONFIRMED, REFUTED
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    investigation = relationship("Investigation", backref="coordination_clusters")
