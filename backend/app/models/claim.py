import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class ClaimExtractionRun(Base):
    """
    Persistent record representing an atomic claim extraction execution run.
    Records extraction lifecycle, text content hashes, processing status,
    number of claims produced (including zero-claim runs), versioning,
    and completion telemetry.
    """
    __tablename__ = "claim_extraction_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evidence_submission_id: Mapped[str] = mapped_column(String(36), ForeignKey("evidence_submissions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Extraction Versioning & Active Run Tracking
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Content and Modality Hashes
    source_text_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_modality: Mapped[str] = mapped_column(String(100), nullable=False)  # CAPTION, RAW_TEXT, OCR_EXTRACTED, TRANSCRIPT, COMBINED[...]

    # Extractor Implementation Metadata
    extractor_name: Mapped[str] = mapped_column(String(100), default="TruthNetClaimExtractor", nullable=False)
    extractor_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)

    # Processing Status: COMPLETED, FAILED, RUNNING
    status: Mapped[str] = mapped_column(String(50), default="COMPLETED", nullable=False)

    # Count of claims produced (explicitly permits 0 for non-factual or empty text)
    claims_produced: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Error details if failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Reprocess Reason / Notes
    reprocess_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("evidence_submission_id", "version", name="uq_claim_run_submission_version"),
    )

    # Relationships
    evidence_submission = relationship("EvidenceSubmission", back_populates="claim_extraction_runs")
    claims = relationship("ClaimRecord", back_populates="extraction_run", cascade="all, delete-orphan")


class SubmissionProcessingLock(Base):
    """
    Physical database-level per-submission lock table ensuring serialized execution
    across concurrent workers and separate OS processes without relying on in-memory locks.
    Includes TTL-based stale worker recovery and monotonic fencing tokens.
    """
    __tablename__ = "submission_processing_locks"

    submission_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    locked_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fencing_token: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    locked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ClaimRecord(Base):
    """
    Persistent model representing an extracted factual claim candidate or structured proposition.
    Retains character-level evidence spans to the originating source text, full language provenance,
    explicit extraction states, scope-aware negation/polarity, attribution links,
    and versioned idempotency tracking.
    """
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_submission_id: Mapped[str] = mapped_column(String(36), ForeignKey("evidence_submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    extraction_run_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("claim_extraction_runs.id", ondelete="CASCADE"), nullable=True, index=True)

    # Extraction Versioning & Idempotency
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Verbatim text and normalized representation
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_claim: Mapped[str] = mapped_column(Text, nullable=False)

    # Extraction State Lifecycle:
    # EXTRACTED_CLAIM_CANDIDATE, STRUCTURED_PROPOSITION, PARTIAL_EXTRACTION, UNRESOLVED_STATEMENT, NON_FACTUAL_STATEMENT
    extraction_state: Mapped[str] = mapped_column(String(50), default="EXTRACTED_CLAIM_CANDIDATE", nullable=False)

    # Polarity & Negation State:
    # AFFIRMATIVE_SURFACE_SYNTAX, NEGATIVE_SURFACE_SYNTAX, UNRESOLVED_POLARITY, UNSUPPORTED_LANGUAGE_POLARITY
    polarity_state: Mapped[str] = mapped_column(String(50), default="AFFIRMATIVE_SURFACE_SYNTAX", nullable=False)

    # Attribution Flag
    is_attributed_assertion: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Structured Subject-Predicate-Object Representation (nullable when unparseable or non-factual)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    predicate: Mapped[str | None] = mapped_column(String(255), nullable=True)
    object: Mapped[str | None] = mapped_column(Text, nullable=True)
    qualifiers: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Source Modality and Character-Level Evidence Spans
    # Modality: CAPTION, RAW_TEXT, OCR_EXTRACTED, TRANSCRIPT
    source_modality: Mapped[str] = mapped_column(String(100), nullable=False)
    evidence_span_start: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence_span_end: Mapped[int] = mapped_column(Integer, nullable=False)
    source_text_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Extracted Entities (Persons, Orgs, Locations, Dates, Quantities)
    extracted_entities: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Multilingual Detection & Provenance
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    language_detection_method: Mapped[str] = mapped_column(String(50), nullable=False)
    language_detector_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    language_detector_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    translation_provenance: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Verification Eligibility & Method Audit
    is_factual_assertion: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    extraction_method: Mapped[str] = mapped_column(String(50), default="HYBRID_DETERMINISTIC_SYNTACTIC", nullable=False)
    extraction_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    uncertainty_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    investigation = relationship("Investigation", back_populates="claims")
    evidence_submission = relationship("EvidenceSubmission", back_populates="claims")
    extraction_run = relationship("ClaimExtractionRun", back_populates="claims")
    assessments = relationship("ClaimAssessmentRecord", back_populates="claim", cascade="all, delete-orphan")
