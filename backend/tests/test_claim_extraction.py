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
from app.claims.offsets import codepoint_to_utf16_offsets, utf16_to_codepoint_offsets
from app.services.pipeline import pipeline_service

# ---------------------------------------------------------------------------
# 1. SCOPE-AWARE CONSERVATIVE NEGATION & UNSUPPORTED LANGUAGE POLARITY
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

@pytest.mark.asyncio
async def test_unsupported_language_polarity_semantics():
    """
    Verifies that Hindi and Telugu claims do NOT report affirmative polarity merely
    because English negation was absent. They report NOT_ANALYZED with explicit caveats.
    """
    inv_id = "test-inv-indic"
    sub_id = "test-sub-indic"

    # Hindi affirmative-looking text
    t_hi = "स्वास्थ्य मंत्रालय ने नई गाइडलाइंस जारी कीं।"
    c_hi = claim_extractor.extract_claims_from_text(t_hi, inv_id, sub_id)[0]
    assert c_hi["polarity_state"] == "NOT_ANALYZED"
    assert c_hi["qualifiers"]["negation"]["polarity_method"] == "UNSUPPORTED_LANGUAGE_POLARITY"
    assert "Linguistic polarity not analyzed" in c_hi["qualifiers"]["negation"]["note"]

    # Hindi text with negation marker
    t_hi_neg = "स्वास्थ्य मंत्रालय ने प्रस्ताव को स्वीकार नहीं किया।"
    c_hi_neg = claim_extractor.extract_claims_from_text(t_hi_neg, inv_id, sub_id)[0]
    assert c_hi_neg["polarity_state"] == "NOT_ANALYZED"
    assert len(c_hi_neg["qualifiers"]["negation"]["markers"]) >= 1
    assert any("नहीं" in m["marker"] for m in c_hi_neg["qualifiers"]["negation"]["markers"])

    # Telugu affirmative-looking text
    t_te = "హైదరాబాద్‌లో భారీ వర్షం కారణంగా పాఠశాలలకు సెలవు ప్రకటించారు."
    c_te = claim_extractor.extract_claims_from_text(t_te, inv_id, sub_id)[0]
    assert c_te["polarity_state"] == "NOT_ANALYZED"
    assert c_te["qualifiers"]["negation"]["polarity_method"] == "UNSUPPORTED_LANGUAGE_POLARITY"

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
async def test_attribution_representation_integrity():
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
    assert attr_info["speaker_span"] == [0, 13]
    assert attr_info["attribution_verb"] == "claimed"
    assert attr_info["verb_span"] == [14, 21]
    assert attr_info["reporting_clause"] == "Senator Smith claimed that"
    assert "Health Ministry did not approve the vaccine" in attr_info["attributed_proposition"]
    assert attr_info["epistemological_status"] == "ATTRIBUTED_REPORTING_STATEMENT"
    assert "NOT an independently established or verified fact" in attr_info["disclaimer"]

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
# 5. RETRY VS. DELIBERATE REPROCESSING IDEMPOTENCY
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pipeline_retry_vs_deliberate_reprocessing(db_session):
    """
    Verifies that:
    1. Pipeline retries with identical text DO NOT create duplicate claim records or bump version.
    2. Deliberate reprocessing (force_reprocess=True) increments version, marks prior claims inactive,
       and records the reprocess reason.
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

    # Pass 2: Pipeline Retry (e.g. worker restarted, re-running on same submission)
    success_2 = await pipeline_service.process_evidence_item(
        sub.id, session_factory=lambda: db_session, force_reprocess=False
    )
    assert success_2 is True

    # Claims count MUST BE EXACTLY 2 (Retry was 100% idempotent!)
    res_2 = await db_session.execute(
        select(ClaimRecord).where(ClaimRecord.evidence_submission_id == sub.id)
    )
    claims_after_retry = list(res_2.scalars().all())
    assert len(claims_after_retry) == 2  # ZERO duplicate records created!
    for c in claims_after_retry:
        assert c.version == 1
        assert c.is_active is True

    # Pass 3: Deliberate Reprocessing (explicit request)
    success_3 = await pipeline_service.process_evidence_item(
        sub.id, session_factory=lambda: db_session, force_reprocess=True, reprocess_reason="CONFIG_UPDATED"
    )
    assert success_3 is True

    res_3 = await db_session.execute(
        select(ClaimRecord).where(ClaimRecord.evidence_submission_id == sub.id)
    )
    all_claims = list(res_3.scalars().all())
    assert len(all_claims) == 4  # 2 historical inactive v1 + 2 active v2

    active_claims = [c for c in all_claims if c.is_active is True]
    inactive_claims = [c for c in all_claims if c.is_active is False]

    assert len(active_claims) == 2
    assert len(inactive_claims) == 2

    for c in active_claims:
        assert c.version == 2
        assert "CONFIG_UPDATED" in (c.uncertainty_notes or "")
    for c in inactive_claims:
        assert c.version == 1

@pytest.mark.asyncio
async def test_failed_replacement_extraction_preserves_active_claims(db_session, monkeypatch):
    """
    Verifies that a failure during replacement extraction (deliberate reprocessing)
    does not leave the submission without valid active claims. Prior active claims
    remain active.
    """
    inv = Investigation(title="Failure Safety Investigation", priority="LOW")
    db_session.add(inv)
    await db_session.flush()

    sub = EvidenceSubmission(
        investigation_id=inv.id,
        submission_type="TEXT",
        caption="Breaking news: Government announced relief fund.",
        raw_text="The bridge collapsed on Tuesday.",
        language="en"
    )
    db_session.add(sub)
    await db_session.commit()

    # Pass 1: Initial extraction succeeds
    success_1 = await pipeline_service.process_evidence_item(sub.id, session_factory=lambda: db_session)
    assert success_1 is True

    res_1 = await db_session.execute(
        select(ClaimRecord).where(ClaimRecord.evidence_submission_id == sub.id, ClaimRecord.is_active == True)
    )
    v1_claims = list(res_1.scalars().all())
    assert len(v1_claims) == 2
    assert all(c.version == 1 for c in v1_claims)

    # Mock extract_claims_from_text to simulate unexpected failure during reprocessing
    def mock_fail(*args, **kwargs):
        raise RuntimeError("Simulated parser crash during reprocessing")

    monkeypatch.setattr(claim_extractor, "extract_claims_from_text", mock_fail)

    # Pass 2: Deliberate reprocessing fails
    await pipeline_service.process_evidence_item(
        sub.id, session_factory=lambda: db_session, force_reprocess=True, reprocess_reason="CRASH_TEST"
    )

    # Verify atomic protection: Version 1 claims are STILL active!
    res_2 = await db_session.execute(
        select(ClaimRecord).where(ClaimRecord.evidence_submission_id == sub.id, ClaimRecord.is_active == True)
    )
    active_after_crash = list(res_2.scalars().all())
    assert len(active_after_crash) == 2
    assert all(c.version == 1 for c in active_after_crash)

@pytest.mark.asyncio
async def test_concurrent_processing_attempts(test_db_engine, db_session):
    """
    Verifies that concurrent processing attempts on the same submission
    maintain database integrity without duplicate active claims.
    """
    import asyncio
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

    test_session_factory = async_sessionmaker(
        bind=test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )

    inv = Investigation(title="Concurrency Test Investigation", priority="MEDIUM")
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

    # Launch concurrent process attempts with distinct session instances
    results = await asyncio.gather(
        pipeline_service.process_evidence_item(sub.id, session_factory=test_session_factory, force_reprocess=False),
        pipeline_service.process_evidence_item(sub.id, session_factory=test_session_factory, force_reprocess=False)
    )
    assert any(results) is True

    # Check active claims in DB
    res = await db_session.execute(
        select(ClaimRecord).where(ClaimRecord.evidence_submission_id == sub.id, ClaimRecord.is_active == True)
    )
    active_claims = list(res.scalars().all())
    # Exactly 2 claims should be active (from the 2 sentences in raw_text & caption)
    assert len(active_claims) == 2

# ---------------------------------------------------------------------------
# 6. RELATIVE-DATE REFERENCE SEMANTICS AUDITING
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_relative_date_reference_semantics():
    """
    Verifies that:
    1. Submission time is NEVER assumed to be the statement reference frame (unresolved).
    2. Missing reference timestamp remains unresolved.
    3. Known PUBLICATION_TIME or STATEMENT_TIME with timezone safely resolves relative dates.
    """
    text = "The minister resigned yesterday."

    # Case A: Without reference timestamp -> RELATIVE_DATE_UNRESOLVED
    ent_none = claim_normalizer.parse_entities(text, reference_timestamp=None)
    d_none = ent_none["dates"][0]
    assert d_none["type"] == "RELATIVE_DATE_UNRESOLVED"
    assert d_none["normalized"] is None
    assert d_none["is_anchored"] is False

    # Case B: With SUBMISSION_TIME -> RELATIVE_DATE_UNRESOLVED (submission time is not statement frame!)
    sub_dt = datetime(2026, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
    ent_sub = claim_normalizer.parse_entities(text, reference_timestamp=sub_dt, reference_timestamp_type="SUBMISSION_TIME")
    d_sub = ent_sub["dates"][0]
    assert d_sub["type"] == "RELATIVE_DATE_UNRESOLVED"
    assert d_sub["normalized"] is None
    assert d_sub["is_anchored"] is False
    assert "submission intake time cannot be assumed" in d_sub["caveat"]

    # Case C: With verified PUBLICATION_TIME -> RELATIVE_DATE_ANCHORED
    pub_dt = datetime(2026, 3, 15, 8, 30, 0, tzinfo=timezone.utc)
    ent_pub = claim_normalizer.parse_entities(text, reference_timestamp=pub_dt, reference_timestamp_type="PUBLICATION_TIME")
    d_pub = ent_pub["dates"][0]
    assert d_pub["type"] == "RELATIVE_DATE_ANCHORED"
    assert d_pub["normalized"] == "2026-03-14"
    assert d_pub["is_anchored"] is True
    assert "PUBLICATION_TIME" in d_pub["caveat"]

# ---------------------------------------------------------------------------
# 7. UNICODE OFFSET CONVENTIONS & EMOJI COMPATIBILITY
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_unicode_evidence_offsets_and_emojis():
    """
    Verifies Unicode Code Point span integrity with Telugu, Hindi, mixed scripts,
    emojis (surrogate pair code points), OCR noise, and compound sentences.
    Verifies codepoint_to_utf16_offsets and utf16_to_codepoint_offsets.
    """
    inv_id = "test-inv-unicode"
    sub_id = "test-sub-unicode"

    # Emoji + English: '🚨' is U+1F6A8 (1 code point in Python, 2 UTF-16 code units in JS)
    text_emoji = "🚨 Breaking news: The dam collapsed on Tuesday in District 4."
    claims_emoji = claim_extractor.extract_claims_from_text(text_emoji, inv_id, sub_id)
    assert len(claims_emoji) == 1
    ce = claims_emoji[0]
    cp_start = ce["evidence_span_start"]
    cp_end = ce["evidence_span_end"]
    # Python code point slice must reproduce claim_text
    assert text_emoji[cp_start:cp_end] == ce["claim_text"]

    # Test conversion to UTF-16
    u16_start, u16_end = codepoint_to_utf16_offsets(text_emoji, cp_start, cp_end)
    assert u16_start == cp_start  # starts after emoji if trimmed, or includes emoji
    # Round-trip back to code point offsets
    rt_start, rt_end = utf16_to_codepoint_offsets(text_emoji, u16_start, u16_end)
    assert (rt_start, rt_end) == (cp_start, cp_end)

    # Telugu Unicode code points
    text_te = "హైదరాబాద్‌లో భారీ వర్షం కారణంగా పాఠశాలలకు సెలవు ప్రకటించారు."
    claims_te = claim_extractor.extract_claims_from_text(text_te, inv_id, sub_id)
    cte = claims_te[0]
    assert text_te[cte["evidence_span_start"]:cte["evidence_span_end"]] == cte["claim_text"]
    u16_te_s, u16_te_e = codepoint_to_utf16_offsets(text_te, cte["evidence_span_start"], cte["evidence_span_end"])
    # Telugu characters are in BMP: code points == UTF-16 code units
    assert (u16_te_s, u16_te_e) == (cte["evidence_span_start"], cte["evidence_span_end"])

    # Hindi Unicode code points
    text_hi = "स्वास्थ्य मंत्रालय ने नई गाइडलाइंस जारी कीं।"
    claims_hi = claim_extractor.extract_claims_from_text(text_hi, inv_id, sub_id)
    chi = claims_hi[0]
    assert text_hi[chi["evidence_span_start"]:chi["evidence_span_end"]] == chi["claim_text"]
    u16_hi_s, u16_hi_e = codepoint_to_utf16_offsets(text_hi, chi["evidence_span_start"], chi["evidence_span_end"])
    assert (u16_hi_s, u16_hi_e) == (chi["evidence_span_start"], chi["evidence_span_end"])

# ---------------------------------------------------------------------------
# 8. GENERAL STRUCTURAL & EDGE CASE TESTS
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
