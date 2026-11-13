from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.claim import ClaimRecord
from app.models.evidence import EvidenceSubmission
from app.models.context_verification import ClaimAssessmentRecord, ClaimEvidenceRelationRecord
from app.schemas.context_verification import (
    ClaimAssessmentResponse,
    ClaimAssessmentHistoryResponse,
    ClaimEvidenceRelationResponse,
    HumanReviewSubmission,
    ClaimVerificationRequest,
    HumanReviewStatus
)
from app.context.verifier import ContextualClaimVerifier

router = APIRouter(tags=["Claim Intelligence & Contextual Verification"])

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

@router.post("/claims/{claim_id}/verify", response_model=ClaimAssessmentResponse, status_code=status.HTTP_200_OK)
async def verify_claim_endpoint(
    claim_id: str,
    payload: Optional[ClaimVerificationRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Executes contextual verification on a specific ClaimRecord.
    Optionally accepts a list of EvidenceItem objects to evaluate alongside
    local historical media matches and metadata.
    """
    claim_res = await db.execute(select(ClaimRecord).where(ClaimRecord.id == claim_id))
    claim = claim_res.scalars().first()
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ClaimRecord with id '{claim_id}' not found."
        )

    evidence_items = payload.evidence_items if payload else None

    try:
        assessment = await ContextualClaimVerifier.verify_claim(
            session=db,
            claim_id=claim_id,
            evidence_items=evidence_items
        )
        return assessment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Contextual verification failed: {str(e)}"
        )

@router.get("/claims/{claim_id}/assessment", response_model=ClaimAssessmentResponse, status_code=status.HTTP_200_OK)
async def get_active_claim_assessment(
    claim_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves the current active ClaimAssessmentRecord and its linked evidence relations.
    """
    stmt = select(ClaimAssessmentRecord).where(
        ClaimAssessmentRecord.claim_id == claim_id,
        ClaimAssessmentRecord.is_active == True
    ).options(selectinload(ClaimAssessmentRecord.evidence_relations))

    res = await db.execute(stmt)
    assessment = res.scalars().first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active assessment found for ClaimRecord '{claim_id}'."
        )
    return assessment

@router.get("/claims/{claim_id}/assessment/history", response_model=ClaimAssessmentHistoryResponse, status_code=status.HTTP_200_OK)
async def get_claim_assessment_history(
    claim_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves the complete immutable version history of assessments for a ClaimRecord.
    """
    # Verify claim exists
    claim_res = await db.execute(select(ClaimRecord).where(ClaimRecord.id == claim_id))
    if not claim_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ClaimRecord with id '{claim_id}' not found."
        )

    stmt = select(ClaimAssessmentRecord).where(
        ClaimAssessmentRecord.claim_id == claim_id
    ).options(
        selectinload(ClaimAssessmentRecord.evidence_relations)
    ).order_by(desc(ClaimAssessmentRecord.version))

    res = await db.execute(stmt)
    history = res.scalars().all()

    active = next((a for a in history if a.is_active), None)

    return ClaimAssessmentHistoryResponse(
        claim_id=claim_id,
        active_assessment=active,
        history=history,
        total_versions=len(history)
    )

@router.post("/claims/{claim_id}/assessment/{assessment_id}/review", response_model=ClaimAssessmentResponse, status_code=status.HTTP_200_OK)
async def submit_human_review(
    claim_id: str,
    assessment_id: str,
    review_data: HumanReviewSubmission,
    db: AsyncSession = Depends(get_db)
):
    """
    Submits an investigator's review determination (CONFIRMED, DISPUTED, MODIFIED)
    with audit notes and timestamp.
    """
    stmt = select(ClaimAssessmentRecord).where(
        ClaimAssessmentRecord.id == assessment_id,
        ClaimAssessmentRecord.claim_id == claim_id
    ).options(selectinload(ClaimAssessmentRecord.evidence_relations))

    res = await db.execute(stmt)
    assessment = res.scalars().first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment '{assessment_id}' for claim '{claim_id}' not found."
        )

    assessment.human_review_status = review_data.status.value if hasattr(review_data.status, "value") else str(review_data.status)
    assessment.human_reviewer_notes = review_data.notes
    assessment.reviewed_by = review_data.reviewer_id
    assessment.human_reviewed_at = utc_now()

    await db.commit()
    await db.refresh(assessment)
    return assessment

@router.get("/submissions/{submission_id}/assessments", response_model=List[ClaimAssessmentResponse], status_code=status.HTTP_200_OK)
async def get_submission_claim_assessments(
    submission_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Lists active assessments for all claims extracted from a specific EvidenceSubmission.
    """
    # Verify submission exists
    sub_res = await db.execute(select(EvidenceSubmission).where(EvidenceSubmission.id == submission_id))
    if not sub_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"EvidenceSubmission '{submission_id}' not found."
        )

    stmt = select(ClaimAssessmentRecord).where(
        ClaimAssessmentRecord.evidence_submission_id == submission_id,
        ClaimAssessmentRecord.is_active == True
    ).options(selectinload(ClaimAssessmentRecord.evidence_relations))

    res = await db.execute(stmt)
    return res.scalars().all()
