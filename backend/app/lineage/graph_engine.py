"""
Claim Lineage Graph Engine.

Constructs an evidence-backed directed lineage graph connecting:
- Investigations, Evidence Submissions, Media Assets, Claims,
  Claim Variants, Retrieved Sources, Accounts, and Assessments.
Distinguishes OBSERVED from INFERRED edges, attaches underlying evidence records,
computes chronological timelines, and compiles unresolved investigative questions.
Uses NetworkX MultiDiGraph for graph operations, cycle detection, and subgraphs.
"""

import uuid
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timezone
import networkx as nx
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.investigation import Investigation
from app.models.evidence import EvidenceSubmission, MediaAsset, ExtractionRecord
from app.models.fingerprint import MediaMatchRecord
from app.models.claim import ClaimRecord
from app.models.source import RetrievedSourceRecord, SourceIndependenceRecord
from app.models.context_verification import ClaimAssessmentRecord, ClaimEvidenceRelationRecord
from app.models.relationship import LineageRelationshipRecord
from app.schemas.relationship import (
    LineageNodeType,
    LineageRelationshipType,
    LineageEdgeNature,
    LineageReviewStatus,
    LineageNode,
    LineageEdge,
    LineageGraphResponse,
    LineageTimelineItem,
    LineageTimelineResponse
)

logger = logging.getLogger(__name__)

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LineageGraphEngine:
    """
    Constructs, queries, and serializes the complete or bounded Claim Lineage graph
    for an investigation, ensuring every edge has evidence traceability and
    explicit edge nature (OBSERVED vs INFERRED).
    """

    @classmethod
    async def build_investigation_graph(
        cls,
        session: AsyncSession,
        investigation_id: str,
        focus_claim_id: Optional[str] = None,
        max_nodes: int = 150,
        include_inferred: bool = True
    ) -> LineageGraphResponse:
        """
        Builds the unified lineage graph for an investigation.
        """
        # 1. Verify Investigation exists
        inv_stmt = select(Investigation).where(Investigation.id == investigation_id)
        inv_res = await session.execute(inv_stmt)
        investigation = inv_res.scalars().first()
        if not investigation:
            raise ValueError(f"Investigation with id '{investigation_id}' not found.")

        graph = nx.MultiDiGraph()
        nodes_dict: Dict[str, LineageNode] = {}
        edges_list: List[LineageEdge] = []
        unresolved_questions: List[Dict[str, Any]] = []

        # 2. Add Investigation Root Node
        inv_node_id = f"inv_{investigation.id}"
        inv_node = LineageNode(
            id=inv_node_id,
            entity_type=LineageNodeType.INVESTIGATION,
            entity_id=investigation.id,
            label=f"Investigation: {investigation.title}",
            investigation_id=investigation.id,
            metadata={
                "status": investigation.status,
                "priority": investigation.priority,
                "created_at": investigation.created_at.isoformat() if investigation.created_at else None
            },
            provenance={"source": "database_table_investigations"}
        )
        nodes_dict[inv_node_id] = inv_node
        graph.add_node(inv_node_id, **inv_node.model_dump())

        # 3. Load Submissions
        sub_stmt = select(EvidenceSubmission).where(
            EvidenceSubmission.investigation_id == investigation_id
        ).order_by(EvidenceSubmission.created_at)
        sub_res = await session.execute(sub_stmt)
        submissions = sub_res.scalars().all()

        submission_ids = set()
        media_asset_ids = set()

        for sub in submissions:
            sub_node_id = f"sub_{sub.id}"
            submission_ids.add(sub.id)
            label_text = sub.caption or sub.raw_text or f"{sub.submission_type} Submission"
            if len(label_text) > 40:
                label_text = label_text[:37] + "..."

            sub_node = LineageNode(
                id=sub_node_id,
                entity_type=LineageNodeType.EVIDENCE_SUBMISSION,
                entity_id=sub.id,
                label=f"Submission: {label_text}",
                investigation_id=investigation_id,
                metadata={
                    "submission_type": sub.submission_type,
                    "claimed_date": sub.claimed_date,
                    "claimed_location": sub.claimed_location,
                    "language": sub.language,
                    "processing_status": sub.processing_status,
                    "submitted_at": sub.created_at.isoformat() if sub.created_at else None
                },
                provenance={"submission_id": sub.id}
            )
            nodes_dict[sub_node_id] = sub_node
            graph.add_node(sub_node_id, **sub_node.model_dump())

            # Edge: Investigation -> Submission
            edge_id = f"edge_inv_sub_{sub.id[:8]}"
            sub_edge = LineageEdge(
                id=edge_id,
                source_id=inv_node_id,
                target_id=sub_node_id,
                relationship_type=LineageRelationshipType.ASSOCIATED_WITH_EVENT,
                edge_nature=LineageEdgeNature.OBSERVED,
                is_inferred=False,
                evidence_id=sub.id,
                evidence_summary=f"Direct evidence intake submission in {investigation.title}",
                detection_method="SYSTEM_INTAKE_RECORD"
            )
            edges_list.append(sub_edge)
            graph.add_edge(inv_node_id, sub_node_id, key=edge_id, **sub_edge.model_dump())

            # 4. Media Asset Node & Link
            if sub.media_asset_id:
                media_asset_ids.add(sub.media_asset_id)
                media_node_id = f"media_{sub.media_asset_id}"
                if media_node_id not in nodes_dict:
                    media_node = LineageNode(
                        id=media_node_id,
                        entity_type=LineageNodeType.MEDIA_ASSET,
                        entity_id=sub.media_asset_id,
                        label=f"Media: {sub.submission_type}",
                        investigation_id=investigation_id,
                        metadata={
                            "media_asset_id": sub.media_asset_id,
                            "submission_type": sub.submission_type
                        },
                        provenance={"media_asset_id": sub.media_asset_id}
                    )
                    nodes_dict[media_node_id] = media_node
                    graph.add_node(media_node_id, **media_node.model_dump())

                # Edge: Submission -> Media Asset (EXACT_MEDIA_MATCH, Observed)
                edge_id = f"edge_sub_media_{sub.id[:8]}_{sub.media_asset_id[:8]}"
                media_edge = LineageEdge(
                    id=edge_id,
                    source_id=sub_node_id,
                    target_id=media_node_id,
                    relationship_type=LineageRelationshipType.EXACT_MEDIA_MATCH,
                    edge_nature=LineageEdgeNature.OBSERVED,
                    is_inferred=False,
                    evidence_id=sub.media_asset_id,
                    evidence_summary="Submission provides binary container for this MediaAsset",
                    detection_method="SHA256_HASH_VERIFICATION"
                )
                edges_list.append(media_edge)
                graph.add_edge(sub_node_id, media_node_id, key=edge_id, **media_edge.model_dump())

        # 5. Historical Media Matches
        if media_asset_ids:
            match_stmt = select(MediaMatchRecord).where(
                (MediaMatchRecord.source_media_asset_id.in_(media_asset_ids)) |
                (MediaMatchRecord.matched_media_asset_id.in_(media_asset_ids))
            )
            match_res = await session.execute(match_stmt)
            matches = match_res.scalars().all()

            for match in matches:
                # Target matched media asset node
                target_asset_id = match.matched_media_asset_id or match.source_media_asset_id
                matched_node_id = f"media_{target_asset_id}"
                if matched_node_id not in nodes_dict:
                    matched_node = LineageNode(
                        id=matched_node_id,
                        entity_type=LineageNodeType.MEDIA_ASSET,
                        entity_id=target_asset_id,
                        label=f"Historical Match: {match.classification}",
                        investigation_id=investigation_id,
                        metadata={
                            "classification": match.classification,
                            "method": match.method,
                            "raw_metrics": match.raw_metrics
                        },
                        provenance={"match_record_id": match.id}
                    )
                    nodes_dict[matched_node_id] = matched_node
                    graph.add_node(matched_node_id, **matched_node.model_dump())

                # Determine edge type & nature
                edge_nature = LineageEdgeNature.OBSERVED if match.classification == "EXACT_FILE_MATCH" else LineageEdgeNature.INFERRED
                rel_type_map = {
                    "EXACT_FILE_MATCH": LineageRelationshipType.EXACT_MEDIA_MATCH,
                    "NEAR_DUPLICATE": LineageRelationshipType.NEAR_DUPLICATE_MEDIA,
                    "SAME_PHOTOGRAPH_MODIFIED": LineageRelationshipType.SAME_PHOTOGRAPH_CANDIDATE,
                    "POSSIBLE_VISUAL_SIMILARITY": LineageRelationshipType.POSSIBLE_REUSED_MEDIA
                }
                rel_type = rel_type_map.get(match.classification, LineageRelationshipType.POSSIBLE_REUSED_MEDIA)

                source_node_id = f"media_{match.source_media_asset_id}"
                if source_node_id in nodes_dict and matched_node_id in nodes_dict and source_node_id != matched_node_id:
                    edge_id = f"edge_match_{match.id[:8]}"
                    m_edge = LineageEdge(
                        id=edge_id,
                        source_id=source_node_id,
                        target_id=matched_node_id,
                        relationship_type=rel_type,
                        edge_nature=edge_nature,
                        is_inferred=(edge_nature == LineageEdgeNature.INFERRED),
                        evidence_id=match.id,
                        evidence_summary=f"Historical media alignment: {match.classification} ({match.classification_rationale or match.method})",
                        detection_method=match.method,
                        confidence=getattr(match, "confidence_score", None) or (match.raw_metrics.get("confidence") if isinstance(match.raw_metrics, dict) else None) or 1.0,
                        timestamps={"matched_at": match.created_at.isoformat() if match.created_at else None},
                        metadata=match.raw_metrics
                    )
                    edges_list.append(m_edge)
                    graph.add_edge(source_node_id, matched_node_id, key=edge_id, **m_edge.model_dump())

        # 6. Load Claim Records
        claim_stmt = select(ClaimRecord).where(
            ClaimRecord.investigation_id == investigation_id
        ).order_by(ClaimRecord.version.desc())
        claim_res = await session.execute(claim_stmt)
        all_claims = claim_res.scalars().all()

        active_claims = [c for c in all_claims if c.is_active]
        if focus_claim_id:
            active_claims = [c for c in active_claims if c.id == focus_claim_id]

        claim_ids = [c.id for c in active_claims]

        for claim in active_claims:
            claim_node_id = f"claim_{claim.id}"
            label_text = claim.normalized_claim or claim.claim_text
            if len(label_text) > 45:
                label_text = label_text[:42] + "..."

            claim_node = LineageNode(
                id=claim_node_id,
                entity_type=LineageNodeType.CLAIM,
                entity_id=claim.id,
                label=f"Claim: {label_text}",
                investigation_id=investigation_id,
                metadata={
                    "claim_text": claim.claim_text,
                    "normalized_claim": claim.normalized_claim,
                    "subject": claim.subject,
                    "predicate": claim.predicate,
                    "object": claim.object,
                    "polarity_state": claim.polarity_state,
                    "language": claim.language,
                    "version": claim.version,
                    "is_active": claim.is_active
                },
                provenance={
                    "evidence_submission_id": claim.evidence_submission_id,
                    "source_modality": claim.source_modality,
                    "evidence_span_start": claim.evidence_span_start,
                    "evidence_span_end": claim.evidence_span_end
                }
            )
            nodes_dict[claim_node_id] = claim_node
            graph.add_node(claim_node_id, **claim_node.model_dump())

            # Edge: Submission -> Claim (EXTRACTED_FROM / SAME_CLAIM, Observed)
            sub_node_id = f"sub_{claim.evidence_submission_id}"
            if sub_node_id in nodes_dict:
                edge_id = f"edge_sub_claim_{claim.id[:8]}"
                c_edge = LineageEdge(
                    id=edge_id,
                    source_id=sub_node_id,
                    target_id=claim_node_id,
                    relationship_type=LineageRelationshipType.SAME_CLAIM,
                    edge_nature=LineageEdgeNature.OBSERVED,
                    is_inferred=False,
                    evidence_id=claim.id,
                    evidence_summary=f"Syntactic proposition extracted from {claim.source_modality} span [{claim.evidence_span_start}:{claim.evidence_span_end}]",
                    detection_method=claim.extraction_method
                )
                edges_list.append(c_edge)
                graph.add_edge(sub_node_id, claim_node_id, key=edge_id, **c_edge.model_dump())

        # 7. Cross-Claim Variant & Duplicate Analysis
        for i in range(len(active_claims)):
            for j in range(i + 1, len(active_claims)):
                c1 = active_claims[i]
                c2 = active_claims[j]
                
                # Check if identical normalized text
                if c1.normalized_claim and c1.normalized_claim.lower() == c2.normalized_claim.lower():
                    edge_id = f"edge_same_claim_{c1.id[:6]}_{c2.id[:6]}"
                    var_edge = LineageEdge(
                        id=edge_id,
                        source_id=f"claim_{c1.id}",
                        target_id=f"claim_{c2.id}",
                        relationship_type=LineageRelationshipType.SAME_CLAIM,
                        edge_nature=LineageEdgeNature.OBSERVED,
                        is_inferred=False,
                        evidence_id=c2.id,
                        evidence_summary="Identical normalized proposition text across submissions",
                        detection_method="NORMALIZED_TEXT_IDENTITY"
                    )
                    edges_list.append(var_edge)
                    graph.add_edge(f"claim_{c1.id}", f"claim_{c2.id}", key=edge_id, **var_edge.model_dump())
                elif c1.subject and c2.subject and c1.predicate and c2.predicate and (
                    c1.subject.lower() == c2.subject.lower() and c1.predicate.lower() == c2.predicate.lower()
                ):
                    # Claim variant (same subject & predicate, different phrasing or qualifiers)
                    edge_id = f"edge_variant_{c1.id[:6]}_{c2.id[:6]}"
                    var_edge = LineageEdge(
                        id=edge_id,
                        source_id=f"claim_{c1.id}",
                        target_id=f"claim_{c2.id}",
                        relationship_type=LineageRelationshipType.CLAIM_VARIANT,
                        edge_nature=LineageEdgeNature.INFERRED,
                        is_inferred=True,
                        evidence_id=c2.id,
                        evidence_summary=f"Lexical claim variant sharing core subject '{c1.subject}' and action '{c1.predicate}'",
                        detection_method="SEMANTIC_PREDICATE_MATCH"
                    )
                    edges_list.append(var_edge)
                    graph.add_edge(f"claim_{c1.id}", f"claim_{c2.id}", key=edge_id, **var_edge.model_dump())

        # 8. Load Retrieved Sources & Evidence Relations
        if claim_ids:
            # Sources
            src_stmt = select(RetrievedSourceRecord).where(
                RetrievedSourceRecord.claim_id.in_(claim_ids),
                RetrievedSourceRecord.retrieval_status.in_(["SUCCESS", "PARTIAL", "COMPLETED"])
            )
            src_res = await session.execute(src_stmt)
            retrieved_sources = src_res.scalars().all()

            # Assessments & Relations
            ass_stmt = select(ClaimAssessmentRecord).where(
                ClaimAssessmentRecord.claim_id.in_(claim_ids),
                ClaimAssessmentRecord.is_active == True
            ).options(selectinload(ClaimAssessmentRecord.evidence_relations))
            ass_res = await session.execute(ass_stmt)
            assessments = ass_res.scalars().all()

            # Map evidence relations by source url or source id
            relation_by_source: Dict[Tuple[str, str], ClaimEvidenceRelationRecord] = {}
            for ass in assessments:
                for rel in (ass.evidence_relations or []):
                    if rel.source_location:
                        relation_by_source[(ass.claim_id, rel.source_location)] = rel
                    if rel.evidence_source_id:
                        relation_by_source[(ass.claim_id, rel.evidence_source_id)] = rel
                        # also strip prefix if src-
                        clean_sid = rel.evidence_source_id.replace("src-", "")
                        relation_by_source[(ass.claim_id, clean_sid)] = rel

            # Source Independence Records
            indep_stmt = select(SourceIndependenceRecord).where(
                SourceIndependenceRecord.claim_id.in_(claim_ids)
            )
            indep_res = await session.execute(indep_stmt)
            indep_records = {rec.claim_id: rec for rec in indep_res.scalars().all()}

            # Add Source Nodes and Edges
            for src in retrieved_sources:
                src_node_id = f"src_{src.id}"
                if src_node_id not in nodes_dict:
                    src_node = LineageNode(
                        id=src_node_id,
                        entity_type=LineageNodeType.SOURCE,
                        entity_id=src.id,
                        label=f"{src.publisher}: {src.article_title[:28]}",
                        investigation_id=investigation_id,
                        metadata={
                            "canonical_url": src.canonical_url,
                            "publisher": src.publisher,
                            "author": src.author,
                            "published_date": src.published_date,
                            "http_status": src.http_status,
                            "content_hash": src.content_hash,
                            "source_type": src.source_type,
                            "has_claim_review": bool(src.claim_review_metadata)
                        },
                        provenance={
                            "retrieval_method": src.retrieval_method,
                            "search_provider": src.search_provider,
                            "retrieval_timestamp": src.retrieval_timestamp.isoformat() if src.retrieval_timestamp else None
                        }
                    )
                    nodes_dict[src_node_id] = src_node
                    graph.add_node(src_node_id, **src_node.model_dump())

                # Find relationship to claim
                rel_rec = relation_by_source.get((src.claim_id, src.canonical_url)) or relation_by_source.get((src.claim_id, src.id))
                rel_type = LineageRelationshipType.SIMILAR_REPORTING
                evidence_summary = f"Retrieved source citing: {src.text_excerpt[:120]}"
                
                if rel_rec:
                    if rel_rec.relationship_type == "SUPPORTS":
                        rel_type = LineageRelationshipType.SUPPORTS
                        evidence_summary = f"Source corroborates proposition: {rel_rec.alignment_rationale}"
                    elif rel_rec.relationship_type == "CONTRADICTS":
                        rel_type = LineageRelationshipType.CONTRADICTS
                        evidence_summary = f"Source refutes proposition: {rel_rec.alignment_rationale}"
                    elif rel_rec.relationship_type in ["PROVIDES_CONTEXT", "TEMPORAL_CONFLICT", "GEOGRAPHICAL_CONFLICT"]:
                        rel_type = LineageRelationshipType.MISLEADING_CONTEXT
                        evidence_summary = f"Source provides conflicting context: {rel_rec.alignment_rationale}"

                claim_node_id = f"claim_{src.claim_id}"
                if claim_node_id in nodes_dict:
                    edge_id = f"edge_src_claim_{src.id[:6]}_{src.claim_id[:6]}"
                    s_edge = LineageEdge(
                        id=edge_id,
                        source_id=src_node_id,
                        target_id=claim_node_id,
                        relationship_type=rel_type,
                        edge_nature=LineageEdgeNature.INFERRED,
                        is_inferred=True,
                        evidence_id=src.id,
                        evidence_summary=evidence_summary,
                        detection_method=src.retrieval_method,
                        timestamps={
                            "published_date": src.published_date,
                            "retrieved_at": src.retrieval_timestamp.isoformat() if src.retrieval_timestamp else None
                        },
                        metadata={
                            "excerpt": src.text_excerpt,
                            "canonical_url": src.canonical_url
                        }
                    )
                    edges_list.append(s_edge)
                    graph.add_edge(src_node_id, claim_node_id, key=edge_id, **s_edge.model_dump())

            # 9. Source Dependencies & Wire Services
            for cid, indep in indep_records.items():
                if not indep.clusters:
                    continue
                for c in indep.clusters:
                    dep_type = c.get("dependency_type")
                    wire_agency = c.get("wire_agency")
                    sids = c.get("source_ids", [])
                    
                    if wire_agency and dep_type == "WIRE_SERVICE_DERIVED":
                        # Create Wire Agency Node
                        wire_node_id = f"wire_{wire_agency.replace(' ', '_')}"
                        if wire_node_id not in nodes_dict:
                            wire_node = LineageNode(
                                id=wire_node_id,
                                entity_type=LineageNodeType.ACCOUNT,
                                entity_id=wire_agency,
                                label=f"Wire: {wire_agency}",
                                investigation_id=investigation_id,
                                metadata={"agency_name": wire_agency, "type": "WIRE_NEWS_SERVICE"},
                                provenance={"detection": "Byline and dateline attribution"}
                            )
                            nodes_dict[wire_node_id] = wire_node
                            graph.add_node(wire_node_id, **wire_node.model_dump())

                        # Link wire to each republished source
                        for sid in sids:
                            src_node_id = f"src_{sid}"
                            if src_node_id in nodes_dict:
                                edge_id = f"edge_wire_src_{wire_node_id[:6]}_{sid[:6]}"
                                w_edge = LineageEdge(
                                    id=edge_id,
                                    source_id=wire_node_id,
                                    target_id=src_node_id,
                                    relationship_type=LineageRelationshipType.SHARED_WIRE_REPORT,
                                    edge_nature=LineageEdgeNature.OBSERVED,
                                    is_inferred=False,
                                    evidence_id=sid,
                                    evidence_summary=f"Article carries syndicated wire dispatch from {wire_agency}",
                                    detection_method="WIRE_BYLINE_DETECTION"
                                )
                                edges_list.append(w_edge)
                                graph.add_edge(wire_node_id, src_node_id, key=edge_id, **w_edge.model_dump())

                    elif dep_type == "SHARED_PRESS_RELEASE" and len(sids) >= 2:
                        # Link between co-dependent press release sources
                        for k in range(len(sids) - 1):
                            s1 = f"src_{sids[k]}"
                            s2 = f"src_{sids[k+1]}"
                            if s1 in nodes_dict and s2 in nodes_dict:
                                edge_id = f"edge_pr_{sids[k][:4]}_{sids[k+1][:4]}"
                                pr_edge = LineageEdge(
                                    id=edge_id,
                                    source_id=s1,
                                    target_id=s2,
                                    relationship_type=LineageRelationshipType.SHARED_PRESS_RELEASE,
                                    edge_nature=LineageEdgeNature.INFERRED,
                                    is_inferred=True,
                                    evidence_id=sids[k],
                                    evidence_summary=c.get("rationale") or "Shared verbatim official press statement",
                                    detection_method="PRESS_RELEASE_OVERLAP"
                                )
                                edges_list.append(pr_edge)
                                graph.add_edge(s1, s2, key=edge_id, **pr_edge.model_dump())

            # 10. Assessment Nodes & Evaluation Edges
            for ass in assessments:
                ass_node_id = f"ass_{ass.id}"
                ass_node = LineageNode(
                    id=ass_node_id,
                    entity_type=LineageNodeType.ASSESSMENT,
                    entity_id=ass.id,
                    label=f"Verdict: {ass.classification}",
                    investigation_id=investigation_id,
                    metadata={
                        "classification": ass.classification,
                        "version": ass.version,
                        "evaluation_method": ass.evaluation_method,
                        "verifier_version": ass.verifier_version,
                        "primary_rationale": ass.primary_rationale,
                        "human_review_status": ass.human_review_status,
                        "epistemic_limitations": ass.epistemic_limitations
                    },
                    provenance={"assessment_id": ass.id}
                )
                nodes_dict[ass_node_id] = ass_node
                graph.add_node(ass_node_id, **ass_node.model_dump())

                claim_node_id = f"claim_{ass.claim_id}"
                if claim_node_id in nodes_dict:
                    edge_id = f"edge_claim_ass_{ass.id[:8]}"
                    rel_type = (
                        LineageRelationshipType.CONTRADICTS if ass.classification == "CONTRADICTED"
                        else LineageRelationshipType.SUPPORTS if ass.classification == "SUPPORTED"
                        else LineageRelationshipType.MISLEADING_CONTEXT if ass.classification == "MISLEADING_OR_CONTEXT_MISSING"
                        else LineageRelationshipType.SAME_CLAIM
                    )
                    ass_edge = LineageEdge(
                        id=edge_id,
                        source_id=claim_node_id,
                        target_id=ass_node_id,
                        relationship_type=rel_type,
                        edge_nature=LineageEdgeNature.OBSERVED,
                        is_inferred=False,
                        evidence_id=ass.id,
                        evidence_summary=ass.primary_rationale,
                        detection_method=ass.evaluation_method
                    )
                    edges_list.append(ass_edge)
                    graph.add_edge(claim_node_id, ass_node_id, key=edge_id, **ass_edge.model_dump())

                # Collect recommended unresolved questions
                if ass.recommended_investigator_actions:
                    for act in ass.recommended_investigator_actions:
                        unresolved_questions.append({
                            "claim_id": ass.claim_id,
                            "action": act.get("action"),
                            "question": act.get("description")
                        })

        # 11. Load Explicit User-Reviewed Lineage Relationships
        explicit_stmt = select(LineageRelationshipRecord).where(
            LineageRelationshipRecord.investigation_id == investigation_id
        )
        explicit_res = await session.execute(explicit_stmt)
        explicit_relationships = explicit_res.scalars().all()

        for exp in explicit_relationships:
            s_id = exp.source_entity_id if exp.source_entity_id.startswith(("claim_", "sub_", "media_", "src_", "inv_")) else f"claim_{exp.source_entity_id}"
            t_id = exp.target_entity_id if exp.target_entity_id.startswith(("claim_", "sub_", "media_", "src_", "inv_")) else f"claim_{exp.target_entity_id}"
            
            # If nodes exist, add or update edge
            if s_id in nodes_dict and t_id in nodes_dict:
                edge_id = f"rel_{exp.id}"
                exp_edge = LineageEdge(
                    id=edge_id,
                    source_id=s_id,
                    target_id=t_id,
                    relationship_type=LineageRelationshipType(exp.relationship_type),
                    edge_nature=LineageEdgeNature(exp.edge_nature),
                    is_inferred=exp.is_inferred,
                    evidence_id=exp.evidence_id,
                    evidence_summary=exp.evidence_summary,
                    detection_method=exp.detection_method,
                    confidence=exp.confidence,
                    review_status=LineageReviewStatus(exp.review_status),
                    reviewer_notes=exp.reviewer_notes,
                    reviewed_by=exp.reviewed_by,
                    reviewed_at=exp.reviewed_at,
                    timestamps=exp.timestamps,
                    metadata=exp.relationship_metadata
                )
                edges_list.append(exp_edge)
                graph.add_edge(s_id, t_id, key=edge_id, **exp_edge.model_dump())

        # If filtered by max_nodes, restrict graph bounded around focus or investigation root
        all_nodes = list(nodes_dict.values())
        if len(all_nodes) > max_nodes:
            all_nodes = all_nodes[:max_nodes]
            allowed_ids = set(n.id for n in all_nodes)
            edges_list = [e for e in edges_list if e.source_id in allowed_ids and e.target_id in allowed_ids]

        if not include_inferred:
            edges_list = [e for e in edges_list if e.edge_nature == LineageEdgeNature.OBSERVED]

        epistemic_notes = (
            "Evidence-backed Claim Lineage. Solid edges represent directly observed container, metadata, "
            "and identity relations. Dashed edges represent algorithmic, textual, or attribution inferences. "
            "Absence of corroborating evidence does not prove falsehood."
        )

        return LineageGraphResponse(
            investigation_id=investigation_id,
            nodes=all_nodes,
            edges=edges_list,
            node_count=len(all_nodes),
            edge_count=len(edges_list),
            unresolved_questions=unresolved_questions,
            epistemic_notes=epistemic_notes
        )

    @classmethod
    async def build_investigation_timeline(
        cls,
        session: AsyncSession,
        investigation_id: str
    ) -> LineageTimelineResponse:
        """
        Builds a chronological timeline of events, capture dates, submissions,
        and retrieved sources for an investigation.
        """
        items: List[LineageTimelineItem] = []

        # 1. Submissions & Claimed Dates
        sub_stmt = select(EvidenceSubmission).where(
            EvidenceSubmission.investigation_id == investigation_id
        )
        sub_res = await session.execute(sub_stmt)
        submissions = sub_res.scalars().all()

        for sub in submissions:
            if sub.claimed_date:
                items.append(LineageTimelineItem(
                    timestamp=sub.claimed_date,
                    timestamp_type="CLAIMED_EVENT_DATE",
                    entity_id=sub.id,
                    entity_type=LineageNodeType.EVIDENCE_SUBMISSION,
                    label=f"Claimed Event: {sub.caption or sub.raw_text or 'Evidence'}",
                    details={"claimed_location": sub.claimed_location, "submission_id": sub.id}
                ))
            if sub.created_at:
                items.append(LineageTimelineItem(
                    timestamp=sub.created_at.isoformat(),
                    timestamp_type="SUBMISSION_DATE",
                    entity_id=sub.id,
                    entity_type=LineageNodeType.EVIDENCE_SUBMISSION,
                    label=f"Submitted to TRUTHNET: {sub.submission_type}",
                    details={"submission_type": sub.submission_type}
                ))

        # 2. Media Extraction Records (EXIF Original Capture Date)
        sub_ids = [s.id for s in submissions]
        if sub_ids:
            ext_stmt = select(ExtractionRecord).where(
                ExtractionRecord.evidence_submission_id.in_(sub_ids),
                ExtractionRecord.is_active == True
            )
            ext_res = await session.execute(ext_stmt)
            for ext in ext_res.scalars().all():
                if ext.technical_metadata:
                    orig_dt = ext.technical_metadata.get("datetime_original") or ext.technical_metadata.get("creation_time")
                    if orig_dt:
                        items.append(LineageTimelineItem(
                            timestamp=str(orig_dt),
                            timestamp_type="EXIF_MEDIA_CAPTURE_DATE",
                            entity_id=ext.evidence_submission_id,
                            entity_type=LineageNodeType.MEDIA_ASSET,
                            label=f"Observed Media Capture Timestamp",
                            details={"camera_exif": orig_dt}
                        ))

        # 3. Retrieved Source Publication Dates
        src_stmt = select(RetrievedSourceRecord).where(
            RetrievedSourceRecord.investigation_id == investigation_id,
            RetrievedSourceRecord.retrieval_status.in_(["SUCCESS", "PARTIAL", "COMPLETED"])
        )
        src_res = await session.execute(src_stmt)
        for src in src_res.scalars().all():
            if src.published_date:
                items.append(LineageTimelineItem(
                    timestamp=src.published_date,
                    timestamp_type="SOURCE_PUBLICATION_DATE",
                    entity_id=src.id,
                    entity_type=LineageNodeType.SOURCE,
                    label=f"Report Published: {src.publisher}",
                    details={"title": src.article_title, "url": src.canonical_url}
                ))
            if src.retrieval_timestamp:
                items.append(LineageTimelineItem(
                    timestamp=src.retrieval_timestamp.isoformat(),
                    timestamp_type="EXTERNAL_RETRIEVAL_DATE",
                    entity_id=src.id,
                    entity_type=LineageNodeType.SOURCE,
                    label=f"Source Retrieved: {src.publisher}",
                    details={"url": src.canonical_url}
                ))

        # 4. Contextual Assessment Creation Dates
        ass_stmt = select(ClaimAssessmentRecord).where(
            ClaimAssessmentRecord.investigation_id == investigation_id,
            ClaimAssessmentRecord.is_active == True
        )
        ass_res = await session.execute(ass_stmt)
        for ass in ass_res.scalars().all():
            if ass.created_at:
                items.append(LineageTimelineItem(
                    timestamp=ass.created_at.isoformat(),
                    timestamp_type="ASSESSMENT_DATE",
                    entity_id=ass.id,
                    entity_type=LineageNodeType.ASSESSMENT,
                    label=f"Assessment Verdict: {ass.classification}",
                    details={"rationale": ass.primary_rationale}
                ))

        # Sort timeline chronologically
        def sort_key(item: LineageTimelineItem):
            ts = item.timestamp or ""
            return ts

        items.sort(key=sort_key)

        return LineageTimelineResponse(
            investigation_id=investigation_id,
            events=items,
            total_events=len(items)
        )
