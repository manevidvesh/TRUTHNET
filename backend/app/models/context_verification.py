import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class ClaimAssessmentRecord(Base):
    """
    Persistent, immutable record representing a contextual verification assessment
    for a specific extracted ClaimRecord.
    Maintains strict versioning, conservative classifications, structured rationale,
    provenance, and a human investigator review lifecycle.
    """
    __tablename__ = "claim_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id: Mapped[str] = mapped_column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_submission_id: Mapped[str] = mapped_column(String(36), ForeignKey("evidence_submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Immutability and Versioning
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    supersede_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Assessment Core Classification:
    # SUPPORTED, CONTRADICTED, MISLEADING_OR_CONTEXT_MISSING, UNVERIFIED, INSUFFICIENT_EVIDENCE, CONFLICTING_EVIDENCE
    classification: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Explainable Structured Findings
    primary_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    contradiction_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    temporal_analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    geographical_analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    archival_signal_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    epistemic_limitations: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_investigator_actions: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Verification Method & Version
    evaluation_method: Mapped[str] = mapped_column(String(50), default="DETERMINISTIC_RULES", nullable=False)
    verifier_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)

    # Human Review Lifecycle:
    # UNREVIEWED, CONFIRMED, DISPUTED, MODIFIED
    human_review_status: Mapped[str] = mapped_column(String(30), default="UNREVIEWED", nullable=False)
    human_reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    human_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("claim_id", "version", name="uq_claim_assessment_version"),
    )

    # Relationships
    claim = relationship("ClaimRecord", back_populates="assessments")
    evidence_submission = relationship("EvidenceSubmission")
    investigation = relationship("Investigation")
    evidence_relations = relationship("ClaimEvidenceRelationRecord", back_populates="assessment", cascade="all, delete-orphan")


class ClaimEvidenceRelationRecord(Base):
    """
    Normalized relational record linking a ClaimAssessmentRecord to a specific
    supporting, contradicting, or contextual evidence item.
    Enforces passage-level granularity (<= 500 chars), character offset grounding,
    provenance retention, and explicit source independence attribution.
    """
    __tablename__ = "claim_evidence_relations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("claim_assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    claim_id: Mapped[str] = mapped_column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)

    evidence_source_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    # LOCAL_SUBMISSION, HISTORICAL_MEDIA_MATCH, EXTERNAL_FACT_CHECK, ARCHIVAL_RECORD, AUTHORITATIVE_SOURCE, USER_PROVIDED
    evidence_source_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Stance & Relationship Type:
    # SUPPORTS, CONTRADICTS, PROVIDES_CONTEXT, PARTIALLY_SUPPORTS, PARTIALLY_CONTRADICTS, DOES_NOT_ADDRESS, TEMPORAL_CONFLICT, GEOGRAPHICAL_CONFLICT
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Passage-Level Grounding (<= 500 chars)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    passage_span_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    passage_span_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Source Provenance Metadata
    source_location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_published_date: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_retrieved_date: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_author: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Source Independence Status: Explicitly UNKNOWN until 04-03 analysis
    source_independence_status: Mapped[str] = mapped_column(String(50), default="UNKNOWN", nullable=False)

    # Alignment Rationale & Limitations
    alignment_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    uncertainty_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    assessment = relationship("ClaimAssessmentRecord", back_populates="evidence_relations")
    claim = relationship("ClaimRecord")
