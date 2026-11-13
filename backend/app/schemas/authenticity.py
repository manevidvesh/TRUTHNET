"""
Pydantic schemas for Media Authenticity & Deepfake Model Detection.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class ModelRegistrationInfo(BaseModel):
    model_id: str
    name: str
    architecture: str
    version: str
    supported_modalities: List[str]
    supported_formats: List[str]
    checkpoint_available: bool
    dependency_available: bool
    runtime_device: str
    status: str
    known_limitations: List[str]
    description: str

    model_config = ConfigDict(from_attributes=True)


class ForensicAnalysisResult(BaseModel):
    ela_analysis: Dict[str, Any]
    noise_analysis: Dict[str, Any]
    spectral_analysis: Dict[str, Any]
    compression_analysis: Dict[str, Any]
    metadata_anomalies: Dict[str, Any]
    face_boundary_analysis: Optional[Dict[str, Any]] = None
    forensic_summary: str

    model_config = ConfigDict(from_attributes=True)


class ExecutedModelResult(BaseModel):
    model_id: str
    model_name: str
    version: str
    runtime_device: str
    raw_metrics: Dict[str, Any]
    interpretation: str
    evaluation_limitations: List[str]

    model_config = ConfigDict(from_attributes=True)


class UnavailableModelResult(BaseModel):
    model_id: str
    model_name: str
    status: str
    reason: str
    prerequisites: str

    model_config = ConfigDict(from_attributes=True)


class MediaAuthenticityResponse(BaseModel):
    id: str
    evidence_submission_id: str
    media_asset_id: Optional[str] = None
    version: int
    is_active: bool
    forensic_analysis: Dict[str, Any]
    model_registry_summary: Dict[str, Any]
    executed_model_results: List[Dict[str, Any]]
    unavailable_models: List[Dict[str, Any]]
    video_frame_analyses: Optional[List[Dict[str, Any]]] = None
    epistemic_disclaimer: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ModelRegistryResponse(BaseModel):
    models: List[ModelRegistrationInfo]
    hardware_runtime: Dict[str, Any]
    total_registered: int
    total_executable: int
    total_unavailable: int

    model_config = ConfigDict(from_attributes=True)
