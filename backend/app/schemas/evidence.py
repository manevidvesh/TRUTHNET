from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class MediaAssetResponse(BaseModel):
    id: str
    sha256_hash: str
    mime_type: str
    file_path: str
    file_size_bytes: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class EvidenceClaimCreate(BaseModel):
    raw_text: str | None = Field(None, description="Verbatim text claim, post body, or caption")
    source_url: str | None = Field(None, description="Public URL where claim was observed")
    caption: str | None = Field(None, description="Contextual caption or description")
    claimed_event: str | None = Field(None, description="Purported real-world event")
    claimed_date: str | None = Field(None, description="Purported date of occurrence")
    claimed_location: str | None = Field(None, description="Purported location or region")
    language: str = Field("en", description="Claim language code (e.g. en, hi, te)")

class EvidenceSubmissionResponse(BaseModel):
    id: str
    investigation_id: str
    media_asset_id: str | None = None
    submission_type: str
    original_filename: str | None = None
    mime_type: str | None = None
    file_size_bytes: int | None = None
    sha256_hash: str | None = None
    raw_text: str | None = None
    source_url: str | None = None
    caption: str | None = None
    claimed_event: str | None = None
    claimed_date: str | None = None
    claimed_location: str | None = None
    language: str
    processing_status: str
    error_message: str | None = None
    created_at: datetime
    media_asset: MediaAssetResponse | None = None

    model_config = ConfigDict(from_attributes=True)

class EvidenceStatusResponse(BaseModel):
    evidence_id: str
    investigation_id: str
    processing_status: str
    error_message: str | None = None
    created_at: datetime

class DerivedArtifactResponse(BaseModel):
    id: str
    evidence_submission_id: str
    artifact_type: str
    sha256_hash: str
    file_size_bytes: int
    mime_type: str
    artifact_metadata: dict | None = None
    download_url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ExtractionRecordResponse(BaseModel):
    id: str
    evidence_submission_id: str
    version: int
    is_active: bool
    category: str = "OBSERVED_DATA"
    extractor_name: str
    extractor_version: str
    execution_timestamp: datetime
    status: str
    modality_statuses: dict | None = None
    technical_metadata: dict | None = None
    video_frames: list[dict] | None = None
    ocr_result: dict | None = None
    transcription_result: dict | None = None
    derived_artifact_ids: list[str] | None = None
    error_message: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrchestratedItemResult(BaseModel):
    submission_id: str | None = None
    item_type: str  # FILE, TEXT, URL
    filename_or_snippet: str
    detected_modality: str  # IMAGE, VIDEO, AUDIO, TEXT, URL, UNSUPPORTED
    status: str  # QUEUED, PROCESSING, COMPLETED, PARTIAL, FAILED, UNSUPPORTED
    assigned_routes: list[str] = Field(default_factory=list)
    sha256_hash: str | None = None
    mime_type: str | None = None
    file_size_bytes: int | None = None
    error_message: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UniversalIntakeResponse(BaseModel):
    investigation_id: str
    total_items_received: int
    accepted_items_count: int
    rejected_items_count: int
    items: list[OrchestratedItemResult]
    summary: str

    model_config = ConfigDict(from_attributes=True)


