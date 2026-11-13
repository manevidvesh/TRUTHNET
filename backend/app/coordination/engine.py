"""
Coordinated Misinformation Intelligence Engine.

Performs explainable, evidence-backed detection of coordinated distribution signals:
1. Repeated or near-identical claim text across submissions.
2. Similar captions across accounts/submissions.
3. Shared media distribution (SHA-256 or perceptual hash collision).
4. Shared external URLs or wire-service citations.
5. Temporal bursts and posting-time synchronization.
6. Graph-based connected component clustering.

Strict Epistemic Safeguards:
- Never labels an account a "bot" or "malicious actor" without explicit proof.
- Distinguishes observed similarities from inferred intent.
- Always exposes raw measurements and explicit epistemic boundaries.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set, Tuple
import networkx as nx
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evidence import EvidenceSubmission, MediaAsset
from app.models.claim import ClaimRecord
from app.models.source import RetrievedSourceRecord
from app.models.fingerprint import MediaMatchRecord
from app.models.relationship import LineageRelationshipRecord
from app.models.coordination import CoordinationClusterRecord

logger = logging.getLogger("truthnet.coordination.engine")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CoordinationAnalysisEngine:
    """
    Deterministic coordination detection engine analyzing multi-submission investigations.
    """

    EPISTEMIC_DISCLAIMER = (
        "Coordination signals quantify observed textual, temporal, and media overlap across submissions. "
        "A similarity signal or shared URL is NOT definitive proof of malicious coordination or automated inauthentic "
        "behavior; legitimate breaking news coverage and organic syndication naturally exhibit high temporal and topical correlation."
    )

    @classmethod
    def compute_jaccard_similarity(cls, text_a: str, text_b: str) -> float:
        """Computes word-token Jaccard similarity between two texts."""
        words_a = set(w.lower() for w in text_a.split() if len(w) > 2)
        words_b = set(w.lower() for w in text_b.split() if len(w) > 2)
        if not words_a or not words_b:
            return 0.0
        intersection = len(words_a.intersection(words_b))
        union = len(words_a.union(words_b))
        return round(float(intersection / union), 4)

    @classmethod
    async def analyze_investigation(
        cls,
        session: AsyncSession,
        investigation_id: str
    ) -> List[CoordinationClusterRecord]:
        """
        Runs comprehensive coordination analysis on an investigation.
        Identifies temporal bursts, shared media, repeated claims, and shared URLs.
        """
        # 1. Load submissions, claims, sources, and media matches
        sub_res = await session.execute(
            select(EvidenceSubmission).where(EvidenceSubmission.investigation_id == investigation_id)
            .order_by(EvidenceSubmission.created_at)
        )
        submissions = list(sub_res.scalars().all())

        claim_res = await session.execute(
            select(ClaimRecord).where(ClaimRecord.investigation_id == investigation_id)
        )
        claims = list(claim_res.scalars().all())

        src_res = await session.execute(
            select(RetrievedSourceRecord).where(RetrievedSourceRecord.investigation_id == investigation_id)
        )
        sources = list(src_res.scalars().all())

        # If fewer than 2 submissions, coordination cannot be established
        if len(submissions) < 2:
            single_cluster = CoordinationClusterRecord(
                investigation_id=investigation_id,
                cluster_type="INSUFFICIENT_COORDINATION_EVIDENCE",
                title="Single Submission Analysis",
                summary="Insufficient submissions to evaluate cross-account coordination or distribution patterns.",
                entities_involved=[{"entity_id": s.id, "entity_type": "EVIDENCE_SUBMISSION", "label": f"Submission {s.id[:8]}"} for s in submissions],
                supporting_observations={"submission_count": len(submissions)},
                detection_method="SINGLETON_EVALUATION",
                confidence=1.0,
                epistemic_limitations=cls.EPISTEMIC_DISCLAIMER,
                review_status="UNREVIEWED"
            )
            # Remove previous clusters
            await session.execute(
                delete(CoordinationClusterRecord).where(CoordinationClusterRecord.investigation_id == investigation_id)
            )
            session.add(single_cluster)
            await session.commit()
            return [single_cluster]

        detected_clusters: List[CoordinationClusterRecord] = []
        coordination_graph = nx.Graph()

        # Add all submission nodes
        for s in submissions:
            coordination_graph.add_node(s.id, submission=s)

        # 2. Analyze Pairwise Overlap
        temporal_burst_pairs = []
        shared_media_pairs = []
        repeated_content_pairs = []
        shared_url_pairs = []

        for i in range(len(submissions)):
            for j in range(i + 1, len(submissions)):
                s1 = submissions[i]
                s2 = submissions[j]

                # A. Temporal delta
                t1 = s1.created_at or utc_now()
                t2 = s2.created_at or utc_now()
                if t1.tzinfo is None:
                    t1 = t1.replace(tzinfo=timezone.utc)
                if t2.tzinfo is None:
                    t2 = t2.replace(tzinfo=timezone.utc)
                delta_seconds = abs((t2 - t1).total_seconds())

                # B. Text content / caption
                text1 = (s1.caption or "") + " " + (s1.raw_text or "")
                text2 = (s2.caption or "") + " " + (s2.raw_text or "")
                jaccard = cls.compute_jaccard_similarity(text1, text2)

                # C. Shared media asset
                same_media = (s1.media_asset_id is not None and s1.media_asset_id == s2.media_asset_id)

                # D. Shared external URL
                same_url = (s1.source_url is not None and s2.source_url is not None and s1.source_url == s2.source_url)

                # Signals evaluation
                if same_media:
                    shared_media_pairs.append((s1, s2))
                    coordination_graph.add_edge(s1.id, s2.id, relation="SHARED_MEDIA")

                if jaccard >= 0.50:
                    repeated_content_pairs.append((s1, s2, jaccard))
                    coordination_graph.add_edge(s1.id, s2.id, relation="REPEATED_CONTENT", similarity=jaccard)

                if same_url:
                    shared_url_pairs.append((s1, s2, s1.source_url))
                    coordination_graph.add_edge(s1.id, s2.id, relation="SHARED_URL")

                if delta_seconds <= 1800 and (jaccard >= 0.40 or same_media or same_url):
                    temporal_burst_pairs.append((s1, s2, delta_seconds))
                    coordination_graph.add_edge(s1.id, s2.id, relation="TEMPORAL_BURST", delta_sec=delta_seconds)

        # 3. Identify Multi-Signal Coordinated Activity
        # Connected components in the coordination graph with 2+ nodes
        components = [c for c in nx.connected_components(coordination_graph) if len(c) > 1]

        for comp in components:
            comp_subs = [s for s in submissions if s.id in comp]
            sub_ids = [s.id for s in comp_subs]

            # Check what signals exist within this component
            has_media = any(s1.id in comp and s2.id in comp for (s1, s2) in shared_media_pairs)
            has_burst = any(s1.id in comp and s2.id in comp for (s1, s2, _) in temporal_burst_pairs)
            has_text = any(s1.id in comp and s2.id in comp for (s1, s2, _) in repeated_content_pairs)
            has_url = any(s1.id in comp and s2.id in comp for (s1, s2, _) in shared_url_pairs)

            signal_count = sum([has_media, has_burst, has_text, has_url])

            if signal_count >= 2:
                cluster_type = "POSSIBLE_COORDINATED_ACTIVITY"
                title = f"Multi-Signal Coordinated Distribution ({len(comp_subs)} submissions)"
                conf = round(min(0.85, 0.50 + signal_count * 0.12), 2)
            elif has_media:
                cluster_type = "SHARED_MEDIA_PATTERN"
                title = f"Shared Media Multi-Distribution ({len(comp_subs)} submissions)"
                conf = 0.75
            elif has_burst:
                cluster_type = "TEMPORAL_BURST"
                title = f"Synchronized Publication Burst ({len(comp_subs)} submissions)"
                conf = 0.70
            elif has_text:
                cluster_type = "REPEATED_CONTENT_PATTERN"
                title = f"Repeated Text Pattern Across Accounts ({len(comp_subs)} submissions)"
                conf = 0.65
            else:
                cluster_type = "SHARED_DISTRIBUTION_PATTERN"
                title = f"Shared Distribution Cluster ({len(comp_subs)} submissions)"
                conf = 0.55

            # Compile entities
            entities = []
            for s in comp_subs:
                label = s.caption or s.raw_text or f"{s.submission_type} Submission"
                entities.append({
                    "entity_id": s.id,
                    "entity_type": "EVIDENCE_SUBMISSION",
                    "label": label[:40]
                })

            summary = (
                f"Cluster of {len(comp_subs)} submissions exhibiting "
                f"{'shared media asset, ' if has_media else ''}"
                f"{'temporal synchronization, ' if has_burst else ''}"
                f"{'high lexical overlap, ' if has_text else ''}"
                f"{'and shared external URL' if has_url else ''}. "
                f"Observed across independent evidence items."
            )

            rec = CoordinationClusterRecord(
                investigation_id=investigation_id,
                cluster_type=cluster_type,
                title=title,
                summary=summary.strip(),
                entities_involved=entities,
                supporting_observations={
                    "member_submission_ids": sub_ids,
                    "has_shared_media": has_media,
                    "has_temporal_burst": has_burst,
                    "has_repeated_content": has_text,
                    "has_shared_url": has_url,
                    "signal_count": signal_count,
                    "connected_component_size": len(comp_subs)
                },
                detection_method="GRAPH_CONNECTED_COMPONENTS_MULTI_SIGNAL",
                confidence=conf,
                epistemic_limitations=cls.EPISTEMIC_DISCLAIMER,
                review_status="UNREVIEWED"
            )
            detected_clusters.append(rec)

            # Persist lineage relationship between members
            for k in range(len(comp_subs) - 1):
                s_from = comp_subs[k]
                s_to = comp_subs[k + 1]
                lin_edge = LineageRelationshipRecord(
                    investigation_id=investigation_id,
                    source_entity_id=s_from.id,
                    source_entity_type="EVIDENCE_SUBMISSION",
                    target_entity_id=s_to.id,
                    target_entity_type="EVIDENCE_SUBMISSION",
                    relationship_type="POSSIBLE_COORDINATION" if signal_count >= 2 else "REPEATED_DISTRIBUTION",
                    edge_nature="SYSTEM_DERIVED",
                    is_inferred=True,
                    evidence_summary=f"Detected {cluster_type} connecting submissions ({signal_count} signals)",
                    detection_method="COORDINATION_ANALYSIS_ENGINE",
                    confidence=conf,
                    review_status="UNREVIEWED"
                )
                session.add(lin_edge)

        # If no clusters found despite multiple submissions
        if not detected_clusters:
            no_coord = CoordinationClusterRecord(
                investigation_id=investigation_id,
                cluster_type="INSUFFICIENT_COORDINATION_EVIDENCE",
                title="No Coordination Patterns Detected",
                summary="Submissions exhibit diverse content, independent publication times, and unlinked media.",
                entities_involved=[{"entity_id": s.id, "entity_type": "EVIDENCE_SUBMISSION", "label": f"Submission {s.id[:8]}"} for s in submissions],
                supporting_observations={"submission_count": len(submissions)},
                detection_method="DETERMINISTIC_CROSS_CHECK",
                confidence=0.85,
                epistemic_limitations=cls.EPISTEMIC_DISCLAIMER,
                review_status="UNREVIEWED"
            )
            detected_clusters.append(no_coord)

        # Clear older clusters for this investigation and save new ones
        await session.execute(
            delete(CoordinationClusterRecord).where(CoordinationClusterRecord.investigation_id == investigation_id)
        )
        for c in detected_clusters:
            session.add(c)
        await session.commit()

        # Emit event to monitoring stream
        try:
            from app.monitoring.events import event_bus
            coord_types = [c.cluster_type for c in detected_clusters if c.cluster_type != "INSUFFICIENT_COORDINATION_EVIDENCE"]
            if coord_types:
                await event_bus.emit(
                    session=session,
                    investigation_id=investigation_id,
                    event_type="COORDINATION_DETECTED",
                    severity="WARNING",
                    summary=f"Detected {len(coord_types)} coordination pattern(s): {', '.join(coord_types)}",
                    details_json={"cluster_count": len(coord_types), "types": coord_types}
                )
        except Exception:
            pass

        logger.info(f"Persisted {len(detected_clusters)} coordination clusters for investigation {investigation_id}.")
        return detected_clusters

    @classmethod
    async def get_clusters(
        cls,
        session: AsyncSession,
        investigation_id: str
    ) -> List[CoordinationClusterRecord]:
        """Fetches active coordination clusters for an investigation."""
        res = await session.execute(
            select(CoordinationClusterRecord)
            .where(CoordinationClusterRecord.investigation_id == investigation_id)
            .order_by(CoordinationClusterRecord.confidence.desc())
        )
        return list(res.scalars().all())


coordination_engine = CoordinationAnalysisEngine()
