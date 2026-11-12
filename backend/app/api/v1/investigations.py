from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.investigation import Investigation, utc_now
from app.models.evidence import EvidenceSubmission
from app.schemas.investigation import InvestigationCreate, InvestigationUpdate, InvestigationResponse

router = APIRouter(prefix="/investigations", tags=["Investigations"])

@router.get("/", response_model=List[InvestigationResponse])
async def list_investigations(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    query = select(
        Investigation,
        func.count(EvidenceSubmission.id).label("evidence_count")
    ).outerjoin(
        EvidenceSubmission, Investigation.id == EvidenceSubmission.investigation_id
    ).group_by(Investigation.id).order_by(desc(Investigation.updated_at))

    if status_filter:
        query = query.where(Investigation.status == status_filter.upper())
    if priority_filter:
        query = query.where(Investigation.priority == priority_filter.upper())

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    rows = result.all()

    items = []
    for inv, count in rows:
        resp = InvestigationResponse(
            id=inv.id,
            title=inv.title,
            description=inv.description,
            status=inv.status,
            priority=inv.priority,
            created_at=inv.created_at,
            updated_at=inv.updated_at,
            evidence_count=count
        )
        items.append(resp)
    return items

@router.post("/", response_model=InvestigationResponse, status_code=status.HTTP_201_CREATED)
async def create_investigation(
    payload: InvestigationCreate,
    db: AsyncSession = Depends(get_db)
):
    inv = Investigation(
        title=payload.title,
        description=payload.description,
        priority=payload.priority.upper(),
        status="ACTIVE"
    )
    db.add(inv)
    await db.commit()
    await db.refresh(inv)

    return InvestigationResponse(
        id=inv.id,
        title=inv.title,
        description=inv.description,
        status=inv.status,
        priority=inv.priority,
        created_at=inv.created_at,
        updated_at=inv.updated_at,
        evidence_count=0
    )

@router.get("/{investigation_id}", response_model=InvestigationResponse)
async def get_investigation(
    investigation_id: str,
    db: AsyncSession = Depends(get_db)
):
    query = select(
        Investigation,
        func.count(EvidenceSubmission.id).label("evidence_count")
    ).outerjoin(
        EvidenceSubmission, Investigation.id == EvidenceSubmission.investigation_id
    ).where(Investigation.id == investigation_id).group_by(Investigation.id)

    result = await db.execute(query)
    row = result.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation not found")

    inv, count = row
    return InvestigationResponse(
        id=inv.id,
        title=inv.title,
        description=inv.description,
        status=inv.status,
        priority=inv.priority,
        created_at=inv.created_at,
        updated_at=inv.updated_at,
        evidence_count=count
    )

@router.patch("/{investigation_id}", response_model=InvestigationResponse)
async def update_investigation(
    investigation_id: str,
    payload: InvestigationUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Investigation).where(Investigation.id == investigation_id))
    inv = result.scalars().first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation not found")

    if payload.title is not None:
        inv.title = payload.title
    if payload.description is not None:
        inv.description = payload.description
    if payload.status is not None:
        inv.status = payload.status.upper()
    if payload.priority is not None:
        inv.priority = payload.priority.upper()
    inv.updated_at = utc_now()

    await db.commit()
    await db.refresh(inv)

    # Count evidence
    count_res = await db.execute(
        select(func.count(EvidenceSubmission.id)).where(EvidenceSubmission.investigation_id == investigation_id)
    )
    count = count_res.scalar() or 0

    return InvestigationResponse(
        id=inv.id,
        title=inv.title,
        description=inv.description,
        status=inv.status,
        priority=inv.priority,
        created_at=inv.created_at,
        updated_at=inv.updated_at,
        evidence_count=count
    )

@router.delete("/{investigation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_investigation(
    investigation_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Investigation).where(Investigation.id == investigation_id))
    inv = result.scalars().first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation not found")

    await db.delete(inv)
    await db.commit()
    return None
