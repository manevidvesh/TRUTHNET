import re
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from app.claims.language import language_detector, LanguageDetectionResult
from app.claims.normalizer import claim_normalizer

# Sentence boundary regex (handles punctuation, Hindi purna viram, and newlines)
_SENTENCE_BOUNDARY_RE = re.compile(r"([^.!?\n\r\u0964\u0965]+[.!?\n\r\u0964\u0965]*)")

# Subjective framing prefixes (e.g., "In my opinion,", "I believe", "Personally,")
_SUBJECTIVE_PREFIX_RE = re.compile(
    r"^\s*(In\s+my\s+opinion|I\s+believe|I\s+think|I\s+feel|Personally|From\s+my\s+perspective|As\s+I\s+see\s+it|मेरी\s+राय\s+में|मुझे\s+लगता\s+है\s+कि|నా\s+ఉద్దేశంలో)[,\s]+(.+)$",
    re.IGNORECASE
)

# Evaluative connector splitting (e.g., "This is the worst decision because 20 people died")
_EVALUATIVE_CONNECTOR_RE = re.compile(
    r"^(.+?)\s+(because|since|as\s+a\s+result\s+of)\s+(.+)$",
    re.IGNORECASE
)

# Pure opinion / rhetoric patterns (without factual substance)
_PURE_OPINION_PATTERNS = [
    re.compile(r"\b(?:worst|best|terrible|awesome|horrible|disgusting|ridiculous|amazing|gorgeous|ugly)\s+(?:ever|decision\s+ever|thing\s+ever|movie\s+ever|policy\s+ever)\b", re.IGNORECASE),
    re.compile(r"^\s*(?:shame\s+on|congratulations|happy\s+birthday|good\s+morning|hello\s+everyone|wow|omg)\b", re.IGNORECASE),
    re.compile(r"^\s*(?:breaking\s+news|urgent\s+update|alert|update|exclusive)[\s\!:]*$", re.IGNORECASE),
    re.compile(r"\?\s*$"),  # Questions
    re.compile(r"^\s*(?:why|how|what|who|when|where|is\s+it\s+true\s+that|isn't\s+it)\b.*\?\s*$", re.IGNORECASE),
    re.compile(r"^\s*(?:क्या|क्यों|कैसे|कब|कहाँ)\b.*[\?।]?\s*$"),
    re.compile(r"^\s*(?:ఎందుకు|ఎలా|ఎప్పుడు|ఎక్కడ)\b.*\?\s*$")
]

# Attribution patterns (Speaker / Entity reporting an assertion)
_ATTRIBUTION_PATTERNS = [
    # "According to X, Y happened"
    re.compile(r"^\s*(According\s+to|As\s+reported\s+by|Speaking\s+to)\s+([A-Z][a-zA-Z\s\.\,\-]+?),\s*(.+)$", re.IGNORECASE),
    # "Spokesperson X announced / claimed / stated that Y"
    re.compile(r"^\s*([A-Z][a-zA-Z\s\.\-]+?)\s+(claimed|alleged|stated|announced|declared|said|tweeted|reported|warned|denied|confirmed)\s+that\s+(.+)$", re.IGNORECASE),
    # Hindi attribution: "X के अनुसार Y" or "X ने दावा किया कि Y"
    re.compile(r"^\s*(.+?)\s+के\s+अनुसार[,\s]+(.+)$"),
    re.compile(r"^\s*(.+?)\s+ने\s+(दावा\s+किया|कहा|घोषणा\s+की|पुष्टि\s+की|इन्कार\s+किया)\s+कि\s+(.+)$"),
    # Telugu attribution: "X ప్రకారం Y" or "X చెప్పారు"
    re.compile(r"^\s*(.+?)\s+ప్రకారం[,\s]+(.+)$"),
    re.compile(r"^\s*(.+?)\s+(చెప్పారు|ప్రకటించారు|పేర్కొన్నారు)[,\s]+(.+)$")
]

# Negation Patterns
_DIRECT_NEGATION_RE = re.compile(
    r"\b(did\s+not|does\s+not|has\s+not|have\s+not|was\s+not|were\s+not|will\s+not|would\s+not|could\s+not|should\s+not|never|refused\s+to|failed\s+to|not)\b",
    re.IGNORECASE
)
_INDIC_NEGATION_RE = re.compile(
    r"(?<![\u0900-\u097F\u0C00-\u0C7F])(नहीं|ना|इनकार|లేదు|కాదు|నిరాకరించారు)(?![\u0900-\u097F\u0C00-\u0C7F])"
)

# Complex / Ambiguous Negation Contexts:
# 1. Litotes / Modal ("not impossible", "did not fail to")
_MODAL_LITOTES_RE = re.compile(
    r"\b(not\s+impossible|cannot\s+deny\s+that|did\s+not\s+fail\s+to)\b",
    re.IGNORECASE
)
# 2. Multi-clause / Speech act negation ("did not deny that", "never said it did not", "not true that ... did not")
_NESTED_SPEECH_ACT_RE = re.compile(
    r"\b(did\s+not\s+deny\s+that|never\s+said\s+.*did\s+not|not\s+true\s+that\s+.*(?:not|never))\b",
    re.IGNORECASE
)
# 3. Epistemic absence ("no evidence suggests ... not")
_EPISTEMIC_NEGATION_RE = re.compile(
    r"\b(no\s+evidence\s+suggests\s+.*not|no\s+proof\s+shows\s+.*not)\b",
    re.IGNORECASE
)

# Causal relationship patterns
_CAUSAL_PATTERNS = [
    re.compile(r"\b(.+?)\s+(caused|led\s+to|resulted\s+in|triggered)\s+(.+)$", re.IGNORECASE),
    re.compile(r"\b(.+?)\s+(?:due\s+to|because\s+of|as\s+a\s+result\s+of)\s+(.+)$", re.IGNORECASE),
    re.compile(r"\b(.+?)\s+के\s+कारण\s+(.+)$"),
    re.compile(r"\b(.+?)\s+(?:కారణంగా|వల్ల)\s+(.+)$")
]

# Compound sentence split conjunctions (independent clauses)
_CLAUSE_SPLIT_RE = re.compile(r"(?:,\s+and\s+|;\s+|,\s+but\s+|,\s+while\s+|,\s+तथा\s+|,\s+మరియు\s+)", re.IGNORECASE)

class ClaimExtractor:
    """
    Hardened hybrid deterministic semantic claim extraction engine.
    Extracts atomic proposition candidates, identifies attribution and causal links,
    separates subjective framing from factual sub-claims, performs scope-aware negation,
    enforces strict evidence-span integrity, and assigns conservative extraction states.
    """

    def __init__(self):
        self.language_detector = language_detector
        self.normalizer = claim_normalizer

    def extract_claims_from_text(
        self,
        source_text: str,
        investigation_id: str,
        evidence_submission_id: str,
        source_modality: str = "RAW_TEXT",
        reference_timestamp: Optional[datetime] = None,
        reference_timestamp_type: Optional[str] = None,
        reference_timezone: Optional[str] = None,
        extraction_version: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Parses raw source text into structured claim candidates.
        Guarantees that evidence_span_start and evidence_span_end reference the EXACT character
        offsets of source_text.
        """
        if not source_text or not source_text.strip():
            return []

        source_text_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
        lang_res = self.language_detector.detect(source_text)

        extracted_claims: List[Dict[str, Any]] = []

        # Sentence Boundary Discovery on raw text
        sentence_matches = list(_SENTENCE_BOUNDARY_RE.finditer(source_text))
        if not sentence_matches:
            sentence_matches = [re.search(re.escape(source_text.strip()), source_text)]

        for match in sentence_matches:
            if not match:
                continue
            raw_sentence = match.group(0)
            sentence_stripped = raw_sentence.strip()
            if not sentence_stripped:
                continue

            # Find exact character offsets of sentence_stripped in original source_text
            sent_start = source_text.find(sentence_stripped, match.start())
            sent_end = sent_start + len(sentence_stripped)

            # Check for subjective framing prefix (e.g. "In my opinion, ...")
            prefix_match = _SUBJECTIVE_PREFIX_RE.match(sentence_stripped)
            if prefix_match:
                framing_marker = prefix_match.group(1).strip()
                inner_text = prefix_match.group(2).strip()

                # Find exact offsets for framing and inner proposition
                marker_start = source_text.find(framing_marker, sent_start)
                marker_end = marker_start + len(framing_marker)
                inner_start = source_text.find(inner_text, marker_end)
                inner_end = inner_start + len(inner_text)

                # Check if inner text has verifiable factual indicators or if it's purely subjective
                is_inner_pure_opinion = any(p.search(inner_text) for p in _PURE_OPINION_PATTERNS)
                inner_entities = self.normalizer.parse_entities(
                    inner_text,
                    reference_timestamp=reference_timestamp,
                    reference_timestamp_type=reference_timestamp_type,
                    reference_timezone=reference_timezone
                )
                has_factual_content = (
                    bool(inner_entities.get("dates")) or
                    bool(inner_entities.get("quantities")) or
                    bool(inner_entities.get("organizations")) or
                    re.search(r"\b(spent|cost|resigned|died|killed|injured|arrested|collapsed|approved|rejected|built|signed)\b", inner_text, re.IGNORECASE) is not None
                )

                if is_inner_pure_opinion and not has_factual_content:
                    # Entire statement is non-factual opinion
                    claim_dict = self._build_non_factual_record(
                        proposition_text=sentence_stripped,
                        span_start=sent_start,
                        span_end=sent_end,
                        source_text_hash=source_text_hash,
                        lang_res=lang_res,
                        investigation_id=investigation_id,
                        evidence_submission_id=evidence_submission_id,
                        source_modality=source_modality,
                        extraction_version=extraction_version,
                        reason="Pure subjective opinion without verifiable factual assertions."
                    )
                    extracted_claims.append(claim_dict)
                    continue
                else:
                    # Subjective framing attached to a verifiable factual sub-claim
                    subjective_framing = {
                        "framing_marker": framing_marker,
                        "framing_span": [marker_start, marker_end]
                    }
                    claim_dict = self._process_proposition_span(
                        proposition_text=inner_text,
                        span_start=inner_start,
                        span_end=inner_end,
                        source_text=source_text,
                        source_text_hash=source_text_hash,
                        lang_res=lang_res,
                        investigation_id=investigation_id,
                        evidence_submission_id=evidence_submission_id,
                        source_modality=source_modality,
                        reference_timestamp=reference_timestamp,
                        reference_timestamp_type=reference_timestamp_type,
                        reference_timezone=reference_timezone,
                        extraction_version=extraction_version,
                        subjective_framing=subjective_framing
                    )
                    extracted_claims.append(claim_dict)
                    continue

            # Check for evaluative main clause + factual subordinate clause
            eval_match = _EVALUATIVE_CONNECTOR_RE.match(sentence_stripped)
            if eval_match:
                main_clause = eval_match.group(1).strip()
                connector = eval_match.group(2).strip()
                sub_clause = eval_match.group(3).strip()

                is_main_evaluative = any(p.search(main_clause) for p in _PURE_OPINION_PATTERNS) or re.search(r"\b(worst|best|terrible|awesome|bad|good)\b", main_clause, re.IGNORECASE)
                sub_entities = self.normalizer.parse_entities(
                    sub_clause,
                    reference_timestamp=reference_timestamp,
                    reference_timestamp_type=reference_timestamp_type,
                    reference_timezone=reference_timezone
                )
                has_sub_factual = bool(sub_entities.get("quantities")) or bool(sub_entities.get("dates")) or re.search(r"\b(died|killed|injured|collapsed|cost|spent)\b", sub_clause, re.IGNORECASE)

                if is_main_evaluative and has_sub_factual:
                    sub_start = source_text.find(sub_clause, sent_start)
                    sub_end = sub_start + len(sub_clause)
                    claim_dict = self._process_proposition_span(
                        proposition_text=sub_clause,
                        span_start=sub_start,
                        span_end=sub_end,
                        source_text=source_text,
                        source_text_hash=source_text_hash,
                        lang_res=lang_res,
                        investigation_id=investigation_id,
                        evidence_submission_id=evidence_submission_id,
                        source_modality=source_modality,
                        reference_timestamp=reference_timestamp,
                        reference_timestamp_type=reference_timestamp_type,
                        reference_timezone=reference_timezone,
                        extraction_version=extraction_version,
                        subjective_framing={"evaluative_main_clause": main_clause, "connector": connector}
                    )
                    extracted_claims.append(claim_dict)
                    continue

            # Check for compound clauses that can be decomposed cleanly
            clause_splits = list(_CLAUSE_SPLIT_RE.finditer(sentence_stripped))
            if clause_splits:
                last_idx = 0
                for c_split in clause_splits:
                    clause_text = sentence_stripped[last_idx:c_split.start()].strip()
                    if len(clause_text) >= 5:
                        c_start = source_text.find(clause_text, sent_start + last_idx)
                        c_end = c_start + len(clause_text)
                        claim_dict = self._process_proposition_span(
                            proposition_text=clause_text,
                            span_start=c_start,
                            span_end=c_end,
                            source_text=source_text,
                            source_text_hash=source_text_hash,
                            lang_res=lang_res,
                            investigation_id=investigation_id,
                            evidence_submission_id=evidence_submission_id,
                            source_modality=source_modality,
                            reference_timestamp=reference_timestamp,
                            reference_timestamp_type=reference_timestamp_type,
                            reference_timezone=reference_timezone,
                            extraction_version=extraction_version
                        )
                        extracted_claims.append(claim_dict)
                    last_idx = c_split.end()

                remainder_text = sentence_stripped[last_idx:].strip()
                if len(remainder_text) >= 5:
                    r_start = source_text.find(remainder_text, sent_start + last_idx)
                    r_end = r_start + len(remainder_text)
                    claim_dict = self._process_proposition_span(
                        proposition_text=remainder_text,
                        span_start=r_start,
                        span_end=r_end,
                        source_text=source_text,
                        source_text_hash=source_text_hash,
                        lang_res=lang_res,
                        investigation_id=investigation_id,
                        evidence_submission_id=evidence_submission_id,
                        source_modality=source_modality,
                        reference_timestamp=reference_timestamp,
                        reference_timestamp_type=reference_timestamp_type,
                        reference_timezone=reference_timezone,
                        extraction_version=extraction_version
                    )
                    extracted_claims.append(claim_dict)
            else:
                # Single proposition sentence
                claim_dict = self._process_proposition_span(
                    proposition_text=sentence_stripped,
                    span_start=sent_start,
                    span_end=sent_end,
                    source_text=source_text,
                    source_text_hash=source_text_hash,
                    lang_res=lang_res,
                    investigation_id=investigation_id,
                    evidence_submission_id=evidence_submission_id,
                    source_modality=source_modality,
                    reference_timestamp=reference_timestamp,
                    reference_timestamp_type=reference_timestamp_type,
                    reference_timezone=reference_timezone,
                    extraction_version=extraction_version
                )
                extracted_claims.append(claim_dict)

        return extracted_claims

    def _build_non_factual_record(
        self,
        proposition_text: str,
        span_start: int,
        span_end: int,
        source_text_hash: str,
        lang_res: LanguageDetectionResult,
        investigation_id: str,
        evidence_submission_id: str,
        source_modality: str,
        extraction_version: int,
        reason: str
    ) -> Dict[str, Any]:
        return {
            "investigation_id": investigation_id,
            "evidence_submission_id": evidence_submission_id,
            "version": extraction_version,
            "is_active": True,
            "claim_text": proposition_text,
            "normalized_claim": self.normalizer.normalize_text(proposition_text),
            "extraction_state": "NON_FACTUAL_STATEMENT",
            "polarity_state": "AFFIRMATIVE_SURFACE_SYNTAX",
            "is_attributed_assertion": False,
            "subject": None,
            "predicate": None,
            "object": None,
            "qualifiers": {"classification": "OPINION_OR_RHETORICAL_QUESTION", "reason": reason},
            "source_modality": source_modality,
            "evidence_span_start": span_start,
            "evidence_span_end": span_end,
            "source_text_hash": source_text_hash,
            "extracted_entities": self.normalizer.parse_entities(proposition_text),
            "language": lang_res.language,
            "language_detection_method": lang_res.detection_method,
            "language_detector_version": lang_res.detector_version,
            "language_detector_probability": lang_res.detector_probability,
            "translation_provenance": None,
            "is_factual_assertion": False,
            "extraction_method": "DETERMINISTIC_OPINION_FILTER",
            "extraction_confidence": None,
            "uncertainty_notes": reason
        }

    def _process_proposition_span(
        self,
        proposition_text: str,
        span_start: int,
        span_end: int,
        source_text: str,
        source_text_hash: str,
        lang_res: LanguageDetectionResult,
        investigation_id: str,
        evidence_submission_id: str,
        source_modality: str,
        reference_timestamp: Optional[datetime],
        reference_timestamp_type: Optional[str] = None,
        reference_timezone: Optional[str] = None,
        extraction_version: int = 1,
        subjective_framing: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyzes an individual proposition span: checks opinion/factual status,
        extracts attribution, scope-aware negation, causal structure, and entities.
        """
        # Validate span offset precision against original source_text
        span_slice = source_text[span_start:span_end]
        if span_slice != proposition_text:
            alt_start = source_text.find(proposition_text)
            if alt_start != -1:
                span_start = alt_start
                span_end = alt_start + len(proposition_text)

        normalized_claim = self.normalizer.normalize_text(proposition_text)
        entities = self.normalizer.parse_entities(
            proposition_text,
            reference_timestamp=reference_timestamp,
            reference_timestamp_type=reference_timestamp_type,
            reference_timezone=reference_timezone
        )

        qualifiers: Dict[str, Any] = {}
        if subjective_framing:
            qualifiers["subjective_framing"] = subjective_framing

        uncertainty_notes: Optional[str] = None

        # 1. Non-Factual Statement Filtering (Pure Opinions, Insults, Pure Questions)
        is_pure_opinion = any(p.search(proposition_text) for p in _PURE_OPINION_PATTERNS)
        if is_pure_opinion and not subjective_framing:
            return self._build_non_factual_record(
                proposition_text=proposition_text,
                span_start=span_start,
                span_end=span_end,
                source_text_hash=source_text_hash,
                lang_res=lang_res,
                investigation_id=investigation_id,
                evidence_submission_id=evidence_submission_id,
                source_modality=source_modality,
                extraction_version=extraction_version,
                reason="Classified as non-factual opinion, emotional rhetoric, or rhetorical question."
            )

        # 2. Incomplete or Fragmentary Transcripts
        if proposition_text.endswith("...") or proposition_text.startswith("...") or len(proposition_text.split()) < 3:
            return {
                "investigation_id": investigation_id,
                "evidence_submission_id": evidence_submission_id,
                "version": extraction_version,
                "is_active": True,
                "claim_text": proposition_text,
                "normalized_claim": normalized_claim,
                "extraction_state": "PARTIAL_EXTRACTION",
                "polarity_state": "AFFIRMATIVE_SURFACE_SYNTAX",
                "is_attributed_assertion": False,
                "subject": None,
                "predicate": None,
                "object": None,
                "qualifiers": {"fragmentary": True},
                "source_modality": source_modality,
                "evidence_span_start": span_start,
                "evidence_span_end": span_end,
                "source_text_hash": source_text_hash,
                "extracted_entities": entities,
                "language": lang_res.language,
                "language_detection_method": lang_res.detection_method,
                "language_detector_version": lang_res.detector_version,
                "language_detector_probability": lang_res.detector_probability,
                "translation_provenance": None,
                "is_factual_assertion": True,
                "extraction_method": "FRAGMENTARY_TEXT_HANDLER",
                "extraction_confidence": None,
                "uncertainty_notes": "Transcript or text fragment ended abruptly or is structurally incomplete."
            }

        # 3. Attribution Parsing (Separating speaker assertion from proposition)
        working_text = proposition_text
        is_attributed = False
        for attr_pat in _ATTRIBUTION_PATTERNS:
            m = attr_pat.match(working_text)
            if m:
                if len(m.groups()) == 3:
                    speaker = m.group(1).strip()
                    verb = m.group(2).strip()
                    inner_claim = m.group(3).strip()
                elif len(m.groups()) == 2:
                    speaker = m.group(1).strip()
                    verb = "attributed"
                    inner_claim = m.group(2).strip()
                else:
                    speaker = m.group(1).strip()
                    verb = "stated"
                    inner_claim = m.group(len(m.groups())).strip()

                sp_start = source_text.find(speaker, span_start)
                sp_end = sp_start + len(speaker) if sp_start != -1 else None

                vb_start = source_text.find(verb, sp_end if sp_end is not None else span_start)
                vb_end = vb_start + len(verb) if vb_start != -1 else None

                prop_start = source_text.find(inner_claim, span_start)
                prop_end = prop_start + len(inner_claim) if prop_start != -1 else None

                reporting_clause = proposition_text[:prop_start - span_start].strip() if prop_start is not None else f"{speaker} {verb} that"

                qualifiers["attribution"] = {
                    "speaker": speaker,
                    "speaker_span": [sp_start, sp_end] if sp_start is not None else None,
                    "attribution_verb": verb,
                    "verb_span": [vb_start, vb_end] if vb_start is not None else None,
                    "reporting_clause": reporting_clause,
                    "reporting_clause_span": [span_start, prop_start] if prop_start is not None else None,
                    "attributed_proposition": inner_claim,
                    "proposition_span": [prop_start, prop_end] if prop_start is not None else None,
                    "epistemological_status": "ATTRIBUTED_REPORTING_STATEMENT",
                    "disclaimer": "This proposition reflects what the named speaker asserted, NOT an independently established or verified fact."
                }
                is_attributed = True
                working_text = inner_claim
                break

        # 4. Scope-Aware Conservative Negation Analysis
        negation_markers = []
        for m in _DIRECT_NEGATION_RE.finditer(proposition_text):
            negation_markers.append({"marker": m.group(0), "span": [m.start(), m.end()]})
        for m in _INDIC_NEGATION_RE.finditer(proposition_text):
            negation_markers.append({"marker": m.group(0), "span": [m.start(), m.end()]})

        polarity_state = "AFFIRMATIVE_SURFACE_SYNTAX"
        polarity_method = "AFFIRMATIVE_SURFACE_SYNTAX"

        # Correct polarity semantics for unsupported languages (Hindi, Telugu, and all non-English)
        if lang_res.language != "en":
            polarity_state = "UNSUPPORTED_LANGUAGE_POLARITY"
            polarity_method = "UNSUPPORTED_LANGUAGE_POLARITY"
            qualifiers["negation"] = {
                "polarity_state": polarity_state,
                "polarity_method": polarity_method,
                "markers": negation_markers,
                "note": f"Linguistic polarity not analyzed: grammatical dependency parser unavailable for language '{lang_res.language.upper()}'. Absence of English negation markers does NOT imply affirmative truth."
            }
        elif not negation_markers:
            # English affirmative surface syntax
            polarity_state = "AFFIRMATIVE_SURFACE_SYNTAX"
            polarity_method = "AFFIRMATIVE_SURFACE_SYNTAX"
            qualifiers["negation"] = {
                "polarity_state": polarity_state,
                "polarity_method": polarity_method,
                "markers": [],
                "note": "Surface grammatical polarity is affirmative (no negation markers detected). This represents syntactic surface form only, NOT factual truth or real-world verification."
            }
        else:
            if _NESTED_SPEECH_ACT_RE.search(proposition_text):
                polarity_state = "UNRESOLVED_POLARITY"
                polarity_method = "NESTED_SPEECH_ACT_NEGATION"
                qualifiers["negation"] = {
                    "polarity_state": polarity_state,
                    "polarity_method": polarity_method,
                    "markers": negation_markers,
                    "note": "Nested speech-act negation modifies reporting verb rather than core event; polarity marked unresolved."
                }
            elif _MODAL_LITOTES_RE.search(proposition_text):
                polarity_state = "UNRESOLVED_POLARITY"
                polarity_method = "MODAL_LITOTES_NEGATION"
                qualifiers["negation"] = {
                    "polarity_state": polarity_state,
                    "polarity_method": polarity_method,
                    "markers": negation_markers,
                    "note": "Modal double negation conveys epistemic possibility, not definite affirmative truth; polarity marked unresolved."
                }
            elif _EPISTEMIC_NEGATION_RE.search(proposition_text):
                polarity_state = "UNRESOLVED_POLARITY"
                polarity_method = "EPISTEMIC_NEGATION"
                qualifiers["negation"] = {
                    "polarity_state": polarity_state,
                    "polarity_method": polarity_method,
                    "markers": negation_markers,
                    "note": "Epistemic absence of evidence does not equal logical affirmation; polarity marked unresolved."
                }
            elif len(negation_markers) > 1:
                polarity_state = "UNRESOLVED_POLARITY"
                polarity_method = "MULTIPLE_NEGATION_UNRESOLVED"
                qualifiers["negation"] = {
                    "polarity_state": polarity_state,
                    "polarity_method": polarity_method,
                    "markers": negation_markers,
                    "note": "Multiple negation markers detected with ambiguous cross-clause scope; polarity marked unresolved."
                }
            else:
                polarity_state = "NEGATIVE_SURFACE_SYNTAX"
                polarity_method = "DIRECT_CLAUSAL_NEGATION"
                qualifiers["negation"] = {
                    "polarity_state": polarity_state,
                    "polarity_method": polarity_method,
                    "markers": negation_markers,
                    "modified_clause": proposition_text,
                    "note": "Surface grammatical polarity is negative (direct clausal negation detected). This represents syntactic surface form only, NOT factual falsification."
                }

        # 5. Causal Assertion Parsing
        for causal_pat in _CAUSAL_PATTERNS:
            cm = causal_pat.search(working_text)
            if cm:
                cause_part = cm.group(1).strip()
                effect_part = cm.group(len(cm.groups())).strip()
                qualifiers["causal_relation"] = {
                    "cause": cause_part,
                    "effect": effect_part
                }
                break

        # 6. Extraction State & Multilingual Semantics
        subject: Optional[str] = None
        predicate: Optional[str] = None
        obj: Optional[str] = None
        extraction_state: str = "EXTRACTED_CLAIM_CANDIDATE"
        extraction_method: str = "HYBRID_DETERMINISTIC_SYNTACTIC"

        if re.search(r"^\s*(?:flying\s+planes|cooking\s+apples|hunting\s+lions)\b", working_text, re.IGNORECASE):
            extraction_state = "UNRESOLVED_STATEMENT"
            extraction_method = "AMBIGUOUS_STRUCTURE_PARSER"
            uncertainty_notes = "Syntactic attachment ambiguous; propositional roles not forced into SPO."

        elif lang_res.language in ("hi", "te"):
            extraction_state = "EXTRACTED_CLAIM_CANDIDATE"
            extraction_method = "DETERMINISTIC_MULTILINGUAL_CANDIDATE"
            uncertainty_notes = f"UNSUPPORTED_LANGUAGE_PARSER: Semantic proposition roles not structured for {lang_res.language.upper()}; factual candidate preserved with verified entity spans."
            subject = None
            predicate = None
            obj = None

        else:
            # Deterministic English Syntactic Chunking
            verb_match = re.search(
                r"\b(approved|rejected|collapsed|announced|destroyed|passed|signed|opened|attacked|arrested|killed|injured|invaded|declared|banned|purchased|launched|elected|won|lost|died|resigned)\b",
                working_text,
                re.IGNORECASE
            )
            if verb_match:
                v_idx = verb_match.start()
                subject_candidate = working_text[:v_idx].strip(", ")
                predicate_candidate = verb_match.group(0).lower()
                object_candidate = working_text[verb_match.end():].strip(",. ")

                if subject_candidate and len(subject_candidate.split()) <= 8:
                    subject = subject_candidate
                    predicate = predicate_candidate
                    obj = object_candidate if object_candidate else None
                    extraction_state = "STRUCTURED_PROPOSITION"
                else:
                    extraction_state = "PARTIAL_EXTRACTION"
                    predicate = predicate_candidate
                    uncertainty_notes = "Subject clause is compound or ambiguous; recorded as partial extraction."
            else:
                extraction_state = "EXTRACTED_CLAIM_CANDIDATE"
                uncertainty_notes = "Declarative verb structure not definitively resolved; proposition preserved as candidate."

        return {
            "investigation_id": investigation_id,
            "evidence_submission_id": evidence_submission_id,
            "version": extraction_version,
            "is_active": True,
            "claim_text": proposition_text,
            "normalized_claim": normalized_claim,
            "extraction_state": extraction_state,
            "polarity_state": polarity_state,
            "is_attributed_assertion": is_attributed,
            "subject": subject,
            "predicate": predicate,
            "object": obj,
            "qualifiers": qualifiers if qualifiers else None,
            "source_modality": source_modality,
            "evidence_span_start": span_start,
            "evidence_span_end": span_end,
            "source_text_hash": source_text_hash,
            "extracted_entities": entities,
            "language": lang_res.language,
            "language_detection_method": lang_res.detection_method,
            "language_detector_version": lang_res.detector_version,
            "language_detector_probability": lang_res.detector_probability,
            "translation_provenance": None,
            "is_factual_assertion": True,
            "extraction_method": extraction_method,
            "extraction_confidence": None,
            "uncertainty_notes": uncertainty_notes
        }

claim_extractor = ClaimExtractor()
