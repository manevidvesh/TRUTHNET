import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import patch
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.investigation import Investigation
from app.models.evidence import EvidenceSubmission, MediaAsset, ExtractionRecord
from app.models.fingerprint import MediaMatchRecord
from app.models.claim import ClaimRecord, ClaimExtractionRun
from app.models.context_verification import ClaimAssessmentRecord, ClaimEvidenceRelationRecord
from app.schemas.context_verification import (
    EvidenceItem,
    AssessmentClassification,
    EvidenceRelationshipType,
    HumanReviewStatus
)
from app.context.verifier import ContextualClaimVerifier
from app.context.temporal import TemporalContextEngine
from app.context.geodesic import evaluate_spatial_relationship, haversine_distance_km
from app.services.pipeline import pipeline_service

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

async def create_base_claim(
    db: AsyncSession,
    claim_text: str = "Heavy rains flooded Mumbai streets",
    normalized_claim: str = "Heavy rains flooded Mumbai streets",
    subject: str = "Heavy rains",
    predicate: str = "flooded",
    obj: str = "Mumbai streets",
    claimed_date: str = "2026-05-10",
    claimed_location: str = "Mumbai",
    caption: str = "Severe flooding in Mumbai today",
    polarity_state: str = "AFFIRMATIVE_SURFACE_SYNTAX",
    is_attributed: bool = False,
    language: str = "en",
    extracted_entities: dict = None,
    media_asset: MediaAsset = None
) -> tuple[Investigation, EvidenceSubmission, ClaimRecord]:
    inv = Investigation(
        title="Test Investigation",
        description="Testing contextual verification",
        priority="MEDIUM",
        status="ACTIVE"
    )
    db.add(inv)
    await db.flush()

    sub = EvidenceSubmission(
        investigation_id=inv.id,
        media_asset_id=media_asset.id if media_asset else None,
        submission_type="IMAGE" if media_asset else "TEXT",
        raw_text=caption,
        caption=caption,
        claimed_date=claimed_date,
        claimed_location=claimed_location,
        language=language,
        processing_status="COMPLETED"
    )
    db.add(sub)
    await db.flush()

    claim = ClaimRecord(
        investigation_id=inv.id,
        evidence_submission_id=sub.id,
        claim_text=claim_text,
        normalized_claim=normalized_claim,
        subject=subject,
        predicate=predicate,
        object=obj,
        polarity_state=polarity_state,
        is_attributed_assertion=is_attributed,
        source_modality="CAPTION",
        evidence_span_start=0,
        evidence_span_end=len(claim_text),
        source_text_hash="test-hash",
        extracted_entities=extracted_entities or {"locations": [claimed_location]},
        language=language,
        language_detection_method="statistical_test"
    )
    db.add(claim)
    await db.commit()
    return inv, sub, claim

# ==============================================================================
# 20 ADVERSARIAL TEST SCENARIOS
# ==============================================================================

@pytest.mark.asyncio
async def test_recycled_media_deceptive_event(db_session: AsyncSession):
    """1. Recycled media: 2018 photo deceptively captioned as 2026 disaster -> MISLEADING_OR_CONTEXT_MISSING."""
    asset = MediaAsset(
        sha256_hash="recycled-asset-hash",
        mime_type="image/jpeg",
        file_path="uploads/recycled.jpg",
        file_size_bytes=1024
    )
    db_session.add(asset)
    await db_session.flush()

    inv, sub, claim = await create_base_claim(
        db_session,
        claim_text="Severe flooding submerged Mumbai in May 2026",
        claimed_date="2026-05-10",
        claimed_location="Mumbai",
        caption="Breaking: Severe flooding in Mumbai today",
        media_asset=asset
    )

    ext = ExtractionRecord(
        evidence_submission_id=sub.id,
        version=1,
        is_active=True,
        extractor_name="TestExtractor",
        extractor_version="1.0.0",
        technical_metadata={"datetime_original": "2018-08-15 12:00:00"}
    )
    db_session.add(ext)
    await db_session.commit()

    assessment = await ContextualClaimVerifier.verify_claim(db_session, claim.id)
    assert assessment.classification == AssessmentClassification.MISLEADING_OR_CONTEXT_MISSING.value
    assert assessment.temporal_analysis["temporal_delta_days"] > 2000
    assert assessment.archival_signal_detected is False

@pytest.mark.asyncio
async def test_legitimate_archival_caption_signal_does_not_force_supported(db_session: AsyncSession):
    """2. Archival caption keywords must be contextual signals only; do NOT force SUPPORTED without corroborating event evidence."""
    asset = MediaAsset(
        sha256_hash="archival-asset-hash",
        mime_type="image/jpeg",
        file_path="uploads/archival.jpg",
        file_size_bytes=1024
    )
    db_session.add(asset)
    await db_session.flush()

    inv, sub, claim = await create_base_claim(
        db_session,
        claim_text="Tohoku tsunami devastated coastal areas in 2011",
        claimed_date="2011-03-11",
        claimed_location="Tokyo",
        caption="Remembering the 2011 Tohoku tsunami (File Photo)",
        media_asset=asset
    )

    # Historical media match from TRUTHNET repository
    match = MediaMatchRecord(
        source_evidence_id=sub.id,
        source_media_asset_id=asset.id,
        classification="EXACT_FILE_MATCH",
        method="TRUTHNET-PERCEPTUAL-HASH",
        disclaimer="Match test"
    )
    db_session.add(match)
    await db_session.commit()

    assessment = await ContextualClaimVerifier.verify_claim(db_session, claim.id)
    # Crucial rule: Archival keywords prevent false accusation of fraud, but do NOT make claim SUPPORTED without event evidence
    assert assessment.archival_signal_detected is True
    assert assessment.classification in [
        AssessmentClassification.INSUFFICIENT_EVIDENCE.value,
        AssessmentClassification.UNVERIFIED.value
    ]
    assert assessment.classification != AssessmentClassification.SUPPORTED.value

@pytest.mark.asyncio
async def test_direct_factual_contradiction(db_session: AsyncSession):
    """3. Direct factual contradiction: Official report refutes claimed wind speed -> CONTRADICTED."""
    inv, sub, claim = await create_base_claim(
        db_session,
        claim_text="Cyclone reached 350 km/h in Chennai",
        subject="Cyclone",
        predicate="reached",
        obj="350 km/h in Chennai",
        claimed_location="Chennai"
    )

    evidence = [
        EvidenceItem(
            evidence_id="met-report-01",
            source_id="gov-imd-chennai-2026",
            publisher="Indian Meteorological Department",
            content_or_passage="Official report confirms maximum sustained winds of Cyclone reached 110 km/h in Chennai. Reports of 350 km/h are false.",
            source_type="OFFICIAL_DOCUMENT"
        )
    ]

    assessment = await ContextualClaimVerifier.verify_claim(db_session, claim.id, evidence_items=evidence)
    assert assessment.classification == AssessmentClassification.CONTRADICTED.value
    assert len(assessment.evidence_relations) == 1
    assert assessment.evidence_relations[0].relationship_type == EvidenceRelationshipType.CONTRADICTS.value

@pytest.mark.asyncio
async def test_well_corroborated_claim_with_explicit_evidence(db_session: AsyncSession):
    """4. Well-corroborated claim with independent evidence -> SUPPORTED with source independence marked UNKNOWN."""
    inv, sub, claim = await create_base_claim(
        db_session,
        claim_text="Treaty was signed in Geneva on October 12",
        subject="Treaty",
        predicate="was signed",
        obj="in Geneva on October 12",
        claimed_location="Geneva"
    )

    evidence = [
        EvidenceItem(
            evidence_id="un-news-01",
            source_id="https://un.org/news/treaty-signed",
            source_url="https://un.org/news/treaty-signed",
            publisher="United Nations Press",
            content_or_passage="The multilateral treaty was signed in Geneva on October 12 by 45 member states.",
            source_type="OFFICIAL_DOCUMENT"
        ),
        EvidenceItem(
            evidence_id="reuters-01",
            source_id="https://reuters.com/world/treaty-geneva",
            source_url="https://reuters.com/world/treaty-geneva",
            publisher="Reuters",
            content_or_passage="Representatives gathered as the treaty was signed in Geneva following week-long talks.",
            source_type="NEWS_ARTICLE"
        )
    ]

    assessment = await ContextualClaimVerifier.verify_claim(db_session, claim.id, evidence_items=evidence)
    assert assessment.classification == AssessmentClassification.SUPPORTED.value
    assert len(assessment.evidence_relations) == 2
    # Rule 5: Source independence must be explicitly marked UNKNOWN
    for rel in assessment.evidence_relations:
        assert rel.source_independence_status == "UNKNOWN"

@pytest.mark.asyncio
async def test_breaking_unverified_claim_zero_evidence(db_session: AsyncSession):
    """5. Breaking claim with zero evidence -> UNVERIFIED (never marked false)."""
    inv, sub, claim = await create_base_claim(
        db_session,
        claim_text="Bridge collapsed in isolated district",
        caption="Breaking: Bridge collapsed in isolated district 10 minutes ago"
    )

    assessment = await ContextualClaimVerifier.verify_claim(db_session, claim.id, evidence_items=[])
    assert assessment.classification == AssessmentClassification.UNVERIFIED.value
    assert "not indicate falsehood" in assessment.primary_rationale.lower()

@pytest.mark.asyncio
async def test_conflicting_authoritative_sources(db_session: AsyncSession):
    """6. Irreconcilable accounts across sources -> CONFLICTING_EVIDENCE."""
    inv, sub, claim = await create_base_claim(
        db_session,
        claim_text="Factory fire caused 14 casualties",
        subject="Factory fire",
        predicate="caused",
        obj="14 casualties"
    )

    evidence = [
        EvidenceItem(
            evidence_id="src-a",
            source_id="official-health-dept",
            publisher="State Health Dept",
            content_or_passage="State Health Dept confirms the factory fire caused 14 casualties in total.",
            source_type="OFFICIAL_DOCUMENT"
        ),
        EvidenceItem(
            evidence_id="src-b",
            source_id="investigative-herald",
            publisher="Investigative Herald",
            content_or_passage="Contradicting health reports, independent investigation found the factory fire caused 120 casualties, not 14.",
            source_type="NEWS_ARTICLE"
        )
    ]

    assessment = await ContextualClaimVerifier.verify_claim(db_session, claim.id, evidence_items=evidence)
    assert assessment.classification == AssessmentClassification.CONFLICTING_EVIDENCE.value
    assert "conflicting" in assessment.primary_rationale.lower()

@pytest.mark.asyncio
async def test_temporal_displacement_same_location(db_session: AsyncSession):
    """7. Annual parade footage from 5 years earlier claimed as 2026 -> MISLEADING_OR_CONTEXT_MISSING."""
    inv, sub, claim = await create_base_claim(
        db_session,
        claim_text="Republic Day parade celebrated at Kartavya Path in 2026",
        claimed_date="2026-01-26",
        claimed_location="New Delhi",
        caption="Live visuals from 2026 Republic Day parade"
    )

    ext = ExtractionRecord(
        evidence_submission_id=sub.id,
        version=1,
        is_active=True,
        extractor_name="TestExtractor",
        extractor_version="1.0.0",
        technical_metadata={"datetime_original": "2021-01-26 10:00:00"}
    )
    db_session.add(ext)
    await db_session.commit()

    assessment = await ContextualClaimVerifier.verify_claim(db_session, claim.id)
    assert assessment.classification == AssessmentClassification.MISLEADING_OR_CONTEXT_MISSING.value
    assert assessment.temporal_analysis["temporal_delta_days"] > 1800

@pytest.mark.asyncio
async def test_geographic_displacement_with_corroborating_context(db_session: AsyncSession):
    """8. Video claimed as Tokyo but verified as Turkey with corroborating context -> CONTRADICTED."""
    inv, sub, claim = await create_base_claim(
        db_session,
        claim_text="Earthquake collapsed building in Tokyo",
        claimed_location="Tokyo",
        caption="Earthquake destroys building in Tokyo"
    )

    # GPS coordinates in Turkey (Istanbul: 41.0082, 28.9784)
    ext = ExtractionRecord(
        evidence_submission_id=sub.id,
        version=1,
        is_active=True,
        extractor_name="TestExtractor",
        extractor_version="1.0.0",
        technical_metadata={"gps": {"latitude": 41.0082, "longitude": 28.9784}}
    )
    db_session.add(ext)

    evidence = [
        EvidenceItem(
            evidence_id="afp-turkey-debunk",
            source_id="afp-fact-check",
            publisher="AFP Fact Check",
            content_or_passage="Video falsely claimed as Tokyo shows 2023 earthquake in Turkey. Building collapse happened in Turkey.",
            source_type="FACT_CHECK_RECORD"
        )
    ]
    await db_session.commit()

    assessment = await ContextualClaimVerifier.verify_claim(db_session, claim.id, evidence_items=evidence)
    assert assessment.classification == AssessmentClassification.CONTRADICTED.value
    assert assessment.geographical_analysis["is_geographical_contradiction"] is True

@pytest.mark.asyncio
async def test_partial_truth_misleading_omission(db_session: AsyncSession):
    """9. Partial truth with critical omission -> MISLEADING_OR_CONTEXT_MISSING."""
    inv, sub, claim = await create_base_claim(
        db_session,
        claim_text="National unemployment reached 10%",
        subject="National unemployment",
        predicate="reached",
        obj="10%"
    )

    evidence = [
        EvidenceItem(
            evidence_id="labor-stats-01",
            source_id="bureau-labor-statistics",
            publisher="Bureau of Labor Statistics",
            content_or_passage="Report clarifies that youth unemployment specifically reached 10%, while total national unemployment baseline is 3.5%. The figure was misrepresented out of context.",
            source_type="OFFICIAL_DOCUMENT"
        )
    ]

    assessment = await ContextualClaimVerifier.verify_claim(db_session, claim.id, evidence_items=evidence)
    assert assessment.classification == AssessmentClassification.MISLEADING_OR_CONTEXT_MISSING.value
    assert "omitted" in assessment.primary_rationale.lower() or "context" in assessment.primary_rationale.lower()

@pytest.mark.asyncio
async def test_negation_inversion_detection(db_session: AsyncSession):
    """10. Negation inversion: Claim asserts resignation, evidence asserts did not resign -> CONTRADICTED."""
    inv, sub, claim = await create_base_claim(
        db_session,
        claim_text="Finance Minister resigned from office today",
        subject="Finance Minister",
        predicate="resigned",
        obj="from office today",
        polarity_state="AFFIRMATIVE_SURFACE_SYNTAX"
    )

    evidence = [
        EvidenceItem(
            evidence_id="gov-spox-01",
            source_id="official-spokesperson-briefing",
            publisher="Ministry Press Office",
            content_or_passage="Official briefing: The Finance Minister did not resign. Rumors claiming resignation are completely false and refuted.",
            source_type="OFFICIAL_DOCUMENT"
        )
    ]

    assessment = await ContextualClaimVerifier.verify_claim(db_session, claim.id, evidence_items=evidence)
    assert assessment.classification == AssessmentClassification.CONTRADICTED.value
    assert assessment.evidence_relations[0].relationship_type == EvidenceRelationshipType.CONTRADICTS.value

@pytest.mark.asyncio
async def test_attributed_statement_vs_direct_assertion(db_session: AsyncSession):
    """11. Preserves attribution scope without confusing speaker statement with objective truth."""
    inv, sub, claim = await create_base_claim(
        db_session,
        claim_text="Spokesperson stated that project funding was approved",
        subject="Spokesperson",
        predicate="stated",
        obj="that project funding was approved",
        is_attributed=True
    )

    evidence = [
        EvidenceItem(
            evidence_id="press-dispatch-01",
            source_id="wire-dispatch-01",
            publisher="National News Wire",
            content_or_passage="During yesterday's briefing, the Spokesperson stated that project funding was approved by unanimous vote.",
            source_type="NEWS_ARTICLE"
        )
    ]

    assessment = await ContextualClaimVerifier.verify_claim(db_session, claim.id, evidence_items=evidence)
    assert assessment.classification == AssessmentClassification.SUPPORTED.value
    assert "attributed statement" in assessment.evidence_relations[0].alignment_rationale.lower()

@pytest.mark.asyncio
async def test_telephoto_camera_gps_observational_signal(db_session: AsyncSession):
    """12. Camera GPS 65 km away on mountain -> observational distance signal, NOT a contradiction without corroborating context."""
    inv, sub, claim = await create_base_claim(
        db_session,
        claim_text="Cricket championship match held in Mumbai stadium",
        claimed_location="Mumbai",
        caption="Match action from Mumbai stadium"
    )

    # 65 km away from Mumbai centroid (e.g. scenic overlook / hill station)
    ext = ExtractionRecord(
        evidence_submission_id=sub.id,
        version=1,
        is_active=True,
        extractor_name="TestExtractor",
        extractor_version="1.0.0",
        technical_metadata={"gps": {"latitude": 18.75, "longitude": 73.40}}
    )
    db_session.add(ext)
    await db_session.commit()

    assessment = await ContextualClaimVerifier.verify_claim(db_session, claim.id)
    geo = assessment.geographical_analysis
    assert geo["is_observational_divergence_signal"] is True
    # Crucial Rule: NO universal threshold, camera GPS alone is NOT a contradiction without corroborating context
    assert geo["is_geographical_contradiction"] is False
    assert assessment.classification != AssessmentClassification.CONTRADICTED.value
    assert "telephoto" in geo["camera_vs_event_caveat"].lower()

@pytest.mark.asyncio
async def test_missing_all_metadata_graceful_handling(db_session: AsyncSession):
    """13. Stripped metadata file with zero EXIF and zero external hits -> INSUFFICIENT_EVIDENCE."""
    inv, sub, claim = await create_base_claim(
        db_session,
        claim_text="Random unverified claim with zero technical metadata",
        caption="Uncredited photo"
    )

    ext = ExtractionRecord(
        evidence_submission_id=sub.id,
        version=1,
        is_active=True,
        extractor_name="TestExtractor",
        extractor_version="1.0.0",
        technical_metadata={}  # Empty metadata
    )
    db_session.add(ext)

    evidence = [
        EvidenceItem(
            evidence_id="unrelated-01",
            source_id="unrelated-source",
            content_or_passage="Weather in Antarctica was extremely cold today with heavy blizzards.",
            source_type="NEWS_ARTICLE"
        )
    ]
    await db_session.commit()

    assessment = await ContextualClaimVerifier.verify_claim(db_session, claim.id, evidence_items=evidence)
    assert assessment.classification == AssessmentClassification.INSUFFICIENT_EVIDENCE.value

@pytest.mark.asyncio
async def test_multilingual_hindi_claim_english_evidence(db_session: AsyncSession):
    """14. Multilingual Hindi claim matched with English evidence report."""
    inv, sub, claim = await create_base_claim(
        db_session,
        claim_text="प्रधानमंत्री ने नई दिल्ली में मेट्रो परियोजना का उद्घाटन किया",
        normalized_claim="प्रधानमंत्री ने नई दिल्ली में मेट्रो परियोजना का उद्घाटन किया",
        subject="प्रधानमंत्री",
        predicate="उद्घाटन किया",
        obj="मेट्रो परियोजना",
        language="hi",
        claimed_location="New Delhi",
        extracted_entities={"locations": ["New Delhi"], "organizations": ["मेट्रो"]}
    )

    evidence = [
        EvidenceItem(
            evidence_id="eng-factcheck-01",
            source_id="pib-english-01",
            publisher="Press Information Bureau",
            content_or_passage="Prime Minister inaugurated the new Metro project in New Delhi today.",
            language="en",
            source_type="OFFICIAL_DOCUMENT"
        )
    ]

    assessment = await ContextualClaimVerifier.verify_claim(db_session, claim.id, evidence_items=evidence)
    assert assessment.classification == AssessmentClassification.SUPPORTED.value
    assert len(assessment.evidence_relations) == 1

@pytest.mark.asyncio
async def test_multilingual_telugu_claim_telugu_evidence(db_session: AsyncSession):
    """15. Multilingual Telugu claim matched with Telugu regional news report."""
    inv, sub, claim = await create_base_claim(
        db_session,
        claim_text="హైదరాబాద్‌లో కొత్త ఐటీ పాలసీని ప్రభుత్వం ప్రకటించింది",
        normalized_claim="హైదరాబాద్‌లో కొత్త ఐటీ పాలసీని ప్రభుత్వం ప్రకటించింది",
        subject="ప్రభుత్వం",
        predicate="ప్రకటించింది",
        obj="కొత్త ఐటీ పాలసీని",
        language="te",
        claimed_location="Hyderabad",
        extracted_entities={"locations": ["హైదరాబాద్"]}
    )

    evidence = [
        EvidenceItem(
            evidence_id="te-news-01",
            source_id="eenadu-01",
            publisher="Eenadu",
            content_or_passage="హైదరాబాద్‌లో ప్రభుత్వం కొత్త ఐటీ పాలసీని అధికారికంగా ప్రకటించింది.",
            language="te",
            source_type="NEWS_ARTICLE"
        )
    ]

    assessment = await ContextualClaimVerifier.verify_claim(db_session, claim.id, evidence_items=evidence)
    assert assessment.classification == AssessmentClassification.SUPPORTED.value
    assert "హైదరాబాద్" in assessment.evidence_relations[0].excerpt

@pytest.mark.asyncio
async def test_pipeline_automatic_verification_with_local_evidence(db_session: AsyncSession):
    """16. Pipeline automatically triggers contextual verification when historical media matches exist."""
    asset = MediaAsset(
        sha256_hash="pipeline-match-asset-hash",
        mime_type="image/jpeg",
        file_path="uploads/pipeline_match.jpg",
        file_size_bytes=2048
    )
    db_session.add(asset)
    await db_session.flush()

    inv, sub, claim = await create_base_claim(
        db_session,
        claim_text="Flooding in Mumbai suburb",
        media_asset=asset
    )

    # Seed historical media match
    match = MediaMatchRecord(
        source_evidence_id=sub.id,
        source_media_asset_id=asset.id,
        classification="EXACT_FILE_MATCH",
        method="TRUTHNET-PERCEPTUAL-HASH",
        disclaimer="Match test"
    )
    db_session.add(match)
    await db_session.commit()

    # Trigger pipeline method
    await pipeline_service._verify_claims_with_local_evidence(db_session, sub.id)

    # Verify ClaimAssessmentRecord was persisted
    stmt = select(ClaimAssessmentRecord).where(ClaimAssessmentRecord.claim_id == claim.id)
    res = await db_session.execute(stmt)
    assessment = res.scalars().first()
    assert assessment is not None
    assert assessment.evidence_submission_id == sub.id

@pytest.mark.asyncio
async def test_pipeline_isolation_on_verification_failure(db_session: AsyncSession):
    """17. Pipeline fault isolation: verification crash does NOT fail pipeline or claim extraction."""
    inv, sub, claim = await create_base_claim(db_session, claim_text="Fault isolation claim")

    with patch.object(ContextualClaimVerifier, "verify_claim", side_effect=RuntimeError("Simulated verifier failure")):
        # Must execute cleanly without raising exception
        await pipeline_service._verify_claims_with_local_evidence(db_session, sub.id)

@pytest.mark.asyncio
async def test_human_review_override_lifecycle(async_client: AsyncClient, db_session: AsyncSession):
    """18. Human review override: investigator updates status with audit notes."""
    inv, sub, claim = await create_base_claim(db_session, claim_text="Review lifecycle claim")

    assessment = await ContextualClaimVerifier.verify_claim(db_session, claim.id, evidence_items=[])
    assert assessment.human_review_status == HumanReviewStatus.UNREVIEWED.value

    # Submit review
    review_payload = {
        "status": "DISPUTED",
        "notes": "Investigator noted that external local witnesses dispute the report timing.",
        "reviewer_id": "investigator-42"
    }
    res = await async_client.post(
        f"/api/v1/claims/{claim.id}/assessment/{assessment.id}/review",
        json=review_payload
    )
    assert res.status_code == 200
    data = res.json()
    assert data["human_review_status"] == "DISPUTED"
    assert data["reviewed_by"] == "investigator-42"
    assert data["human_reviewed_at"] is not None

@pytest.mark.asyncio
async def test_re_verification_version_immutability(async_client: AsyncClient, db_session: AsyncSession):
    """19. Re-verification immutability: Version 2 created, Version 1 preserved as inactive with supersede reason."""
    inv, sub, claim = await create_base_claim(
        db_session,
        claim_text="Border agreement ratified by parliament",
        subject="Border agreement",
        predicate="ratified",
        obj="by parliament"
    )

    # Initial verification: Version 1 (UNVERIFIED)
    v1 = await ContextualClaimVerifier.verify_claim(db_session, claim.id, evidence_items=[])
    assert v1.version == 1
    assert v1.is_active is True

    # Re-verification with newly arrived evidence item
    new_evidence = [
        EvidenceItem(
            evidence_id="parliament-gazette-01",
            source_id="official-gazette",
            publisher="Official Gazette",
            content_or_passage="Parliament officially confirmed the border agreement was ratified by unanimous vote.",
            source_type="OFFICIAL_DOCUMENT"
        )
    ]
    v2 = await ContextualClaimVerifier.verify_claim(db_session, claim.id, evidence_items=new_evidence)
    assert v2.version == 2
    assert v2.is_active is True
    assert v2.classification == AssessmentClassification.SUPPORTED.value

    # Check version 1 is inactive
    re_v1 = (await db_session.execute(select(ClaimAssessmentRecord).where(ClaimAssessmentRecord.id == v1.id))).scalars().first()
    assert re_v1.is_active is False
    assert re_v1.supersede_reason == "REVERIFICATION_WITH_NEW_EVIDENCE"

    # Verify history endpoint
    hist_res = await async_client.get(f"/api/v1/claims/{claim.id}/assessment/history")
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert hist_data["total_versions"] == 2
    assert hist_data["active_assessment"]["version"] == 2

@pytest.mark.asyncio
async def test_source_dependency_marked_unknown(db_session: AsyncSession):
    """20. Multiple evidence items provided: source independence must be explicitly UNKNOWN, not claimed as corroboration."""
    inv, sub, claim = await create_base_claim(
        db_session,
        claim_text="Spacecraft successfully touched down on lunar south pole",
        subject="Spacecraft",
        predicate="touched down",
        obj="on lunar south pole"
    )

    evidence = [
        EvidenceItem(
            evidence_id="news-a",
            source_id="https://news-a.com/lunar-landing",
            publisher="News Agency Alpha",
            content_or_passage="Spacecraft successfully touched down on lunar south pole in historic mission.",
            source_type="NEWS_ARTICLE"
        ),
        EvidenceItem(
            evidence_id="news-b",
            source_id="https://news-b.com/lunar-landing",
            publisher="News Agency Beta",
            content_or_passage="Officials cheered as spacecraft successfully touched down on lunar south pole.",
            source_type="NEWS_ARTICLE"
        ),
        EvidenceItem(
            evidence_id="news-c",
            source_id="https://news-c.com/lunar-landing",
            publisher="News Agency Gamma",
            content_or_passage="Live broadcast showed spacecraft touched down on lunar south pole today.",
            source_type="NEWS_ARTICLE"
        )
    ]

    assessment = await ContextualClaimVerifier.verify_claim(db_session, claim.id, evidence_items=evidence)
    assert assessment.classification == AssessmentClassification.SUPPORTED.value
    assert len(assessment.evidence_relations) == 3

    # Strictly check that every relation is marked UNKNOWN
    for rel in assessment.evidence_relations:
        assert rel.source_independence_status == "UNKNOWN"
    assert "source independence is explicitly marked unknown" in assessment.primary_rationale.lower()
