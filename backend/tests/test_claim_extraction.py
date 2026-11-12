import pytest
from app.models.investigation import Investigation
from app.models.evidence import EvidenceSubmission
from app.models.claim import ClaimRecord
from app.claims.extractor import claim_extractor
from app.claims.language import language_detector
from app.claims.normalizer import claim_normalizer
from app.services.pipeline import pipeline_service

@pytest.mark.asyncio
async def test_negation_and_double_negation():
    """Verifies that single negation and double negation are accurately distinguished."""
    inv_id = "test-inv-1"
    sub_id = "test-sub-1"

    # Single negation
    text_single = "The Health Ministry did not approve the experimental vaccine."
    claims_single = claim_extractor.extract_claims_from_text(text_single, inv_id, sub_id)
    assert len(claims_single) == 1
    c1 = claims_single[0]
    assert c1["qualifiers"] is not None
    assert c1["qualifiers"]["negation"]["is_negated"] is True
    assert c1["qualifiers"]["negation"]["has_double_negation"] is False
    assert text_single[c1["evidence_span_start"]:c1["evidence_span_end"]] == c1["claim_text"]

    # Double negation
    text_double = "It is not true that the ministry did not approve the experimental vaccine."
    claims_double = claim_extractor.extract_claims_from_text(text_double, inv_id, sub_id)
    assert len(claims_double) == 1
    c2 = claims_double[0]
    assert c2["qualifiers"] is not None
    assert c2["qualifiers"]["negation"]["is_negated"] is False
    assert c2["qualifiers"]["negation"]["has_double_negation"] is True
    assert text_double[c2["evidence_span_start"]:c2["evidence_span_end"]] == c2["claim_text"]

@pytest.mark.asyncio
async def test_speaker_attribution():
    """Verifies that attribution source and verb are decoupled from the proposition."""
    inv_id = "test-inv-1"
    sub_id = "test-sub-1"

    text = "Senator Smith claimed that the dam collapsed on Monday."
    claims = claim_extractor.extract_claims_from_text(text, inv_id, sub_id)
    assert len(claims) == 1
    c = claims[0]
    assert c["qualifiers"] is not None
    assert "attribution" in c["qualifiers"]
    assert c["qualifiers"]["attribution"]["speaker"] == "Senator Smith"
    assert c["qualifiers"]["attribution"]["verb"].lower() == "claimed"
    assert text[c["evidence_span_start"]:c["evidence_span_end"]] == c["claim_text"]

@pytest.mark.asyncio
async def test_causal_assertions():
    """Verifies cause-and-effect relationship representation."""
    inv_id = "test-inv-1"
    sub_id = "test-sub-1"

    text = "The dam breach caused massive flooding in District 4."
    claims = claim_extractor.extract_claims_from_text(text, inv_id, sub_id)
    assert len(claims) == 1
    c = claims[0]
    assert c["qualifiers"] is not None
    assert "causal_relation" in c["qualifiers"]
    assert "dam breach" in c["qualifiers"]["causal_relation"]["cause"].lower()
    assert "massive flooding" in c["qualifiers"]["causal_relation"]["effect"].lower()
    assert text[c["evidence_span_start"]:c["evidence_span_end"]] == c["claim_text"]

@pytest.mark.asyncio
async def test_multiple_propositions_in_one_sentence():
    """Verifies that compound sentences are decomposed into discrete atomic propositions with distinct spans."""
    inv_id = "test-inv-1"
    sub_id = "test-sub-1"

    text = "The bridge collapsed on Tuesday, and the governor declared a state of emergency."
    claims = claim_extractor.extract_claims_from_text(text, inv_id, sub_id)
    assert len(claims) == 2

    c1 = claims[0]
    c2 = claims[1]
    assert "bridge collapsed" in c1["claim_text"].lower()
    assert "governor declared" in c2["claim_text"].lower()
    # Check exact offsets
    assert text[c1["evidence_span_start"]:c1["evidence_span_end"]] == c1["claim_text"]
    assert text[c2["evidence_span_start"]:c2["evidence_span_end"]] == c2["claim_text"]
    assert c1["evidence_span_end"] <= c2["evidence_span_start"]

@pytest.mark.asyncio
async def test_ambiguous_sentence_structure():
    """Verifies ambiguous structures are recorded as UNRESOLVED_STATEMENT without forcing artificial SPO."""
    inv_id = "test-inv-1"
    sub_id = "test-sub-1"

    text = "Flying planes can be dangerous during storms."
    claims = claim_extractor.extract_claims_from_text(text, inv_id, sub_id)
    assert len(claims) == 1
    c = claims[0]
    assert c["extraction_state"] == "UNRESOLVED_STATEMENT"
    assert c["subject"] is None
    assert c["predicate"] is None
    assert c["uncertainty_notes"] is not None
    assert text[c["evidence_span_start"]:c["evidence_span_end"]] == c["claim_text"]

@pytest.mark.asyncio
async def test_mixed_language_and_transliteration():
    """Verifies code-switching and Romanized transliteration (Hinglish) detection."""
    inv_id = "test-inv-1"
    sub_id = "test-sub-1"

    # Hinglish transliteration
    text_hinglish = "Aaj Delhi me new policy announce hui, sab log discuss kar rahe hai."
    claims_h = claim_extractor.extract_claims_from_text(text_hinglish, inv_id, sub_id)
    assert len(claims_h) == 1
    ch = claims_h[0]
    assert ch["language"] == "MIXED"
    assert ch["language_detection_method"] == "transliteration_heuristic"

    # Mixed scripts
    text_mixed = "This is English with Devanagari स्वास्थ्य mixed together."
    res = language_detector.detect(text_mixed)
    assert res.language == "MIXED"
    assert res.detection_method == "mixed_script_detection"

@pytest.mark.asyncio
async def test_multilingual_hindi_and_telugu_text():
    """Verifies genuine Hindi (Devanagari) and Telugu text preservation and detection."""
    inv_id = "test-inv-1"
    sub_id = "test-sub-1"

    # Hindi
    text_hi = "स्वास्थ्य मंत्रालय ने नई गाइडलाइंस जारी कीं।"
    claims_hi = claim_extractor.extract_claims_from_text(text_hi, inv_id, sub_id)
    assert len(claims_hi) == 1
    chi = claims_hi[0]
    assert chi["language"] == "hi"
    assert chi["claim_text"] == text_hi
    assert text_hi[chi["evidence_span_start"]:chi["evidence_span_end"]] == text_hi
    assert chi["is_factual_assertion"] is True

    # Telugu
    text_te = "హైదరాబాద్‌లో భారీ వర్షం కారణంగా పాఠశాలలకు సెలవు ప్రకటించారు."
    claims_te = claim_extractor.extract_claims_from_text(text_te, inv_id, sub_id)
    assert len(claims_te) == 1
    cte = claims_te[0]
    assert cte["language"] == "te"
    assert cte["claim_text"] == text_te
    assert text_te[cte["evidence_span_start"]:cte["evidence_span_end"]] == text_te
    assert cte["is_factual_assertion"] is True

@pytest.mark.asyncio
async def test_ocr_noise_resilience():
    """Verifies that noisy OCR extractions preserve exact character offsets."""
    inv_id = "test-inv-1"
    sub_id = "test-sub-1"

    text_ocr = "Teh g0vernment has ann0unced relief measures for flood victims."
    claims = claim_extractor.extract_claims_from_text(text_ocr, inv_id, sub_id, source_modality="OCR_EXTRACTED")
    assert len(claims) == 1
    c = claims[0]
    assert c["source_modality"] == "OCR_EXTRACTED"
    assert text_ocr[c["evidence_span_start"]:c["evidence_span_end"]] == c["claim_text"]

@pytest.mark.asyncio
async def test_short_text_threshold():
    """Verifies that short text or symbols do not return spurious language detection."""
    res_short = language_detector.detect("Hi")
    assert res_short.language == "UNKNOWN"
    assert res_short.detection_method == "short_text_threshold"
    assert res_short.detector_probability is None

    res_symbols = language_detector.detect("12345 67890 ???")
    assert res_symbols.language == "UNKNOWN"
    assert res_symbols.detection_method == "no_alphabetic_features"
    assert res_symbols.detector_probability is None

@pytest.mark.asyncio
async def test_incomplete_transcript_fragments():
    """Verifies abrupt cutoff transcripts are tagged as PARTIAL_EXTRACTION."""
    inv_id = "test-inv-1"
    sub_id = "test-sub-1"

    text = "...because the minister was..."
    claims = claim_extractor.extract_claims_from_text(text, inv_id, sub_id, source_modality="TRANSCRIPT")
    assert len(claims) == 1
    c = claims[0]
    assert c["extraction_state"] == "PARTIAL_EXTRACTION"
    assert c["qualifiers"]["fragmentary"] is True
    assert text[c["evidence_span_start"]:c["evidence_span_end"]] == c["claim_text"]

@pytest.mark.asyncio
async def test_non_factual_opinions_and_rhetoric():
    """Verifies subjective opinions and questions are classified as NON_FACTUAL_STATEMENT."""
    inv_id = "test-inv-1"
    sub_id = "test-sub-1"

    opinions = [
        "In my opinion this is the worst decision ever made.",
        "Why is the government hiding the truth?",
        "Shame on everyone involved in this scandal!"
    ]
    for op in opinions:
        claims = claim_extractor.extract_claims_from_text(op, inv_id, sub_id)
        assert len(claims) == 1
        c = claims[0]
        assert c["is_factual_assertion"] is False
        assert c["extraction_state"] == "NON_FACTUAL_STATEMENT"
        assert op[c["evidence_span_start"]:c["evidence_span_end"]] == c["claim_text"]

@pytest.mark.asyncio
async def test_evidence_span_correctness_after_normalization():
    """Ensures that evidence spans strictly reference original text even when punctuation or spaces vary."""
    inv_id = "test-inv-1"
    sub_id = "test-sub-1"

    raw_text = '  "The bridge collapsed on Tuesday."   Government announced 10 crore relief.  '
    claims = claim_extractor.extract_claims_from_text(raw_text, inv_id, sub_id)
    assert len(claims) >= 2
    for c in claims:
        # Crucial invariant: raw slice matches claim_text
        start = c["evidence_span_start"]
        end = c["evidence_span_end"]
        assert raw_text[start:end] == c["claim_text"]

@pytest.mark.asyncio
async def test_end_to_end_pipeline_claim_persistence(db_session):
    """
    Tests full pipeline integration: ingests a TEXT submission with caption and raw text,
    runs PipelineService, and verifies that ClaimRecords are persisted in SQLite WAL and queryable.
    """
    inv = Investigation(title="Test Claim Investigation", priority="HIGH")
    db_session.add(inv)
    await db_session.flush()

    sub = EvidenceSubmission(
        investigation_id=inv.id,
        submission_type="TEXT",
        caption="Breaking news: Government announced 10 crore relief fund for flood victims.",
        raw_text="The bridge collapsed on Tuesday due to heavy rainfall.",
        language="en"
    )
    db_session.add(sub)
    await db_session.commit()

    # Process submission through pipeline
    success = await pipeline_service.process_evidence_item(sub.id, session_factory=lambda: db_session)
    assert success is True

    # Query persisted claims from DB
    from sqlalchemy import select
    result = await db_session.execute(
        select(ClaimRecord).where(ClaimRecord.evidence_submission_id == sub.id)
    )
    persisted_claims = list(result.scalars().all())

    # We expect at least 2 claims (1 from caption, 1 from raw_text)
    assert len(persisted_claims) >= 2
    modalities = {c.source_modality for c in persisted_claims}
    assert "CAPTION" in modalities
    assert "RAW_TEXT" in modalities

    for claim in persisted_claims:
        assert claim.investigation_id == inv.id
        assert claim.evidence_submission_id == sub.id
        assert claim.source_text_hash is not None
        assert claim.evidence_span_start >= 0
        assert claim.evidence_span_end > claim.evidence_span_start
        assert claim.extraction_state in (
            "EXTRACTED_CLAIM_CANDIDATE",
            "STRUCTURED_PROPOSITION",
            "PARTIAL_EXTRACTION"
        )
