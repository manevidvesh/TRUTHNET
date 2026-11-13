"""
API Endpoints for Coordinated Misinformation Intelligence.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.coordination import CoordinationClusterRecord
from app.schemas.coordination import (
    CoordinationClusterResponse,
    CoordinationAnalysisResponse
)
from app.coordination.engine import coordination_engine

logger = logging.getLogger("truthnet.api.coordination")

router = APIRouter(prefix="/investigations/{investigation_id}/coordination", tags=["Coordination Intelligence"])


@router.get("", response_model=CoordinationAnalysisResponse)
async def get_coordination_analysis(
    investigation_id: str,
    db: AsyncSession = Depends(get_db)
) -> CoordinationAnalysisResponse:
    """
    Returns existing coordination clusters and detected distribution signals for an investigation.
    If no analysis has been run yet, triggers analysis automatically.
    """
    clusters = await coordination_engine.get_clusters(db, investigation_id)
    if not clusters:
        clusters = await coordination_engine.analyze_investigation(db, investigation_id)

    cluster_responses = [CoordinationClusterResponse.model_validate(c) for c in clusters]
    signals = list(set(c.cluster_type for c in clusters if c.cluster_type != "INSUFFICIENT_COORDINATION_EVIDENCE"))

    return CoordinationAnalysisResponse(
        investigation_id=investigation_id,
        clusters=cluster_responses,
        total_clusters=len(cluster_responses),
        signals_detected=signals,
        epistemic_disclaimer=coordination_engine.EPISTEMIC_DISCLAIMER
    )


@router.post("/analyze", response_model=CoordinationAnalysisResponse)
async def trigger_coordination_analysis(
    investigation_id: str,
    db: AsyncSession = Depends(get_db)
) -> CoordinationAnalysisResponse:
    """
    Triggers on-demand re-analysis of coordination signals across submissions.
    """
    clusters = await coordination_engine.analyze_investigation(db, investigation_id)
    cluster_responses = [CoordinationClusterResponse.model_validate(c) for c in clusters]
    signals = list(set(c.cluster_type for c in clusters if c.cluster_type != "INSUFFICIENT_COORDINATION_EVIDENCE"))

    return CoordinationAnalysisResponse(
        investigation_id=investigation_id,
        clusters=cluster_responses,
        total_clusters=len(cluster_responses),
        signals_detected=signals,
        epistemic_disclaimer=coordination_engine.EPISTEMIC_DISCLAIMER
    )


@router.post("/{cluster_id}/review", response_model=CoordinationClusterResponse)
async def review_coordination_cluster(
    investigation_id: str,
    cluster_id: str,
    review_status: str = Body(..., embed=True),
    reviewer_notes: Optional[str] = Body(None, embed=True),
    db: AsyncSession = Depends(get_db)
) -> CoordinationClusterResponse:
    """
    Human-in-the-loop review of a detected coordination cluster.
    """
    res = await db.execute(
        select(CoordinationClusterRecord).where(
            CoordinationClusterRecord.id == cluster_id,
            CoordinationClusterRecord.investigation_id == investigation_id
        )
    )
    cluster = res.scalars().first()
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coordination cluster {cluster_id} not found."
        )

    cluster.review_status = review_status
    if reviewer_notes:
        cluster.reviewer_notes = reviewer_notes
    await db.commit()
    await db.refresh(cluster)

    return CoordinationClusterResponse.model_validate(cluster)
