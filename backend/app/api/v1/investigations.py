import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.investigation import Investigation, utc_now
from app.models.evidence import EvidenceSubmission, MediaAsset
from app.models.claim import ClaimRecord
from app.models.source import RetrievedSourceRecord, SourceIndependenceRecord
from app.models.fingerprint import MediaMatchRecord
from app.models.context_verification import ClaimAssessmentRecord
from app.models.relationship import LineageRelationshipRecord
from app.models.authenticity import MediaAuthenticityRecord
from app.schemas.investigation import (
    InvestigationCreate,
    InvestigationUpdate,
    InvestigationResponse,
    InvestigationReportResponse
)

router = APIRouter(prefix="/investigations", tags=["Investigations"])

@router.get("/", response_model=List[InvestigationResponse])
async def list_investigations(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    query = select(
        Investigation,
        func.count(EvidenceSubmission.id).label("evidence_count")
    ).outerjoin(
        EvidenceSubmission, Investigation.id == EvidenceSubmission.investigation_id
    ).group_by(Investigation.id).order_by(desc(Investigation.updated_at))

    if status_filter:
        query = query.where(Investigation.status == status_filter.upper())
    if priority_filter:
        query = query.where(Investigation.priority == priority_filter.upper())

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    rows = result.all()

    items = []
    for inv, count in rows:
        resp = InvestigationResponse(
            id=inv.id,
            title=inv.title,
            description=inv.description,
            status=inv.status,
            priority=inv.priority,
            created_at=inv.created_at,
            updated_at=inv.updated_at,
            evidence_count=count
        )
        items.append(resp)
    return items

@router.post("/", response_model=InvestigationResponse, status_code=status.HTTP_201_CREATED)
async def create_investigation(
    payload: InvestigationCreate,
    db: AsyncSession = Depends(get_db)
):
    inv = Investigation(
        title=payload.title,
        description=payload.description,
        priority=payload.priority.upper(),
        status="ACTIVE"
    )
    db.add(inv)
    await db.commit()
    await db.refresh(inv)

    return InvestigationResponse(
        id=inv.id,
        title=inv.title,
        description=inv.description,
        status=inv.status,
        priority=inv.priority,
        created_at=inv.created_at,
        updated_at=inv.updated_at,
        evidence_count=0
    )

@router.get("/{investigation_id}", response_model=InvestigationResponse)
async def get_investigation(
    investigation_id: str,
    db: AsyncSession = Depends(get_db)
):
    query = select(
        Investigation,
        func.count(EvidenceSubmission.id).label("evidence_count")
    ).outerjoin(
        EvidenceSubmission, Investigation.id == EvidenceSubmission.investigation_id
    ).where(Investigation.id == investigation_id).group_by(Investigation.id)

    result = await db.execute(query)
    row = result.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation not found")

    inv, count = row
    return InvestigationResponse(
        id=inv.id,
        title=inv.title,
        description=inv.description,
        status=inv.status,
        priority=inv.priority,
        created_at=inv.created_at,
        updated_at=inv.updated_at,
        evidence_count=count
    )

@router.patch("/{investigation_id}", response_model=InvestigationResponse)
async def update_investigation(
    investigation_id: str,
    payload: InvestigationUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Investigation).where(Investigation.id == investigation_id))
    inv = result.scalars().first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation not found")

    if payload.title is not None:
        inv.title = payload.title
    if payload.description is not None:
        inv.description = payload.description
    if payload.status is not None:
        inv.status = payload.status.upper()
    if payload.priority is not None:
        inv.priority = payload.priority.upper()
    inv.updated_at = utc_now()

    await db.commit()
    await db.refresh(inv)

    # Count evidence
    count_res = await db.execute(
        select(func.count(EvidenceSubmission.id)).where(EvidenceSubmission.investigation_id == investigation_id)
    )
    count = count_res.scalar() or 0

    return InvestigationResponse(
        id=inv.id,
        title=inv.title,
        description=inv.description,
        status=inv.status,
        priority=inv.priority,
        created_at=inv.created_at,
        updated_at=inv.updated_at,
        evidence_count=count
    )

@router.delete("/{investigation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_investigation(
    investigation_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Investigation).where(Investigation.id == investigation_id))
    inv = result.scalars().first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation not found")

    await db.delete(inv)
    await db.commit()
    return None


async def build_investigation_report_data(investigation_id: str, db: AsyncSession) -> Dict[str, Any]:
    # 1. Investigation
    res = await db.execute(select(Investigation).where(Investigation.id == investigation_id))
    inv = res.scalars().first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Investigation '{investigation_id}' not found.")

    # 2. Submissions
    sub_res = await db.execute(
        select(EvidenceSubmission)
        .where(EvidenceSubmission.investigation_id == investigation_id)
        .order_by(EvidenceSubmission.created_at)
    )
    submissions = sub_res.scalars().all()
    sub_ids = [s.id for s in submissions]
    media_asset_ids = [s.media_asset_id for s in submissions if s.media_asset_id]

    # 3. Media Assets
    media_assets = []
    if media_asset_ids:
        asset_res = await db.execute(select(MediaAsset).where(MediaAsset.id.in_(media_asset_ids)))
        media_assets = asset_res.scalars().all()

    # 4. Claims
    claim_res = await db.execute(
        select(ClaimRecord)
        .where(ClaimRecord.investigation_id == investigation_id)
        .order_by(ClaimRecord.version.desc())
    )
    claims = claim_res.scalars().all()
    claim_ids = [c.id for c in claims]

    # 5. Media Matches
    matches = []
    if media_asset_ids or sub_ids:
        match_stmt = select(MediaMatchRecord).where(
            (MediaMatchRecord.source_media_asset_id.in_(media_asset_ids)) |
            (MediaMatchRecord.matched_media_asset_id.in_(media_asset_ids)) |
            (MediaMatchRecord.source_evidence_id.in_(sub_ids))
        )
        match_res = await db.execute(match_stmt)
        matches = match_res.scalars().all()

    # 6. Retrieved Sources
    sources = []
    if claim_ids:
        src_res = await db.execute(
            select(RetrievedSourceRecord).where(
                (RetrievedSourceRecord.investigation_id == investigation_id) |
                (RetrievedSourceRecord.claim_id.in_(claim_ids))
            )
        )
        sources = src_res.scalars().all()

    # 7. Source Independence
    indep_records = []
    if claim_ids:
        indep_res = await db.execute(
            select(SourceIndependenceRecord).where(SourceIndependenceRecord.claim_id.in_(claim_ids))
        )
        indep_records = indep_res.scalars().all()

    # 8. Assessments
    assessments = []
    if claim_ids:
        ass_res = await db.execute(
            select(ClaimAssessmentRecord).where(
                (ClaimAssessmentRecord.investigation_id == investigation_id) |
                (ClaimAssessmentRecord.claim_id.in_(claim_ids))
            ).where(ClaimAssessmentRecord.is_active == True)
        )
        assessments = ass_res.scalars().all()

    # 9. Relationships
    rel_res = await db.execute(
        select(LineageRelationshipRecord).where(LineageRelationshipRecord.investigation_id == investigation_id)
    )
    relationships = rel_res.scalars().all()

    # 10. Authenticity & Deepfake Records
    auth_records = []
    if sub_ids:
        auth_res = await db.execute(
            select(MediaAuthenticityRecord).where(
                MediaAuthenticityRecord.evidence_submission_id.in_(sub_ids),
                MediaAuthenticityRecord.is_active == True
            )
        )
        auth_records = auth_res.scalars().all()

    # Simulation check
    is_simulated = any(
        "SIMULATED" in str(x).upper()
        for x in [inv.title, inv.description] + [s.text_excerpt for s in sources] + [c.claim_text for c in claims]
    )

    # Disaggregated media matches list
    clean_matches = []
    for m in matches:
        raw_m = m.raw_metrics if isinstance(m.raw_metrics, dict) else {}
        is_exact = (m.classification == "EXACT_FILE_MATCH")
        clean_matches.append({
            "id": m.id,
            "source_media_asset_id": m.source_media_asset_id,
            "matched_media_asset_id": m.matched_media_asset_id,
            "classification": m.classification,
            "method": m.method,
            "rationale": m.classification_rationale,
            "homography_inliers": raw_m.get("homography_inliers") or raw_m.get("inlier_count"),
            "inlier_ratio": raw_m.get("inlier_ratio"),
            "phash_distance": raw_m.get("phash_distance"),
            "dhash_distance": raw_m.get("dhash_distance"),
            "ransac_status": raw_m.get("ransac_status"),
            "is_candidate_match": not is_exact,
            "requires_human_review": not is_exact,
            "disclaimer": getattr(m, "disclaimer", None) or "Candidate visual match requiring investigator review. Measurement indicates feature correspondence, not absolute identity.",
            "raw_metrics": raw_m,
            "matched_at": m.created_at.isoformat() if m.created_at else None
        })

    # Clean submissions
    clean_submissions = [{
        "id": s.id,
        "submission_type": s.submission_type,
        "caption": s.caption,
        "raw_text": s.raw_text,
        "claimed_date": s.claimed_date,
        "claimed_location": s.claimed_location,
        "media_asset_id": s.media_asset_id,
        "created_at": s.created_at.isoformat() if s.created_at else None
    } for s in submissions]

    # Clean media assets
    clean_assets = [{
        "id": a.id,
        "sha256_hash": a.sha256_hash,
        "mime_type": a.mime_type,
        "file_size_bytes": a.file_size_bytes,
        "created_at": a.created_at.isoformat() if a.created_at else None
    } for a in media_assets]

    # Clean claims
    ass_map = {a.claim_id: a for a in assessments}
    clean_claims = [{
        "id": c.id,
        "claim_text": c.claim_text,
        "normalized_claim": c.normalized_claim,
        "subject": c.subject,
        "predicate": c.predicate,
        "object": c.object,
        "polarity_state": c.polarity_state,
        "language": c.language,
        "is_active": c.is_active,
        "assessment_classification": ass_map[c.id].classification if c.id in ass_map else "UNVERIFIED"
    } for c in claims]

    # Clean sources
    clean_sources = [{
        "id": s.id,
        "claim_id": s.claim_id,
        "publisher": s.publisher,
        "canonical_url": s.canonical_url,
        "article_title": s.article_title,
        "published_date": s.published_date,
        "content_hash": s.content_hash,
        "source_type": s.source_type,
        "retrieval_method": s.retrieval_method,
        "text_excerpt": s.text_excerpt[:300] if s.text_excerpt else ""
    } for s in sources]

    # Clean source independence
    clean_indep = [{
        "claim_id": i.claim_id,
        "total_sources_evaluated": i.total_sources_count,
        "independent_sources_count": i.independent_sources_count,
        "independence_assessment": i.independence_assessment,
        "clusters": i.clusters,
        "explanation": i.explanation
    } for i in indep_records]

    # Clean assessments
    clean_assessments = [{
        "id": a.id,
        "claim_id": a.claim_id,
        "classification": a.classification,
        "primary_rationale": a.primary_rationale,
        "evaluation_method": a.evaluation_method,
        "epistemic_limitations": a.epistemic_limitations,
        "human_review_status": a.human_review_status,
        "created_at": a.created_at.isoformat() if a.created_at else None
    } for a in assessments]

    # Clean review log
    clean_reviews = [{
        "relationship_id": r.id,
        "source_entity_id": r.source_entity_id,
        "target_entity_id": r.target_entity_id,
        "relationship_type": r.relationship_type,
        "edge_nature": r.edge_nature,
        "review_status": r.review_status,
        "reviewer_notes": r.reviewer_notes,
        "reviewed_by": r.reviewed_by,
        "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None
    } for r in relationships if r.review_status != "UNREVIEWED"]

    # Clean authenticity records
    clean_authenticity = [{
        "id": a.id,
        "evidence_submission_id": a.evidence_submission_id,
        "media_asset_id": a.media_asset_id,
        "version": a.version,
        "forensic_analysis": a.forensic_analysis,
        "model_registry_summary": a.model_registry_summary,
        "executed_model_results": a.executed_model_results,
        "unavailable_models": a.unavailable_models,
        "video_frame_analyses": a.video_frame_analyses,
        "epistemic_disclaimer": a.epistemic_disclaimer,
        "created_at": a.created_at.isoformat() if a.created_at else None
    } for a in auth_records]

    # Epistemic Limitations & Guidelines
    limitations = [
        "1. Media Authenticity vs Proposition Truth: Visual matching indicates whether media existed previously or was edited, but does not independently prove or disprove accompanying textual propositions.",
        "2. Absence of Evidence: Lack of corroborating external reporting indicates insufficient evidence, never proof that a claim is false.",
        "3. Wire Repeat Attribution: Multiple republications of syndicated wire releases (e.g. PTI, Reuters) represent single source dependency, not multiple corroborations.",
        "4. Deterministic Verification: All verdicts are grounded in explicit registered evidence records without generative model hallucination."
    ]

    # Executive Summary compilation
    verdicts = [a.classification for a in assessments]
    verdict_summary = ", ".join(set(verdicts)) if verdicts else "UNVERIFIED"
    exec_summary = (
        f"Investigation '{inv.title}' contains {len(submissions)} submission(s), "
        f"{len(clean_claims)} extracted claim(s), {len(clean_sources)} retrieved source(s), and "
        f"{len(clean_matches)} historical media match(es). Overall claim verdict status: {verdict_summary}. "
        f"Grounded entirely in traceable evidence artifacts."
    )

    return {
        "investigation": {
            "id": inv.id,
            "title": inv.title,
            "description": inv.description,
            "status": inv.status,
            "priority": inv.priority,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "updated_at": inv.updated_at.isoformat() if inv.updated_at else None
        },
        "is_simulated_scenario": is_simulated,
        "simulation_disclaimer": "⚠️ SIMULATED EVIDENCE RECORD — NOT LIVE EXTERNAL EVIDENCE (For Demonstration & Verification Purposes Only)" if is_simulated else None,
        "executive_summary": exec_summary,
        "metrics": {
            "submissions_count": len(submissions),
            "media_assets_count": len(media_assets),
            "claims_count": len(claims),
            "sources_count": len(sources),
            "matches_count": len(matches),
            "assessments_count": len(assessments),
            "relationships_count": len(relationships)
        },
        "submissions": clean_submissions,
        "media_assets": clean_assets,
        "claims": clean_claims,
        "historical_media_matches": clean_matches,
        "retrieved_sources": clean_sources,
        "source_independence_evaluations": clean_indep,
        "contextual_assessments": clean_assessments,
        "epistemic_limitations": limitations,
        "human_review_log": clean_reviews,
        "authenticity_records": clean_authenticity,
        "generated_at": utc_now().isoformat()
    }


@router.get("/{investigation_id}/report", response_model=InvestigationReportResponse)
async def get_investigation_report(
    investigation_id: str,
    format: Optional[str] = Query(None, description="Output format: 'json' or 'html'"),
    db: AsyncSession = Depends(get_db)
):
    """
    Generates a comprehensive, evidence-grounded investigation report summarizing
    evidence submissions, extracted claims, historical media rediscovery findings,
    retrieved sources, source independence evaluations, and contextual verdicts.
    """
    data = await build_investigation_report_data(investigation_id=investigation_id, db=db)
    if format == "html":
        return HTMLResponse(content=render_html_report(data))
    return data


@router.get("/{investigation_id}/report/html", response_class=HTMLResponse)
async def get_investigation_report_html(
    investigation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Serves a clean, printable HTML investigation report dossier.
    """
    data = await build_investigation_report_data(investigation_id=investigation_id, db=db)
    return HTMLResponse(content=render_html_report(data))


def render_html_report(data: Dict[str, Any]) -> str:
    inv = data["investigation"]
    sim_banner = f"""
    <div style="background: #fffbeb; border: 2px solid #f59e0b; color: #92400e; padding: 12px 16px; border-radius: 8px; margin-bottom: 24px; font-weight: 600;">
        ⚠️ SIMULATED DATASET — NOT LIVE EXTERNAL EVIDENCE (For Demonstration & Verification Purposes Only)
    </div>
    """ if data.get("is_simulated_scenario") else ""

    claims_html = ""
    for c in data.get("claims", []):
        claims_html += f"""
        <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between;">
                <strong>Claim:</strong> <span>{c['claim_text']}</span>
                <span style="font-weight: bold; color: #0284c7;">[{c['assessment_classification']}]</span>
            </div>
            <div style="font-size: 12px; color: #64748b; margin-top: 6px;">
                Subject: <i>{c.get('subject') or 'N/A'}</i> | Predicate: <i>{c.get('predicate') or 'N/A'}</i> | Polarity: <code>{c.get('polarity_state')}</code>
            </div>
        </div>
        """

    media_matches_html = ""
    for m in data.get("historical_media_matches", []):
        media_matches_html += f"""
        <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between;">
                <strong>Match Classification:</strong> <span>{m['classification']}</span>
                <span>Method: <code>{m['method']}</code></span>
            </div>
            <p style="margin: 8px 0; font-size: 13px;">{m['rationale']}</p>
            <div style="background: #e2e8f0; padding: 8px; border-radius: 4px; font-size: 12px;">
                <b>Disaggregated Metrics:</b> Homography Inliers: <code>{m.get('homography_inliers') or 'N/A'}</code> | Inlier Ratio: <code>{m.get('inlier_ratio') or 'N/A'}</code> | pHash Distance: <code>{m.get('phash_distance') or 'N/A'}</code>
            </div>
            <div style="font-size: 11px; color: #d97706; margin-top: 6px;">
                <i>{m.get('disclaimer')}</i>
            </div>
        </div>
        """

    sources_html = ""
    for s in data.get("retrieved_sources", []):
        sources_html += f"""
        <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between;">
                <strong>{s['publisher']}:</strong> <span>{s['article_title']}</span>
            </div>
            <p style="font-size: 12px; color: #475569; margin: 4px 0;">URL: <a href="{s['canonical_url']}" target="_blank">{s['canonical_url']}</a></p>
            <p style="font-size: 12px; font-style: italic; color: #334155;">"{s['text_excerpt']}"</p>
        </div>
        """

    assessments_html = ""
    for a in data.get("contextual_assessments", []):
        assessments_html += f"""
        <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; font-size: 14px;">
                <strong>Verdict:</strong> <span style="font-weight: 700; color: #0f766e;">{a['classification']}</span>
            </div>
            <p style="margin: 6px 0; font-size: 13px;"><b>Primary Rationale:</b> {a['primary_rationale']}</p>
            <p style="font-size: 12px; color: #64748b;"><b>Epistemic Boundaries:</b> {a['epistemic_limitations']}</p>
        </div>
        """

    limitations_html = "".join(f"<li>{item}</li>" for item in data.get("epistemic_limitations", []))

    auth_html = ""
    for auth in data.get("authenticity_records", []):
        forensic = auth.get("forensic_analysis", {})
        ela = forensic.get("ela_analysis", {})
        spectral = forensic.get("spectral_analysis", {})
        noise = forensic.get("noise_analysis", {})
        exec_models = auth.get("executed_model_results", [])
        unavail = auth.get("unavailable_models", [])

        exec_models_str = ", ".join(m.get("model_name", m.get("model_id")) for m in exec_models) or "None executed"
        unavail_models_str = ", ".join(f"{u.get('model_name') or u.get('model_id')} ({u.get('status')})" for u in unavail)

        auth_html += f"""
        <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; font-size: 14px;">
                <strong>Submission:</strong> <code>{auth['evidence_submission_id'][:8]}...</code>
                <span>Version: <b>v{auth['version']}</b></span>
            </div>
            <p style="margin: 6px 0; font-size: 13px;"><b>Forensic Summary:</b> {forensic.get('forensic_summary', 'Analyzed')}</p>
            <div style="background: #e2e8f0; padding: 8px; border-radius: 4px; font-size: 12px; margin: 6px 0;">
                <b>Technical Measurements:</b> ELA Mean Error: <code>{ela.get('mean_error', 'N/A')}</code> | Noise Channel Divergence: <code>{noise.get('channel_divergence', 'N/A')}</code> | 2D Spectral Decay Slope: <code>{spectral.get('decay_slope', 'N/A')}</code>
            </div>
            <div style="font-size: 12px; margin: 4px 0;">
                <b>Executed Models:</b> <span style="color: #059669;">{exec_models_str}</span>
            </div>
            <div style="font-size: 12px; color: #64748b; margin: 4px 0;">
                <b>Unavailable/Excluded Models:</b> {unavail_models_str}
            </div>
            <div style="font-size: 11px; color: #d97706; margin-top: 6px;">
                <i>{auth.get('epistemic_disclaimer')}</i>
            </div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>TRUTHNET AI — Investigation Dossier: {inv['title']}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #ffffff; color: #0f172a; margin: 40px auto; max-width: 900px; line-height: 1.5; }}
        h1 {{ font-size: 24px; border-bottom: 2px solid #0f172a; padding-bottom: 8px; margin-bottom: 16px; }}
        h2 {{ font-size: 18px; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; margin: 24px 0 12px; color: #1e293b; }}
        .meta-box {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; background: #f1f5f9; padding: 12px; border-radius: 6px; margin-bottom: 20px; font-size: 13px; }}
        .btn-print {{ background: #0284c7; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; float: right; font-weight: 600; }}
        @media print {{ .btn-print {{ display: none; }} body {{ margin: 0; }} }}
    </style>
</head>
<body>
    <button class="btn-print" onclick="window.print()">Print Dossier</button>
    <h1>TRUTHNET AI — Intelligence Investigation Dossier</h1>
    {sim_banner}
    <div class="meta-box">
        <div><b>Case Title:</b><br>{inv['title']}</div>
        <div><b>Case Status:</b><br>{inv['status']}</div>
        <div><b>Priority:</b><br>{inv['priority']}</div>
        <div><b>Generated:</b><br>{data['generated_at'][:19].replace('T', ' ')}</div>
    </div>

    <h2>Executive Summary</h2>
    <p style="background: #f8fafc; border-left: 4px solid #0284c7; padding: 12px; font-size: 14px;">{data['executive_summary']}</p>

    <h2>Extracted Claims & Propositions</h2>
    {claims_html or '<p style="color: #94a3b8;">No claims recorded.</p>'}

    <h2>Historical Media Rediscovery Findings</h2>
    {media_matches_html or '<p style="color: #94a3b8;">No historical media matches recorded.</p>'}

    <h2>Media Authenticity & Deepfake Forensic Analysis</h2>
    {auth_html or '<p style="color: #94a3b8;">No media authenticity records found.</p>'}

    <h2>Retrieved External Sources & Fact-Checks</h2>
    {sources_html or '<p style="color: #94a3b8;">No external sources retrieved.</p>'}

    <h2>Contextual Claim Assessments</h2>
    {assessments_html or '<p style="color: #94a3b8;">No contextual assessments recorded.</p>'}

    <h2>Epistemic Principles & Limitations</h2>
    <ul style="font-size: 13px; color: #475569; padding-left: 20px;">
        {limitations_html}
    </ul>
</body>
</html>
"""
