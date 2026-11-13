"""
Authenticity Analysis Service.

Coordinates technical forensic evaluation and deepfake model execution for media submissions.
Strictly separates physical/mathematical forensic observations from probabilistic model inferences.
Enforces epistemic honesty: records unavailable models and checkpoints with exact reasons.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np
from PIL import Image

from app.core.config import settings
from app.models.evidence import EvidenceSubmission, MediaAsset, DerivedArtifact
from app.models.authenticity import MediaAuthenticityRecord
from app.authenticity.forensics import TechnicalForensicsEngine
from app.authenticity.registry import model_registry, ModelStatus
from app.authenticity.video_authenticity import video_authenticity_analyzer

logger = logging.getLogger("truthnet.services.authenticity")


class AuthenticityService:
    """
    Service for executing media authenticity, technical forensics, and deepfake model registry audits.
    """

    EPISTEMIC_DISCLAIMER = (
        "Technical forensic metrics (ELA, noise residuals, 2D FFT/DCT power spectra, block grid alignments) "
        "and model predictions are isolated signals. They do NOT constitute an automatic verdict of falsity. "
        "Models evaluate specific distributional markers under bounded training assumptions; their execution status, "
        "runtimes, and known limitations are explicitly enumerated."
    )

    @classmethod
    async def analyze_submission(
        cls,
        session: AsyncSession,
        submission_id: str
    ) -> Optional[MediaAuthenticityRecord]:
        """
        Runs complete authenticity evaluation on an EvidenceSubmission.
        Works for IMAGE and VIDEO submissions.
        """
        # 1. Fetch submission and asset
        sub_res = await session.execute(
            select(EvidenceSubmission).where(EvidenceSubmission.id == submission_id)
        )
        submission = sub_res.scalars().first()
        if not submission:
            logger.error(f"Cannot run authenticity analysis: submission {submission_id} not found.")
            return None

        if submission.submission_type not in ("IMAGE", "VIDEO"):
            logger.info(f"Submission {submission_id} has type {submission.submission_type}; authenticity analysis skipped.")
            return None

        if not submission.media_asset_id:
            logger.warning(f"Submission {submission_id} has no media_asset_id.")
            return None

        asset_res = await session.execute(
            select(MediaAsset).where(MediaAsset.id == submission.media_asset_id)
        )
        asset = asset_res.scalars().first()
        if not asset:
            logger.warning(f"MediaAsset {submission.media_asset_id} not found.")
            return None

        file_path = (settings.BASE_DIR / "data" / asset.file_path).resolve()
        if not file_path.exists():
            logger.error(f"Binary file for asset {asset.id} does not exist at {file_path}")
            return None

        # Fetch any derived artifacts (e.g. keyframes for video)
        arts_res = await session.execute(
            select(DerivedArtifact).where(DerivedArtifact.evidence_submission_id == submission_id)
        )
        artifacts = arts_res.scalars().all()

        forensic_analysis: Dict[str, Any] = {}
        executed_models: List[Dict[str, Any]] = []
        unavailable_models: List[Dict[str, Any]] = []
        video_frames: Optional[List[Dict[str, Any]]] = None

        tech_meta = getattr(asset, "technical_metadata", None)

        if submission.submission_type == "IMAGE":
            # 1. Technical Forensics Suite
            forensic_analysis = TechnicalForensicsEngine.analyze_image_forensics(
                image_path=file_path,
                raw_metadata=tech_meta
            )

            # 2. Model Inferences
            try:
                with Image.open(file_path) as pil_img:
                    rgb_img = pil_img.convert("RGB")
                    img_np = np.array(rgb_img)

                    # Iterate through all registered models in registry
                    for reg_model in model_registry.get_registered_models():
                        mid = reg_model["model_id"]
                        inf_result = model_registry.execute_inference(
                            model_id=mid,
                            image_np=img_np,
                            mime_type=asset.mime_type,
                            metadata=tech_meta
                        )
                        if inf_result.get("status") == ModelStatus.INFERENCE_EXECUTED:
                            executed_models.append(inf_result)
                        else:
                            unavailable_models.append({
                                "model_id": mid,
                                "model_name": reg_model["name"],
                                "status": inf_result.get("status"),
                                "reason": inf_result.get("reason", inf_result.get("error", "Unavailable")),
                                "prerequisites": inf_result.get("prerequisites", "None specified"),
                                "architecture": reg_model["architecture"],
                                "version": reg_model["version"]
                            })
            except Exception as e:
                logger.error(f"Image model execution failed on {file_path}: {e}", exc_info=True)
                forensic_analysis["model_dispatch_error"] = str(e)

        elif submission.submission_type == "VIDEO":
            # 1. Prepare keyframe candidates
            keyframe_records: List[Dict[str, Any]] = []
            for art in artifacts:
                if art.artifact_type == "KEYFRAME" and art.file_path:
                    abs_p = (settings.BASE_DIR / "data" / art.file_path).resolve()
                    meta = art.metadata_json or {}
                    keyframe_records.append({
                        "path": str(abs_p),
                        "absolute_path": str(abs_p),
                        "actual_timestamp_ms": meta.get("actual_timestamp_ms", 0.0),
                        "timestamp_ms": meta.get("target_timestamp_ms", 0.0)
                    })

            # 2. Run Video Authenticity Analyzer across frames
            video_res = video_authenticity_analyzer.analyze_video(
                video_path=file_path,
                evidence_id=submission.id,
                keyframe_records=keyframe_records
            )
            video_frames = video_res.get("video_frame_analyses", [])

            # Run image forensics on first keyframe or fallback to thumbnail
            first_frame_path = None
            if keyframe_records and Path(keyframe_records[0]["path"]).exists():
                first_frame_path = Path(keyframe_records[0]["path"])
            
            if first_frame_path and first_frame_path.exists():
                forensic_analysis = TechnicalForensicsEngine.analyze_image_forensics(
                    image_path=first_frame_path,
                    raw_metadata=tech_meta
                )
                forensic_analysis["representative_keyframe"] = str(first_frame_path.name)
            else:
                forensic_analysis = {
                    "forensic_summary": "Video analysis performed across decodable keyframe samples.",
                    "temporal_consistency": video_res.get("temporal_consistency", {}),
                    "epistemic_disclaimer": video_res.get("epistemic_disclaimer", cls.EPISTEMIC_DISCLAIMER)
                }

            # Gather model execution summaries across video frames
            executed_model_ids = set()
            for vf in (video_frames or []):
                for inf in vf.get("model_inferences", []):
                    if inf.get("status") == ModelStatus.INFERENCE_EXECUTED:
                        executed_model_ids.add(inf.get("model_id"))

            for reg_model in model_registry.get_registered_models():
                mid = reg_model["model_id"]
                if mid in executed_model_ids:
                    executed_models.append({
                        "model_id": mid,
                        "model_name": reg_model["name"],
                        "version": reg_model["version"],
                        "runtime_device": reg_model["runtime_device"],
                        "status": ModelStatus.INFERENCE_EXECUTED,
                        "scope": "EVALUATED_ACROSS_SAMPLED_KEYFRAMES",
                        "raw_metrics": {"cross_frame_execution": True},
                        "evaluation_limitations": reg_model["known_limitations"]
                    })
                else:
                    unavailable_models.append({
                        "model_id": mid,
                        "model_name": reg_model["name"],
                        "status": (
                            ModelStatus.DEPENDENCY_UNAVAILABLE if not reg_model["dependency_available"]
                            else ModelStatus.MODEL_CHECKPOINT_UNAVAILABLE if not reg_model["checkpoint_available"]
                            else ModelStatus.UNSUPPORTED_INPUT
                        ),
                        "reason": (
                            f"Dependency '{reg_model['dependency_name']}' is not installed."
                            if not reg_model["dependency_available"]
                            else f"Checkpoint '{reg_model['checkpoint_name']}' is not locally packaged."
                            if not reg_model["checkpoint_available"]
                            else "Modality constraint."
                        ),
                        "prerequisites": f"Setup {reg_model['dependency_name']}." if not reg_model["dependency_available"] else "Download checkpoint.",
                        "architecture": reg_model["architecture"],
                        "version": reg_model["version"]
                    })

        # Summary of model registry
        reg_summary = {
            "total_registered_models": len(model_registry.models),
            "executed_count": len(executed_models),
            "unavailable_count": len(unavailable_models),
            "hardware_runtime": model_registry.hardware_info
        }

        # 3. Handle versioning: deactivate older records for this submission
        prior_res = await session.execute(
            select(MediaAuthenticityRecord)
            .where(MediaAuthenticityRecord.evidence_submission_id == submission_id)
            .order_by(MediaAuthenticityRecord.version.desc())
        )
        priors = prior_res.scalars().all()
        next_ver = 1
        if priors:
            next_ver = priors[0].version + 1
            for p in priors:
                p.is_active = False

        record = MediaAuthenticityRecord(
            evidence_submission_id=submission_id,
            media_asset_id=asset.id,
            version=next_ver,
            is_active=True,
            forensic_analysis=forensic_analysis,
            model_registry_summary=reg_summary,
            executed_model_results=executed_models,
            unavailable_models=unavailable_models,
            video_frame_analyses=video_frames,
            epistemic_disclaimer=cls.EPISTEMIC_DISCLAIMER
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)

        logger.info(
            f"Persisted MediaAuthenticityRecord {record.id} v{record.version} for submission {submission_id} "
            f"({len(executed_models)} executed, {len(unavailable_models)} unavailable)."
        )
        return record

    @classmethod
    async def get_active_record(
        cls,
        session: AsyncSession,
        submission_id: str
    ) -> Optional[MediaAuthenticityRecord]:
        """
        Retrieves the latest active MediaAuthenticityRecord for a submission.
        """
        res = await session.execute(
            select(MediaAuthenticityRecord)
            .where(
                MediaAuthenticityRecord.evidence_submission_id == submission_id,
                MediaAuthenticityRecord.is_active == True
            )
            .order_by(MediaAuthenticityRecord.version.desc())
        )
        return res.scalars().first()

    @classmethod
    async def get_investigation_records(
        cls,
        session: AsyncSession,
        investigation_id: str
    ) -> List[MediaAuthenticityRecord]:
        """
        Retrieves all active authenticity records for submissions in an investigation.
        """
        sub_q = select(EvidenceSubmission.id).where(EvidenceSubmission.investigation_id == investigation_id)
        res = await session.execute(
            select(MediaAuthenticityRecord)
            .where(
                MediaAuthenticityRecord.evidence_submission_id.in_(sub_q),
                MediaAuthenticityRecord.is_active == True
            )
        )
        return list(res.scalars().all())


authenticity_service = AuthenticityService()
