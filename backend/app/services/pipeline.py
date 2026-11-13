import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from app.core.config import settings
from app.core.database import async_session_factory
from app.core.security import safe_url_head_or_get
from app.core.storage import storage_manager
from app.models.evidence import EvidenceSubmission, MediaAsset, ExtractionRecord, DerivedArtifact
from app.models.claim import ClaimRecord, ClaimExtractionRun
from app.claims.extractor import claim_extractor
from app.claims.locking import submission_lock_manager, StaleLockException
from app.extractors.metadata import ImageMetadataExtractor, VideoMetadataExtractor, AudioMetadataExtractor
from app.extractors.video_frames import keyframe_extractor
from app.extractors.audio_demux import audio_demuxer
from app.extractors.ocr import ocr_service
from app.extractors.transcription import transcription_service
from app.indexing.indexer import media_indexer
from app.matching.engine import match_engine
from app.services.authenticity_service import authenticity_service

logger = logging.getLogger("truthnet.pipeline")

class PipelineService:
    def __init__(self, session_factory=None):
        self.session_factory = session_factory

    async def process_evidence_item(
        self,
        evidence_id: str,
        session_factory=None,
        force_reprocess: bool = False,
        reprocess_reason: Optional[str] = None
    ) -> bool:
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

                ocr_result: Optional[Dict[str, Any]] = None
                transcription_result: Optional[Dict[str, Any]] = None

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

                    # Auto-indexing into persistent historical media index
                    if submission.submission_type == "IMAGE":
                        try:
                            await media_indexer.index_media_asset(session, asset.id)
                        except Exception as idx_err:
                            logger.warning(f"Auto-indexing failed for asset {asset.id}: {idx_err}")
                    elif submission.submission_type == "VIDEO":
                        try:
                            keyframe_arts = [art for art in derived_artifacts_to_add if art.artifact_type == "KEYFRAME"]
                            await media_indexer.index_video_keyframes(session, asset.id, keyframe_arts)
                        except Exception as idx_err:
                            logger.warning(f"Video frame auto-indexing failed for asset {asset.id}: {idx_err}")

                    # Auto-discover historical matches
                    try:
                        await match_engine.match_evidence(session, submission.id)
                    except Exception as m_err:
                        logger.warning(f"Auto-matching failed for submission {submission.id}: {m_err}")

                    # Phase 5: Media Authenticity & Deepfake Model Detection
                    try:
                        await authenticity_service.analyze_submission(session, submission.id)
                    except Exception as auth_err:
                        logger.warning(f"Authenticity analysis non-fatal failure for submission {submission.id}: {auth_err}")

                elif submission.submission_type == "URL":
                    if not submission.source_url:
                        raise ValueError("No source URL provided for URL submission")
                    
                    is_reachable, status_code, err_msg = await safe_url_head_or_get(submission.source_url)
                    if not is_reachable:
                        raise ValueError(err_msg)

                    # Safely scrape webpage article text if raw_text is not yet populated
                    if not submission.raw_text:
                        try:
                            from app.retrieval.scraper import WebScraper
                            scraped = await WebScraper.scrape_url(submission.source_url)
                            if scraped and scraped.get("text_excerpt"):
                                submission.raw_text = scraped["text_excerpt"]
                                if not submission.caption and scraped.get("article_title"):
                                    submission.caption = scraped["article_title"]
                                await session.commit()
                        except Exception as scrape_err:
                            logger.warning(f"URL scraping non-fatal warning for {evidence_id}: {scrape_err}")

                elif submission.submission_type == "TEXT":
                    if not submission.raw_text and not submission.caption:
                        raise ValueError("Text submission is completely empty")

                # Auto-extract factual claims across available text modalities
                try:
                    await self._extract_and_persist_claims(
                        session,
                        submission,
                        ocr_result,
                        transcription_result,
                        force_reprocess=force_reprocess,
                        reprocess_reason=reprocess_reason,
                        session_factory=factory
                    )
                except StaleLockException as sle:
                    logger.warning(f"Claim extraction worker superseded for submission {submission.id}: {sle}")
                    await session.rollback()
                    return False
                except Exception as c_err:
                    logger.warning(f"Claim extraction non-fatal failure for submission {submission.id}: {c_err}")

                # Auto-verify claims if relevant local evidence is available
                try:
                    await self._verify_claims_with_local_evidence(session, evidence_id)
                except Exception as v_err:
                    logger.warning(f"Contextual verification non-fatal warning for evidence {evidence_id}: {v_err}")

                # If all validation passes:
                sub_res = await session.execute(
                    select(EvidenceSubmission).where(EvidenceSubmission.id == evidence_id)
                )
                current_sub = sub_res.scalars().first()
                if current_sub:
                    current_sub.processing_status = "COMPLETED"
                    current_sub.error_message = None
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

    async def _extract_and_persist_claims(
        self,
        session,
        submission: EvidenceSubmission,
        ocr_result: Optional[Dict[str, Any]] = None,
        transcription_result: Optional[Dict[str, Any]] = None,
        force_reprocess: bool = False,
        reprocess_reason: Optional[str] = None,
        session_factory=None
    ) -> List[ClaimRecord]:
        """
        Extracts factual claim propositions across available text modalities
        (caption, raw_text, OCR text, and speech transcripts) and persists ClaimRecords
        alongside a persistent ClaimExtractionRun record.

        Strictly distinguishes:
        1. Pipeline Retries: Same submission, identical source-text hash, extraction already
           succeeded (including zero-claim completions). Skips re-extraction and returns
           existing active claims (or empty list) without version bump.
        2. Deliberate Reprocessing: Configuration changed, text updated, or explicit force_reprocess.
           Extracts new version in memory, deactivates prior claims atomically, and preserves historical audit trail.
        3. Zero-Claim Completions: Persists a ClaimExtractionRun with claims_produced=0 and status=COMPLETED
           so empty/non-factual texts are never mistaken for unrun extractions.
        4. Serialized Concurrency: Uses submission_lock_manager (database table lock with TTL) to guarantee
           per-submission execution serialization across multiple processes and workers.
        """
        import hashlib
        from datetime import datetime, timezone
        from typing import Tuple

        factory = session_factory or self.session_factory or async_session_factory

        # 1. Collect current available text modalities
        text_modalities: List[Tuple[str, str]] = []
        if submission.caption and submission.caption.strip():
            text_modalities.append(("CAPTION", submission.caption))
        if submission.raw_text and submission.raw_text.strip():
            text_modalities.append(("RAW_TEXT", submission.raw_text))
        if ocr_result and isinstance(ocr_result, dict):
            ocr_text = ocr_result.get("text")
            if ocr_text and ocr_text.strip():
                text_modalities.append(("OCR_EXTRACTED", ocr_text))
        if transcription_result and isinstance(transcription_result, dict):
            tr_text = transcription_result.get("transcript")
            if tr_text and tr_text.strip():
                text_modalities.append(("TRANSCRIPT", tr_text))

        # Build composite source text and hash across modalities
        if text_modalities:
            sorted_modalities = sorted(text_modalities, key=lambda x: x[0])
            composite_text = "||".join(f"{mod}:{txt}" for mod, txt in sorted_modalities)
            composite_hash = hashlib.sha256(composite_text.encode("utf-8")).hexdigest()
            current_hashes = {hashlib.sha256(text.encode("utf-8")).hexdigest() for _, text in text_modalities}
            if len(text_modalities) > 1:
                mod_names = "+".join(m[0] for m in sorted_modalities)
                primary_modality = f"COMBINED[{mod_names}]"
            else:
                primary_modality = text_modalities[0][0]
        else:
            # Handles empty or whitespace-only inputs if permitted by ingestion layer
            raw_content = (submission.caption or "") + (submission.raw_text or "")
            composite_hash = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()
            current_hashes = {composite_hash}
            primary_modality = "EMPTY"

        sub_id = submission.id
        inv_id = submission.investigation_id
        ref_timestamp = submission.created_at

        current_extractor_name = "TruthNetClaimExtractor"
        current_extractor_version = "1.0.0"

        # Acquire per-submission database lock with active renewal heartbeat and monotonic fencing
        async with submission_lock_manager.acquire_lock(session, sub_id, session_factory=factory) as lease:
            # 2. Query prior runs and claims for this submission
            runs_res = await session.execute(
                select(ClaimExtractionRun).where(ClaimExtractionRun.evidence_submission_id == sub_id)
            )
            prior_runs = list(runs_res.scalars().all())
            active_run = next((r for r in prior_runs if r.is_active is True), None)

            prior_claims_res = await session.execute(
                select(ClaimRecord).where(ClaimRecord.evidence_submission_id == sub_id)
            )
            prior_claims = list(prior_claims_res.scalars().all())
            active_claims = [c for c in prior_claims if c.is_active is True]

            # 3. Check for Idempotent Retry
            # Verify ALL identity attributes: submission ID, source hash, modality, extractor name, extractor version
            is_same_sub = (active_run.evidence_submission_id == sub_id) if active_run else False
            is_same_hash = (active_run.source_text_hash == composite_hash) if active_run else False
            is_same_modality = False
            if active_run:
                if active_run.source_modality == primary_modality:
                    is_same_modality = True
                elif active_run.source_modality == "COMBINED" and primary_modality.startswith("COMBINED"):
                    is_same_modality = True

            is_same_extractor = (active_run.extractor_name == current_extractor_name) if active_run else False
            is_same_version = (active_run.extractor_version == current_extractor_version) if active_run else False

            if (
                not force_reprocess
                and active_run
                and active_run.status == "COMPLETED"
                and is_same_sub
                and is_same_hash
                and is_same_modality
                and is_same_extractor
                and is_same_version
            ):
                if active_run.claims_produced == 0:
                    logger.info(
                        f"Idempotent retry for submission {sub_id}: "
                        f"Active extraction run v{active_run.version} completed with 0 claims "
                        f"(modality={primary_modality}, version={current_extractor_version}). Returning existing 0 claims."
                    )
                    return []
                logger.info(
                    f"Idempotent retry for submission {sub_id}: "
                    f"Active extraction run v{active_run.version} already completed with {len(active_claims)} claims "
                    f"(modality={primary_modality}, version={current_extractor_version}). Returning existing claims."
                )
                return active_claims

            # Case B: Backward compatibility with runs from earlier baselines without ClaimExtractionRun
            if not force_reprocess and active_claims and not active_run:
                active_hashes = {c.source_text_hash for c in active_claims}
                if current_hashes.issubset(active_hashes):
                    logger.info(
                        f"Idempotent retry for submission {sub_id}: "
                        f"Active claims version {active_claims[0].version} match text hashes. Returning existing claims."
                    )
                    return active_claims

            # 4. Deliberate Reprocessing / Initial Extraction
            max_run_ver = max([r.version for r in prior_runs], default=0)
            max_claim_ver = max([c.version for c in prior_claims], default=0)
            next_claim_version = max(max_run_ver, max_claim_ver) + 1

            # Execute extraction in memory first (guarantees atomic version switching)
            claims_to_add: List[ClaimRecord] = []
            try:
                for modality, text in text_modalities:
                    extracted = claim_extractor.extract_claims_from_text(
                        source_text=text,
                        investigation_id=inv_id,
                        evidence_submission_id=sub_id,
                        source_modality=modality,
                        reference_timestamp=ref_timestamp,
                        reference_timestamp_type="SUBMISSION_TIME",
                        extraction_version=next_claim_version
                    )
                    for c_data in extracted:
                        if c_data.get("is_factual_assertion") is False or c_data.get("extraction_state") == "NON_FACTUAL_STATEMENT":
                            continue
                        if reprocess_reason:
                            prior_notes = c_data.get("uncertainty_notes") or ""
                            c_data["uncertainty_notes"] = f"Reprocessed v{next_claim_version} ({reprocess_reason}). {prior_notes}".strip()
                        claims_to_add.append(ClaimRecord(**c_data))
            except Exception as extract_err:
                # Failure isolation: Record FAILED run without deactivating prior active records!
                failed_run = ClaimExtractionRun(
                    evidence_submission_id=sub_id,
                    version=next_claim_version,
                    source_text_hash=composite_hash,
                    source_modality=primary_modality,
                    extractor_name=current_extractor_name,
                    extractor_version=current_extractor_version,
                    status="FAILED",
                    claims_produced=0,
                    is_active=False,
                    error_message=str(extract_err),
                    reprocess_reason=reprocess_reason,
                    completed_at=datetime.now(timezone.utc)
                )
                session.add(failed_run)
                await session.commit()
                raise extract_err

            # Pre-commit Fencing Verification: ensure this worker still holds the valid lease
            is_valid_lease = await submission_lock_manager.verify_lease(session, lease)
            if not is_valid_lease:
                raise StaleLockException(
                    f"Worker {lease.owner_token} lost lock lease for submission {sub_id} "
                    f"(fence={lease.fencing_token}) before commit. Fencing blocked stale write."
                )

            # Atomic database update: deactivate prior runs & claims
            for pr in prior_runs:
                pr.is_active = False

            for pc in prior_claims:
                pc.is_active = False

            # Create persistent ClaimExtractionRun record
            run_record = ClaimExtractionRun(
                evidence_submission_id=sub_id,
                version=next_claim_version,
                source_text_hash=composite_hash,
                source_modality=primary_modality,
                extractor_name=current_extractor_name,
                extractor_version=current_extractor_version,
                status="COMPLETED",
                claims_produced=len(claims_to_add),
                is_active=True,
                error_message=None,
                reprocess_reason=reprocess_reason,
                completed_at=datetime.now(timezone.utc)
            )
            session.add(run_record)
            await session.flush()

            for rec in claims_to_add:
                rec.extraction_run_id = run_record.id
                session.add(rec)

            if claims_to_add or prior_claims or prior_runs:
                await session.flush()

            # Atomic commit with fencing verification directly within the write transaction
            await submission_lock_manager.commit_with_fencing(session, lease)

            return claims_to_add

    async def _verify_claims_with_local_evidence(
        self,
        session: AsyncSession,
        evidence_id: str
    ) -> None:
        """
        Safely triggers initial contextual verification for active extracted claims
        if relevant local evidence is available (such as historical media matches).
        Preserves complete fault isolation: never fails evidence intake.
        """
        sub_res = await session.execute(
            select(EvidenceSubmission).where(EvidenceSubmission.id == evidence_id)
        )
        sub = sub_res.scalars().first()
        if not sub or not sub.media_asset_id:
            return

        from app.models.fingerprint import MediaMatchRecord
        match_res = await session.execute(
            select(MediaMatchRecord).where(
                (MediaMatchRecord.source_evidence_id == sub.id) |
                (MediaMatchRecord.source_media_asset_id == sub.media_asset_id)
            )
        )
        matches = match_res.scalars().all()
        if not matches:
            return

        claims_res = await session.execute(
            select(ClaimRecord).where(
                ClaimRecord.evidence_submission_id == sub.id,
                ClaimRecord.is_active == True
            )
        )
        claims = claims_res.scalars().all()
        if not claims:
            return

        from app.context.verifier import ContextualClaimVerifier
        for claim in claims:
            try:
                await ContextualClaimVerifier.verify_claim(session, claim.id)
            except Exception as cv_err:
                logger.warning(f"Contextual verification warning for claim {claim.id}: {cv_err}")

pipeline_service = PipelineService()
