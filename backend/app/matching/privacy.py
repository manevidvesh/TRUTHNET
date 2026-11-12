import logging
from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.evidence import EvidenceSubmission
from app.models.fingerprint import MediaMatchRecord
from app.schemas.fingerprint import MediaMatchResponse

logger = logging.getLogger("truthnet.matching.privacy")

class MatchPrivacyPolicy:
    """
    Enforces strict access isolation between investigative boundaries.
    Prevents cross-investigation leakage of case names, confidential theories,
    private notes, submission dates, and investigator identities.
    """

    @classmethod
    def _sanitize_metrics(cls, metrics: Optional[Dict[str, Any]], is_same_investigation: bool) -> Optional[Dict[str, Any]]:
        if not metrics:
            return None
        
        sanitized = {}
        for k, v in metrics.items():
            # Strip internal server filesystem paths
            if "path" in k.lower():
                continue
            if isinstance(v, dict):
                sanitized[k] = cls._sanitize_metrics(v, is_same_investigation)
            else:
                sanitized[k] = v
        return sanitized

    @classmethod
    async def sanitize_match(
        cls,
        match: MediaMatchRecord,
        requesting_investigation_id: str,
        db_session: AsyncSession
    ) -> MediaMatchResponse:
        # Determine if matched media belongs to the requesting investigation
        is_same_investigation = False

        if match.matched_media_asset_id:
            # Query submissions referencing the matched asset within requesting investigation
            same_inv_res = await db_session.execute(
                select(EvidenceSubmission).where(
                    EvidenceSubmission.media_asset_id == match.matched_media_asset_id,
                    EvidenceSubmission.investigation_id == requesting_investigation_id
                )
            )
            if same_inv_res.scalars().first():
                is_same_investigation = True

        scope = "CURRENT_INVESTIGATION" if is_same_investigation else "GLOBAL_INDEX_ANONYMIZED"

        # Foreign derived artifact IDs belong to another investigation and must not be leaked
        sanitized_artifact_id = match.matched_artifact_id if is_same_investigation else None

        # Clean raw metrics to remove internal disk storage paths
        sanitized_metrics = cls._sanitize_metrics(match.raw_metrics, is_same_investigation)

        return MediaMatchResponse(
            id=match.id,
            source_evidence_id=match.source_evidence_id,
            source_media_asset_id=match.source_media_asset_id,
            matched_media_asset_id=match.matched_media_asset_id,
            matched_artifact_id=sanitized_artifact_id,
            classification=match.classification,
            method=match.method,
            algorithm_version=match.algorithm_version,
            is_video_frame_match=match.is_video_frame_match,
            matched_frame_timestamp_ms=match.matched_frame_timestamp_ms,
            consecutive_frames_matched=match.consecutive_frames_matched,
            raw_metrics=sanitized_metrics,
            classification_rationale=match.classification_rationale,
            disclaimer=match.disclaimer,
            scope=scope,
            created_at=match.created_at
        )

    @classmethod
    async def sanitize_matches(
        cls,
        matches: List[MediaMatchRecord],
        requesting_investigation_id: str,
        db_session: AsyncSession
    ) -> List[MediaMatchResponse]:
        results = []
        for m in matches:
            sanitized = await cls.sanitize_match(m, requesting_investigation_id, db_session)
            results.append(sanitized)
        return results

match_privacy_policy = MatchPrivacyPolicy()
