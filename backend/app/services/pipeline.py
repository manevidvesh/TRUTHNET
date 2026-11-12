import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from app.core.config import settings
from app.core.database import async_session_factory
from app.core.security import safe_url_head_or_get
from app.core.storage import storage_manager
from app.models.evidence import EvidenceSubmission, MediaAsset, ExtractionRecord, DerivedArtifact
from app.extractors.metadata import ImageMetadataExtractor, VideoMetadataExtractor, AudioMetadataExtractor
from app.extractors.video_frames import keyframe_extractor
from app.extractors.audio_demux import audio_demuxer
from app.extractors.ocr import ocr_service
from app.extractors.transcription import transcription_service

logger = logging.getLogger("truthnet.pipeline")

class PipelineService:
    def __init__(self, session_factory=None):
        self.session_factory = session_factory

    async def process_evidence_item(self, evidence_id: str, session_factory=None) -> bool:
        """
        Asynchronously validates and processes an ingested evidence item across all modalities.
        Extracts technical metadata, keyframes, audio streams, OCR text, and speech transcription.
        Maintains independent failure isolation per modality and versions extraction results.
        """
        factory = session_factory or self.session_factory or async_session_factory
        async with factory() as session:
            try:
                result = await session.execute(
                    select(EvidenceSubmission).where(EvidenceSubmission.id == evidence_id)
                )
                submission = result.scalars().first()
                if not submission:
                    logger.error(f"Evidence submission {evidence_id} not found during processing.")
                    return False

                submission.processing_status = "PROCESSING"
                await session.commit()

                # Process by submission type
                if submission.submission_type in ("IMAGE", "AUDIO", "VIDEO"):
                    if not submission.media_asset_id:
                        raise ValueError(f"Missing MediaAsset for {submission.submission_type} submission")
                    
                    asset_res = await session.execute(
                        select(MediaAsset).where(MediaAsset.id == submission.media_asset_id)
                    )
                    asset = asset_res.scalars().first()
                    if not asset:
                        raise ValueError(f"MediaAsset {submission.media_asset_id} record not found")

                    file_path = (settings.BASE_DIR / "data" / asset.file_path).resolve()
                    if not file_path.exists():
                        raise FileNotFoundError(f"Binary file missing at {file_path}")
                    if file_path.stat().st_size == 0:
                        raise ValueError("Submitted media file is zero bytes (empty or corrupt)")

                    # Deactivate prior extraction records for reprocessing versioning
                    prior_records_res = await session.execute(
                        select(ExtractionRecord).where(ExtractionRecord.evidence_submission_id == submission.id)
                    )
                    prior_records = prior_records_res.scalars().all()
                    next_version = len(prior_records) + 1
                    for rec in prior_records:
                        rec.is_active = False

                    modality_statuses: Dict[str, str] = {}
                    derived_artifacts_to_add: List[DerivedArtifact] = []
                    technical_metadata: Optional[Dict[str, Any]] = None
                    video_frames: Optional[List[Dict[str, Any]]] = None
                    ocr_result: Optional[Dict[str, Any]] = None
                    transcription_result: Optional[Dict[str, Any]] = None

                    # --- IMAGE PROCESSING ---
                    if submission.submission_type == "IMAGE":
                        # Modality 1: Technical Metadata
                        try:
                            technical_metadata = ImageMetadataExtractor.extract(file_path)
                            modality_statuses["metadata"] = technical_metadata.get("metadata_status", "COMPLETED")
                        except Exception as e:
                            logger.warning(f"Image metadata extraction failed for {evidence_id}: {e}")
                            modality_statuses["metadata"] = "FAILED"
                            technical_metadata = {"error": str(e), "category": "OBSERVED_DATA"}

                        # Modality 2: OCR
                        try:
                            ocr_result = await ocr_service.extract_text(file_path)
                            modality_statuses["ocr"] = ocr_result.get("status", "COMPLETED")
                        except Exception as e:
                            logger.warning(f"OCR extraction failed for {evidence_id}: {e}")
                            modality_statuses["ocr"] = "FAILED"
                            ocr_result = {"error": str(e), "category": "OBSERVED_DATA", "status": "FAILED"}

                    # --- VIDEO PROCESSING ---
                    elif submission.submission_type == "VIDEO":
                        # Modality 1: Container & Stream Metadata
                        try:
                            technical_metadata = VideoMetadataExtractor.extract(file_path)
                            modality_statuses["metadata"] = technical_metadata.get("metadata_status", "COMPLETED")
                        except Exception as e:
                            logger.warning(f"Video metadata extraction failed for {evidence_id}: {e}")
                            modality_statuses["metadata"] = "FAILED"
                            technical_metadata = {"error": str(e), "category": "OBSERVED_DATA", "has_audio": False}

                        # Modality 2: Visual Boundary Keyframe Extraction
                        try:
                            frames, kf_summary = keyframe_extractor.extract_keyframes(file_path, submission.id)
                            video_frames = frames
                            modality_statuses["frames"] = kf_summary.get("status", "COMPLETED")

                            for frame in frames:
                                art = DerivedArtifact(
                                    evidence_submission_id=submission.id,
                                    artifact_type="KEYFRAME",
                                    sha256_hash=frame["sha256_hash"],
                                    relative_path=frame["relative_path"],
                                    file_size_bytes=frame["file_size_bytes"],
                                    mime_type=frame["mime_type"],
                                    artifact_metadata={
                                        "frame_index": frame["frame_index"],
                                        "target_timestamp_ms": frame["target_timestamp_ms"],
                                        "actual_timestamp_ms": frame["actual_timestamp_ms"],
                                        "is_boundary_frame": frame["is_boundary_frame"]
                                    }
                                )
                                derived_artifacts_to_add.append(art)
                        except Exception as e:
                            logger.warning(f"Keyframe extraction failed for {evidence_id}: {e}")
                            modality_statuses["frames"] = "FAILED"

                        # Modality 3: Audio Stream Demuxing & Speech Transcription
                        has_audio = technical_metadata.get("has_audio", False) if technical_metadata else False
                        if has_audio:
                            try:
                                audio_res = audio_demuxer.extract_audio_from_video(file_path, submission.id)
                                modality_statuses["audio_demux"] = audio_res.get("status", "COMPLETED")
                                
                                if audio_res.get("artifact"):
                                    art_dict = audio_res["artifact"]
                                    audio_art = DerivedArtifact(
                                        evidence_submission_id=submission.id,
                                        artifact_type="EXTRACTED_AUDIO",
                                        sha256_hash=art_dict["sha256_hash"],
                                        relative_path=art_dict["relative_path"],
                                        file_size_bytes=art_dict["file_size_bytes"],
                                        mime_type=art_dict["mime_type"],
                                        artifact_metadata=art_dict.get("artifact_metadata")
                                    )
                                    derived_artifacts_to_add.append(audio_art)

                                    # Connect extracted audio to transcription pipeline
                                    try:
                                        wav_path = storage_manager.resolve_safe_path(art_dict["relative_path"])
                                        transcription_result = await transcription_service.transcribe(wav_path)
                                        modality_statuses["transcription"] = transcription_result.get("status", "COMPLETED")
                                    except Exception as t_err:
                                        logger.warning(f"Transcription failed for {evidence_id}: {t_err}")
                                        modality_statuses["transcription"] = "FAILED"
                                        transcription_result = {"error": str(t_err), "status": "FAILED", "category": "OBSERVED_DATA"}
                            except Exception as e:
                                logger.warning(f"Audio demuxing failed for {evidence_id}: {e}")
                                modality_statuses["audio_demux"] = "FAILED"
                                modality_statuses["transcription"] = "SKIPPED"
                        else:
                            modality_statuses["audio_demux"] = "NO_AUDIO_STREAM"
                            modality_statuses["transcription"] = "SKIPPED"

                    # --- AUDIO PROCESSING ---
                    elif submission.submission_type == "AUDIO":
                        # Modality 1: Technical Audio Metadata
                        try:
                            technical_metadata = AudioMetadataExtractor.extract(file_path)
                            modality_statuses["metadata"] = technical_metadata.get("metadata_status", "COMPLETED")
                        except Exception as e:
                            logger.warning(f"Audio metadata extraction failed for {evidence_id}: {e}")
                            modality_statuses["metadata"] = "FAILED"
                            technical_metadata = {"error": str(e), "category": "OBSERVED_DATA"}

                        # Modality 2: Speech Transcription
                        try:
                            transcription_result = await transcription_service.transcribe(file_path)
                            modality_statuses["transcription"] = transcription_result.get("status", "COMPLETED")
                        except Exception as e:
                            logger.warning(f"Audio transcription failed for {evidence_id}: {e}")
                            modality_statuses["transcription"] = "FAILED"
                            transcription_result = {"error": str(e), "category": "OBSERVED_DATA", "status": "FAILED"}

                    # Save derived artifacts to DB
                    for art in derived_artifacts_to_add:
                        session.add(art)
                    if derived_artifacts_to_add:
                        await session.flush()
                    derived_artifact_ids = [art.id for art in derived_artifacts_to_add]

                    # Record status: COMPLETED if primary modalities completed, or PARTIAL
                    statuses_list = list(modality_statuses.values())
                    if all(s in ("COMPLETED", "SKIPPED", "NO_AUDIO_STREAM") for s in statuses_list):
                        overall_status = "COMPLETED"
                    elif any(s == "COMPLETED" for s in statuses_list):
                        overall_status = "PARTIAL"
                    else:
                        overall_status = "FAILED"

                    extraction_rec = ExtractionRecord(
                        evidence_submission_id=submission.id,
                        version=next_version,
                        is_active=True,
                        category="OBSERVED_DATA",
                        extractor_name="TruthNetMultimodalExtractor",
                        extractor_version="2.0.0",
                        status=overall_status,
                        modality_statuses=modality_statuses,
                        technical_metadata=technical_metadata,
                        video_frames=video_frames,
                        ocr_result=ocr_result,
                        transcription_result=transcription_result,
                        derived_artifact_ids=derived_artifact_ids
                    )
                    session.add(extraction_rec)

                elif submission.submission_type == "URL":
                    if not submission.source_url:
                        raise ValueError("No source URL provided for URL submission")
                    
                    is_reachable, status_code, err_msg = await safe_url_head_or_get(submission.source_url)
                    if not is_reachable:
                        raise ValueError(err_msg)

                elif submission.submission_type == "TEXT":
                    if not submission.raw_text and not submission.caption:
                        raise ValueError("Text submission is completely empty")

                # If all validation passes:
                submission.processing_status = "COMPLETED"
                submission.error_message = None
                await session.commit()
                return True

            except Exception as e:
                logger.warning(f"Fault isolation caught error for evidence {evidence_id}: {str(e)}")
                try:
                    result = await session.execute(
                        select(EvidenceSubmission).where(EvidenceSubmission.id == evidence_id)
                    )
                    sub = result.scalars().first()
                    if sub:
                        sub.processing_status = "FAILED"
                        sub.error_message = str(e)
                        await session.commit()
                except Exception as db_err:
                    logger.error(f"Failed to record error state for {evidence_id}: {db_err}")
                return False

    async def recover_pending_jobs(self, session_factory=None) -> int:
        """
        Scans for stranded PENDING or PROCESSING submissions across application restarts.
        Processes them to restore consistent pipeline state.
        Returns count of recovered jobs.
        """
        factory = session_factory or self.session_factory or async_session_factory
        stranded_ids: List[str] = []

        async with factory() as session:
            result = await session.execute(
                select(EvidenceSubmission.id).where(
                    EvidenceSubmission.processing_status.in_(["PENDING", "PROCESSING"])
                )
            )
            stranded_ids = list(result.scalars().all())

        if stranded_ids:
            logger.info(f"Recovering {len(stranded_ids)} stranded evidence processing jobs after restart...")
            for eid in stranded_ids:
                await self.process_evidence_item(eid, session_factory=factory)

        return len(stranded_ids)

pipeline_service = PipelineService()
