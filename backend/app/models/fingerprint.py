import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class MediaFingerprint(Base):
    """
    Persistent perceptual and cryptographic fingerprint for a MediaAsset.
    Retains complete algorithm and preprocessing version provenance.
    """
    __tablename__ = "media_fingerprints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    media_asset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("media_assets.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    
    # Versioning & Preprocessing Provenance
    algorithm_name: Mapped[str] = mapped_column(String(100), default="TRUTHNET-PERCEPTUAL-HASH", nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    preprocessing_version: Mapped[str] = mapped_column(String(50), default="PREPROCESS-V1", nullable=False)
    parameters: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Hashes
    sha256_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    phash_hex: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    dhash_hex: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    ahash_hex: Mapped[str | None] = mapped_column(String(16), nullable=True)
    colorhash_hex: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Local Feature Descriptors (ORB)
    orb_keypoints_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    orb_descriptor_rel_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Status & Timestamps
    indexing_status: Mapped[str] = mapped_column(String(50), default="INDEXED", nullable=False)
    indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship
    media_asset = relationship("MediaAsset", back_populates="fingerprint")

class FrameFingerprint(Base):
    """
    Perceptual fingerprint for a derived video keyframe with timestamp provenance.
    """
    __tablename__ = "frame_fingerprints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    media_asset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("media_assets.id", ondelete="CASCADE"), index=True, nullable=False
    )
    derived_artifact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("derived_artifacts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    
    frame_index: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp_ms: Mapped[float] = mapped_column(Float, nullable=False)
    
    algorithm_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    preprocessing_version: Mapped[str] = mapped_column(String(50), default="PREPROCESS-V1", nullable=False)
    
    phash_hex: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    dhash_hex: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    
    indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    media_asset = relationship("MediaAsset", back_populates="frame_fingerprints")
    derived_artifact = relationship("DerivedArtifact")

class MediaMatchRecord(Base):
    """
    Persistent audit record of a match evaluation between an EvidenceSubmission
    and historical MediaAssets or video keyframes in the repository.
    """
    __tablename__ = "media_match_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_evidence_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evidence_submissions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source_media_asset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("media_assets.id", ondelete="CASCADE"), index=True, nullable=False
    )
    matched_media_asset_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("media_assets.id", ondelete="SET NULL"), index=True, nullable=True
    )
    matched_artifact_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("derived_artifacts.id", ondelete="SET NULL"), index=True, nullable=True
    )

    # Classification & Provenance
    classification: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # EXACT_FILE_MATCH, NEAR_DUPLICATE, SAME_PHOTOGRAPH_MODIFIED, POSSIBLE_VISUAL_SIMILARITY, INSUFFICIENT_MATCH_EVIDENCE, NO_LOCAL_MATCH_FOUND
    method: Mapped[str] = mapped_column(String(100), nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    
    # Video Frame Matching Context
    is_video_frame_match: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    matched_frame_timestamp_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    consecutive_frames_matched: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Raw Measurements (No Arbitrary Confidence Scores)
    raw_metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    classification_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    disclaimer: Mapped[str] = mapped_column(String(500), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    source_evidence = relationship("EvidenceSubmission", foreign_keys=[source_evidence_id])
    source_media_asset = relationship("MediaAsset", foreign_keys=[source_media_asset_id])
    matched_media_asset = relationship("MediaAsset", foreign_keys=[matched_media_asset_id])

