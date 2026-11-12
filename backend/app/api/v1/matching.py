import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.investigation import Investigation
from app.models.evidence import EvidenceSubmission
from app.models.fingerprint import MediaMatchRecord
from app.schemas.fingerprint import MediaMatchResponse
from app.matching.engine import match_engine
from app.matching.privacy import match_privacy_policy
from app.indexing.indexer import media_indexer

logger = logging.getLogger("truthnet.api.matching")

router = APIRouter(prefix="/investigations/{investigation_id}/evidence/{evidence_id}/matching", tags=["Historical Matching"])
indexing_router = APIRouter(prefix="/indexing", tags=["Media Indexing"])

@router.post("/match", response_model=List[MediaMatchResponse])
async def execute_media_matching(
    investigation_id: str,
    evidence_id: str,
    max_hamming: int = 12,
    db: AsyncSession = Depends(get_db)
):
    # Verify investigation and evidence exist
    ev_res = await db.execute(
        select(EvidenceSubmission).where(
            EvidenceSubmission.investigation_id == investigation_id,
            EvidenceSubmission.id == evidence_id
        )
    )
    evidence = ev_res.scalars().first()
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence submission not found")

    matches = await match_engine.match_evidence(
        db_session=db,
        evidence_id=evidence_id,
        max_hamming=max_hamming
    )
    await db.commit()

    return await match_privacy_policy.sanitize_matches(
        matches=matches,
        requesting_investigation_id=investigation_id,
        db_session=db
    )

@router.get("/matches", response_model=List[MediaMatchResponse])
async def get_evidence_matches(
    investigation_id: str,
    evidence_id: str,
    db: AsyncSession = Depends(get_db)
):
    ev_res = await db.execute(
        select(EvidenceSubmission).where(
            EvidenceSubmission.investigation_id == investigation_id,
            EvidenceSubmission.id == evidence_id
        )
    )
    evidence = ev_res.scalars().first()
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence submission not found")

    matches_res = await db.execute(
        select(MediaMatchRecord).where(
            MediaMatchRecord.source_evidence_id == evidence_id
        ).order_by(MediaMatchRecord.created_at.desc())
    )
    matches = matches_res.scalars().all()

    return await match_privacy_policy.sanitize_matches(
        matches=matches,
        requesting_investigation_id=investigation_id,
        db_session=db
    )

@router.get("/external-search")
async def get_external_reverse_search_status(
    investigation_id: str,
    evidence_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    External reverse search provider status.
    In accordance with TRUTHNET engineering constraints, external commercial search engines
    (Google Lens, Bing, TinEye, Wayback) are marked as UNAVAILABLE.
    No fabricated or mocked external hits are ever returned.
    """
    ev_res = await db.execute(
        select(EvidenceSubmission).where(
            EvidenceSubmission.investigation_id == investigation_id,
            EvidenceSubmission.id == evidence_id
        )
    )
    evidence = ev_res.scalars().first()
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence submission not found")

    return {
        "status": "UNAVAILABLE",
        "evidence_id": evidence_id,
        "providers": {
            "google_lens": {"status": "UNAVAILABLE", "reason": "External search integration not configured in local-first environment"},
            "tineye": {"status": "UNAVAILABLE", "reason": "External search integration not configured in local-first environment"},
            "bing_visual_search": {"status": "UNAVAILABLE", "reason": "External search integration not configured in local-first environment"},
            "wayback_machine": {"status": "UNAVAILABLE", "reason": "External search integration not configured in local-first environment"}
        },
        "disclaimer": "External search integrations are unavailable in this release. Matches are derived exclusively from the local historical media index."
    }

@indexing_router.post("/reindex")
async def trigger_media_reindexing(
    db: AsyncSession = Depends(get_db)
):
    results = await media_indexer.reindex_all(db)
    await db.commit()
    return {
        "status": "COMPLETED",
        "results": results
    }
