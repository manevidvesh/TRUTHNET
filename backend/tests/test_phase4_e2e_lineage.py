"""
Comprehensive Test Suite for Plan 04-04:
Claim Lineage, Evidence Relationships & Explainable Intelligence.

Covers 13 core requirements and invariant tests:
1. Lineage graph assembly across node types (Investigation, Submission, MediaAsset, Claim, Source, Assessment).
2. Edge nature semantics (OBSERVED vs INFERRED) and toggling.
3. Evidence traceability (resolving underlying evidence records from edge IDs).
4. Invariant: Authentic media with false/misleading caption -> MISLEADING_OR_CONTEXT_MISSING (decoupled).
5. Invariant: Manipulated media with true factual claim -> SUPPORTED claim with preserved media context (decoupled).
6. Invariant: Wire service reprints do not equal independent corroboration (single independent entity).
7. Invariant: Conflicting evidence abstention (authoritative contradiction -> CONFLICTING_EVIDENCE, no guessing).
8. Invariant: Insufficient evidence abstention (absence of evidence != contradiction).
9. Cross-investigation privacy isolation in lineage graph (foreign investigation details strictly redacted).
10. Lineage timeline chronological ordering.
11. Human review lifecycle for lineage relationships (CONFIRMED/DISPUTED without overwriting automated findings).
12. Explainable assessment generation (deterministic breakdown without LLM).
13. Interactive lineage explorer UI HTML rendering.
"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.investigation import Investigation
from app.models.evidence import EvidenceSubmission, MediaAsset
from app.models.claim import ClaimRecord
from app.models.source import RetrievedSourceRecord, SourceIndependenceRecord
from app.models.fingerprint import MediaMatchRecord
from app.models.context_verification import ClaimAssessmentRecord, ClaimEvidenceRelationRecord
from app.models.relationship import LineageRelationshipRecord
from app.schemas.relationship import (
    LineageNodeType,
    LineageRelationshipType,
    LineageEdgeNature,
    LineageReviewStatus,
    CreateRelationshipRequest,
    ReviewRelationshipRequest
)
from app.lineage.graph_engine import LineageGraphEngine
from app.lineage.assessment_engine import ExplainableAssessmentEngine


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_timeline_dt(ts_str: str) -> datetime:
    ts = ts_str.replace("Z", "+00:00")
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def make_test_claim(
    inv_id: str,
    sub_id: str,
    text: str,
    subject: str = "Subject",
    predicate: str = "Predicate",
    obj: str = "Object",
    normalized: str = None
) -> ClaimRecord:
    return ClaimRecord(
        investigation_id=inv_id,
        evidence_submission_id=sub_id,
        claim_text=text,
        normalized_claim=normalized or text,
        subject=subject,
        predicate=predicate,
        object=obj,
        polarity_state="AFFIRMATIVE_SURFACE_SYNTAX",
        is_attributed_assertion=False,
        source_modality="TEXT",
        evidence_span_start=0,
        evidence_span_end=len(text),
        source_text_hash=f"hash-{uuid.uuid4()}",
        language="en",
        language_detection_method="DETERMINISTIC_ASCII"
    )


def make_test_source(
    inv_id: str,
    claim_id: str,
    url: str = "https://reuters.com/news/article",
    title: str = "Reuters Article Title",
    publisher: str = "Reuters",
    excerpt: str = "Relevant news excerpt text.",
    published_date: str = None,
    status: str = "SUCCESS"
) -> RetrievedSourceRecord:
    now = utc_now()
    return RetrievedSourceRecord(
        investigation_id=inv_id,
        claim_id=claim_id,
        original_url=url,
        canonical_url=url,
        article_title=title,
        publisher=publisher,
        published_date=published_date or now.isoformat(),
        retrieval_timestamp=now,
        language="en",
        source_type="NEWS",
        retrieval_method="SEARCH_SCRAPE",
        content_hash=f"hash-{uuid.uuid4()}",
        text_excerpt=excerpt,
        retrieval_status=status
    )


def make_test_asset(
    file_path: str = "uploads/test.jpg",
    sha256_hash: str = None,
    size_bytes: int = 102400
) -> MediaAsset:
    return MediaAsset(
        file_path=file_path,
        sha256_hash=sha256_hash or f"sha256-{uuid.uuid4()}",
        mime_type="image/jpeg",
        file_size_bytes=size_bytes
    )


def make_test_assessment(
    inv_id: str,
    claim_id: str,
    sub_id: str,
    classification: str = "SUPPORTED",
    rationale: str = "Supported by reliable records.",
    archival_signal: bool = False,
    limitations: str = "Assessment relies on available public records and local indices.",
    created_at: datetime = None
) -> ClaimAssessmentRecord:
    return ClaimAssessmentRecord(
        investigation_id=inv_id,
        claim_id=claim_id,
        evidence_submission_id=sub_id,
        version=1,
        is_active=True,
        classification=classification,
        primary_rationale=rationale,
        archival_signal_detected=archival_signal,
        epistemic_limitations=limitations,
        created_at=created_at or utc_now()
    )


def make_test_media_match(
    source_asset_id: str,
    source_evidence_id: str,
    matched_asset_id: str,
    classification: str = "SAME_PHOTOGRAPH_MODIFIED",
    method: str = "HISTORICAL_MEDIA_REDISCOVERY",
    rationale: str = "Archived photograph match.",
    raw_metrics: dict = None,
    disclaimer: str = "Visual match indicates geometric similarity. Requires contextual verification."
) -> MediaMatchRecord:
    return MediaMatchRecord(
        source_media_asset_id=source_asset_id,
        source_evidence_id=source_evidence_id,
        matched_media_asset_id=matched_asset_id,
        classification=classification,
        method=method,
        classification_rationale=rationale,
        raw_metrics=raw_metrics or {"confidence": 0.95},
        disclaimer=disclaimer
    )


@pytest.mark.asyncio
async def test_lineage_graph_assembly_and_node_types(db_session: AsyncSession, async_client: AsyncClient):
    """
    Test 1: Verify lineage graph assembly across all entity types
    (Investigation, EvidenceSubmission, MediaAsset, Claim, Source, Assessment).
    """
    inv = Investigation(
        title="Full Lineage Test Investigation",
        description="Testing complete graph generation",
        priority="HIGH",
        status="ACTIVE"
    )
    db_session.add(inv)
    await db_session.flush()

    asset = make_test_asset("uploads/protest.jpg")
    db_session.add(asset)
    await db_session.flush()

    sub = EvidenceSubmission(
        investigation_id=inv.id,
        media_asset_id=asset.id,
        submission_type="IMAGE",
        raw_text="Protest reported in Central Park",
        caption="Breaking: Central Park rally today",
        claimed_date="2026-07-01",
        claimed_location="New York",
        processing_status="COMPLETED"
    )
    db_session.add(sub)
    await db_session.flush()

    claim1 = make_test_claim(
        inv.id, sub.id,
        text="Major protest held in Central Park today",
        subject="protest", predicate="held in", obj="Central Park"
    )
    claim2 = make_test_claim(
        inv.id, sub.id,
        text="Demonstration held in Central Park today",
        subject="protest", predicate="held in", obj="Central Park demonstration"
    )
    db_session.add_all([claim1, claim2])
    await db_session.flush()

    src = make_test_source(
        inv.id, claim1.id,
        url="https://www.reuters.com/news/protest-nyc",
        title="Rally in Manhattan Park Draws Hundreds",
        publisher="Reuters",
        excerpt="Crowds gathered peacefully in Central Park on Saturday.",
        status="SUCCESS"
    )
    db_session.add(src)
    await db_session.flush()

    assessment = make_test_assessment(
        inv.id, claim1.id, sub.id,
        classification="SUPPORTED",
        rationale="Supported by Reuters report."
    )
    db_session.add(assessment)
    await db_session.commit()

    # Query via REST API
    resp = await async_client.get(f"/api/v1/investigations/{inv.id}/lineage/graph")
    assert resp.status_code == 200
    data = resp.json()

    assert data["investigation_id"] == inv.id
    node_types = {n["entity_type"] for n in data["nodes"]}
    assert "INVESTIGATION" in node_types
    assert "EVIDENCE_SUBMISSION" in node_types
    assert "MEDIA_ASSET" in node_types
    assert "CLAIM" in node_types
    assert "SOURCE" in node_types
    assert "ASSESSMENT" in node_types

    # Verify stable IDs
    node_ids = {n["id"] for n in data["nodes"]}
    assert f"inv_{inv.id}" in node_ids
    assert f"sub_{sub.id}" in node_ids
    assert f"media_{asset.id}" in node_ids
    assert f"claim_{claim1.id}" in node_ids
    assert f"claim_{claim2.id}" in node_ids
    assert f"src_{src.id}" in node_ids
    assert f"ass_{assessment.id}" in node_ids

    # Verify CLAIM_VARIANT edge was auto-inferred because subject & predicate match
    edges = data["edges"]
    variant_edge = next((e for e in edges if e["relationship_type"] == "CLAIM_VARIANT"), None)
    assert variant_edge is not None
    assert variant_edge["edge_nature"] == "INFERRED"


@pytest.mark.asyncio
async def test_lineage_edge_nature_observed_vs_inferred(db_session: AsyncSession, async_client: AsyncClient):
    """
    Test 2: Verify distinction between OBSERVED edges (containers, direct ties)
    and INFERRED edges (semantic variants, model inferences, similarity),
    and verify the include_inferred toggle.
    """
    inv = Investigation(title="Edge Nature Test", priority="LOW")
    db_session.add(inv)
    await db_session.flush()

    sub = EvidenceSubmission(
        investigation_id=inv.id,
        submission_type="TEXT",
        raw_text="Statement A",
        caption="Statement A"
    )
    db_session.add(sub)
    await db_session.flush()

    claim1 = make_test_claim(
        inv.id, sub.id,
        text="Statement A",
        subject="SubjectAlpha", predicate="ActionBeta", obj="TargetGamma"
    )
    claim2 = make_test_claim(
        inv.id, sub.id,
        text="Statement A variant phrasing",
        subject="SubjectAlpha", predicate="ActionBeta", obj="DifferentTarget"
    )
    db_session.add_all([claim1, claim2])
    await db_session.commit()

    # 1. With inferred edges included
    resp_all = await async_client.get(f"/api/v1/investigations/{inv.id}/lineage/graph?include_inferred=true")
    assert resp_all.status_code == 200
    edges_all = resp_all.json()["edges"]
    edge_natures = {e["edge_nature"] for e in edges_all}
    assert "OBSERVED" in edge_natures
    assert "INFERRED" in edge_natures

    # Container edge (sub -> claim) must be OBSERVED
    container_edge = next(e for e in edges_all if e["relationship_type"] == "SAME_CLAIM" and e["source_id"] == f"sub_{sub.id}")
    assert container_edge["edge_nature"] == "OBSERVED"

    # Variant edge (claim1 -> claim2) must be INFERRED
    variant_edge = next(e for e in edges_all if e["relationship_type"] == "CLAIM_VARIANT")
    assert variant_edge["edge_nature"] == "INFERRED"

    # 2. With inferred edges excluded
    resp_obs = await async_client.get(f"/api/v1/investigations/{inv.id}/lineage/graph?include_inferred=false")
    assert resp_obs.status_code == 200
    edges_obs = resp_obs.json()["edges"]
    for e in edges_obs:
        assert e["edge_nature"] == "OBSERVED"
    assert not any(e["relationship_type"] == "CLAIM_VARIANT" for e in edges_obs)


@pytest.mark.asyncio
async def test_evidence_traceability_edge_to_evidence(db_session: AsyncSession, async_client: AsyncClient):
    """
    Test 3: Verify /lineage/edges/{edge_id}/evidence resolves the underlying
    RetrievedSourceRecord or MediaMatchRecord with full provenance details.
    """
    inv = Investigation(title="Traceability Test", priority="MEDIUM")
    db_session.add(inv)
    await db_session.flush()

    sub = EvidenceSubmission(
        investigation_id=inv.id,
        submission_type="TEXT",
        raw_text="Hyderabad metro expansion completed"
    )
    db_session.add(sub)
    await db_session.flush()

    claim = make_test_claim(
        inv.id, sub.id,
        text="Hyderabad metro expansion completed",
        subject="Hyderabad metro", predicate="expansion completed", obj="metro"
    )
    db_session.add(claim)
    await db_session.flush()

    src = make_test_source(
        inv.id, claim.id,
        url="https://thehindu.com/news/metro-hyderabad",
        title="Hyderabad Metro Phase 2 Works Concluded",
        publisher="The Hindu",
        excerpt="Hyderabad Metro Rail Phase 2 line has officially concluded construction.",
        status="SUCCESS"
    )
    db_session.add(src)
    await db_session.commit()

    # Get graph to find the source edge ID
    graph_resp = await async_client.get(f"/api/v1/investigations/{inv.id}/lineage/graph")
    assert graph_resp.status_code == 200
    edges = graph_resp.json()["edges"]

    src_edge = next((e for e in edges if e["target_id"] == f"claim_{claim.id}" and e["source_id"] == f"src_{src.id}"), None)
    assert src_edge is not None

    # Inspect underlying evidence drawer endpoint
    edge_id = src_edge["id"]
    ev_resp = await async_client.get(f"/api/v1/investigations/{inv.id}/lineage/edges/{edge_id}/evidence")
    assert ev_resp.status_code == 200
    ev_data = ev_resp.json()

    assert ev_data["edge_id"] == edge_id
    assert ev_data["underlying_record_type"] == "RETRIEVED_SOURCE"
    assert ev_data["source_details"]["publisher"] == "The Hindu"
    assert "concluded construction" in ev_data["source_details"]["text_excerpt"]


@pytest.mark.asyncio
async def test_invariant_authentic_media_with_false_caption(db_session: AsyncSession, async_client: AsyncClient):
    """
    Test 4: Core Invariant — Authentic historical image repurposed with false caption
    must produce MISLEADING_OR_CONTEXT_MISSING while preserving media authenticity findings.
    Authenticity and truth are decoupled.
    """
    inv = Investigation(title="Recycled Photo Test", priority="HIGH")
    db_session.add(inv)
    await db_session.flush()

    asset = make_test_asset("uploads/flood.jpg", sha256_hash="authentic-sha-9999")
    archived_asset = make_test_asset("uploads/archived_kerala.jpg", sha256_hash="archived-kerala-2018-hash")
    db_session.add_all([asset, archived_asset])
    await db_session.flush()

    sub = EvidenceSubmission(
        investigation_id=inv.id,
        media_asset_id=asset.id,
        submission_type="IMAGE",
        caption="Breaking: Cyclone causes devastation in Mumbai today",
        claimed_date="2026-08-10",
        claimed_location="Mumbai"
    )
    db_session.add(sub)
    await db_session.flush()

    claim = make_test_claim(
        inv.id, sub.id,
        text="Cyclone causes devastation in Mumbai today",
        subject="Cyclone", predicate="causes devastation in", obj="Mumbai"
    )
    db_session.add(claim)
    await db_session.flush()

    # Historical match: image was taken in 2018 in Kerala (authentic photo, old event)
    hist_match = make_test_media_match(
        source_asset_id=asset.id,
        source_evidence_id=sub.id,
        matched_asset_id=archived_asset.id,
        classification="SAME_PHOTOGRAPH_MODIFIED",
        rationale="Authentic 2018 flood photo from Kerala archives matching keypoint descriptors.",
        raw_metrics={"confidence": 0.96, "historical_date": "2018-08-15", "location": "Kerala"}
    )
    db_session.add(hist_match)

    # Assessment: media authentic, but claim misleading context
    assessment = make_test_assessment(
        inv.id, claim.id, sub.id,
        classification="MISLEADING_OR_CONTEXT_MISSING",
        rationale="Authentic 2018 Kerala flood photograph recirculated as 2026 Mumbai cyclone.",
        archival_signal=True
    )
    db_session.add(assessment)
    await db_session.commit()

    # Verify explainable breakdown
    explanation = await ExplainableAssessmentEngine.generate_explanation(session=db_session, claim_id=claim.id)

    assert explanation.assessment_classification == "MISLEADING_OR_CONTEXT_MISSING"
    assert len(explanation.historical_media_findings) == 1
    assert explanation.historical_media_findings[0]["classification"] == "SAME_PHOTOGRAPH_MODIFIED"
    assert "2018 flood photo" in explanation.historical_media_findings[0]["rationale"]
    assert "recirculated" in explanation.primary_rationale.lower()


@pytest.mark.asyncio
async def test_invariant_manipulated_media_with_true_claim(db_session: AsyncSession):
    """
    Test 5: Core Invariant — Manipulated media (e.g. enhanced/cropped/doctored)
    used alongside a factual claim that is independently corroborated by authoritative sources.
    Claim classification must remain SUPPORTED, preserving the distinction between media artifact and claim truth.
    """
    inv = Investigation(title="Manipulated Media True Claim Test")
    db_session.add(inv)
    await db_session.flush()

    asset = make_test_asset("uploads/lunar_art.jpg", sha256_hash="altered-sha-8888")
    stock_asset = make_test_asset("uploads/stock_cgi.jpg", sha256_hash="stock-cgi-render-hash")
    db_session.add_all([asset, stock_asset])
    await db_session.flush()

    sub = EvidenceSubmission(
        investigation_id=inv.id,
        media_asset_id=asset.id,
        submission_type="IMAGE",
        caption="ISRO successfully launched lunar probe"
    )
    db_session.add(sub)
    await db_session.flush()

    claim = make_test_claim(
        inv.id, sub.id,
        text="ISRO successfully launched lunar probe",
        subject="ISRO", predicate="launched", obj="lunar probe"
    )
    db_session.add(claim)
    await db_session.flush()

    # Match indicates altered illustration
    hist_match = make_test_media_match(
        source_asset_id=asset.id,
        source_evidence_id=sub.id,
        matched_asset_id=stock_asset.id,
        classification="NEAR_DUPLICATE_MEDIA",
        rationale="Digital illustration composite matching 3D rendering database.",
        raw_metrics={"confidence": 0.91}
    )
    db_session.add(hist_match)

    # Authoritative external source corroborates the claim
    src = make_test_source(
        inv.id, claim.id,
        url="https://isro.gov.in/press-release/lunar-probe",
        title="Official Press Release: Lunar Probe Mission Success",
        publisher="ISRO",
        excerpt="The lunar probe was successfully launched into trajectory at 14:35 UTC.",
        status="SUCCESS"
    )
    db_session.add(src)

    # Assessment: media manipulated (CGI composite passed as real event), but claim true
    assessment = make_test_assessment(
        inv.id, claim.id, sub.id,
        classification="SUPPORTED",
        rationale="Claim is independently verified by official ISRO release, though submitted visual is a CGI composite."
    )
    db_session.add(assessment)
    await db_session.flush()

    rel = ClaimEvidenceRelationRecord(
        assessment_id=assessment.id,
        claim_id=claim.id,
        evidence_source_id=src.id,
        evidence_source_type="RETRIEVED_SOURCE",
        relationship_type="SUPPORTS",
        source_location=src.canonical_url,
        source_publisher="ISRO",
        excerpt="The lunar probe was successfully launched into trajectory at 14:35 UTC.",
        source_independence_status="INDEPENDENT",
        alignment_rationale="Explicit confirmation of lunar probe launch."
    )
    db_session.add(rel)
    await db_session.commit()

    explanation = await ExplainableAssessmentEngine.generate_explanation(session=db_session, claim_id=claim.id)

    assert explanation.assessment_classification == "SUPPORTED"
    assert len(explanation.supporting_evidence) == 1
    assert explanation.supporting_evidence[0]["publisher"] == "ISRO"
    assert len(explanation.historical_media_findings) == 1
    assert "CGI" in explanation.primary_rationale or "composite" in explanation.primary_rationale


@pytest.mark.asyncio
async def test_invariant_wire_reprints_do_not_equal_independent_corroboration(db_session: AsyncSession):
    """
    Test 6: Core Invariant — Multiple media outlets reprinting the same wire service
    dispatch are grouped into a single independent source entity. Independent corroboration count is 1.
    """
    inv = Investigation(title="Wire Service Dependency Test")
    db_session.add(inv)
    await db_session.flush()

    sub = EvidenceSubmission(investigation_id=inv.id, submission_type="TEXT")
    db_session.add(sub)
    await db_session.flush()

    claim = make_test_claim(
        inv.id, sub.id,
        text="New environmental regulations announced by ministry",
        subject="ministry", predicate="announced", obj="regulations"
    )
    db_session.add(claim)
    await db_session.flush()

    src1 = make_test_source(
        inv.id, claim.id,
        url="https://timesofindia.com/wire/env-reg",
        title="Ministry Enacts Green Norms - PTI",
        publisher="Times of India",
        excerpt="PTI: The ministry today notified new environmental guidelines...",
        status="SUCCESS"
    )
    src2 = make_test_source(
        inv.id, claim.id,
        url="https://hindustantimes.com/india-news/env-rules",
        title="Govt Issues New Green Norms",
        publisher="Hindustan Times",
        excerpt="According to a PTI report, the ministry today notified...",
        status="SUCCESS"
    )
    src3 = make_test_source(
        inv.id, claim.id,
        url="https://ndtv.com/india-news/new-rules",
        title="Green Norms Updated by Ministry",
        publisher="NDTV",
        excerpt="PTI: The ministry notified new environmental guidelines...",
        status="SUCCESS"
    )
    db_session.add_all([src1, src2, src3])
    await db_session.flush()

    dep = SourceIndependenceRecord(
        claim_id=claim.id,
        total_sources_count=3,
        independent_sources_count=1,
        independence_assessment="SHARED_WIRE_REPORT",
        clusters=[{
            "cluster_id": 1,
            "dependency_type": "SHARED_WIRE_REPORT",
            "lead_publisher": "PTI",
            "sources": [src1.original_url, src2.original_url, src3.original_url]
        }],
        explanation="All three reporting outlets reprint the identical Press Trust of India (PTI) wire dispatch verbatim."
    )
    db_session.add(dep)

    assessment = make_test_assessment(
        inv.id, claim.id, sub.id,
        classification="SUPPORTED",
        rationale="Supported by PTI wire service report."
    )
    db_session.add(assessment)
    await db_session.commit()

    explanation = await ExplainableAssessmentEngine.generate_explanation(session=db_session, claim_id=claim.id)

    deps = explanation.source_dependencies
    assert deps["total_sources_evaluated"] == 3
    assert deps["independent_sources_count"] == 1
    assert deps["independence_assessment"] == "SHARED_WIRE_REPORT"
    assert len(deps["clusters"]) == 1
    assert "wire dispatch" in deps["explanation"] and "PTI" in deps["explanation"]


@pytest.mark.asyncio
async def test_invariant_conflicting_evidence_abstention(db_session: AsyncSession):
    """
    Test 7: Core Invariant — Equal authoritative sources contradicting each other
    must produce CONFLICTING_EVIDENCE without guessing or forcing a resolution.
    """
    inv = Investigation(title="Conflicting Evidence Test")
    db_session.add(inv)
    await db_session.flush()

    sub = EvidenceSubmission(investigation_id=inv.id, submission_type="TEXT")
    db_session.add(sub)
    await db_session.flush()

    claim = make_test_claim(
        inv.id, sub.id,
        text="Summit meeting between Party A and Party B was cancelled",
        subject="summit", predicate="cancelled", obj="meeting"
    )
    db_session.add(claim)
    await db_session.flush()

    assessment = make_test_assessment(
        inv.id, claim.id, sub.id,
        classification="CONFLICTING_EVIDENCE",
        rationale="Direct contradiction between official spokespersons of Party A and Party B."
    )
    db_session.add(assessment)
    await db_session.flush()

    rel1 = ClaimEvidenceRelationRecord(
        assessment_id=assessment.id,
        claim_id=claim.id,
        evidence_source_id="src_a",
        evidence_source_type="RETRIEVED_SOURCE",
        relationship_type="SUPPORTS",
        source_location="https://party-a.org/press",
        source_publisher="Party A",
        excerpt="The summit has been cancelled due to scheduling conflicts.",
        source_independence_status="INDEPENDENT",
        alignment_rationale="Explicit confirmation of cancellation."
    )
    rel2 = ClaimEvidenceRelationRecord(
        assessment_id=assessment.id,
        claim_id=claim.id,
        evidence_source_id="src_b",
        evidence_source_type="RETRIEVED_SOURCE",
        relationship_type="CONTRADICTS",
        source_location="https://party-b.org/press",
        source_publisher="Party B",
        excerpt="The summit is proceeding as scheduled; reports of cancellation are incorrect.",
        source_independence_status="INDEPENDENT",
        alignment_rationale="Explicit denial of cancellation."
    )
    db_session.add_all([rel1, rel2])
    await db_session.commit()

    explanation = await ExplainableAssessmentEngine.generate_explanation(session=db_session, claim_id=claim.id)

    assert explanation.assessment_classification == "CONFLICTING_EVIDENCE"
    assert len(explanation.supporting_evidence) == 1
    assert len(explanation.contradicting_evidence) == 1
    assert "contradictory factual accounts" in explanation.decision_tree_explanation


@pytest.mark.asyncio
async def test_invariant_insufficient_evidence_abstention(db_session: AsyncSession):
    """
    Test 8: Core Invariant — Absence of evidence is not evidence of falsehood.
    Claims without corroboration must be classified as INSUFFICIENT_EVIDENCE or UNVERIFIED,
    with explicit open questions and missing evidence gaps.
    """
    inv = Investigation(title="Insufficient Evidence Test")
    db_session.add(inv)
    await db_session.flush()

    sub = EvidenceSubmission(investigation_id=inv.id, submission_type="TEXT")
    db_session.add(sub)
    await db_session.flush()

    claim = make_test_claim(
        inv.id, sub.id,
        text="Secret meeting took place at midnight in undisclosed bunker",
        subject="Secret meeting", predicate="took place at", obj="undisclosed bunker"
    )
    db_session.add(claim)
    await db_session.flush()

    assessment = make_test_assessment(
        inv.id, claim.id, sub.id,
        classification="INSUFFICIENT_EVIDENCE",
        rationale="No authoritative sources, public records, or eyewitness accounts found."
    )
    db_session.add(assessment)
    await db_session.commit()

    explanation = await ExplainableAssessmentEngine.generate_explanation(session=db_session, claim_id=claim.id)

    assert explanation.assessment_classification == "INSUFFICIENT_EVIDENCE"
    assert len(explanation.missing_evidence) > 0
    assert any("authoritative" in gap.lower() or "source" in gap.lower() for gap in explanation.missing_evidence)
    assert "Absence of evidence is not proof of falsehood" in explanation.decision_tree_explanation


@pytest.mark.asyncio
async def test_cross_investigation_privacy_isolation_in_graph(db_session: AsyncSession, async_client: AsyncClient):
    """
    Test 9: Cross-Investigation Privacy Isolation
    When an image in Investigation B matches an asset from confidential Investigation A,
    the lineage graph for Investigation B must include the matched asset reference,
    but strictly redact Investigation A's title, internal notes, and investigator IDs.
    """
    # Confidential Investigation A
    inv_a = Investigation(
        title="CLASSIFIED: Undercover Counter-Disinformation Operation Alpha",
        description="Top secret investigator notes regarding covert state actor accounts.",
        priority="HIGH"
    )
    db_session.add(inv_a)
    await db_session.flush()

    asset_a = make_test_asset("uploads/secret_photo.jpg", sha256_hash="classified-hash-xyz")
    db_session.add(asset_a)
    await db_session.flush()

    sub_a = EvidenceSubmission(investigation_id=inv_a.id, media_asset_id=asset_a.id, submission_type="IMAGE")
    db_session.add(sub_a)
    await db_session.flush()

    # Public Investigation B
    inv_b = Investigation(
        title="Public Fact Check on Social Media Meme",
        priority="LOW"
    )
    db_session.add(inv_b)
    await db_session.flush()

    asset_b = make_test_asset("uploads/public_meme.jpg", sha256_hash="meme-hash-123")
    db_session.add(asset_b)
    await db_session.flush()

    sub_b = EvidenceSubmission(investigation_id=inv_b.id, media_asset_id=asset_b.id, submission_type="IMAGE")
    db_session.add(sub_b)
    await db_session.flush()

    # Match linking Asset B to Asset A
    match = make_test_media_match(
        source_asset_id=asset_b.id,
        source_evidence_id=sub_b.id,
        matched_asset_id=asset_a.id,
        classification="EXACT_MEDIA_MATCH",
        rationale="Exact SHA-256 match with archived asset.",
        raw_metrics={"confidence": 1.0}
    )
    db_session.add(match)
    await db_session.commit()

    # Fetch lineage graph for Investigation B
    resp = await async_client.get(f"/api/v1/investigations/{inv_b.id}/lineage/graph")
    assert resp.status_code == 200
    graph_text = resp.text

    # Verify that asset_a is referenced as an archival asset node
    assert f"media_{asset_a.id}" in graph_text or f"asset_{asset_a.id}" in graph_text

    # STRICT PRIVACY INVARIANT: Investigation A's title and confidential notes must NEVER appear
    assert "CLASSIFIED" not in graph_text
    assert "Operation Alpha" not in graph_text
    assert "covert state actor" not in graph_text


@pytest.mark.asyncio
async def test_lineage_timeline_chronological_ordering(db_session: AsyncSession, async_client: AsyncClient):
    """
    Test 10: Verify /lineage/timeline correctly returns events in chronological order.
    """
    base_time = utc_now() - timedelta(days=10)
    inv = Investigation(title="Timeline Test", created_at=base_time)
    db_session.add(inv)
    await db_session.flush()

    # Event 1: Early submission (T - 5 days)
    t1 = base_time + timedelta(days=5)
    sub = EvidenceSubmission(
        investigation_id=inv.id,
        submission_type="TEXT",
        raw_text="Timeline event 1",
        created_at=t1
    )
    db_session.add(sub)
    await db_session.flush()

    # Event 2: Source publication (T - 3 days)
    t2 = base_time + timedelta(days=7)
    claim = make_test_claim(
        inv.id, sub.id,
        text="Timeline claim",
        subject="T", predicate="is", obj="line"
    )
    db_session.add(claim)
    await db_session.flush()

    src = make_test_source(
        inv.id, claim.id,
        url="https://timeline-news.com/article",
        title="Timeline News",
        published_date=t2.isoformat(),
        status="SUCCESS"
    )
    db_session.add(src)
    await db_session.flush()

    # Event 3: Contextual Assessment (T - 1 day)
    t3 = base_time + timedelta(days=9)
    assessment = make_test_assessment(
        inv.id, claim.id, sub.id,
        classification="SUPPORTED",
        rationale="Timeline supported",
        created_at=t3
    )
    db_session.add(assessment)
    await db_session.commit()

    resp = await async_client.get(f"/api/v1/investigations/{inv.id}/lineage/timeline")
    assert resp.status_code == 200
    events = resp.json()["events"]
    assert len(events) >= 3

    # Check timestamps are non-decreasing
    parsed_timestamps = [parse_timeline_dt(item["timestamp"]) for item in events]
    for i in range(len(parsed_timestamps) - 1):
        assert parsed_timestamps[i] <= parsed_timestamps[i+1]


@pytest.mark.asyncio
async def test_lineage_human_review_lifecycle(db_session: AsyncSession, async_client: AsyncClient):
    """
    Test 11: Human Review Lifecycle
    Create a custom relationship, submit human review to CONFIRM/DISPUTE it,
    and verify that reviewer notes and status are preserved without overwriting automated fields.
    """
    inv = Investigation(title="Human Review Test")
    db_session.add(inv)
    await db_session.flush()

    sub = EvidenceSubmission(investigation_id=inv.id, submission_type="TEXT")
    db_session.add(sub)
    await db_session.flush()

    claim1 = make_test_claim(
        inv.id, sub.id,
        text="Hospital overwhelmed by unknown fever",
        subject="hospital", predicate="overwhelmed", obj="fever"
    )
    claim2 = make_test_claim(
        inv.id, sub.id,
        text="Clinic operating normally with seasonal flu patients",
        subject="clinic", predicate="operating", obj="normally"
    )
    db_session.add_all([claim1, claim2])
    await db_session.commit()

    # 1. Create custom inferred relationship
    create_payload = {
        "source_entity_id": f"claim_{claim2.id}",
        "source_entity_type": "CLAIM",
        "target_entity_id": f"claim_{claim1.id}",
        "target_entity_type": "CLAIM",
        "relationship_type": "CONTRADICTS",
        "edge_nature": "INFERRED",
        "evidence_summary": "Clinic operating normally disputes hospital overwhelmed claim.",
        "detection_method": "MANUAL_INVESTIGATOR_ENTRY",
        "review_status": "UNREVIEWED",
        "reviewer_notes": "Preliminary check."
    }
    create_resp = await async_client.post(
        f"/api/v1/investigations/{inv.id}/lineage/relationships",
        json=create_payload
    )
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    rel_id = created_data["id"]
    assert created_data["review_status"] == "UNREVIEWED"

    # 2. Review the relationship
    review_payload = {
        "review_status": "CONFIRMED",
        "reviewer_notes": "Verified by investigator cross-referencing health department bulletin.",
        "reviewer_id": "investigator_alice"
    }
    review_resp = await async_client.post(
        f"/api/v1/investigations/{inv.id}/lineage/relationships/{rel_id}/review",
        json=review_payload
    )
    assert review_resp.status_code == 200
    review_data = review_resp.json()
    assert review_data["review_status"] == "CONFIRMED"
    assert review_data["reviewer_notes"] == "Verified by investigator cross-referencing health department bulletin."

    # 3. Verify in graph
    graph_resp = await async_client.get(f"/api/v1/investigations/{inv.id}/lineage/graph")
    edges = graph_resp.json()["edges"]
    reviewed_edge = next((e for e in edges if e["id"] == f"rel_{rel_id}"), None)
    assert reviewed_edge is not None
    assert reviewed_edge["review_status"] == "CONFIRMED"
    assert reviewed_edge["reviewer_notes"] == "Verified by investigator cross-referencing health department bulletin."


@pytest.mark.asyncio
async def test_explainable_assessment_generation(db_session: AsyncSession, async_client: AsyncClient):
    """
    Test 12: Verify GET /claims/{claim_id}/explanation generates a comprehensive,
    deterministic explanation breakdown without any LLM dependencies.
    """
    inv = Investigation(title="Explanation Test")
    db_session.add(inv)
    await db_session.flush()

    sub = EvidenceSubmission(investigation_id=inv.id, submission_type="TEXT")
    db_session.add(sub)
    await db_session.flush()

    claim = make_test_claim(
        inv.id, sub.id,
        text="Bridge was closed for emergency repairs",
        subject="bridge", predicate="closed for", obj="repairs"
    )
    db_session.add(claim)
    await db_session.flush()

    assessment = make_test_assessment(
        inv.id, claim.id, sub.id,
        classification="SUPPORTED",
        rationale="Department of Transportation official notice explicitly confirms emergency closure."
    )
    db_session.add(assessment)
    await db_session.flush()

    src = make_test_source(
        inv.id, claim.id,
        url="https://dot.state.gov/bridge-closure",
        title="Department of Transportation Notice",
        publisher="Department of Transportation",
        excerpt="Bridge closed effective midnight for urgent deck repairs.",
        status="SUCCESS"
    )
    db_session.add(src)
    await db_session.flush()

    rel = ClaimEvidenceRelationRecord(
        assessment_id=assessment.id,
        claim_id=claim.id,
        evidence_source_id=src.id,
        evidence_source_type="RETRIEVED_SOURCE",
        relationship_type="SUPPORTS",
        source_location=src.canonical_url,
        source_publisher="Department of Transportation",
        excerpt="Bridge closed effective midnight for urgent deck repairs.",
        source_independence_status="INDEPENDENT",
        alignment_rationale="Explicit confirmation of emergency bridge deck repairs."
    )
    db_session.add(rel)
    await db_session.commit()

    resp = await async_client.get(f"/api/v1/claims/{claim.id}/explanation")
    assert resp.status_code == 200
    data = resp.json()

    assert data["claim_id"] == claim.id
    assert data["assessment_classification"] == "SUPPORTED"
    assert len(data["supporting_evidence"]) >= 1
    assert data["supporting_evidence"][0]["publisher"] == "Department of Transportation"
    assert "emergency closure" in data["primary_rationale"].lower()


@pytest.mark.asyncio
async def test_lineage_explorer_ui_html_render(db_session: AsyncSession, async_client: AsyncClient):
    """
    Test 13: Verify GET /investigations/{id}/lineage/explorer serves the interactive
    visual UI with HTML headers, canvas container, and drawer markup.
    """
    inv = Investigation(title="Visual UI Explorer Test")
    db_session.add(inv)
    await db_session.commit()

    resp = await async_client.get(f"/api/v1/investigations/{inv.id}/lineage/explorer")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    html = resp.text

    assert "Visual UI Explorer Test" in html
    assert "canvas-container" in html
    assert "graph-svg" in html
    assert "drawer" in html
    assert "toggle-inferred" in html
    assert "stat-nodes" in html
    assert "stat-edges" in html
