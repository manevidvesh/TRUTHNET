"""
Universal Evidence Input Orchestration Service.

Provides a unified intake and dispatch layer for multimodal evidence:
- Automatically classifies modalities (Images, Videos, Audio, Text Claims, URLs).
- Validates file sizes, zero-byte corruptions, and supported formats.
- Dispatches each item to its appropriate processing pipeline.
- Supports mixed-modality and batch submissions within a single investigation.
- Tracks itemized processing routes, individual failures, and overall ingestion status.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from urllib.parse import urlparse
from fastapi import UploadFile, BackgroundTasks, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.investigation import Investigation
from app.models.evidence import EvidenceSubmission, MediaAsset
from app.core.storage import storage_manager
from app.schemas.evidence import OrchestratedItemResult, UniversalIntakeResponse
from app.services.pipeline import pipeline_service

logger = logging.getLogger("truthnet.orchestrator")


class EvidenceOrchestrator:
    """
    Coordinates unified evidence ingestion across all supported modalities.
    """

    SUPPORTED_IMAGE_MIMES = {
        "image/jpeg", "image/png", "image/webp", "image/bmp", "image/gif", "image/tiff"
    }
    SUPPORTED_VIDEO_MIMES = {
        "video/mp4", "video/webm", "video/quicktime", "video/x-matroska", "video/avi", "video/x-msvideo"
    }
    SUPPORTED_AUDIO_MIMES = {
        "audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3", "audio/ogg", "audio/flac", "audio/aac", "audio/m4a"
    }
    SUPPORTED_TEXT_MIMES = {
        "text/plain", "text/markdown", "application/json"
    }

    SUPPORTED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff", ".tif"}
    SUPPORTED_VIDEO_EXTS = {".mp4", ".webm", ".mov", ".mkv", ".avi"}
    SUPPORTED_AUDIO_EXTS = {".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a"}
    SUPPORTED_TEXT_EXTS = {".txt", ".md", ".json"}

    @classmethod
    def detect_file_modality(cls, filename: str, mime_type: Optional[str]) -> Tuple[str, List[str]]:
        """
        Determines the evidence modality and assigned processing routes from MIME and extension.
        Returns (modality, assigned_routes).
        """
        ext = Path(filename).suffix.lower() if filename else ""
        mime = (mime_type or "").lower().split(";")[0].strip()

        if mime in cls.SUPPORTED_IMAGE_MIMES or ext in cls.SUPPORTED_IMAGE_EXTS or (mime and mime.startswith("image/")):
            return "IMAGE", [
                "Technical Metadata (EXIF/Sensor)",
                "Dual-Engine OCR Extraction",
                "Perceptual Fingerprinting (pHash/dHash)",
                "ORB + RANSAC Historical Rediscovery",
                "Factual Claim Extraction",
                "Contextual Verification"
            ]
        elif mime in cls.SUPPORTED_VIDEO_MIMES or ext in cls.SUPPORTED_VIDEO_EXTS or (mime and mime.startswith("video/")):
            return "VIDEO", [
                "Container & Stream Metadata",
                "Boundary Keyframe Sampling",
                "PyAV Audio Demuxing",
                "CTranslate2 Whisper Speech Transcription",
                "Keyframe Perceptual Indexing",
                "Factual Claim Extraction"
            ]
        elif mime in cls.SUPPORTED_AUDIO_MIMES or ext in cls.SUPPORTED_AUDIO_EXTS or (mime and mime.startswith("audio/")):
            return "AUDIO", [
                "Technical Audio Metadata",
                "CTranslate2 Whisper Speech Transcription",
                "Factual Claim Extraction",
                "Contextual Verification"
            ]
        elif mime in cls.SUPPORTED_TEXT_MIMES or ext in cls.SUPPORTED_TEXT_EXTS or (mime and mime.startswith("text/")):
            return "TEXT", [
                "Text Proposition Normalization",
                "Multilingual Factual Claim Extraction",
                "Claim Lineage Mapping",
                "Contextual Verification"
            ]
        else:
            return "UNSUPPORTED", []

    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validates whether a string has a valid HTTP/HTTPS scheme and network location.
        """
        try:
            parsed = urlparse(url.strip())
            return parsed.scheme in ("http", "https") and bool(parsed.netloc)
        except Exception:
            return False

    async def orchestrate_intake(
        self,
        db: AsyncSession,
        investigation_id: str,
        files: Optional[List[UploadFile]] = None,
        raw_text: Optional[str] = None,
        source_url: Optional[str] = None,
        caption: Optional[str] = None,
        claimed_event: Optional[str] = None,
        claimed_date: Optional[str] = None,
        claimed_location: Optional[str] = None,
        language: str = "en",
        background_tasks: Optional[BackgroundTasks] = None,
        sync_process: bool = False
    ) -> UniversalIntakeResponse:
        """
        Ingests, validates, classifies, and dispatches single or mixed-modality evidence.
        Fault-isolated: individual item rejection or failure never corrupts the investigation.
        """
        # 1. Verify Investigation exists
        inv_res = await db.execute(select(Investigation).where(Investigation.id == investigation_id))
        inv = inv_res.scalars().first()
        if not inv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Investigation '{investigation_id}' not found"
            )

        # 2. Check input presence
        valid_files = [f for f in (files or []) if f and f.filename and f.filename.strip()]
        has_files = len(valid_files) > 0
        has_text = bool(raw_text and raw_text.strip())
        has_url = bool(source_url and source_url.strip())

        if not has_files and not has_text and not has_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one media file, text claim, or source URL must be provided."
            )

        items_results: List[OrchestratedItemResult] = []
        submission_ids_to_process: List[str] = []
        accepted_count = 0
        rejected_count = 0

        # 3. Process Uploaded Files
        for file in valid_files:
            modality, routes = self.detect_file_modality(file.filename, file.content_type)

            # Check unsupported formats
            if modality == "UNSUPPORTED":
                items_results.append(
                    OrchestratedItemResult(
                        submission_id=None,
                        item_type="FILE",
                        filename_or_snippet=file.filename,
                        detected_modality="UNSUPPORTED",
                        status="UNSUPPORTED",
                        assigned_routes=[],
                        error_message=f"Unsupported file format or MIME type: {file.content_type or 'unknown'}"
                    )
                )
                rejected_count += 1
                continue

            # Stream save and compute hash
            try:
                sha256_hash, mime_type, file_size, rel_path = await storage_manager.save_upload_stream(file)
            except ValueError as ve:
                # 0-byte or corrupt file
                items_results.append(
                    OrchestratedItemResult(
                        submission_id=None,
                        item_type="FILE",
                        filename_or_snippet=file.filename,
                        detected_modality=modality,
                        status="FAILED",
                        assigned_routes=routes,
                        error_message=str(ve)
                    )
                )
                rejected_count += 1
                continue
            except Exception as save_err:
                items_results.append(
                    OrchestratedItemResult(
                        submission_id=None,
                        item_type="FILE",
                        filename_or_snippet=file.filename,
                        detected_modality=modality,
                        status="FAILED",
                        assigned_routes=routes,
                        error_message=f"Storage streaming error: {str(save_err)}"
                    )
                )
                rejected_count += 1
                continue

            # Deduplicate MediaAsset
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

            # Create distinct EvidenceSubmission
            sub = EvidenceSubmission(
                investigation_id=investigation_id,
                media_asset_id=asset.id,
                submission_type=modality,
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
            db.add(sub)
            await db.flush()

            submission_ids_to_process.append(sub.id)
            items_results.append(
                OrchestratedItemResult(
                    submission_id=sub.id,
                    item_type="FILE",
                    filename_or_snippet=file.filename,
                    detected_modality=modality,
                    status="QUEUED",
                    assigned_routes=routes,
                    sha256_hash=sha256_hash,
                    mime_type=mime_type,
                    file_size_bytes=file_size
                )
            )
            accepted_count += 1

        # 4. Process Raw Text Claim
        if has_text:
            cleaned_text = raw_text.strip()
            text_snippet = cleaned_text[:60] + "..." if len(cleaned_text) > 60 else cleaned_text
            text_routes = [
                "Text Proposition Normalization",
                "Multilingual Factual Claim Extraction",
                "Claim Lineage Mapping",
                "Contextual Verification"
            ]

            try:
                sha256_hash, mime_type, file_size, rel_path = storage_manager.save_raw_text(cleaned_text)
                
                # Check MediaAsset for text
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

                sub_text = EvidenceSubmission(
                    investigation_id=investigation_id,
                    media_asset_id=asset.id,
                    submission_type="TEXT",
                    mime_type=mime_type,
                    file_size_bytes=file_size,
                    sha256_hash=sha256_hash,
                    raw_text=cleaned_text,
                    caption=caption or text_snippet,
                    claimed_event=claimed_event,
                    claimed_date=claimed_date,
                    claimed_location=claimed_location,
                    language=language,
                    processing_status="PENDING"
                )
                db.add(sub_text)
                await db.flush()

                submission_ids_to_process.append(sub_text.id)
                items_results.append(
                    OrchestratedItemResult(
                        submission_id=sub_text.id,
                        item_type="TEXT",
                        filename_or_snippet=text_snippet,
                        detected_modality="TEXT",
                        status="QUEUED",
                        assigned_routes=text_routes,
                        sha256_hash=sha256_hash,
                        mime_type=mime_type,
                        file_size_bytes=file_size
                    )
                )
                accepted_count += 1
            except Exception as text_err:
                items_results.append(
                    OrchestratedItemResult(
                        submission_id=None,
                        item_type="TEXT",
                        filename_or_snippet=text_snippet,
                        detected_modality="TEXT",
                        status="FAILED",
                        assigned_routes=text_routes,
                        error_message=f"Failed to persist text claim: {str(text_err)}"
                    )
                )
                rejected_count += 1

        # 5. Process Source URL
        if has_url:
            cleaned_url = source_url.strip()
            url_routes = [
                "SSRF Verification & Security",
                "Web Article Extraction & Scraping",
                "ClaimReview LD-JSON Parsing",
                "Factual Claim Extraction",
                "Source Independence Analysis"
            ]

            if not self.validate_url(cleaned_url):
                items_results.append(
                    OrchestratedItemResult(
                        submission_id=None,
                        item_type="URL",
                        filename_or_snippet=cleaned_url,
                        detected_modality="URL",
                        status="FAILED",
                        assigned_routes=url_routes,
                        error_message="Invalid URL format. Must start with http:// or https://"
                    )
                )
                rejected_count += 1
            else:
                sub_url = EvidenceSubmission(
                    investigation_id=investigation_id,
                    media_asset_id=None,
                    submission_type="URL",
                    mime_type="text/html",
                    source_url=cleaned_url,
                    caption=caption or f"External Source: {cleaned_url}",
                    claimed_event=claimed_event,
                    claimed_date=claimed_date,
                    claimed_location=claimed_location,
                    language=language,
                    processing_status="PENDING"
                )
                db.add(sub_url)
                await db.flush()

                submission_ids_to_process.append(sub_url.id)
                items_results.append(
                    OrchestratedItemResult(
                        submission_id=sub_url.id,
                        item_type="URL",
                        filename_or_snippet=cleaned_url,
                        detected_modality="URL",
                        status="QUEUED",
                        assigned_routes=url_routes,
                        mime_type="text/html"
                    )
                )
                accepted_count += 1

        # Commit all successfully staged submissions
        await db.commit()

        # Emit event to monitoring stream
        try:
            from app.monitoring.events import event_bus
            await event_bus.emit(
                session=db,
                investigation_id=investigation_id,
                event_type="EVIDENCE_INGESTED",
                severity="INFO",
                summary=f"Universal intake: {accepted_count} item(s) accepted across modalities",
                details_json={
                    "total_items": total_items,
                    "accepted_count": accepted_count,
                    "rejected_count": rejected_count,
                    "submission_ids": submission_ids_to_process
                }
            )
        except Exception as ev_err:
            logger.debug(f"Event emission ignored: {ev_err}")

        # 6. Dispatch Processing
        if sync_process:
            for sub_id in submission_ids_to_process:
                success = await pipeline_service.process_evidence_item(sub_id)
                # Update item result status in response
                for item in items_results:
                    if item.submission_id == sub_id:
                        item.status = "COMPLETED" if success else "FAILED"
        elif background_tasks:
            for sub_id in submission_ids_to_process:
                background_tasks.add_task(pipeline_service.process_evidence_item, sub_id)

        # 7. Build Orchestrated Summary
        total_items = len(items_results)
        summary = (
            f"Universal intake orchestrated {accepted_count}/{total_items} items successfully for investigation {investigation_id[:8]}."
        )
        if rejected_count > 0:
            summary += f" ({rejected_count} item{'s' if rejected_count > 1 else ''} rejected or invalid)."

        return UniversalIntakeResponse(
            investigation_id=investigation_id,
            total_items_received=total_items,
            accepted_items_count=accepted_count,
            rejected_items_count=rejected_count,
            items=items_results,
            summary=summary
        )


evidence_orchestrator = EvidenceOrchestrator()
