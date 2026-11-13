"""
Database models for Media Authenticity & Deepfake Model Detection.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MediaAuthenticityRecord(Base):
    """
    Stores versioned, evidence-backed forensic measurements and deepfake model outputs.
    Strictly separates technical observed anomalies from model inference results.
    """
    __tablename__ = "media_authenticity_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evidence_submission_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evidence_submissions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    media_asset_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("media_assets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Observed Forensic Measurements (ELA, noise variance, spectral slope, EXIF)
    forensic_analysis: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Model Registry Snapshot
    model_registry_summary: Mapped[dict] = mapped_column(JSON, nullable=False)
    executed_model_results: Mapped[list] = mapped_column(JSON, nullable=False)
    unavailable_models: Mapped[list] = mapped_column(JSON, nullable=False)

    # Video keyframe breakdown (when evidence is VIDEO)
    video_frame_analyses: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Epistemic limitations & disclaimers
    epistemic_disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    submission = relationship("EvidenceSubmission", backref="authenticity_records")
