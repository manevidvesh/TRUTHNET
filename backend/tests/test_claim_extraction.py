import pytest
import hashlib
from datetime import datetime, timezone
from sqlalchemy import select
from app.models.investigation import Investigation
from app.models.evidence import EvidenceSubmission
from app.models.claim import ClaimRecord
from app.claims.extractor import claim_extractor
from app.claims.language import language_detector
from app.claims.normalizer import claim_normalizer
from app.services.pipeline import pipeline_service

# ---------------------------------------------------------------------------
# 1. SCOPE-AWARE CONSERVATIVE NEGATION TESTS
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scope_aware_adversarial_negations():
    """
    Verifies that complex, modal, epistemic, and nested speech-act negations
    are marked UNRESOLVED_POLARITY rather than silently inverted, while direct
    clausal negation is marked RESOLVED_NEGATIVE.
    """
    inv_id = "test-inv-neg"
    sub_id = "test-sub-neg"

    # Case 1: Direct single clausal negation -> RESOLVED_NEGATIVE
    t1 = "The ministry did not approve the vaccine."
    c1 = claim_extractor.extract_claims_from_text(t1, inv_id, sub_id)[0]
    assert c1["polarity_state"] == "RESOLVED_NEGATIVE"
    assert c1["qualifiers"]["negation"]["polarity_method"] == "DIRECT_CLAUSAL_NEGATION"
    assert len(c1["qualifiers"]["negation"]["markers"]) == 1
    assert t1[c1["evidence_span_start"]:c1["evidence_span_end"]] == c1["claim_text"]

    # Case 2: Nested speech-act negation -> UNRESOLVED_POLARITY
    t2 = "The ministry did not deny that it approved the vaccine."
    c2 = claim_extractor.extract_claims_from_text(t2, inv_id, sub_id)[0]
    assert c2["polarity_state"] == "UNRESOLVED_POLARITY"
    assert c2["qualifiers"]["negation"]["polarity_method"] == "NESTED_SPEECH_ACT_NEGATION"
    assert "Nested speech-act negation" in c2["qualifiers"]["negation"]["note"]

    # Case 3: Modal litotes negation -> UNRESOLVED_POLARITY
    t3 = "It is not impossible that the ministry approved the vaccine."
    c3 = claim_extractor.extract_claims_from_text(t3, inv_id, sub_id)[0]
    assert c3["polarity_state"] == "UNRESOLVED_POLARITY"
    assert c3["qualifiers"]["negation"]["polarity_method"] == "MODAL_LITOTES_NEGATION"
    assert "Modal double negation" in c3["qualifiers"]["negation"]["note"]

    # Case 4: Cross-clause speech act negation -> UNRESOLVED_POLARITY
    t4 = "The ministry never said it did not approve the vaccine."
    c4 = claim_extractor.extract_claims_from_text(t4, inv_id, sub_id)[0]
    assert c4["polarity_state"] == "UNRESOLVED_POLARITY"
    assert c4["qualifiers"]["negation"]["polarity_method"] == "NESTED_SPEECH_ACT_NEGATION"

    # Case 5: Epistemic absence of evidence -> UNRESOLVED_POLARITY
    t5 = "No evidence suggests the vaccine was not approved."
    c5 = claim_extractor.extract_claims_from_text(t5, inv_id, sub_id)[0]
    assert c5["polarity_state"] == "UNRESOLVED_POLARITY"
    assert c5["qualifiers"]["negation"]["polarity_method"] == "EPISTEMIC_NEGATION"
    assert "Epistemic absence of evidence" in c5["qualifiers"]["negation"]["note"]

# ---------------------------------------------------------------------------
# 2. SUBJECTIVE FRAMING VS. FACTUAL SUB-CLAIMS
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_subjective_framing_vs_factual_subclaims():
    """
    Verifies that subjective framing is separated from independently verifiable assertions,
    and pure opinions without factual substance are rejected as NON_FACTUAL_STATEMENT.
    """
    inv_id = "test-inv-frame"
    sub_id = "test-sub-frame"

    # Case A: Subjective framing with verifiable financial sub-claim
    t_a = "In my opinion, the government spent ₹500 crore on the project."
    claims_a = claim_extractor.extract_claims_from_text(t_a, inv_id, sub_id)
    assert len(claims_a) == 1
    ca = claims_a[0]
    assert ca["is_factual_assertion"] is True
    assert ca["extraction_state"] in ("EXTRACTED_CLAIM_CANDIDATE", "STRUCTURED_PROPOSITION")
    assert "subjective_framing" in ca["qualifiers"]
    assert ca["qualifiers"]["subjective_framing"]["framing_marker"].lower() == "in my opinion"
    qty_matches = [q["raw"] for q in ca["extracted_entities"]["quantities"]]
    assert any("500 crore" in q for q in qty_matches)
    assert t_a[ca["evidence_span_start"]:ca["evidence_span_end"]] == ca["claim_text"]

    # Case B: Belief framing with factual temporal resignation
    t_b = "I believe the minister resigned yesterday."
    claims_b = claim_extractor.extract_claims_from_text(t_b, inv_id, sub_id)
    assert len(claims_b) == 1
    cb = claims_b[0]
    assert cb["is_factual_assertion"] is True
    assert cb["qualifiers"]["subjective_framing"]["framing_marker"].lower() == "i believe"
    assert t_b[cb["evidence_span_start"]:cb["evidence_span_end"]] == cb["claim_text"]

    # Case C: Evaluative main clause + factual subordinate clause
    t_c = "This is the worst decision because 20 people died."
    claims_c = claim_extractor.extract_claims_from_text(t_c, inv_id, sub_id)
    assert len(claims_c) == 1
    cc = claims_c[0]
    assert cc["is_factual_assertion"] is True
    assert "20 people died" in cc["claim_text"]
    assert cc["qualifiers"]["subjective_framing"]["evaluative_main_clause"] == "This is the worst decision"
    assert t_c[cc["evidence_span_start"]:cc["evidence_span_end"]] == cc["claim_text"]

    # Case D: Pure opinion without factual substance -> NON_FACTUAL_STATEMENT
    t_d = "In my opinion, this is the worst decision ever."
    claims_d = claim_extractor.extract_claims_from_text(t_d, inv_id, sub_id)
    assert len(claims_d) == 1
    cd = claims_d[0]
    assert cd["is_factual_assertion"] is False
    assert cd["extraction_state"] == "NON_FACTUAL_STATEMENT"
    assert t_d[cd["evidence_span_start"]:cd["evidence_span_end"]] == cd["claim_text"]

# ---------------------------------------------------------------------------
# 3. ATTRIBUTION PRESERVATION ON EMBEDDED PROPOSITION
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_attribution_preservation():
    """
    Verifies that an attributed assertion is explicitly distinguished from an un-attributed fact,
    and speaker attribution metadata survives extraction with spans.
    """
    inv_id = "test-inv-attr"
    sub_id = "test-sub-attr"

    # Attributed statement
    t_attr = "Senator Smith claimed that the Health Ministry did not approve the vaccine."
    c_attr = claim_extractor.extract_claims_from_text(t_attr, inv_id, sub_id)[0]
    assert c_attr["is_attributed_assertion"] is True
    assert "attribution" in c_attr["qualifiers"]
    attr_info = c_attr["qualifiers"]["attribution"]
    assert attr_info["speaker"] == "Senator Smith"
    assert attr_info["attribution_verb"].lower() == "claimed"
    assert "Health Ministry did not approve the vaccine" in attr_info["attributed_proposition"]

    # Direct assertion (un-attributed)
    t_direct = "The Health Ministry did not approve the vaccine."
    c_direct = claim_extractor.extract_claims_from_text(t_direct, inv_id, sub_id)[0]
    assert c_direct["is_attributed_assertion"] is False
    assert c_direct["qualifiers"] is None or "attribution" not in c_direct["qualifiers"]

# ---------------------------------------------------------------------------
# 4. MULTILINGUAL EXTRACTION-STATE SEMANTICS (HINDI & TELUGU)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_multilingual_hindi_and_telugu_extraction_states():
    """
    Verifies that Hindi and Telugu factual sentences are classified as EXTRACTED_CLAIM_CANDIDATE
    rather than claiming STRUCTURED_PROPOSITION, because semantic dependency parsing is not supported.
    Verifies subject/predicate are None and uncertainty documents UNSUPPORTED_LANGUAGE_PARSER.
    """
    inv_id = "test-inv-multi"
    sub_id = "test-sub-multi"

    # Hindi
    t_hi = "स्वास्थ्य मंत्रालय ने नई गाइडलाइंस जारी कीं।"
    c_hi = claim_extractor.extract_claims_from_text(t_hi, inv_id, sub_id)[0]
    assert c_hi["language"] == "hi"
    assert c_hi["extraction_state"] == "EXTRACTED_CLAIM_CANDIDATE"
    assert c_hi["subject"] is None
    assert c_hi["predicate"] is None
    assert c_hi["object"] is None
    assert "UNSUPPORTED_LANGUAGE_PARSER" in c_hi["uncertainty_notes"]
    assert c_hi["is_factual_assertion"] is True
    assert t_hi[c_hi["evidence_span_start"]:c_hi["evidence_span_end"]] == t_hi

    # Telugu
    t_te = "హైదరాబాద్‌లో భారీ వర్షం కారణంగా పాఠశాలలకు సెలవు ప్రకటించారు."
    c_te = claim_extractor.extract_claims_from_text(t_te, inv_id, sub_id)[0]
    assert c_te["language"] == "te"
    assert c_te["extraction_state"] == "EXTRACTED_CLAIM_CANDIDATE"
    assert c_te["subject"] is None
    assert c_te["predicate"] is None
    assert c_te["object"] is None
    assert "UNSUPPORTED_LANGUAGE_PARSER" in c_te["uncertainty_notes"]
    assert c_te["is_factual_assertion"] is True
    assert t_te[c_te["evidence_span_start"]:c_te["evidence_span_end"]] == t_te

# ---------------------------------------------------------------------------
# 5. SPAN INTEGRITY & PROVENANCE ACROSS SCRIPT RANGES
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_provenance_and_span_integrity():
    """
    Verifies that source_text_hash corresponds to the SHA-256 of original text,
    and start_char/end_char accurately slice the exact verbatim text for English, Hindi, and Telugu.
    """
    inv_id = "test-inv-prov"
    sub_id = "test-sub-prov"

    samples = [
        "The bridge collapsed on Tuesday due to heavy rain.",
        "स्वास्थ्य मंत्रालय ने नई गाइडलाइंस जारी कीं।",
        "హైదరాబాద్‌లో భారీ వర్షం కారణంగా పాఠశాలలకు సెలవు ప్రకటించారు.",
        "Breaking news: Opposition demanded immediate resignation of the minister."
    ]

    for raw in samples:
        expected_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        claims = claim_extractor.extract_claims_from_text(raw, inv_id, sub_id)
        assert len(claims) >= 1
        for c in claims:
            assert c["source_text_hash"] == expected_hash
            start = c["evidence_span_start"]
            end = c["evidence_span_end"]
            assert raw[start:end] == c["claim_text"]

# ---------------------------------------------------------------------------
# 6. PIPELINE IDEMPOTENCY AND REPROCESSING TESTS
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pipeline_idempotency_and_versioning(db_session):
    """
    Verifies that retrying or reprocessing an evidence item does NOT create duplicate active claims,
    preserves historical claim versions, and marks prior claims is_active=False.
    """
    inv = Investigation(title="Idempotency Test Investigation", priority="MEDIUM")
    db_session.add(inv)
    await db_session.flush()

    sub = EvidenceSubmission(
        investigation_id=inv.id,
        submission_type="TEXT",
        caption="Breaking news: Government announced 10 crore relief fund.",
        raw_text="The bridge collapsed on Tuesday.",
        language="en"
    )
    db_session.add(sub)
    await db_session.commit()

    # Pass 1: Initial Processing
    success_1 = await pipeline_service.process_evidence_item(sub.id, session_factory=lambda: db_session)
    assert success_1 is True

    # Check Pass 1 claims in DB
    res_1 = await db_session.execute(
        select(ClaimRecord).where(ClaimRecord.evidence_submission_id == sub.id)
    )
    claims_pass_1 = list(res_1.scalars().all())
    assert len(claims_pass_1) == 2
    for c in claims_pass_1:
        assert c.version == 1
        assert c.is_active is True

    # Pass 2: Retry / Reprocessing (simulating worker restart or user reprocess)
    success_2 = await pipeline_service.process_evidence_item(sub.id, session_factory=lambda: db_session)
    assert success_2 is True

    # Check DB state after reprocessing
    res_2 = await db_session.execute(
        select(ClaimRecord).where(ClaimRecord.evidence_submission_id == sub.id)
    )
    all_claims = list(res_2.scalars().all())
    assert len(all_claims) == 4  # 2 historical version 1 + 2 active version 2

    active_claims = [c for c in all_claims if c.is_active is True]
    inactive_claims = [c for c in all_claims if c.is_active is False]

    assert len(active_claims) == 2  # Active claims are NOT duplicated!
    assert len(inactive_claims) == 2

    for c in active_claims:
        assert c.version == 2
    for c in inactive_claims:
        assert c.version == 1

# ---------------------------------------------------------------------------
# 7. DATE AND LOCATION PROVENANCE AUDITING
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_date_and_location_provenance_audit():
    """
    Verifies that relative dates without timezone-aware timestamps remain unanchored,
    and gazetteer centroids are explicitly flagged as reference centroids, not incident GPS.
    """
    # A. Relative date without reference timestamp -> RELATIVE_DATE_UNRESOLVED
    ent_no_ref = claim_normalizer.parse_entities("The incident occurred yesterday in New Delhi.", reference_timestamp=None)
    date_ent = ent_no_ref["dates"][0]
    assert date_ent["raw"] == "yesterday"
    assert date_ent["type"] == "RELATIVE_DATE_UNRESOLVED"
    assert date_ent["normalized"] is None
    assert date_ent["is_anchored"] is False
    assert "cannot be anchored" in date_ent["caveat"]

    # B. Relative date WITH timezone-aware reference timestamp -> anchored estimate
    ref_dt = datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc)
    ent_with_ref = claim_normalizer.parse_entities("The incident occurred yesterday in New Delhi.", reference_timestamp=ref_dt)
    date_anchored = ent_with_ref["dates"][0]
    assert date_anchored["type"] == "RELATIVE_DATE"
    assert date_anchored["normalized"] == "2026-03-14"
    assert date_anchored["is_anchored"] is True

    # C. Location Centroid Audit
    loc_ent = ent_no_ref["locations"][0]
    assert loc_ent["canonical_name"] == "New Delhi"
    assert loc_ent["is_reference_centroid"] is True
    assert loc_ent["reference_centroid_lat"] == 28.6139
    assert loc_ent["reference_centroid_lon"] == 77.2090
    assert "NOT incident or crime scene location" in loc_ent["centroid_caveat"]

# ---------------------------------------------------------------------------
# 8. STRUCTURAL, CAUSAL & AMBIGUOUS SENTENCE TESTS
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_causal_assertions():
    """Verifies cause-and-effect relationship representation."""
    inv_id = "test-inv-causal"
    sub_id = "test-sub-causal"

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
    """Verifies compound sentences are decomposed into discrete atomic propositions with distinct spans."""
    inv_id = "test-inv-multi-prop"
    sub_id = "test-sub-multi-prop"

    text = "The bridge collapsed on Tuesday, and the governor declared a state of emergency."
    claims = claim_extractor.extract_claims_from_text(text, inv_id, sub_id)
    assert len(claims) == 2

    c1 = claims[0]
    c2 = claims[1]
    assert "bridge collapsed" in c1["claim_text"].lower()
    assert "governor declared" in c2["claim_text"].lower()
    assert text[c1["evidence_span_start"]:c1["evidence_span_end"]] == c1["claim_text"]
    assert text[c2["evidence_span_start"]:c2["evidence_span_end"]] == c2["claim_text"]
    assert c1["evidence_span_end"] <= c2["evidence_span_start"]

@pytest.mark.asyncio
async def test_ambiguous_sentence_structure():
    """Verifies ambiguous structures are recorded as UNRESOLVED_STATEMENT without forcing artificial SPO."""
    inv_id = "test-inv-ambig"
    sub_id = "test-sub-ambig"

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
    inv_id = "test-inv-hing"
    sub_id = "test-sub-hing"

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
async def test_ocr_noise_resilience():
    """Verifies that noisy OCR extractions preserve exact character offsets."""
    inv_id = "test-inv-ocr"
    sub_id = "test-sub-ocr"

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
    inv_id = "test-inv-frag"
    sub_id = "test-sub-frag"

    text = "...because the minister was..."
    claims = claim_extractor.extract_claims_from_text(text, inv_id, sub_id, source_modality="TRANSCRIPT")
    assert len(claims) == 1
    c = claims[0]
    assert c["extraction_state"] == "PARTIAL_EXTRACTION"
    assert c["qualifiers"]["fragmentary"] is True
    assert text[c["evidence_span_start"]:c["evidence_span_end"]] == c["claim_text"]

@pytest.mark.asyncio
async def test_evidence_span_correctness_after_normalization():
    """Ensures that evidence spans strictly reference original text even when punctuation or spaces vary."""
    inv_id = "test-inv-norm"
    sub_id = "test-sub-norm"

    raw_text = '  "The bridge collapsed on Tuesday."   Government announced 10 crore relief.  '
    claims = claim_extractor.extract_claims_from_text(raw_text, inv_id, sub_id)
    assert len(claims) >= 2
    for c in claims:
        start = c["evidence_span_start"]
        end = c["evidence_span_end"]
        assert raw_text[start:end] == c["claim_text"]
