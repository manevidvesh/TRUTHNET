import re
from typing import Optional, Dict, Any, List, Tuple
from app.models.claim import ClaimRecord
from app.schemas.context_verification import EvidenceItem, EvidenceRelationshipType

# Maximum length for evidence excerpts
MAX_EXCERPT_LENGTH = 500

NEGATION_PATTERNS = [
    r"\bdid\s+not\b",
    r"\bwas\s+not\b",
    r"\bwere\s+not\b",
    r"\bhas\s+not\b",
    r"\bhave\s+not\b",
    r"\bis\s+not\b",
    r"\bare\s+not\b",
    r"\bnot\s+true\b",
    r"\bfake\b",
    r"\bfalse\b",
    r"\bdebunked\b",
    r"\bdenied\b",
    r"\brefuted\b",
    r"\bno\s+evidence\b",
    r"\bnever\b",
    r"\buntrue\b",
    r"\bmisleading\b",
    r"\bcontradicting\b",
    r"\bcontradicts\b",
    r"\bnot\s+\d+\b",
]

def extract_passage_excerpt(
    text: str,
    target_terms: List[str],
    max_len: int = MAX_EXCERPT_LENGTH
) -> Tuple[str, int, int]:
    """
    Extracts a verbatim excerpt of length <= max_len centered around the first
    or best occurrence of target_terms, returning (excerpt, start_char, end_char).
    """
    if not text:
        return ("", 0, 0)

    clean_text = text.strip()
    if len(clean_text) <= max_len:
        return (clean_text, 0, len(clean_text))

    # Search for first term match
    best_pos = -1
    for term in target_terms:
        if not term or len(term) < 3:
            continue
        idx = clean_text.lower().find(term.lower())
        if idx != -1:
            best_pos = idx
            break

    if best_pos == -1:
        # Default to prefix if no term matches
        return (clean_text[:max_len], 0, max_len)

    # Window around best_pos
    half_window = max_len // 2
    start = max(0, best_pos - half_window)
    end = min(len(clean_text), start + max_len)
    if end - start < max_len and start > 0:
        start = max(0, end - max_len)

    excerpt = clean_text[start:end]
    return (excerpt, start, end)

class EvidenceAligner:
    """
    Evaluates evidence items against a specific ClaimRecord proposition,
    enforcing passage-level grounding, entity relevance, stance classification,
    and cautious source independence marking.
    """

    @classmethod
    def evaluate_evidence_item(
        cls,
        claim: ClaimRecord,
        evidence: EvidenceItem,
        temporal_analysis: Optional[Dict[str, Any]] = None,
        spatial_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Determines the specific relationship between an EvidenceItem and a ClaimRecord.
        EPISTEMOLOGICAL INVARIANT:
        Every evidence relationship must be relevant to the specific proposition being assessed.
        Historical media matches or technical metadata that pertain only to the media container
        must not be treated as evidence for unrelated textual claims.
        """
        content = evidence.content_or_passage or ""
        content_lower = content.lower()
        claim_text_lower = claim.claim_text.lower()
        normalized_claim_lower = claim.normalized_claim.lower()

        # Build target key terms from claim components
        key_terms: List[str] = []
        if claim.subject:
            key_terms.append(claim.subject.strip())
        if claim.predicate:
            key_terms.append(claim.predicate.strip())
        if claim.object:
            key_terms.append(claim.object.strip())

        # Add entities from extracted_entities JSON
        if claim.extracted_entities and isinstance(claim.extracted_entities, dict):
            for ent_type, ent_vals in claim.extracted_entities.items():
                if isinstance(ent_vals, list):
                    for v in ent_vals:
                        if isinstance(v, str) and len(v) > 2:
                            key_terms.append(v.strip())

        # Also extract numbers or notable tokens if available
        numbers = re.findall(r"\b\d+(?:\.\d+)?%?\b", claim.claim_text)
        for num in numbers:
            key_terms.append(num)

        # Extract grounded excerpt
        excerpt, span_start, span_end = extract_passage_excerpt(content, key_terms)

        # 1. Relevance check: does this evidence address the claim proposition?
        # Check lexical / entity overlap
        overlap_count = 0
        for term in key_terms:
            if term.lower() in content_lower:
                overlap_count += 1

        is_media_match_only = (
            evidence.source_type == "HISTORICAL_MEDIA_MATCH"
            or (evidence.source_type == "LOCAL_SUBMISSION" and "technical media metadata" in content_lower)
        )

        # If evidence discusses something unrelated to the proposition:
        if overlap_count == 0 and not is_media_match_only:
            return {
                "relationship_type": EvidenceRelationshipType.DOES_NOT_ADDRESS,
                "excerpt": excerpt,
                "passage_span_start": span_start,
                "passage_span_end": span_end,
                "source_independence_status": "UNKNOWN",
                "alignment_rationale": "Evidence content does not contain proposition entities, subject, or predicate.",
                "uncertainty_notes": "Evidence does not address the claim proposition."
            }

        # If it's a media match or local technical metadata: evaluate temporal/spatial provenance
        if is_media_match_only:
            # Check if temporal or spatial discrepancies were identified for the media
            if temporal_analysis and temporal_analysis.get("is_temporal_discrepancy"):
                return {
                    "relationship_type": EvidenceRelationshipType.TEMPORAL_CONFLICT,
                    "excerpt": excerpt,
                    "passage_span_start": span_start,
                    "passage_span_end": span_end,
                    "source_independence_status": "UNKNOWN",
                    "alignment_rationale": "Media metadata/match establishes that media capture predates claimed event timing.",
                    "uncertainty_notes": "Media metadata provides provenance identifying temporal conflict with claimed context."
                }
            elif spatial_analysis and spatial_analysis.get("is_geographical_contradiction"):
                return {
                    "relationship_type": EvidenceRelationshipType.GEOGRAPHICAL_CONFLICT,
                    "excerpt": excerpt,
                    "passage_span_start": span_start,
                    "passage_span_end": span_end,
                    "source_independence_status": "UNKNOWN",
                    "alignment_rationale": "Media metadata/match confirms geographic contradiction with corroborating context.",
                    "uncertainty_notes": "Media provenance provides geographic provenance contradicting claimed location."
                }
            elif overlap_count == 0:
                return {
                    "relationship_type": EvidenceRelationshipType.PROVIDES_CONTEXT,
                    "excerpt": excerpt,
                    "passage_span_start": span_start,
                    "passage_span_end": span_end,
                    "source_independence_status": "UNKNOWN",
                    "alignment_rationale": "Media metadata provides provenance about the media asset, but does not corroborate or refute the textual claim proposition.",
                    "uncertainty_notes": "Media provenance context only; not proposition evidence."
                }

        # 2. Check for explicit Negation Inversion Conflict
        # If claim is affirmative and evidence explicitly contains negation near matching subject/predicate
        has_evidence_negation = any(re.search(pat, content_lower) for pat in NEGATION_PATTERNS)
        claim_is_affirmative = (claim.polarity_state == "AFFIRMATIVE_SURFACE_SYNTAX")
        claim_is_negative = (claim.polarity_state == "NEGATIVE_SURFACE_SYNTAX")

        # Refutation keywords indicating direct contradiction
        refutation_terms = [
            "false", "fabricated", "fake", "refuted", "debunked", "untrue",
            "did not resign", "denied", "contradicting", "contradicts", "conflicting"
        ]
        contains_refutation = any(term in content_lower for term in refutation_terms)
        has_number_negation = any(re.search(rf"\bnot\s+{num}\b", content_lower) for num in numbers)

        if (claim_is_affirmative and contains_refutation and overlap_count >= 1) or \
           (claim_is_affirmative and (has_evidence_negation or has_number_negation) and overlap_count >= 1):
            return {
                "relationship_type": EvidenceRelationshipType.CONTRADICTS,
                "excerpt": excerpt,
                "passage_span_start": span_start,
                "passage_span_end": span_end,
                "source_independence_status": "UNKNOWN",
                "alignment_rationale": "Evidence explicitly contains negation, refutation, or contradictory assertion regarding the proposition.",
                "uncertainty_notes": "Direct syntactic or factual contradiction detected."
            }

        # 3. Check for Misleading Omission / Partial Truth
        # (e.g. claim asserts broad statistic "unemployment 10%", but evidence clarifies "youth unemployment was 10%, overall 3.5%")
        omission_terms = ["only", "specifically", "youth", "sub-category", "misrepresented", "out of context", "baseline"]
        has_omission_framing = any(ot in content_lower for ot in omission_terms)

        # 4. Check for Quantitative or Entity Contradiction
        # If claim asserts a number (e.g. 350 km/h) and evidence asserts a different number (e.g. 110 km/h) for same subject/event
        if numbers:
            claim_nums = set(numbers)
            evidence_nums = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", content))
            # If evidence has numbers but none match the claimed numbers, and entities align:
            if evidence_nums and not (claim_nums & evidence_nums) and overlap_count >= 2:
                return {
                    "relationship_type": EvidenceRelationshipType.CONTRADICTS,
                    "excerpt": excerpt,
                    "passage_span_start": span_start,
                    "passage_span_end": span_end,
                    "source_independence_status": "UNKNOWN",
                    "alignment_rationale": f"Quantitative discrepancy: claim asserts {list(claim_nums)}, but evidence asserts {list(evidence_nums)} for the same subject/event.",
                    "uncertainty_notes": "Numeric contradiction between claim and evidence."
                }

        if has_omission_framing and overlap_count >= 2:
            return {
                "relationship_type": EvidenceRelationshipType.PROVIDES_CONTEXT,
                "excerpt": excerpt,
                "passage_span_start": span_start,
                "passage_span_end": span_end,
                "source_independence_status": "UNKNOWN",
                "alignment_rationale": "Evidence indicates the claim presents authentic figures or facts but omits critical qualifying baseline context.",
                "uncertainty_notes": "Contextual omission detected."
            }

        # 5. Check for Attributed Statement stance
        if claim.is_attributed_assertion:
            # Claim is "Minister said X". If evidence confirms statement was made:
            speech_verbs = ["said", "stated", "announced", "tweeted", "remarked", "claimed"]
            if any(sv in content_lower for sv in speech_verbs) and overlap_count >= 1:
                return {
                    "relationship_type": EvidenceRelationshipType.SUPPORTS,
                    "excerpt": excerpt,
                    "passage_span_start": span_start,
                    "passage_span_end": span_end,
                    "source_independence_status": "UNKNOWN",
                    "alignment_rationale": "Evidence corroborates that the attributed statement was made by the named speaker. (Note: confirms speech act occurred, does not verify underlying truth of speaker's assertion).",
                    "uncertainty_notes": "Attributed statement corroborated as a speech act."
                }

        # 6. Direct Support
        if overlap_count >= 2:
            return {
                "relationship_type": EvidenceRelationshipType.SUPPORTS,
                "excerpt": excerpt,
                "passage_span_start": span_start,
                "passage_span_end": span_end,
                "source_independence_status": "UNKNOWN",
                "alignment_rationale": "Evidence directly corroborates the core entities, predicate, and context of the proposition.",
                "uncertainty_notes": None
            }
        elif overlap_count == 1:
            return {
                "relationship_type": EvidenceRelationshipType.PARTIALLY_SUPPORTS,
                "excerpt": excerpt,
                "passage_span_start": span_start,
                "passage_span_end": span_end,
                "source_independence_status": "UNKNOWN",
                "alignment_rationale": "Evidence mentions key entities of the proposition, providing partial contextual corroboration.",
                "uncertainty_notes": "Partial entity alignment."
            }

        return {
            "relationship_type": EvidenceRelationshipType.PROVIDES_CONTEXT,
            "excerpt": excerpt,
            "passage_span_start": span_start,
            "passage_span_end": span_end,
            "source_independence_status": "UNKNOWN",
            "alignment_rationale": "Evidence provides background context related to the submission.",
            "uncertainty_notes": "Contextual alignment."
        }
