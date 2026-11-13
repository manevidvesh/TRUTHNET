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
            return HTMLResponse("<html><body style='background:#0f172a;color:#f8fafc;font-family:sans-serif;padding:40px;'><h2>TRUTHNET AI Workbench</h2><p>No investigations found in database. Please initialize or create an investigation first.</p></body></html>")

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


HTML_EXPLORER_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TRUTHNET AI — Intelligence Workbench & Claim Lineage</title>
    <style>
        :root {
            --bg: #0b1120;
            --surface: #1e293b;
            --surface-hover: #334155;
            --border: #334155;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --accent-blue: #38bdf8;
            --accent-cyan: #06b6d4;
            --accent-green: #22c55e;
            --accent-red: #ef4444;
            --accent-amber: #f59e0b;
            --accent-purple: #c084fc;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; }
        body { background: var(--bg); color: var(--text); display: flex; flex-direction: column; height: 100vh; overflow: hidden; }

        /* Top Header & Navigation */
        #top-header { height: 54px; background: #0f172a; border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; padding: 0 20px; z-index: 20; }
        .brand { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 15px; letter-spacing: 0.5px; color: var(--accent-blue); }
        .brand-badge { background: #0284c7; color: #e0f2fe; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
        .case-label { font-size: 13px; color: var(--text-muted); max-width: 400px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

        .tab-nav { display: flex; gap: 4px; }
        .tab-btn { background: transparent; border: 1px solid transparent; color: var(--text-muted); padding: 6px 14px; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.15s; }
        .tab-btn:hover { background: var(--surface); color: var(--text); }
        .tab-btn.active { background: var(--surface); color: var(--accent-blue); border-color: var(--border); font-weight: 600; }

        /* Simulation Warning Banner */
        #sim-banner { display: none; background: #78350f; border-bottom: 2px solid var(--accent-amber); color: #fef3c7; padding: 8px 16px; font-size: 12px; font-weight: 700; text-align: center; letter-spacing: 0.5px; }

        /* Layout Container */
        #content-area { flex: 1; display: flex; overflow: hidden; position: relative; }

        /* Sidebar for Graph */
        #sidebar { width: 320px; background: var(--surface); border-right: 1px solid var(--border); display: flex; flex-direction: column; }
        .sidebar-header { padding: 14px; border-bottom: 1px solid var(--border); }
        .sidebar-header h3 { font-size: 14px; color: var(--text); }
        .sidebar-header p { font-size: 11px; color: var(--text-muted); margin-top: 2px; }

        .controls { padding: 12px 14px; border-bottom: 1px solid var(--border); display: flex; flex-direction: column; gap: 10px; font-size: 12px; }
        .toggle-row { display: flex; justify-content: space-between; align-items: center; color: var(--text-muted); }

        .node-list { flex: 1; overflow-y: auto; padding: 10px; display: flex; flex-direction: column; gap: 6px; }
        .node-item { padding: 8px 10px; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; cursor: pointer; transition: all 0.15s; font-size: 12px; }
        .node-item:hover { border-color: var(--accent-blue); background: var(--surface-hover); }
        .node-type-badge { display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 600; margin-bottom: 4px; }
        .badge-INVESTIGATION { background: #0369a1; color: #e0f2fe; }
        .badge-CLAIM { background: #15803d; color: #dcfce7; }
        .badge-SOURCE { background: #4338ca; color: #e0e7ff; }
        .badge-MEDIA_ASSET { background: #7c2d12; color: #ffedd5; }
        .badge-ASSESSMENT { background: #b45309; color: #fef3c7; }

        /* View Panels */
        .view-panel { flex: 1; display: none; overflow: auto; position: relative; }
        .view-panel.active { display: flex; flex-direction: column; }

        /* Canvas */
        #canvas-container { flex: 1; position: relative; background: radial-gradient(#1e293b 1px, transparent 1px); background-size: 24px 24px; overflow: hidden; }
        svg { width: 100%; height: 100%; }

        .legend { position: absolute; bottom: 16px; left: 16px; background: rgba(15,23,42,0.92); border: 1px solid var(--border); border-radius: 6px; padding: 10px 14px; font-size: 11px; display: flex; gap: 12px; pointer-events: none; z-index: 5; }
        .legend-item { display: flex; align-items: center; gap: 6px; }
        .line-indicator { width: 14px; height: 3px; border-radius: 1px; }

        /* Drawer */
        #drawer { width: 420px; background: var(--surface); border-left: 1px solid var(--border); display: flex; flex-direction: column; overflow-y: auto; transform: translateX(100%); transition: transform 0.25s ease-out; position: absolute; right: 0; top: 0; bottom: 0; z-index: 15; box-shadow: -4px 0 25px rgba(0,0,0,0.6); }
        #drawer.open { transform: translateX(0); }
        .drawer-header { padding: 14px 16px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
        .drawer-header h3 { font-size: 15px; color: var(--accent-blue); }
        .close-btn { cursor: pointer; color: var(--text-muted); font-size: 20px; }
        .drawer-body { padding: 16px; display: flex; flex-direction: column; gap: 14px; font-size: 13px; }
        .card { background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 12px; display: flex; flex-direction: column; gap: 6px; }
        .card h4 { font-size: 11px; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.5px; }
        .card p { line-height: 1.4; color: var(--text); word-break: break-word; }
        .quote-block { border-left: 3px solid var(--accent-blue); padding-left: 10px; font-style: italic; color: var(--text-muted); }

        /* Review Form in Drawer */
        .review-box { background: #172554; border: 1px solid #1e40af; border-radius: 6px; padding: 12px; display: flex; flex-direction: column; gap: 10px; }
        .review-box label { font-size: 11px; font-weight: 600; color: #bfdbfe; text-transform: uppercase; }
        .review-box select, .review-box input, .review-box textarea { background: #0f172a; border: 1px solid #1e3a8a; color: #fff; padding: 8px; border-radius: 4px; font-size: 12px; }
        .btn-submit-review { background: #2563eb; color: #fff; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; font-weight: 600; font-size: 12px; }
        .btn-submit-review:hover { background: #1d4ed8; }

        /* Timeline & Other Views */
        .container-padding { padding: 24px; max-width: 1000px; margin: 0 auto; width: 100%; display: flex; flex-direction: column; gap: 16px; }
        .timeline-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px; display: flex; gap: 16px; align-items: flex-start; }
        .timeline-badge { min-width: 130px; font-size: 11px; font-weight: 600; padding: 4px 8px; border-radius: 4px; text-align: center; }
        .badge-claimed { background: #7c2d12; color: #ffedd5; }
        .badge-capture { background: #431407; color: #fed7aa; }
        .badge-source { background: #1e1b4b; color: #c7d2fe; }
        .badge-assessment { background: #064e3b; color: #a7f3d0; }
        .badge-submit { background: #1e293b; color: #94a3b8; border: 1px solid var(--border); }

        /* Media Rediscovery Grid */
        .media-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .media-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 16px; display: flex; flex-direction: column; gap: 10px; }
        .metric-badge { background: #0f172a; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-family: monospace; }
    </style>
</head>
<body>
    <div id="sim-banner">⚠️ SIMULATED DATASET — NOT LIVE EXTERNAL EVIDENCE (For Demonstration & Verification Purposes Only)</div>

    <div id="top-header">
        <div class="brand">
            <span>TRUTHNET AI</span>
            <span class="brand-badge">WORKBENCH</span>
            <span class="case-label">Case: <b>{{INV_TITLE}}</b></span>
        </div>
        <div class="tab-nav">
            <button class="tab-btn active" id="btn-tab-graph" onclick="switchTab('graph')">🌐 Lineage Graph</button>
            <button class="tab-btn" id="btn-tab-timeline" onclick="switchTab('timeline')">⏱️ Timeline</button>
            <button class="tab-btn" id="btn-tab-media" onclick="switchTab('media')">🔍 Historical Media</button>
            <button class="tab-btn" id="btn-tab-decision" onclick="switchTab('decision')">🧠 Decision Engine</button>
            <button class="tab-btn" id="btn-tab-report" onclick="switchTab('report')">📄 Case Report</button>
        </div>
    </div>

    <div id="content-area">
        <!-- 1. GRAPH VIEW -->
        <div id="view-graph" class="view-panel active" style="flex-direction: row;">
            <div id="sidebar">
                <div class="sidebar-header">
                    <h3>CLAIM LINEAGE</h3>
                    <p>Evidence-backed Entity Relationships</p>
                </div>
                <div class="controls">
                    <div class="toggle-row">
                        <span>Show Inferred Edges (Dashed)</span>
                        <input type="checkbox" id="toggle-inferred" checked style="cursor: pointer;">
                    </div>
                    <div class="toggle-row" style="font-size: 11px; padding-top: 4px; border-top: 1px solid var(--border);">
                        <span>Nodes: <b id="stat-nodes" style="color: var(--accent-blue);">0</b></span>
                        <span>Edges: <b id="stat-edges" style="color: var(--accent-blue);">0</b></span>
                    </div>
                </div>
                <div class="node-list" id="node-list">
                    <!-- Populated dynamically -->
                </div>
            </div>

            <div id="canvas-container">
                <svg id="graph-svg"></svg>
                <div class="legend">
                    <div class="legend-item"><div class="line-indicator" style="background: #38bdf8;"></div> OBSERVED</div>
                    <div class="legend-item"><div class="line-indicator" style="background: #06b6d4;"></div> SYSTEM_DERIVED</div>
                    <div class="legend-item"><div class="line-indicator" style="background: #fbbf24; border-bottom: 2px dashed #fbbf24; height: 1px;"></div> INFERRED</div>
                    <div class="legend-item"><div class="line-indicator" style="background: #22c55e;"></div> HUMAN_CONFIRMED</div>
                </div>
            </div>
        </div>

        <!-- 2. TIMELINE VIEW -->
        <div id="view-timeline" class="view-panel">
            <div class="container-padding">
                <h2 style="font-size: 18px; color: var(--accent-blue);">Chronological Investigation Timeline</h2>
                <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;">Traceable sequence of observed camera captures, claimed dates, submissions, publications, and assessments.</p>
                <div id="timeline-list" style="display: flex; flex-direction: column; gap: 12px;">
                    <!-- Populated dynamically -->
                </div>
            </div>
        </div>

        <!-- 3. HISTORICAL MEDIA VIEW -->
        <div id="view-media" class="view-panel">
            <div class="container-padding">
                <h2 style="font-size: 18px; color: var(--accent-blue);">Historical Media Rediscovery & Contextual Analysis</h2>
                <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;">Side-by-side comparison between submitted suspect media and archival candidate matches with raw visual measurements.</p>
                <div id="media-matches-container" style="display: flex; flex-direction: column; gap: 16px;">
                    <!-- Populated dynamically -->
                </div>
            </div>
        </div>

        <!-- 4. DECISION ENGINE VIEW -->
        <div id="view-decision" class="view-panel">
            <div class="container-padding">
                <h2 style="font-size: 18px; color: var(--accent-blue);">Explainable Assessment & Decision Engine</h2>
                <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;">Deterministic verification path, stance breakdown, and multi-signal source independence analysis.</p>
                <div id="decision-container" style="display: flex; flex-direction: column; gap: 16px;">
                    <!-- Populated dynamically -->
                </div>
            </div>
        </div>

        <!-- 5. REPORT VIEW -->
        <div id="view-report" class="view-panel">
            <div class="container-padding">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h2 style="font-size: 18px; color: var(--accent-blue);">Investigation Dossier Report</h2>
                    <a id="btn-open-dossier" href="/api/v1/investigations/{{INV_ID}}/report/html" target="_blank" style="background: var(--accent-blue); color: #000; text-decoration: none; padding: 6px 14px; border-radius: 4px; font-weight: 600; font-size: 12px;">Open Printable Dossier</a>
                </div>
                <div id="report-embed" style="background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 20px;">
                    <!-- Report summary loaded dynamically -->
                </div>
            </div>
        </div>

        <!-- Evidence Inspector Drawer -->
        <div id="drawer">
            <div class="drawer-header">
                <h3 id="drawer-title">Evidence Inspector</h3>
                <span class="close-btn" onclick="closeDrawer()">&times;</span>
            </div>
            <div class="drawer-body" id="drawer-content">
                <p style="color: var(--text-muted);">Select a graph node or edge to inspect verified evidence and reasoning.</p>
            </div>
        </div>
    </div>

    <script>
        const invId = "{{INV_ID}}";
        let graphData = null;
        let reportData = null;

        function switchTab(tab) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));

            document.getElementById('btn-tab-' + tab).classList.add('active');
            document.getElementById('view-' + tab).classList.add('active');

            if (tab === 'timeline') loadTimeline();
            if (tab === 'media') loadMediaFindings();
            if (tab === 'decision') loadDecisionEngine();
            if (tab === 'report') loadReportView();
        }

        async function initWorkbench() {
            try {
                // Check report data to detect simulation status
                const repRes = await fetch(`/api/v1/investigations/${invId}/report`);
                if (repRes.ok) {
                    reportData = await repRes.json();
                    if (reportData.is_simulated_scenario) {
                        document.getElementById("sim-banner").style.display = "block";
                    }
                }
            } catch (e) {
                console.warn("Could not load report status:", e);
            }
            await loadGraph();
        }

        async function loadGraph() {
            const includeInferred = document.getElementById("toggle-inferred").checked;
            const res = await fetch(`/api/v1/investigations/${invId}/lineage/graph?include_inferred=${includeInferred}`);
            graphData = await res.json();

            const statNodes = document.getElementById("stat-nodes");
            const statEdges = document.getElementById("stat-edges");
            if (statNodes) statNodes.innerText = graphData.node_count;
            if (statEdges) statEdges.innerText = graphData.edge_count;

            renderSidebarList(graphData.nodes);
            renderSvgGraph(graphData.nodes, graphData.edges);
        }

        function renderSidebarList(nodes) {
            const container = document.getElementById("node-list");
            container.innerHTML = "";
            nodes.forEach(n => {
                const div = document.createElement("div");
                div.className = "node-item";
                div.innerHTML = `
                    <span class="node-type-badge badge-${n.entity_type}">${n.entity_type}</span>
                    <p><strong>${n.label}</strong></p>
                `;
                div.onclick = () => inspectNode(n);
                container.appendChild(div);
            });
        }

        function renderSvgGraph(nodes, edges) {
            const svg = document.getElementById("graph-svg");
            svg.innerHTML = "";

            const width = svg.clientWidth || 900;
            const height = svg.clientHeight || 600;

            const positions = {};
            const n = nodes.length;
            nodes.forEach((node, i) => {
                const angle = (i / Math.max(n, 1)) * 2 * Math.PI;
                const r = Math.min(width, height) * 0.35;
                positions[node.id] = {
                    x: width / 2 + r * Math.cos(angle),
                    y: height / 2 + r * Math.sin(angle)
                };
            });

            // Draw Edges
            edges.forEach(e => {
                const p1 = positions[e.source_id];
                const p2 = positions[e.target_id];
                if (!p1 || !p2) return;

                let color = "#38bdf8";
                if (e.edge_nature === "HUMAN_CONFIRMED") color = "#22c55e";
                else if (e.edge_nature === "SYSTEM_DERIVED") color = "#06b6d4";
                else if (e.edge_nature === "INFERRED") color = "#fbbf24";

                const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
                line.setAttribute("x1", p1.x);
                line.setAttribute("y1", p1.y);
                line.setAttribute("x2", p2.x);
                line.setAttribute("y2", p2.y);
                line.setAttribute("stroke", color);
                line.setAttribute("stroke-width", e.edge_nature === "HUMAN_CONFIRMED" ? "3" : "2");
                if (e.is_inferred) {
                    line.setAttribute("stroke-dasharray", "5,5");
                }
                line.style.cursor = "pointer";
                line.onclick = () => inspectEdge(e);
                svg.appendChild(line);
            });

            // Draw Nodes
            nodes.forEach(n => {
                const p = positions[n.id];
                if (!p) return;

                let fill = "#38bdf8";
                if (n.entity_type === "CLAIM") fill = "#22c55e";
                else if (n.entity_type === "SOURCE") fill = "#818cf8";
                else if (n.entity_type === "ASSESSMENT") fill = "#fbbf24";
                else if (n.entity_type === "MEDIA_ASSET") fill = "#fb923c";

                const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
                g.style.cursor = "pointer";
                g.onclick = () => inspectNode(n);

                const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                circle.setAttribute("cx", p.x);
                circle.setAttribute("cy", p.y);
                circle.setAttribute("r", "16");
                circle.setAttribute("fill", fill);
                circle.setAttribute("stroke", "#0b1120");
                circle.setAttribute("stroke-width", "2");
                g.appendChild(circle);

                const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
                text.setAttribute("x", p.x);
                text.setAttribute("y", p.y + 26);
                text.setAttribute("text-anchor", "middle");
                text.setAttribute("fill", "#f8fafc");
                text.setAttribute("font-size", "11px");
                text.textContent = n.label.length > 20 ? n.label.substring(0, 18) + '...' : n.label;
                g.appendChild(text);

                svg.appendChild(g);
            });
        }

        function inspectNode(node) {
            const drawer = document.getElementById("drawer");
            const title = document.getElementById("drawer-title");
            const content = document.getElementById("drawer-content");

            title.innerText = `${node.entity_type} Details`;
            content.innerHTML = `
                <div class="card">
                    <h4>Label</h4>
                    <p><strong>${node.label}</strong></p>
                </div>
                <div class="card">
                    <h4>Entity Identifier</h4>
                    <p style="font-family: monospace; font-size: 11px;">${node.entity_id}</p>
                </div>
                <div class="card">
                    <h4>Observed Metadata & Attributes</h4>
                    <pre style="font-size: 11px; color: var(--text-muted); overflow-x: auto;">${JSON.stringify(node.metadata, null, 2)}</pre>
                </div>
                <div class="card">
                    <h4>Provenance Details</h4>
                    <pre style="font-size: 11px; color: var(--text-muted); overflow-x: auto;">${JSON.stringify(node.provenance, null, 2)}</pre>
                </div>
            `;
            drawer.classList.add("open");
        }

        async function inspectEdge(edge) {
            const drawer = document.getElementById("drawer");
            const title = document.getElementById("drawer-title");
            const content = document.getElementById("drawer-content");

            title.innerText = `Relationship: ${edge.relationship_type}`;
            
            content.innerHTML = `
                <div class="card">
                    <h4>Relationship Stance & Nature</h4>
                    <p><strong>${edge.relationship_type}</strong></p>
                    <p style="font-size: 12px; color: var(--accent-cyan);">Edge Nature: <b>${edge.edge_nature}</b> (Inferred: ${edge.is_inferred})</p>
                </div>
                <div class="card">
                    <h4>Detection Method</h4>
                    <p>${edge.detection_method}</p>
                </div>
                <div class="card">
                    <h4>Evidence Summary</h4>
                    <p class="quote-block">${edge.evidence_summary}</p>
                </div>
                <div class="card" id="deep-evidence-card">
                    <h4>Underlying Evidence Record</h4>
                    <p style="color: var(--text-muted);">Loading underlying evidence record...</p>
                </div>
                
                <!-- Human Review Form -->
                <div class="review-box">
                    <label>Investigator Determination</label>
                    <select id="review-status-select">
                        <option value="CONFIRMED" ${edge.review_status === 'CONFIRMED' ? 'selected' : ''}>CONFIRMED (Investigator Validated)</option>
                        <option value="DISPUTED" ${edge.review_status === 'DISPUTED' ? 'selected' : ''}>DISPUTED (Investigator Rejected)</option>
                        <option value="MODIFIED" ${edge.review_status === 'MODIFIED' ? 'selected' : ''}>MODIFIED</option>
                    </select>
                    <label>Reviewer Notes</label>
                    <textarea id="review-notes-input" rows="2" placeholder="Document investigative basis...">${edge.reviewer_notes || ''}</textarea>
                    <button class="btn-submit-review" onclick="submitReview('${edge.id}')">Record Determination</button>
                </div>
            `;
            drawer.classList.add("open");

            try {
                const evRes = await fetch(`/api/v1/investigations/${invId}/lineage/edges/${edge.id}/evidence`);
                const evData = await evRes.json();
                let recordHtml = "";
                if (evData.source_details) {
                    recordHtml = `
                        <p><strong>Publisher:</strong> ${evData.source_details.publisher}</p>
                        <p><strong>URL:</strong> <a href="${evData.source_details.canonical_url}" target="_blank" style="color: var(--accent-blue);">${evData.source_details.canonical_url}</a></p>
                        <p><strong>Excerpt:</strong> "${evData.source_details.text_excerpt}"</p>
                        <p><strong>SHA-256 Hash:</strong> <code>${evData.source_details.content_hash}</code></p>
                    `;
                } else if (evData.match_details) {
                    recordHtml = `
                        <p><strong>Match Classification:</strong> ${evData.match_details.classification}</p>
                        <p><strong>Method:</strong> ${evData.match_details.method}</p>
                        <p><strong>Rationale:</strong> ${evData.match_details.rationale}</p>
                        <pre style="font-size: 11px;">${JSON.stringify(evData.match_details.raw_metrics, null, 2)}</pre>
                    `;
                } else {
                    recordHtml = `<pre style="font-size: 11px;">${JSON.stringify(evData, null, 2)}</pre>`;
                }
                document.getElementById("deep-evidence-card").innerHTML = `
                    <h4>Underlying Evidence Record</h4>
                    ${recordHtml}
                `;
            } catch (err) {
                document.getElementById("deep-evidence-card").innerHTML = `<p style="color: var(--accent-red);">Failed to load evidence record: ${err.message}</p>`;
            }
        }

        async function submitReview(edgeId) {
            const status = document.getElementById("review-status-select").value;
            const notes = document.getElementById("review-notes-input").value;

            // Strip rel_ prefix if present
            const cleanId = edgeId.replace("rel_", "");
            try {
                const res = await fetch(`/api/v1/investigations/${invId}/lineage/relationships/${cleanId}/review`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        review_status: status,
                        reviewer_notes: notes,
                        reviewer_id: "investigator_lead"
                    })
                });
                if (res.ok) {
                    alert("Determination successfully recorded.");
                    closeDrawer();
                    await loadGraph();
                } else {
                    const err = await res.json();
                    alert("Failed to submit review: " + (err.detail || "Unknown error"));
                }
            } catch (e) {
                alert("Network error: " + e.message);
            }
        }

        async function loadTimeline() {
            const container = document.getElementById("timeline-list");
            container.innerHTML = "<p style='color: var(--text-muted);'>Loading chronological timeline...</p>";
            try {
                const res = await fetch(`/api/v1/investigations/${invId}/lineage/timeline`);
                const data = await res.json();
                container.innerHTML = "";

                if (!data.events || data.events.length === 0) {
                    container.innerHTML = "<p style='color: var(--text-muted);'>No timeline events recorded.</p>";
                    return;
                }

                data.events.forEach(ev => {
                    const div = document.createElement("div");
                    div.className = "timeline-card";
                    let badgeClass = "badge-submit";
                    if (ev.timestamp_type === "CLAIMED_EVENT_DATE") badgeClass = "badge-claimed";
                    else if (ev.timestamp_type === "EXIF_MEDIA_CAPTURE_DATE") badgeClass = "badge-capture";
                    else if (ev.timestamp_type === "SOURCE_PUBLICATION_DATE") badgeClass = "badge-source";
                    else if (ev.timestamp_type === "ASSESSMENT_DATE") badgeClass = "badge-assessment";

                    div.innerHTML = `
                        <div class="timeline-badge ${badgeClass}">${ev.timestamp_type.replace('_', ' ')}</div>
                        <div style="flex: 1;">
                            <div style="display: flex; justify-content: space-between; font-size: 13px;">
                                <strong>${ev.label}</strong>
                                <span style="font-family: monospace; color: var(--accent-blue);">${ev.timestamp || 'N/A'}</span>
                            </div>
                            <pre style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">${JSON.stringify(ev.details, null, 2)}</pre>
                        </div>
                    `;
                    container.appendChild(div);
                });
            } catch (e) {
                container.innerHTML = `<p style="color: var(--accent-red);">Failed to load timeline: ${e.message}</p>`;
            }
        }

        async function loadMediaFindings() {
            const container = document.getElementById("media-matches-container");
            container.innerHTML = "<p style='color: var(--text-muted);'>Loading media rediscovery findings...</p>";
            try {
                if (!reportData) {
                    const res = await fetch(`/api/v1/investigations/${invId}/report`);
                    reportData = await res.json();
                }

                const matches = reportData.historical_media_matches || [];
                if (matches.length === 0) {
                    container.innerHTML = "<p style='color: var(--text-muted);'>No historical media matches identified in index.</p>";
                    return;
                }

                container.innerHTML = "";
                matches.forEach(m => {
                    const div = document.createElement("div");
                    div.className = "media-card";
                    div.innerHTML = `
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong style="color: var(--accent-amber); font-size: 14px;">Classification: ${m.classification}</strong>
                            <span class="metric-badge">Method: ${m.method}</span>
                        </div>
                        <p style="font-size: 13px; color: var(--text);">${m.rationale}</p>
                        <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 6px;">
                            <span class="metric-badge">Homography Inliers: <b>${m.homography_inliers || 'N/A'}</b></span>
                            <span class="metric-badge">Inlier Ratio: <b>${m.inlier_ratio || 'N/A'}</b></span>
                            <span class="metric-badge">pHash Distance: <b>${m.phash_distance || 'N/A'}</b></span>
                            <span class="metric-badge">RANSAC: <b>${m.ransac_status || 'N/A'}</b></span>
                        </div>
                        <p style="font-size: 11px; color: #f59e0b; margin-top: 6px; font-style: italic;">⚠️ ${m.disclaimer}</p>
                    `;
                    container.appendChild(div);
                });
            } catch (e) {
                container.innerHTML = `<p style="color: var(--accent-red);">Failed to load media findings: ${e.message}</p>`;
            }
        }

        async function loadDecisionEngine() {
            const container = document.getElementById("decision-container");
            container.innerHTML = "<p style='color: var(--text-muted);'>Loading explainable decision engine...</p>";
            try {
                if (!reportData) {
                    const res = await fetch(`/api/v1/investigations/${invId}/report`);
                    reportData = await res.json();
                }

                const claims = reportData.claims || [];
                if (claims.length === 0) {
                    container.innerHTML = "<p style='color: var(--text-muted);'>No extracted claims recorded for this case.</p>";
                    return;
                }

                container.innerHTML = "";
                for (const c of claims) {
                    let expl = null;
                    try {
                        const explRes = await fetch(`/api/v1/claims/${c.id}/explanation`);
                        if (explRes.ok) expl = await explRes.json();
                    } catch (e) {}

                    const div = document.createElement("div");
                    div.className = "card";
                    div.innerHTML = `
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong style="font-size: 14px; color: var(--accent-blue);">${c.claim_text}</strong>
                            <span style="font-weight: 700; color: #4ade80;">[${c.assessment_classification}]</span>
                        </div>
                        <p style="font-size: 12px; color: var(--text-muted);">Subject: <i>${c.subject || 'N/A'}</i> | Action: <i>${c.predicate || 'N/A'}</i> | Polarity: <code>${c.polarity_state}</code></p>
                        
                        ${expl ? `
                            <div style="margin-top: 10px; background: #0f172a; padding: 10px; border-radius: 4px;">
                                <h4 style="font-size: 11px; color: var(--accent-cyan); margin-bottom: 6px;">DETERMINISTIC DECISION-TREE TRACE</h4>
                                <pre style="font-size: 11px; color: var(--text); white-space: pre-wrap;">${expl.decision_tree_explanation}</pre>
                            </div>
                            <div style="margin-top: 10px;">
                                <h4 style="font-size: 11px; color: var(--accent-cyan); margin-bottom: 4px;">SOURCE INDEPENDENCE EVALUATION</h4>
                                <p style="font-size: 12px;">Assessment: <b>${expl.source_dependencies.independence_assessment}</b> (${expl.source_dependencies.independent_sources_count} independent / ${expl.source_dependencies.total_sources_evaluated} total)</p>
                                <p style="font-size: 11px; color: var(--text-muted);">${expl.source_dependencies.explanation}</p>
                            </div>
                        ` : ''}
                    `;
                    container.appendChild(div);
                }
            } catch (e) {
                container.innerHTML = `<p style="color: var(--accent-red);">Failed to load decision engine: ${e.message}</p>`;
            }
        }

        async function loadReportView() {
            const container = document.getElementById("report-embed");
            try {
                if (!reportData) {
                    const res = await fetch(`/api/v1/investigations/${invId}/report`);
                    reportData = await res.json();
                }
                container.innerHTML = `
                    <h3 style="font-size: 16px; margin-bottom: 10px; color: var(--accent-blue);">Executive Case Summary</h3>
                    <p style="font-size: 14px; line-height: 1.5; background: #0f172a; padding: 14px; border-radius: 6px; border-left: 4px solid var(--accent-blue);">${reportData.executive_summary}</p>
                    
                    <h4 style="font-size: 13px; margin: 16px 0 8px; color: var(--text-muted); text-transform: uppercase;">Investigation Metrics</h4>
                    <div style="display: flex; gap: 14px; flex-wrap: wrap;">
                        <span class="metric-badge">Submissions: <b>${reportData.metrics.submissions_count}</b></span>
                        <span class="metric-badge">Claims: <b>${reportData.metrics.claims_count}</b></span>
                        <span class="metric-badge">Retrieved Sources: <b>${reportData.metrics.sources_count}</b></span>
                        <span class="metric-badge">Media Matches: <b>${reportData.metrics.matches_count}</b></span>
                        <span class="metric-badge">Assessments: <b>${reportData.metrics.assessments_count}</b></span>
                    </div>

                    <h4 style="font-size: 13px; margin: 16px 0 8px; color: var(--text-muted); text-transform: uppercase;">Epistemic Limitations</h4>
                    <ul style="font-size: 12px; color: var(--text-muted); padding-left: 20px; line-height: 1.6;">
                        ${reportData.epistemic_limitations.map(l => `<li>${l}</li>`).join('')}
                    </ul>
                `;
            } catch (e) {
                container.innerHTML = `<p style="color: var(--accent-red);">Failed to load report: ${e.message}</p>`;
            }
        }

        function closeDrawer() {
            document.getElementById("drawer").classList.remove("open");
        }

        document.getElementById("toggle-inferred").addEventListener("change", loadGraph);
        window.addEventListener("load", initWorkbench);
    </script>
</body>
</html>
"""


