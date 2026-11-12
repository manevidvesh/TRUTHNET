from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field

class MediaFingerprintResponse(BaseModel):
    id: str
    media_asset_id: str
    algorithm_name: str
    algorithm_version: str
    preprocessing_version: str
    parameters: Optional[Dict[str, Any]] = None
    sha256_hash: str
    phash_hex: str
    dhash_hex: str
    ahash_hex: Optional[str] = None
    colorhash_hex: Optional[str] = None
    orb_keypoints_count: int
    indexing_status: str
    indexed_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FrameFingerprintResponse(BaseModel):
    id: str
    media_asset_id: str
    derived_artifact_id: str
    frame_index: int
    timestamp_ms: float
    algorithm_version: str
    preprocessing_version: str
    phash_hex: str
    dhash_hex: str
    indexed_at: datetime

    model_config = ConfigDict(from_attributes=True)
