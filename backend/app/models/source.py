import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class RetrievedSourceRecord(Base):
    """
    Persistent record representing an externally retrieved document, news article,
    fact-check record, or reference page with complete provenance, timestamps,
    content hash, HTTP telemetry, and ClaimReview metadata.
    """
    __tablename__ = "retrieved_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id: Mapped[str] = mapped_column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)
    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)

    # URLs & Identity
    canonical_url: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)
    original_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    article_title: Mapped[str] = mapped_column(String(500), nullable=False)

    # Authorship & Publisher Provenance
    publisher: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_date: Mapped[str | None] = mapped_column(String(100), nullable=True)
    modified_date: Mapped[str | None] = mapped_column(String(100), nullable=True)
    retrieval_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Technical Classification & Telemetry
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), default="NEWS_ARTICLE", nullable=False)
    retrieval_method: Mapped[str] = mapped_column(String(50), default="WEB_SEARCH_SCRAPER", nullable=False)
    search_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Content & Excerpt
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_excerpt: Mapped[str] = mapped_column(Text, nullable=False)

    # Third-Party ClaimReview JSON-LD Metadata (if discovered)
    claim_review_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Retrieval Status: SUCCESS, PARTIAL, FAILED, UNAVAILABLE, RATE_LIMITED, SSRF_BLOCKED
    retrieval_status: Mapped[str] = mapped_column(String(50), default="SUCCESS", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    claim = relationship("ClaimRecord", backref="retrieved_sources")
    investigation = relationship("Investigation")


class SourceIndependenceRecord(Base):
    """
    Persistent record representing the multi-signal source independence analysis
    for a claim. Evaluates wire-service attribution, shared quotes, text overlap,
    and publication timelines into explainable source clusters.
    """
    __tablename__ = "source_independence_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id: Mapped[str] = mapped_column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)

    total_sources_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    independent_sources_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Assessment: INDEPENDENT_REPORTING, WIRE_SERVICE_DERIVED, SHARED_PRESS_RELEASE,
    # REPEATS_ORIGINAL_SOURCE, POSSIBLE_CONTENT_DEPENDENCY, UNKNOWN_DEPENDENCY
    independence_assessment: Mapped[str] = mapped_column(String(50), default="UNKNOWN_DEPENDENCY", nullable=False)

    # Structured cluster breakdown & signals
    clusters: Mapped[list | None] = mapped_column(JSON, nullable=True)
    observable_signals: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship
    claim = relationship("ClaimRecord", backref="source_independence_analyses")
