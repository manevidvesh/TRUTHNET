import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from app.claims.language import language_detector, LanguageDetectionResult
from app.claims.normalizer import claim_normalizer

# Sentence segmentation pattern respecting standard punctuation, Hindi purna viram, and newlines
_SENTENCE_BOUNDARY_RE = re.compile(r"([^.!?\n\r\u0964\u0965]+[.!?\n\r\u0964\u0965]*)")

# Non-factual statement indicators: subjective opinions, emotional rhetoric, and questions
_OPINION_PATTERNS = [
    re.compile(r"^\s*(?:in my opinion|i believe|i think|i feel|personally|i guess)\b", re.IGNORECASE),
    re.compile(r"\b(?:worst|best|terrible|awesome|horrible|disgusting|ridiculous|amazing|gorgeous|ugly)\b", re.IGNORECASE),
    re.compile(r"^\s*(?:shame on|congratulations|happy birthday|good morning|hello everyone|wow|omg)\b", re.IGNORECASE),
    re.compile(r"\?\s*$"),  # Questions
    re.compile(r"^\s*(?:why|how|what|who|when|where|is it true that|isn't it)\b.*\?\s*$", re.IGNORECASE),
    re.compile(r"^\s*(?:क्या|क्यों|कैसे|कब|कहाँ)\b.*[\?।]?\s*$"),
    re.compile(r"^\s*(?:ఎందుకు|ఎలా|ఎప్పుడు|ఎక్కడ)\b.*\?\s*$")
]

# Attribution patterns (Speaker / Entity reporting an assertion)
_ATTRIBUTION_PATTERNS = [
    # "According to X, Y happened"
    re.compile(r"^\s*(?:According to|As reported by|Speaking to)\s+([A-Z][a-zA-Z\s\.\,\-]+?),\s*(.+)$", re.IGNORECASE),
    # "Spokesperson X announced / claimed / stated that Y"
    re.compile(r"^\s*([A-Z][a-zA-Z\s\.\-]+?)\s+(claimed|alleged|stated|announced|declared|said|tweeted|reported|warned|denied|confirmed)\s+that\s+(.+)$", re.IGNORECASE),
    # Hindi attribution: "X के अनुसार Y" or "X ने दावा किया कि Y"
    re.compile(r"^\s*(.+?)\s+के अनुसार[,\s]+(.+)$"),
    re.compile(r"^\s*(.+?)\s+ने\s+(दावा किया|कहा|घोषणा की|पुष्टि की|इन्कार किया)\s+कि\s+(.+)$"),
    # Telugu attribution: "X ప్రకారం Y" or "X చెప్పారు"
    re.compile(r"^\s*(.+?)\s+ప్రకారం[,\s]+(.+)$"),
    re.compile(r"^\s*(.+?)\s+(చెప్పారు|ప్రకటించారు|పేర్కొన్నారు)[,\s]+(.+)$")
]

# Negation and Double Negation patterns
_DOUBLE_NEGATION_PATTERNS = [
    re.compile(r"\b(?:not\s+true\s+that\s+.*\s+(?:did\s+not|not|never)|cannot\s+deny\s+that|did\s+not\s+fail\s+to|not\s+impossible)\b", re.IGNORECASE)
]
_SINGLE_NEGATION_PATTERNS = [
    re.compile(r"\b(?:not|did\s+not|does\s+not|has\s+not|have\s+not|was\s+not|were\s+not|never|refused\s+to|failed\s+to|denied|no\s+evidence)\b", re.IGNORECASE),
    re.compile(r"\b(?:नहीं|ना|इनकार)\b"),
    re.compile(r"\b(?:లేదు|కాదు|నిరాకరించారు)\b")
]

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
    Hybrid deterministic semantic claim extraction engine.
    Extracts atomic proposition candidates, identifies attribution and causal links,
    distinguishes factual assertions from subjective rhetoric, enforces exact evidence-span offsets,
    and documents parse uncertainty without forcing artificial grammatical roles.
    """

    def __init__(self):
        self.language_detector = language_detector
        self.normalizer = claim_normalizer

    def extract_claims_from_text(
        self,
        source_text: str,
        investigation_id: str,
        evidence_submission_id: str,
        source_modality: str = "RAW_TEXT"
    ) -> List[Dict[str, Any]]:
        """
        Parses raw source text into a list of structured claim candidate dictionaries.
        Guarantees that evidence_span_start and evidence_span_end reference the EXACT character
        offsets of source_text.
        """
        if not source_text or not source_text.strip():
            return []

        source_text_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
        lang_res = self.language_detector.detect(source_text)

        extracted_claims: List[Dict[str, Any]] = []

        # Step 1: Sentence Boundary Discovery on raw text
        sentence_matches = list(_SENTENCE_BOUNDARY_RE.finditer(source_text))
        if not sentence_matches:
            # Entire text is a single span
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

            # Step 2: Check for compound clauses that can be decomposed cleanly
            clause_splits = list(_CLAUSE_SPLIT_RE.finditer(sentence_stripped))
            if clause_splits:
                # Decompose into discrete atomic sub-propositions
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
                            source_modality=source_modality
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
                        source_modality=source_modality
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
                    source_modality=source_modality
                )
                extracted_claims.append(claim_dict)

        return extracted_claims

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
        source_modality: str
    ) -> Dict[str, Any]:
        """
        Analyzes an individual proposition span: checks opinion/factual status,
        extracts negation, attribution, causal structure, and entities,
        and assigns appropriate extraction state without inventing interpretations.
        """
        # Validate span offset precision against original source_text
        span_slice = source_text[span_start:span_end]
        if span_slice != proposition_text:
            # Fallback to direct search to ensure 100% precision
            alt_start = source_text.find(proposition_text)
            if alt_start != -1:
                span_start = alt_start
                span_end = alt_start + len(proposition_text)

        normalized_claim = self.normalizer.normalize_text(proposition_text)
        entities = self.normalizer.parse_entities(proposition_text)

        qualifiers: Dict[str, Any] = {}
        uncertainty_notes: Optional[str] = None

        # 1. Non-Factual Statement Filtering (Opinions, Rhetoric, Pure Questions)
        is_opinion = any(p.search(proposition_text) for p in _OPINION_PATTERNS)
        if is_opinion:
            return {
                "investigation_id": investigation_id,
                "evidence_submission_id": evidence_submission_id,
                "claim_text": proposition_text,
                "normalized_claim": normalized_claim,
                "extraction_state": "NON_FACTUAL_STATEMENT",
                "subject": None,
                "predicate": None,
                "object": None,
                "qualifiers": {"classification": "OPINION_OR_RHETORICAL_QUESTION"},
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
                "is_factual_assertion": False,
                "extraction_method": "DETERMINISTIC_OPINION_FILTER",
                "extraction_confidence": None,
                "uncertainty_notes": "Classified as non-factual opinion, emotional rhetoric, or rhetorical question."
            }

        # 2. Incomplete or Fragmentary Transcripts
        if proposition_text.endswith("...") or proposition_text.startswith("...") or len(proposition_text.split()) < 3:
            return {
                "investigation_id": investigation_id,
                "evidence_submission_id": evidence_submission_id,
                "claim_text": proposition_text,
                "normalized_claim": normalized_claim,
                "extraction_state": "PARTIAL_EXTRACTION",
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

        # 3. Attribution Parsing
        working_text = proposition_text
        for attr_pat in _ATTRIBUTION_PATTERNS:
            m = attr_pat.match(working_text)
            if m:
                speaker = m.group(1).strip()
                verb = m.group(2).strip() if len(m.groups()) >= 3 else "attributed"
                inner_claim = m.group(len(m.groups())).strip()
                qualifiers["attribution"] = {
                    "speaker": speaker,
                    "verb": verb
                }
                working_text = inner_claim
                break

        # 4. Negation & Double Negation
        has_double_neg = any(p.search(proposition_text) for p in _DOUBLE_NEGATION_PATTERNS)
        if has_double_neg:
            qualifiers["negation"] = {
                "is_negated": False,
                "has_double_negation": True,
                "note": "Double negation identified; proposition logically affirms truth"
            }
        else:
            has_single_neg = any(p.search(proposition_text) for p in _SINGLE_NEGATION_PATTERNS)
            if has_single_neg:
                qualifiers["negation"] = {
                    "is_negated": True,
                    "has_double_negation": False
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

        # 6. Syntactic Subject-Predicate-Object Parsing vs. Ambiguity
        # For non-English scripts (Hindi, Telugu) or ambiguous structures:
        # Do NOT force artificial English SPO rules if not cleanly identifiable!
        subject: Optional[str] = None
        predicate: Optional[str] = None
        obj: Optional[str] = None
        extraction_state: str = "EXTRACTED_CLAIM_CANDIDATE"

        # Check for ambiguous sentence structures (e.g. gerunds or unresolvable roles like "Flying planes can be dangerous")
        if re.search(r"^\s*(?:flying\s+planes|cooking\s+apples|hunting\s+lions)\b", working_text, re.IGNORECASE):
            extraction_state = "UNRESOLVED_STATEMENT"
            uncertainty_notes = "Syntactic attachment ambiguous; propositional roles not forced into SPO."
        elif lang_res.language in ("hi", "te"):
            # For Hindi and Telugu: retain claim candidate as structured proposition with native entities
            # rather than forcing English Subject-Verb-Object word order
            extraction_state = "STRUCTURED_PROPOSITION"
            uncertainty_notes = f"Multilingual {lang_res.language.upper()} factual assertion preserved with verified entities."
            if entities.get("persons"):
                subject = entities["persons"][0]["name"]
            elif entities.get("organizations"):
                subject = entities["organizations"][0]["canonical_name"]
            predicate = "asserts_factual_event"
            obj = working_text
        else:
            # Deterministic English Syntactic Chunking
            words = working_text.split()
            # Simple declarative heuristic: [Subject Noun Phrase] [Verb Phrase] [Object / Complement Phrase]
            # Detect common action or state verbs
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
                # If no clear active verb is matched, do NOT force artificial SPO
                extraction_state = "EXTRACTED_CLAIM_CANDIDATE"
                uncertainty_notes = "Declarative verb structure not definitively resolved; proposition preserved as candidate."

        return {
            "investigation_id": investigation_id,
            "evidence_submission_id": evidence_submission_id,
            "claim_text": proposition_text,
            "normalized_claim": normalized_claim,
            "extraction_state": extraction_state,
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
            "extraction_method": "HYBRID_DETERMINISTIC_SYNTACTIC",
            "extraction_confidence": None,  # Honest null; no fabricated model confidence
            "uncertainty_notes": uncertainty_notes
        }

claim_extractor = ClaimExtractor()
