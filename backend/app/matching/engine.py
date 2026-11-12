import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.evidence import EvidenceSubmission, MediaAsset
from app.models.fingerprint import MediaFingerprint, MediaMatchRecord
from app.indexing.indexer import media_indexer
from app.indexing.descriptor_store import descriptor_store
from app.matching.candidate_retrieval import candidate_retrieval
from app.matching.geometric import geometric_verifier

logger = logging.getLogger("truthnet.matching.engine")

class MatchEngine:
    """
    Historical media matching engine.
    Enforces the six discrete classifications:
      1. EXACT_FILE_MATCH
      2. NEAR_DUPLICATE
      3. SAME_PHOTOGRAPH_MODIFIED
      4. POSSIBLE_VISUAL_SIMILARITY
      5. INSUFFICIENT_MATCH_EVIDENCE
      6. NO_LOCAL_MATCH_FOUND
    Exposes raw measurements without arbitrary confidence percentages.
    Adheres strictly to epistemological rules: no event-level claims from ORB alone.
    """

    MATCH_ENGINE_VERSION = "TRUTHNET-MATCH-V1"

    async def match_evidence(
        self,
        db_session: AsyncSession,
        evidence_id: str,
        max_hamming: int = 12
    ) -> List[MediaMatchRecord]:
        ev_res = await db_session.execute(
            select(EvidenceSubmission).where(EvidenceSubmission.id == evidence_id)
        )
        submission = ev_res.scalars().first()
        if not submission or not submission.media_asset_id:
            logger.warning(f"No media asset found for evidence {evidence_id}")
            return []

        # 1. Retrieve or generate target fingerprint
        fp_res = await db_session.execute(
            select(MediaFingerprint).where(MediaFingerprint.media_asset_id == submission.media_asset_id)
        )
        target_fp = fp_res.scalars().first()

        if not target_fp and submission.submission_type == "IMAGE":
            target_fp = await media_indexer.index_media_asset(db_session, submission.media_asset_id)

        target_dict = {
            "sha256_hash": target_fp.sha256_hash if target_fp else submission.sha256_hash,
            "phash_hex": target_fp.phash_hex if target_fp else None,
            "dhash_hex": target_fp.dhash_hex if target_fp else None
        }

        # 2. Candidate Retrieval
        candidates, telemetry = await candidate_retrieval.find_candidates(
            db_session=db_session,
            target_fingerprint=target_dict,
            max_hamming=max_hamming,
            exclude_media_asset_id=submission.media_asset_id
        )

        records: List[MediaMatchRecord] = []

        # 3. Handle Negative Search Outcome
        if not candidates:
            total_scanned = telemetry.get("fingerprints_examined", 0)
            no_match_rec = MediaMatchRecord(
                source_evidence_id=submission.id,
                source_media_asset_id=submission.media_asset_id,
                matched_media_asset_id=None,
                classification="NO_LOCAL_MATCH_FOUND",
                method=telemetry.get("method", "EXACT_SHA256_AND_BOUNDED_HAMMING_SCAN"),
                algorithm_version=self.MATCH_ENGINE_VERSION,
                raw_metrics=telemetry,
                classification_rationale="No historical media in the local index met the candidate threshold.",
                disclaimer=(
                    f"No matching media found in the local repository (search bounded to {total_scanned} "
                    f"indexed assets; does not constitute proof that media has never appeared elsewhere)."
                )
            )
            db_session.add(no_match_rec)
            await db_session.flush()
            return [no_match_rec]

        # Load query features once if available
        q_pts, q_descs = None, None
        if target_fp and target_fp.orb_descriptor_rel_path:
            q_pts, q_descs = descriptor_store.load_features(target_fp.orb_descriptor_rel_path)

        # Pre-compute frame match statistics per candidate video asset
        video_frame_stats: Dict[str, Dict[str, Any]] = {}
        for c in candidates:
            if c.get("is_video_frame") and c.get("candidate_media_asset_id"):
                v_id = c["candidate_media_asset_id"]
                if v_id not in video_frame_stats:
                    video_frame_stats[v_id] = {"indices": [], "total_frames": 0, "max_consecutive": 1}
                if "frame_index" in c and c["frame_index"] is not None:
                    video_frame_stats[v_id]["indices"].append(c["frame_index"])
                video_frame_stats[v_id]["total_frames"] += 1

        for v_id, stats in video_frame_stats.items():
            sorted_indices = sorted(set(stats["indices"]))
            max_c = 1 if sorted_indices else 0
            cur = 1
            for i in range(1, len(sorted_indices)):
                if sorted_indices[i] == sorted_indices[i - 1] + 1:
                    cur += 1
                    max_c = max(max_c, cur)
                else:
                    cur = 1
            stats["max_consecutive"] = max_c

        # 4. Classify each retrieved candidate
        for cand in candidates:
            is_vf = cand.get("is_video_frame", False)
            v_id = cand.get("candidate_media_asset_id")
            vf_stats = video_frame_stats.get(v_id, {}) if is_vf else {}
            consec_frames = vf_stats.get("max_consecutive", 1 if is_vf else 0)
            tot_frames = vf_stats.get("total_frames", 1 if is_vf else 0)

            # Classification 1: EXACT_FILE_MATCH
            if cand.get("is_exact_binary"):
                rec = MediaMatchRecord(
                    source_evidence_id=submission.id,
                    source_media_asset_id=submission.media_asset_id,
                    matched_media_asset_id=cand["candidate_media_asset_id"],
                    matched_artifact_id=cand.get("matched_artifact_id"),
                    classification="EXACT_FILE_MATCH",
                    method="SHA256_EXACT_BINARY_IDENTITY",
                    algorithm_version=self.MATCH_ENGINE_VERSION,
                    is_video_frame_match=is_vf,
                    matched_frame_timestamp_ms=cand.get("frame_timestamp_ms"),
                    consecutive_frames_matched=consec_frames,
                    raw_metrics={"distance": 0, "telemetry": telemetry},
                    classification_rationale="Cryptographic SHA-256 hash match confirms exact identical binary file.",
                    disclaimer="Exact binary identity confirmed via cryptographic SHA-256 equality."
                )
                records.append(rec)
                continue

            # Check for feature-poor / textureless query image
            if target_fp and target_fp.orb_keypoints_count < 10:
                rec = MediaMatchRecord(
                    source_evidence_id=submission.id,
                    source_media_asset_id=submission.media_asset_id,
                    matched_media_asset_id=cand["candidate_media_asset_id"],
                    matched_artifact_id=cand.get("matched_artifact_id"),
                    classification="INSUFFICIENT_MATCH_EVIDENCE",
                    method="PERCEPTUAL_PREFILTER_FEATURE_CHECK",
                    algorithm_version=self.MATCH_ENGINE_VERSION,
                    is_video_frame_match=is_vf,
                    matched_frame_timestamp_ms=cand.get("frame_timestamp_ms"),
                    consecutive_frames_matched=consec_frames,
                    raw_metrics=cand,
                    classification_rationale="Query image has fewer than 10 distinctive keypoints (low texture/resolution).",
                    disclaimer="Insufficient distinctive visual features to verify or refute geometric correspondence."
                )
                records.append(rec)
                continue

            # Classification 2: NEAR_DUPLICATE
            if cand.get("phash_distance", 64) <= 4 and cand.get("dhash_distance", 64) <= 4:
                disclaimer_text = (
                    f"Frame-level similarity observed at {cand.get('frame_timestamp_ms', 0)}ms "
                    f"across {tot_frames} frames ({consec_frames} consecutive). "
                    f"Does not prove whole-video identity or sub-clip identity."
                    if is_vf else
                    "Near-duplicate visual composition observed. Does not certify pixel-for-pixel identity."
                )
                rec = MediaMatchRecord(
                    source_evidence_id=submission.id,
                    source_media_asset_id=submission.media_asset_id,
                    matched_media_asset_id=cand["candidate_media_asset_id"],
                    matched_artifact_id=cand.get("matched_artifact_id"),
                    classification="NEAR_DUPLICATE",
                    method="PERCEPTUAL_HASH_HAMMING",
                    algorithm_version=self.MATCH_ENGINE_VERSION,
                    is_video_frame_match=is_vf,
                    matched_frame_timestamp_ms=cand.get("frame_timestamp_ms"),
                    consecutive_frames_matched=consec_frames,
                    raw_metrics=cand,
                    classification_rationale=(
                        f"pHash distance {cand['phash_distance']} and dHash distance {cand['dhash_distance']} "
                        f"fall within near-duplicate threshold (<= 4)."
                    ),
                    disclaimer=disclaimer_text
                )
                records.append(rec)
                continue

            # Geometric verification check
            c_pts, c_descs = None, None
            if cand.get("descriptor_rel_path"):
                c_pts, c_descs = descriptor_store.load_features(cand["descriptor_rel_path"])

            geom_res = geometric_verifier.verify_geometry(q_pts, q_descs, c_pts, c_descs)
            combined_metrics = {**cand, "geometric_verification": geom_res}

            # Classification 3: SAME_PHOTOGRAPH_MODIFIED
            if geom_res.get("is_geometric_match"):
                disclaimer_text = (
                    f"Geometric frame correspondence at {cand.get('frame_timestamp_ms', 0)}ms. "
                    f"Does not establish whole-video identity."
                    if is_vf else
                    "Projective geometric correspondence confirmed across feature points. "
                    "Consistent with an edited, cropped, or transformed variant of the same underlying image capture, "
                    "or identical planar subject. Does not establish or infer event identity, location, date, or source provenance."
                )
                rec = MediaMatchRecord(
                    source_evidence_id=submission.id,
                    source_media_asset_id=submission.media_asset_id,
                    matched_media_asset_id=cand["candidate_media_asset_id"],
                    matched_artifact_id=cand.get("matched_artifact_id"),
                    classification="SAME_PHOTOGRAPH_MODIFIED",
                    method="ORB_RANSAC_HOMOGRAPHY",
                    algorithm_version=self.MATCH_ENGINE_VERSION,
                    is_video_frame_match=is_vf,
                    matched_frame_timestamp_ms=cand.get("frame_timestamp_ms"),
                    consecutive_frames_matched=consec_frames,
                    raw_metrics=combined_metrics,
                    classification_rationale=(
                        f"RANSAC homography confirmed with {geom_res['inlier_count']} inliers, "
                        f"inlier ratio {geom_res['inlier_ratio']}, and non-degenerate projective matrix."
                    ),
                    disclaimer=disclaimer_text
                )
                records.append(rec)
                continue

            # Feature-poor candidate
            if geom_res.get("status") == "INSUFFICIENT_FEATURES":
                rec = MediaMatchRecord(
                    source_evidence_id=submission.id,
                    source_media_asset_id=submission.media_asset_id,
                    matched_media_asset_id=cand["candidate_media_asset_id"],
                    matched_artifact_id=cand.get("matched_artifact_id"),
                    classification="INSUFFICIENT_MATCH_EVIDENCE",
                    method="ORB_RANSAC_HOMOGRAPHY",
                    algorithm_version=self.MATCH_ENGINE_VERSION,
                    is_video_frame_match=is_vf,
                    matched_frame_timestamp_ms=cand.get("frame_timestamp_ms"),
                    consecutive_frames_matched=consec_frames,
                    raw_metrics=combined_metrics,
                    classification_rationale=geom_res.get("failure_reason"),
                    disclaimer="Insufficient features extracted from candidate to evaluate projective geometry."
                )
                records.append(rec)
                continue

            # Classification 4: POSSIBLE_VISUAL_SIMILARITY
            rec = MediaMatchRecord(
                source_evidence_id=submission.id,
                source_media_asset_id=submission.media_asset_id,
                matched_media_asset_id=cand["candidate_media_asset_id"],
                matched_artifact_id=cand.get("matched_artifact_id"),
                classification="POSSIBLE_VISUAL_SIMILARITY",
                method="PERCEPTUAL_PREFILTER_AND_FEATURE_ALIGNMENT",
                algorithm_version=self.MATCH_ENGINE_VERSION,
                is_video_frame_match=is_vf,
                matched_frame_timestamp_ms=cand.get("frame_timestamp_ms"),
                consecutive_frames_matched=consec_frames,
                raw_metrics=combined_metrics,
                classification_rationale=(
                    f"Candidate passed perceptual candidate pre-filter (pHash dist {cand.get('phash_distance')}) "
                    f"but geometric RANSAC homography rejected projective consistency "
                    f"({geom_res.get('failure_reason')})."
                ),
                disclaimer=(
                    "Visual similarity observed without projective geometric consensus. "
                    "Does NOT prove or imply same event or scene."
                )
            )
            records.append(rec)

        for r in records:
            db_session.add(r)
        await db_session.flush()

        return records

match_engine = MatchEngine()
