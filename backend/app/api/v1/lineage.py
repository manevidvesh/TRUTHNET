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

    await db.commit()
    await db.refresh(rec)

    return {
        "status": "success",
        "relationship_id": rec.id,
        "review_status": rec.review_status,
        "reviewer_notes": rec.reviewer_notes,
        "reviewed_at": rec.reviewed_at.isoformat() if rec.reviewed_at else None
    }


# ==============================================================================
# INTERACTIVE INVESTIGATOR RELATIONSHIP EXPLORER UI
# ==============================================================================

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
    <title>TRUTHNET AI — Claim Lineage & Evidence Explorer</title>
    <style>
        :root {
            --bg: #0f172a;
            --surface: #1e293b;
            --surface-hover: #334155;
            --border: #475569;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --accent-blue: #38bdf8;
            --accent-green: #4ade80;
            --accent-red: #f87171;
            --accent-amber: #fbbf24;
            --accent-purple: #c084fc;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; }
        body { background: var(--bg); color: var(--text); display: flex; height: 100vh; overflow: hidden; }
        
        #sidebar { width: 320px; background: var(--surface); border-right: 1px solid var(--border); display: flex; flex-direction: column; }
        .sidebar-header { padding: 16px; border-bottom: 1px solid var(--border); }
        .sidebar-header h2 { font-size: 16px; color: var(--accent-blue); letter-spacing: 0.5px; }
        .sidebar-header p { font-size: 12px; color: var(--text-muted); margin-top: 4px; }
        
        .controls { padding: 14px; border-bottom: 1px solid var(--border); display: flex; flex-direction: column; gap: 10px; }
        .toggle-row { display: flex; justify-content: space-between; align-items: center; font-size: 13px; color: var(--text-muted); }
        .toggle-switch { cursor: pointer; }
        
        .node-list { flex: 1; overflow-y: auto; padding: 12px; display: flex; flex-direction: column; gap: 8px; }
        .node-item { padding: 10px; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; cursor: pointer; transition: all 0.15s; font-size: 12px; }
        .node-item:hover { border-color: var(--accent-blue); background: var(--surface-hover); }
        .node-type-badge { display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; margin-bottom: 4px; }
        .badge-INVESTIGATION { background: #0369a1; color: #e0f2fe; }
        .badge-CLAIM { background: #15803d; color: #dcfce7; }
        .badge-SOURCE { background: #4338ca; color: #e0e7ff; }
        .badge-MEDIA_ASSET { background: #7c2d12; color: #ffedd5; }
        .badge-ASSESSMENT { background: #b45309; color: #fef3c7; }
        
        #main { flex: 1; display: flex; flex-direction: column; position: relative; }
        .top-bar { height: 50px; background: var(--surface); border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; padding: 0 20px; font-size: 13px; }
        .stats { color: var(--text-muted); display: flex; gap: 16px; }
        .stats b { color: var(--text); }
        
        #canvas-container { flex: 1; position: relative; background: radial-gradient(#1e293b 1px, transparent 1px); background-size: 24px 24px; overflow: hidden; }
        svg { width: 100%; height: 100%; }
        
        /* Drawer */
        #drawer { width: 380px; background: var(--surface); border-left: 1px solid var(--border); display: flex; flex-direction: column; overflow-y: auto; transform: translateX(100%); transition: transform 0.25s ease-out; position: absolute; right: 0; top: 0; bottom: 0; z-index: 10; box-shadow: -4px 0 20px rgba(0,0,0,0.5); }
        #drawer.open { transform: translateX(0); }
        .drawer-header { padding: 16px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
        .drawer-header h3 { font-size: 15px; color: var(--accent-blue); }
        .close-btn { cursor: pointer; color: var(--text-muted); font-size: 18px; }
        .drawer-body { padding: 16px; display: flex; flex-direction: column; gap: 14px; font-size: 13px; }
        .card { background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 12px; display: flex; flex-direction: column; gap: 6px; }
        .card h4 { font-size: 11px; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.5px; }
        .card p { line-height: 1.4; color: var(--text); word-break: break-word; }
        .quote-block { border-left: 3px solid var(--accent-blue); padding-left: 10px; font-style: italic; color: var(--text-muted); }
        
        .legend { position: absolute; bottom: 16px; left: 16px; background: rgba(30,41,59,0.9); border: 1px solid var(--border); border-radius: 6px; padding: 10px 14px; font-size: 11px; display: flex; gap: 14px; pointer-events: none; }
        .legend-item { display: flex; align-items: center; gap: 6px; }
        .dot { width: 8px; height: 8px; border-radius: 50%; }
    </style>
</head>
<body>
    <div id="sidebar">
        <div class="sidebar-header">
            <h2>CLAIM LINEAGE WORKBENCH</h2>
            <p>Investigation: <b>{{INV_TITLE}}</b></p>
        </div>
        <div class="controls">
            <div class="toggle-row">
                <span>Show Inferred Edges (Dashed)</span>
                <input type="checkbox" id="toggle-inferred" checked class="toggle-switch">
            </div>
        </div>
        <div class="node-list" id="node-list">
            <!-- Dynamically populated -->
        </div>
    </div>

    <div id="main">
        <div class="top-bar">
            <div class="stats">
                <span>Investigation ID: <b>{{INV_ID}}</b></span>
                <span>Nodes: <b id="stat-nodes">0</b></span>
                <span>Edges: <b id="stat-edges">0</b></span>
            </div>
            <div style="font-size: 12px; color: var(--text-muted);">
                Click any node or relationship to inspect underlying evidence
            </div>
        </div>

        <div id="canvas-container">
            <svg id="graph-svg"></svg>
            <div class="legend">
                <div class="legend-item"><div class="dot" style="background: #4ade80;"></div> SUPPORTS</div>
                <div class="legend-item"><div class="dot" style="background: #f87171;"></div> CONTRADICTS</div>
                <div class="legend-item"><div class="dot" style="background: #fbbf24;"></div> MISLEADING / CONTEXT</div>
                <div class="legend-item"><div class="dot" style="background: #38bdf8;"></div> IDENTITY / MATCH</div>
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

        async function loadGraph() {
            const includeInferred = document.getElementById("toggle-inferred").checked;
            const res = await fetch(`/api/v1/investigations/${invId}/lineage/graph?include_inferred=${includeInferred}`);
            graphData = await res.json();
            
            document.getElementById("stat-nodes").innerText = graphData.node_count;
            document.getElementById("stat-edges").innerText = graphData.edge_count;

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
                if (e.relationship_type === "SUPPORTS") color = "#4ade80";
                else if (e.relationship_type === "CONTRADICTS") color = "#f87171";
                else if (e.relationship_type === "MISLEADING_CONTEXT" || e.relationship_type === "HISTORICAL_CONTEXT_CONFLICT") color = "#fbbf24";

                const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
                line.setAttribute("x1", p1.x);
                line.setAttribute("y1", p1.y);
                line.setAttribute("x2", p2.x);
                line.setAttribute("y2", p2.y);
                line.setAttribute("stroke", color);
                line.setAttribute("stroke-width", "2");
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
                if (n.entity_type === "CLAIM") fill = "#4ade80";
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
                circle.setAttribute("stroke", "#0f172a");
                circle.setAttribute("stroke-width", "2");
                g.appendChild(circle);

                const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
                text.setAttribute("x", p.x);
                text.setAttribute("y", p.y + 28);
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
                    <h4>Metadata & Observed Attributes</h4>
                    <pre style="font-size: 11px; color: var(--text-muted); overflow-x: auto;">${JSON.stringify(node.metadata, null, 2)}</pre>
                </div>
                <div class="card">
                    <h4>Provenance</h4>
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
            
            let evidenceHtml = `<p style="color: var(--text-muted);">Loading underlying evidence record...</p>`;
            content.innerHTML = `
                <div class="card">
                    <h4>Relationship Stance</h4>
                    <p><strong>${edge.relationship_type}</strong> (${edge.edge_nature})</p>
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
                    ${evidenceHtml}
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

        function closeDrawer() {
            document.getElementById("drawer").classList.remove("open");
        }

        document.getElementById("toggle-inferred").addEventListener("change", loadGraph);
        window.addEventListener("load", loadGraph);
    </script>
</body>
</html>
"""

