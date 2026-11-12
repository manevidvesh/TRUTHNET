import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.fingerprint import MediaFingerprint, FrameFingerprint
from app.indexing.hasher import media_hasher

logger = logging.getLogger("truthnet.matching.candidate_retrieval")

class CandidateRetrievalService:
    """
    Measurable candidate retrieval service.
    Scans the persistent historical media index for exact SHA-256 equality
    and perceptual hash candidates within configurable Hamming distance thresholds.
    Exposes explicit search telemetry without claiming unbenchmarked nearest-neighbour properties.
    """

    async def find_candidates(
        self,
        db_session: AsyncSession,
        target_fingerprint: Dict[str, Any],
        max_hamming: int = 12,
        exclude_media_asset_id: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        t_start = time.perf_counter()
        candidates: List[Dict[str, Any]] = []
        fingerprints_examined = 0

        target_sha256 = target_fingerprint.get("sha256_hash")
        target_phash = target_fingerprint.get("phash_hex")
        target_dhash = target_fingerprint.get("dhash_hex")

        # 1. Exact Binary Identity Lookup
        # In TRUTHNET, exact duplicate files reuse the same MediaAsset.
        # We check if this MediaAsset has previous submissions or if another asset shares the hash.
        if target_sha256:
            # Check other assets with same SHA-256
            exact_q = select(MediaFingerprint).where(MediaFingerprint.sha256_hash == target_sha256)
            if exclude_media_asset_id:
                exact_q = exact_q.where(MediaFingerprint.media_asset_id != exclude_media_asset_id)
            
            exact_res = await db_session.execute(exact_q)
            exact_fps = exact_res.scalars().all()
            for efp in exact_fps:
                fingerprints_examined += 1
                candidates.append({
                    "candidate_media_asset_id": efp.media_asset_id,
                    "matched_artifact_id": None,
                    "is_exact_binary": True,
                    "is_video_frame": False,
                    "frame_timestamp_ms": None,
                    "phash_distance": 0,
                    "dhash_distance": 0,
                    "descriptor_rel_path": efp.orb_descriptor_rel_path,
                    "algorithm_version": efp.algorithm_version
                })

        # Also check if the media asset itself has other submissions (reused deduplicated asset)
        if exclude_media_asset_id:
            from app.models.evidence import EvidenceSubmission
            other_subs_q = select(EvidenceSubmission).where(
                EvidenceSubmission.media_asset_id == exclude_media_asset_id
            )
            other_subs_res = await db_session.execute(other_subs_q)
            other_subs = other_subs_res.scalars().all()
            if len(other_subs) > 1:
                # MediaAsset is shared across multiple submissions -> Exact Binary Match!
                candidates.append({
                    "candidate_media_asset_id": exclude_media_asset_id,
                    "matched_artifact_id": None,
                    "is_exact_binary": True,
                    "is_video_frame": False,
                    "frame_timestamp_ms": None,
                    "phash_distance": 0,
                    "dhash_distance": 0,
                    "descriptor_rel_path": target_fingerprint.get("descriptor_rel_path"),
                    "algorithm_version": "1.0.0"
                })

        # 2. Perceptual Candidate Scan (Media Assets)
        media_q = select(MediaFingerprint)
        if exclude_media_asset_id:
            media_q = media_q.where(MediaFingerprint.media_asset_id != exclude_media_asset_id)
        if target_sha256:
            # Exclude already identified exact binary matches
            media_q = media_q.where(MediaFingerprint.sha256_hash != target_sha256)

        media_res = await db_session.execute(media_q)
        all_media_fps = media_res.scalars().all()

        for fp in all_media_fps:
            fingerprints_examined += 1
            p_dist = media_hasher.hamming_distance(target_phash, fp.phash_hex) if target_phash else 64
            d_dist = media_hasher.hamming_distance(target_dhash, fp.dhash_hex) if target_dhash else 64

            if p_dist <= max_hamming or d_dist <= max_hamming:
                candidates.append({
                    "candidate_media_asset_id": fp.media_asset_id,
                    "matched_artifact_id": None,
                    "is_exact_binary": False,
                    "is_video_frame": False,
                    "frame_timestamp_ms": None,
                    "phash_distance": p_dist,
                    "dhash_distance": d_dist,
                    "descriptor_rel_path": fp.orb_descriptor_rel_path,
                    "algorithm_version": fp.algorithm_version
                })

        # 3. Perceptual Candidate Scan (Video Frames)
        frame_q = select(FrameFingerprint)
        if exclude_media_asset_id:
            frame_q = frame_q.where(FrameFingerprint.media_asset_id != exclude_media_asset_id)

        frame_res = await db_session.execute(frame_q)
        all_frame_fps = frame_res.scalars().all()

        for ffp in all_frame_fps:
            fingerprints_examined += 1
            p_dist = media_hasher.hamming_distance(target_phash, ffp.phash_hex) if target_phash else 64
            d_dist = media_hasher.hamming_distance(target_dhash, ffp.dhash_hex) if target_dhash else 64

            if p_dist <= max_hamming or d_dist <= max_hamming:
                candidates.append({
                    "candidate_media_asset_id": ffp.media_asset_id,
                    "matched_artifact_id": ffp.derived_artifact_id,
                    "is_exact_binary": False,
                    "is_video_frame": True,
                    "frame_timestamp_ms": ffp.timestamp_ms,
                    "frame_index": ffp.frame_index,
                    "phash_distance": p_dist,
                    "dhash_distance": d_dist,
                    "descriptor_rel_path": None,
                    "algorithm_version": ffp.algorithm_version
                })

        t_end = time.perf_counter()
        elapsed_ms = (t_end - t_start) * 1000.0

        # Sort candidates: exact binary matches first, then by minimum Hamming distance
        candidates.sort(
            key=lambda c: (
                0 if c.get("is_exact_binary") else 1,
                min(c.get("phash_distance", 64), c.get("dhash_distance", 64))
            )
        )

        telemetry = {
            "fingerprints_examined": fingerprints_examined,
            "candidates_found": len(candidates),
            "retrieval_latency_ms": round(elapsed_ms, 2),
            "max_hamming_threshold": max_hamming,
            "method": "EXACT_SHA256_AND_BOUNDED_HAMMING_SCAN"
        }

        return candidates, telemetry

candidate_retrieval = CandidateRetrievalService()
