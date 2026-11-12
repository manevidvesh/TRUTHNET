from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.storage import storage_manager
from app.models.investigation import Investigation
from app.models.evidence import EvidenceSubmission, MediaAsset, ExtractionRecord, DerivedArtifact
from app.schemas.evidence import (
    EvidenceSubmissionResponse,
    EvidenceClaimCreate,
    EvidenceStatusResponse,
    MediaAssetResponse,
    ExtractionRecordResponse,
    DerivedArtifactResponse
)
from app.services.pipeline import pipeline_service

router = APIRouter(prefix="/investigations/{investigation_id}/evidence", tags=["Evidence Intake"])

def get_submission_type(mime: str) -> str:
    if mime.startswith("image/"):
        return "IMAGE"
    elif mime.startswith("video/"):
        return "VIDEO"
    elif mime.startswith("audio/"):
        return "AUDIO"
    elif mime.startswith("text/"):
        return "TEXT"
    return "IMAGE"

@router.post("/upload", response_model=EvidenceSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def upload_evidence_file(
    investigation_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    caption: Optional[str] = Form(None),
    claimed_event: Optional[str] = Form(None),
    claimed_date: Optional[str] = Form(None),
    claimed_location: Optional[str] = Form(None),
    language: str = Form("en"),
    db: AsyncSession = Depends(get_db)
):
    # Verify investigation exists
    inv_res = await db.execute(select(Investigation).where(Investigation.id == investigation_id))
    inv = inv_res.scalars().first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation not found")

    # Stream upload and compute SHA-256
    sha256_hash, mime_type, file_size, rel_path = await storage_manager.save_upload_stream(file)
    submission_type = get_submission_type(mime_type)

    # Find or create MediaAsset (Deduplication within single atomic transaction)
    asset_res = await db.execute(select(MediaAsset).where(MediaAsset.sha256_hash == sha256_hash))
    asset = asset_res.scalars().first()
    if not asset:
        asset = MediaAsset(
            sha256_hash=sha256_hash,
            mime_type=mime_type,
            file_path=rel_path,
            file_size_bytes=file_size
        )
        db.add(asset)
        await db.flush()  # Flush to generate asset.id without committing prematurely

    # Create distinct EvidenceSubmission
    submission = EvidenceSubmission(
        investigation_id=investigation_id,
        media_asset_id=asset.id,
        submission_type=submission_type,
        original_filename=file.filename,
        mime_type=mime_type,
        file_size_bytes=file_size,
        sha256_hash=sha256_hash,
        caption=caption,
        claimed_event=claimed_event,
        claimed_date=claimed_date,
        claimed_location=claimed_location,
        language=language,
        processing_status="PENDING"
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    # Queue background validation task
    background_tasks.add_task(pipeline_service.process_evidence_item, submission.id)

    # Load with media asset for response
    asset_response = MediaAssetResponse(
        id=asset.id,
        sha256_hash=asset.sha256_hash,
        mime_type=asset.mime_type,
        file_path=asset.file_path,
        file_size_bytes=asset.file_size_bytes,
        created_at=asset.created_at
    )
    resp = EvidenceSubmissionResponse.model_validate(submission)
    resp.media_asset = asset_response
    return resp

@router.post("/claim", response_model=EvidenceSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_evidence_claim(
    investigation_id: str,
    payload: EvidenceClaimCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    inv_res = await db.execute(select(Investigation).where(Investigation.id == investigation_id))
    inv = inv_res.scalars().first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation not found")

    if not payload.raw_text and not payload.source_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Either raw_text or source_url must be provided")

    media_asset_id = None
    media_asset_response = None
    sha256_hash = None
    file_size = None
    mime_type = None

    if payload.raw_text:
        submission_type = "TEXT"
        sha256_hash, mime_type, file_size, rel_path = storage_manager.save_raw_text(payload.raw_text)
        
        # Check MediaAsset
        asset_res = await db.execute(select(MediaAsset).where(MediaAsset.sha256_hash == sha256_hash))
        asset = asset_res.scalars().first()
        if not asset:
            asset = MediaAsset(
                sha256_hash=sha256_hash,
                mime_type=mime_type,
                file_path=rel_path,
                file_size_bytes=file_size
            )
            db.add(asset)
            await db.flush()
        media_asset_id = asset.id
        media_asset_response = MediaAssetResponse.model_validate(asset)
    else:
        submission_type = "URL"
        mime_type = "text/html"

    submission = EvidenceSubmission(
        investigation_id=investigation_id,
        media_asset_id=media_asset_id,
        submission_type=submission_type,
        mime_type=mime_type,
        file_size_bytes=file_size,
        sha256_hash=sha256_hash,
        raw_text=payload.raw_text,
        source_url=payload.source_url,
        caption=payload.caption,
        claimed_event=payload.claimed_event,
        claimed_date=payload.claimed_date,
        claimed_location=payload.claimed_location,
        language=payload.language,
        processing_status="PENDING"
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    # Queue background validation task
    background_tasks.add_task(pipeline_service.process_evidence_item, submission.id)

    resp = EvidenceSubmissionResponse.model_validate(submission)
    resp.media_asset = media_asset_response
    return resp

@router.get("/", response_model=List[EvidenceSubmissionResponse])
async def list_evidence_submissions(
    investigation_id: str,
    db: AsyncSession = Depends(get_db)
):
    query = select(EvidenceSubmission).options(
        selectinload(EvidenceSubmission.media_asset)
    ).where(EvidenceSubmission.investigation_id == investigation_id).order_by(EvidenceSubmission.created_at.desc())
    
    result = await db.execute(query)
    submissions = result.scalars().all()
    return [EvidenceSubmissionResponse.model_validate(sub) for sub in submissions]

@router.get("/{evidence_id}", response_model=EvidenceSubmissionResponse)
async def get_evidence_submission(
    investigation_id: str,
    evidence_id: str,
    db: AsyncSession = Depends(get_db)
):
    query = select(EvidenceSubmission).options(
        selectinload(EvidenceSubmission.media_asset)
    ).where(
        EvidenceSubmission.investigation_id == investigation_id,
        EvidenceSubmission.id == evidence_id
    )
    result = await db.execute(query)
    sub = result.scalars().first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence submission not found")
    return EvidenceSubmissionResponse.model_validate(sub)

@router.get("/{evidence_id}/status", response_model=EvidenceStatusResponse)
async def get_evidence_status(
    investigation_id: str,
    evidence_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(EvidenceSubmission).where(
            EvidenceSubmission.investigation_id == investigation_id,
            EvidenceSubmission.id == evidence_id
        )
    )
    sub = result.scalars().first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence submission not found")
    
    return EvidenceStatusResponse(
        evidence_id=sub.id,
        investigation_id=sub.investigation_id,
        processing_status=sub.processing_status,
        error_message=sub.error_message,
        created_at=sub.created_at
    )

@router.post("/{evidence_id}/retry", response_model=EvidenceStatusResponse)
async def retry_evidence_processing(
    investigation_id: str,
    evidence_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(EvidenceSubmission).where(
            EvidenceSubmission.investigation_id == investigation_id,
            EvidenceSubmission.id == evidence_id
        )
    )
    sub = result.scalars().first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence submission not found")

    sub.processing_status = "PENDING"
    sub.error_message = None
    await db.commit()

    background_tasks.add_task(pipeline_service.process_evidence_item, sub.id)

    return EvidenceStatusResponse(
        evidence_id=sub.id,
        investigation_id=sub.investigation_id,
        processing_status=sub.processing_status,
        error_message=sub.error_message,
        created_at=sub.created_at
    )

@router.get("/{evidence_id}/extracted", response_model=ExtractionRecordResponse)
async def get_extracted_evidence_data(
    investigation_id: str,
    evidence_id: str,
    db: AsyncSession = Depends(get_db)
):
    # Verify evidence belongs to investigation
    ev_res = await db.execute(
        select(EvidenceSubmission).where(
            EvidenceSubmission.investigation_id == investigation_id,
            EvidenceSubmission.id == evidence_id
        )
    )
    evidence = ev_res.scalars().first()
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence submission not found")

    rec_res = await db.execute(
        select(ExtractionRecord).where(
            ExtractionRecord.evidence_submission_id == evidence_id,
            ExtractionRecord.is_active == True
        ).order_by(ExtractionRecord.version.desc())
    )
    record = rec_res.scalars().first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction record not yet available or processing pending"
        )
    return ExtractionRecordResponse.model_validate(record)

@router.get("/{evidence_id}/artifacts", response_model=List[DerivedArtifactResponse])
async def list_derived_artifacts(
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

    art_res = await db.execute(
        select(DerivedArtifact).where(
            DerivedArtifact.evidence_submission_id == evidence_id
        ).order_by(DerivedArtifact.created_at.asc())
    )
    artifacts = art_res.scalars().all()
    
    responses = []
    for art in artifacts:
        dl_url = f"/api/v1/investigations/{investigation_id}/evidence/{evidence_id}/artifacts/{art.id}/content"
        responses.append(
            DerivedArtifactResponse(
                id=art.id,
                evidence_submission_id=art.evidence_submission_id,
                artifact_type=art.artifact_type,
                sha256_hash=art.sha256_hash,
                file_size_bytes=art.file_size_bytes,
                mime_type=art.mime_type,
                artifact_metadata=art.artifact_metadata,
                download_url=dl_url,
                created_at=art.created_at
            )
        )
    return responses

@router.get("/{evidence_id}/artifacts/{artifact_id}/content")
async def get_derived_artifact_content(
    investigation_id: str,
    evidence_id: str,
    artifact_id: str,
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

    art_res = await db.execute(
        select(DerivedArtifact).where(
            DerivedArtifact.id == artifact_id,
            DerivedArtifact.evidence_submission_id == evidence_id
        )
    )
    artifact = art_res.scalars().first()
    if not artifact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Derived artifact not found")

    safe_path = storage_manager.resolve_safe_path(artifact.relative_path)
    if not safe_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact file missing on disk")

    return FileResponse(
        path=safe_path,
        media_type=artifact.mime_type,
        filename=safe_path.name
    )

