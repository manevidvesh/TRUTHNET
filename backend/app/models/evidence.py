import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class MediaAsset(Base):
    __tablename__ = "media_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sha256_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Submissions reusing this media asset
    submissions = relationship("EvidenceSubmission", back_populates="media_asset")

class EvidenceSubmission(Base):
    __tablename__ = "evidence_submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    media_asset_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("media_assets.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Submission technical classification
    submission_type: Mapped[str] = mapped_column(String(20), nullable=False)  # TEXT, IMAGE, AUDIO, VIDEO, URL
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sha256_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    
    # Direct content or URL
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    
    # User-Claimed Context (strictly separated from observed technical facts)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    claimed_event: Mapped[str | None] = mapped_column(String(255), nullable=True)
    claimed_date: Mapped[str | None] = mapped_column(String(100), nullable=True)
    claimed_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str] = mapped_column(String(20), default="en", nullable=False)
    
    # Pipeline Processing State
    processing_status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)  # PENDING, PROCESSING, COMPLETED, FAILED
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    investigation = relationship("Investigation", back_populates="evidence_submissions")
    media_asset = relationship("MediaAsset", back_populates="submissions")
