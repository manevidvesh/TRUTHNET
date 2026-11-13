"""
Claim Lineage & Explainable Assessment API Router.

Provides endpoints for:
- Building and filtering the interactive directed lineage graph.
- Inspecting individual nodes, edges, and underlying evidence.
- Chronological timeline generation.
- Generating deterministic explainable assessment reports.
- Human review and auditing of lineage relationships.
- Serving an interactive, visual relationship explorer UI.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.investigation import Investigation
from app.models.claim import ClaimRecord
from app.models.source import RetrievedSourceRecord
from app.models.fingerprint import MediaMatchRecord
from app.models.relationship import LineageRelationshipRecord
from app.schemas.relationship import (
    LineageGraphResponse,
    LineageNode,
    LineageEdge,
    LineageEdgeNature,
    LineageTimelineResponse,
    CreateRelationshipRequest,
    ReviewRelationshipRequest,
    ExplainableAssessmentResponse,
    LineageReviewStatus
)
from app.lineage.graph_engine import LineageGraphEngine
from app.lineage.assessment_engine import ExplainableAssessmentEngine

router = APIRouter(tags=["Claim Lineage & Explainable Intelligence"])

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@router.get("/investigations/{investigation_id}/lineage/graph", response_model=LineageGraphResponse, status_code=status.HTTP_200_OK)
async def get_investigation_lineage_graph(
    investigation_id: str,
    focus_claim_id: Optional[str] = Query(None, description="Optional claim ID to focus the subgraph around"),
    max_nodes: int = Query(150, ge=5, le=500, description="Maximum number of nodes to include"),
    include_inferred: bool = Query(True, description="Whether to include inferred edges alongside observed ones"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves the complete or bounded evidence-backed Claim Lineage graph for an investigation.
    Distinguishes OBSERVED from INFERRED edges and provides evidence traceability.
    """
    try:
        graph = await LineageGraphEngine.build_investigation_graph(
            session=db,
            investigation_id=investigation_id,
            focus_claim_id=focus_claim_id,
            max_nodes=max_nodes,
            include_inferred=include_inferred
        )
        return graph
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build lineage graph: {str(e)}"
        )


@router.get("/investigations/{investigation_id}/lineage/timeline", response_model=LineageTimelineResponse, status_code=status.HTTP_200_OK)
async def get_investigation_lineage_timeline(
    investigation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns a chronologically sorted timeline of media capture timestamps,
    evidence submissions, claimed event dates, and retrieved source publications.
    """
    try:
        timeline = await LineageGraphEngine.build_investigation_timeline(
            session=db,
            investigation_id=investigation_id
        )
        return timeline
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build investigation timeline: {str(e)}"
        )


@router.get("/investigations/{investigation_id}/lineage/nodes/{node_id}", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_lineage_node_details(
    investigation_id: str,
    node_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves detailed metadata, provenance, and adjacent relationships for a single node.
    """
    graph = await LineageGraphEngine.build_investigation_graph(session=db, investigation_id=investigation_id)
    node = next((n for n in graph.nodes if n.id == node_id), None)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Node '{node_id}' not found in investigation.")

    incoming = [e for e in graph.edges if e.target_id == node_id]
    outgoing = [e for e in graph.edges if e.source_id == node_id]

    return {
        "node": node,
        "incoming_edges": incoming,
        "outgoing_edges": outgoing,
        "total_connections": len(incoming) + len(outgoing)
    }


@router.get("/investigations/{investigation_id}/lineage/edges/{edge_id}", response_model=LineageEdge, status_code=status.HTTP_200_OK)
async def get_lineage_edge_details(
    investigation_id: str,
    edge_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves full details for an individual edge in the lineage graph.
    """
    graph = await LineageGraphEngine.build_investigation_graph(session=db, investigation_id=investigation_id)
    edge = next((e for e in graph.edges if e.id == edge_id), None)
    if not edge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Edge '{edge_id}' not found.")
    return edge


@router.get("/investigations/{investigation_id}/lineage/edges/{edge_id}/evidence", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_edge_supporting_evidence(
    investigation_id: str,
    edge_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Inspects the underlying evidence record (source passage, media match, or submission)
    that establishes a specific relationship.
    """
    graph = await LineageGraphEngine.build_investigation_graph(session=db, investigation_id=investigation_id)
    edge = next((e for e in graph.edges if e.id == edge_id), None)
    if not edge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Edge '{edge_id}' not found.")

    evidence_data: Dict[str, Any] = {
        "edge_id": edge.id,
        "relationship_type": edge.relationship_type,
        "edge_nature": edge.edge_nature,
        "detection_method": edge.detection_method,
        "evidence_id": edge.evidence_id,
        "evidence_summary": edge.evidence_summary
    }

    if edge.evidence_id:
        # Check RetrievedSourceRecord
        src_res = await db.execute(select(RetrievedSourceRecord).where(RetrievedSourceRecord.id == edge.evidence_id))
        src = src_res.scalars().first()
        if src:
            evidence_data["underlying_record_type"] = "RETRIEVED_SOURCE"
            evidence_data["source_details"] = {
                "article_title": src.article_title,
                "canonical_url": src.canonical_url,
                "publisher": src.publisher,
                "author": src.author,
                "published_date": src.published_date,
                "text_excerpt": src.text_excerpt,
                "content_hash": src.content_hash,
                "retrieval_method": src.retrieval_method,
                "claim_review": src.claim_review_metadata
            }
            return evidence_data

        # Check MediaMatchRecord
        match_res = await db.execute(select(MediaMatchRecord).where(MediaMatchRecord.id == edge.evidence_id))
        match = match_res.scalars().first()
        if match:
            evidence_data["underlying_record_type"] = "HISTORICAL_MEDIA_MATCH"
            evidence_data["match_details"] = {
                "classification": match.classification,
                "method": match.method,
                "confidence_score": getattr(match, "confidence_score", None) or (match.raw_metrics.get("confidence") if isinstance(match.raw_metrics, dict) else None) or 1.0,
                "rationale": match.classification_rationale,
                "raw_metrics": match.raw_metrics,
                "source_media_asset_id": match.source_media_asset_id,
                "matched_media_asset_id": match.matched_media_asset_id
            }
            return evidence_data

    return evidence_data


@router.get("/claims/{claim_id}/lineage", response_model=LineageGraphResponse, status_code=status.HTTP_200_OK)
async def get_claim_focused_lineage(
    claim_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the focused lineage subgraph centered on a specific claim and its immediate connections.
    """
    claim_res = await db.execute(select(ClaimRecord).where(ClaimRecord.id == claim_id))
    claim = claim_res.scalars().first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ClaimRecord with id '{claim_id}' not found.")

    graph = await LineageGraphEngine.build_investigation_graph(
        session=db,
        investigation_id=claim.investigation_id,
        focus_claim_id=claim_id
    )
    return graph


@router.get("/claims/{claim_id}/explanation", response_model=ExplainableAssessmentResponse, status_code=status.HTTP_200_OK)
async def get_claim_explainable_assessment(
    claim_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Generates a deterministic explainable assessment showing exactly why TRUTHNET
    classified a claim, detailing supporting, contradicting, and unaddressed evidence,
    source dependencies, and historical context findings.
    """
    try:
        explanation = await ExplainableAssessmentEngine.generate_explanation(session=db, claim_id=claim_id)
        return explanation
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {str(e)}"
        )


@router.post("/investigations/{investigation_id}/lineage/relationships", response_model=LineageEdge, status_code=status.HTTP_201_CREATED)
async def create_lineage_relationship(
    investigation_id: str,
    payload: CreateRelationshipRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Allows an investigator to record an explicit relationship (e.g. verified claim variant,
    same claim, or attribution link).
    """
    inv_res = await db.execute(select(Investigation).where(Investigation.id == investigation_id))
    if not inv_res.scalars().first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Investigation '{investigation_id}' not found.")

    rec = LineageRelationshipRecord(
        investigation_id=investigation_id,
        source_entity_id=payload.source_entity_id,
        source_entity_type=payload.source_entity_type.value,
        target_entity_id=payload.target_entity_id,
        target_entity_type=payload.target_entity_type.value,
        relationship_type=payload.relationship_type.value,
        edge_nature=payload.edge_nature.value,
        is_inferred=(payload.edge_nature.value == "INFERRED"),
        evidence_summary=payload.evidence_summary,
        detection_method=payload.detection_method,
        review_status=payload.review_status.value,
        reviewer_notes=payload.reviewer_notes,
        created_at=utc_now()
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)

    return LineageEdge(
        id=rec.id,
        source_id=rec.source_entity_id,
        target_id=rec.target_entity_id,
        relationship_type=rec.relationship_type,
        edge_nature=rec.edge_nature,
        is_inferred=rec.is_inferred,
        evidence_summary=rec.evidence_summary,
        detection_method=rec.detection_method,
        review_status=LineageReviewStatus(rec.review_status),
        reviewer_notes=rec.reviewer_notes
    )


@router.post("/investigations/{investigation_id}/lineage/relationships/{relationship_id}/review", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def review_lineage_relationship(
    investigation_id: str,
    relationship_id: str,
    payload: ReviewRelationshipRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Records an investigator's review determination (CONFIRMED, DISPUTED, MODIFIED)
    with notes on an explicit or recorded relationship.
    """
    rel_res = await db.execute(select(LineageRelationshipRecord).where(
        LineageRelationshipRecord.id == relationship_id,
        LineageRelationshipRecord.investigation_id == investigation_id
    ))
    rec = rel_res.scalars().first()
    if not rec:
        # Check if this edge is an ID from the graph
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"LineageRelationshipRecord with id '{relationship_id}' not found for review."
        )

    rec.review_status = payload.review_status.value
    rec.reviewer_notes = payload.reviewer_notes
    rec.reviewed_by = payload.reviewer_id
    rec.reviewed_at = utc_now()
    if payload.review_status == LineageReviewStatus.CONFIRMED:
        rec.edge_nature = LineageEdgeNature.HUMAN_CONFIRMED.value
        rec.is_inferred = False

    await db.commit()
    await db.refresh(rec)

    return {
        "status": "success",
        "relationship_id": rec.id,
        "review_status": rec.review_status,
        "edge_nature": rec.edge_nature,
        "reviewer_notes": rec.reviewer_notes,
        "reviewed_at": rec.reviewed_at.isoformat() if rec.reviewed_at else None
    }


# ==============================================================================
# INTERACTIVE INVESTIGATOR RELATIONSHIP EXPLORER UI
# ==============================================================================

@router.get("/workbench", response_class=HTMLResponse)
async def workbench_ui(
    investigation_id: Optional[str] = Query(None, description="Optional investigation ID to load"),
    db: AsyncSession = Depends(get_db)
):
    """
    TRUTHNET AI Investigator Intelligence Workbench.
    """
    if investigation_id:
        inv_res = await db.execute(select(Investigation).where(Investigation.id == investigation_id))
        inv = inv_res.scalars().first()
        if not inv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Investigation '{investigation_id}' not found.")
    else:
        inv_res = await db.execute(select(Investigation).order_by(Investigation.updated_at.desc()).limit(1))
        inv = inv_res.scalars().first()
        if not inv:
            inv = Investigation(
                title="Primary Misinformation Investigation",
                description="Default intelligence workspace auto-created for investigation.",
                priority="HIGH"
            )
            db.add(inv)
            await db.commit()
            await db.refresh(inv)

    html_content = HTML_EXPLORER_TEMPLATE.replace("{{INV_ID}}", inv.id).replace("{{INV_TITLE}}", inv.title)
    return HTMLResponse(content=html_content)


@router.get("/investigations/{investigation_id}/lineage/explorer", response_class=HTMLResponse)
async def lineage_explorer_ui(
    investigation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Serves a calm, information-dense, interactive Relationship & Evidence Explorer
    for investigators to visualize nodes, expand claims, click edges for underlying
    evidence, and review assessments.
    """
    inv_res = await db.execute(select(Investigation).where(Investigation.id == investigation_id))
    inv = inv_res.scalars().first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Investigation '{investigation_id}' not found.")

    html_content = HTML_EXPLORER_TEMPLATE.replace("{{INV_ID}}", inv.id).replace("{{INV_TITLE}}", inv.title)
    return HTMLResponse(content=html_content)


from app.ui.workbench import WORKBENCH_HTML as HTML_EXPLORER_TEMPLATE
