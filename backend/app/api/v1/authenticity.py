"""
API Endpoints for Media Authenticity, Technical Forensics, and Deepfake Detection.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.authenticity import (
    ModelRegistrationInfo,
    MediaAuthenticityResponse,
    ModelRegistryResponse
)
from app.authenticity.registry import model_registry
from app.services.authenticity_service import authenticity_service

logger = logging.getLogger("truthnet.api.authenticity")

router = APIRouter(tags=["Media Authenticity & Deepfake Detection"])


@router.get("/authenticity/models", response_model=ModelRegistryResponse)
async def get_registered_models() -> ModelRegistryResponse:
    """
    Returns the auditable Model Registry catalog, checkpoint availability,
    runtime dependencies, and hardware status. Never claims a model ran when it was only registered.
    """
    reg_models = model_registry.get_registered_models()
    model_infos = [ModelRegistrationInfo(**m) for m in reg_models]
    total_executable = sum(1 for m in reg_models if m["checkpoint_available"] and m["dependency_available"])
    total_unavailable = len(reg_models) - total_executable

    return ModelRegistryResponse(
        models=model_infos,
        hardware_runtime=model_registry.hardware_info,
        total_registered=len(reg_models),
        total_executable=total_executable,
        total_unavailable=total_unavailable
    )


@router.get(
    "/investigations/{investigation_id}/evidence/{evidence_id}/authenticity",
    response_model=MediaAuthenticityResponse
)
async def get_evidence_authenticity(
    investigation_id: str,
    evidence_id: str,
    db: AsyncSession = Depends(get_db)
) -> MediaAuthenticityResponse:
    """
    Retrieves the latest active technical forensic measurements and deepfake model outputs
    for a specific evidence item.
    """
    record = await authenticity_service.get_active_record(db, evidence_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No authenticity analysis record found for evidence item {evidence_id}."
        )
    return MediaAuthenticityResponse.model_validate(record)


@router.post(
    "/investigations/{investigation_id}/evidence/{evidence_id}/authenticity/reanalyze",
    response_model=MediaAuthenticityResponse
)
async def reanalyze_evidence_authenticity(
    investigation_id: str,
    evidence_id: str,
    db: AsyncSession = Depends(get_db)
) -> MediaAuthenticityResponse:
    """
    Triggers on-demand re-execution of technical forensics and model evaluation,
    persisting a new version of the authenticity record.
    """
    record = await authenticity_service.analyze_submission(db, evidence_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to run authenticity analysis for evidence item {evidence_id} (check format and file existence)."
        )
    return MediaAuthenticityResponse.model_validate(record)


@router.get(
    "/investigations/{investigation_id}/authenticity",
    response_model=List[MediaAuthenticityResponse]
)
async def get_investigation_authenticity_records(
    investigation_id: str,
    db: AsyncSession = Depends(get_db)
) -> List[MediaAuthenticityResponse]:
    """
    Retrieves all active authenticity records for evidence submissions in an investigation.
    """
    records = await authenticity_service.get_investigation_records(db, investigation_id)
    return [MediaAuthenticityResponse.model_validate(r) for r in records]
