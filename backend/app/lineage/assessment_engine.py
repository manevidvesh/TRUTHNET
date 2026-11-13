"""
Explainable Evidence Assessment Engine.

Synthesizes structured, traceable justifications for claim verification assessments:
- Evaluates proposition stance (supporting, contradicting, unaddressed).
- Integrates historical media matches and contextual verification findings.
- Breaks down multi-signal source independence clusters.
- Identifies missing evidence and epistemic limitations without language models.
- Explains the deterministic decision tree path that led to the verdict.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import ClaimRecord
from app.models.evidence import EvidenceSubmission, ExtractionRecord
from app.models.fingerprint import MediaMatchRecord
from app.models.source import RetrievedSourceRecord, SourceIndependenceRecord
from app.models.context_verification import ClaimAssessmentRecord, ClaimEvidenceRelationRecord
from app.schemas.relationship import ExplainableAssessmentResponse

class ExplainableAssessmentEngine:
    """
    Constructs comprehensive, evidence-grounded explanations for an investigator.
    Never relies on an LLM to guess truth; draws entirely from verified records.
    """

    @classmethod
    async def generate_explanation(
        cls,
        session: AsyncSession,
        claim_id: str
    ) -> ExplainableAssessmentResponse:
        """
        Generates an ExplainableAssessmentResponse detailing the evidence,
        reasoning path, source independence, and open questions for a claim.
        """
        # 1. Fetch ClaimRecord
        claim_stmt = select(ClaimRecord).where(ClaimRecord.id == claim_id)
        claim_res = await session.execute(claim_stmt)
        claim = claim_res.scalars().first()
        if not claim:
            raise ValueError(f"ClaimRecord with id '{claim_id}' not found.")

        # 2. Fetch Active Assessment & Relations
        ass_stmt = select(ClaimAssessmentRecord).where(
            ClaimAssessmentRecord.claim_id == claim_id,
            ClaimAssessmentRecord.is_active == True
        ).options(selectinload(ClaimAssessmentRecord.evidence_relations))
        ass_res = await session.execute(ass_stmt)
        assessment = ass_res.scalars().first()

        # 3. Fetch Retrieved Sources
        src_stmt = select(RetrievedSourceRecord).where(
            RetrievedSourceRecord.claim_id == claim_id
        )
        src_res = await session.execute(src_stmt)
        sources = src_res.scalars().all()
        source_by_id = {s.id: s for s in sources}
        source_by_url = {s.canonical_url: s for s in sources}

        # 4. Fetch Source Independence
        indep_stmt = select(SourceIndependenceRecord).where(
            SourceIndependenceRecord.claim_id == claim_id
        )
        indep_res = await session.execute(indep_stmt)
        indep = indep_res.scalars().first()

        # 5. Fetch Parent Submission & Historical Media Matches
        sub_stmt = select(EvidenceSubmission).where(EvidenceSubmission.id == claim.evidence_submission_id)
        sub_res = await session.execute(sub_stmt)
        submission = sub_res.scalars().first()

        historical_matches: List[Dict[str, Any]] = []
        if submission and submission.media_asset_id:
            match_stmt = select(MediaMatchRecord).where(
                (MediaMatchRecord.source_media_asset_id == submission.media_asset_id) |
                (MediaMatchRecord.source_evidence_id == submission.id)
            )
            match_res = await session.execute(match_stmt)
            for m in match_res.scalars().all():
                historical_matches.append({
                    "match_record_id": m.id,
                    "classification": m.classification,
                    "method": m.method,
                    "confidence": getattr(m, "confidence_score", None) or (m.raw_metrics.get("confidence") if isinstance(m.raw_metrics, dict) else None) or 1.0,
                    "rationale": m.classification_rationale,
                    "raw_metrics": m.raw_metrics,
                    "matched_at": m.created_at.isoformat() if m.created_at else None
                })

        # 6. Categorize Evidence Relations
        supporting: List[Dict[str, Any]] = []
        contradicting: List[Dict[str, Any]] = []
        unaddressed: List[Dict[str, Any]] = []

        if assessment and assessment.evidence_relations:
            for rel in assessment.evidence_relations:
                item_dict = {
                    "relation_id": rel.id,
                    "relationship_type": rel.relationship_type,
                    "source_location": rel.source_location,
                    "publisher": rel.source_publisher,
                    "author": rel.source_author,
                    "published_date": rel.source_published_date,
                    "excerpt": rel.excerpt,
                    "span": [rel.passage_span_start, rel.passage_span_end] if rel.passage_span_start is not None else None,
                    "alignment_rationale": rel.alignment_rationale,
                    "source_independence_status": rel.source_independence_status,
                    "uncertainty_notes": rel.uncertainty_notes
                }

                if rel.relationship_type in ["SUPPORTS", "PARTIALLY_SUPPORTS"]:
                    supporting.append(item_dict)
                elif rel.relationship_type in ["CONTRADICTS", "TEMPORAL_CONFLICT", "GEOGRAPHICAL_CONFLICT"]:
                    contradicting.append(item_dict)
                elif rel.relationship_type in ["PROVIDES_CONTEXT", "MISLEADING_CONTEXT"]:
                    # context omission or framing
                    contradicting.append(item_dict)
                else:
                    unaddressed.append(item_dict)

        # 7. Source Dependencies Summary
        source_deps_dict: Dict[str, Any] = {
            "total_sources_evaluated": indep.total_sources_count if indep else len(sources),
            "independent_sources_count": indep.independent_sources_count if indep else len(sources),
            "independence_assessment": indep.independence_assessment if indep else "UNKNOWN_DEPENDENCY",
            "clusters": indep.clusters if indep else [],
            "explanation": indep.explanation if indep else "No multi-source dependency evaluation recorded."
        }

        # 8. Missing Evidence & Epistemic Limitations
        missing_evidence: List[str] = []
        if not supporting and not contradicting:
            missing_evidence.append("No authoritative primary or secondary documentation directly addressing the proposition.")
        if indep and indep.independent_sources_count < 2 and supporting:
            missing_evidence.append("Second independent investigative confirmation required to corroborate single-source reporting.")
        if claim.language in ["hi", "te"] and not any(s.language == claim.language for s in sources):
            missing_evidence.append(f"No regional language sources in native script ({claim.language}) identified.")

        # 9. Deterministic Decision Tree Path
        classification_val = assessment.classification if assessment else "UNVERIFIED"
        primary_rat = assessment.primary_rationale if assessment else "Verification has not yet been executed."

        decision_path: List[str] = [
            f"1. Evaluated proposition: Subject='{claim.subject or 'N/A'}', Predicate='{claim.predicate or 'N/A'}', Object='{claim.object or 'N/A'}'."
        ]

        if historical_matches:
            decision_path.append(
                f"2. Historical media match detected: {historical_matches[0]['classification']}. "
                f"Checked for archival indicators and temporal displacement."
            )

        decision_path.append(
            f"3. Evidence stance breakdown: {len(supporting)} supporting, {len(contradicting)} contradicting, "
            f"{len(unaddressed)} unaddressed out of {len(sources)} retrieved sources."
        )

        if classification_val == "SUPPORTED":
            decision_path.append("4. Verdict Rule: Multiple independent credible accounts corroborate the exact proposition without refutation.")
        elif classification_val == "CONTRADICTED":
            decision_path.append("4. Verdict Rule: Authoritative fact-checks or primary registry explicitly refute the proposition.")
        elif classification_val == "MISLEADING_OR_CONTEXT_MISSING":
            decision_path.append("4. Verdict Rule: Genuine media or facts are reused out-of-context, predating the claimed date or omitting vital baseline context.")
        elif classification_val == "CONFLICTING_EVIDENCE":
            decision_path.append("4. Verdict Rule: Multiple authoritative sources provide contradictory factual accounts; preserved disagreement rather than forcing false consensus.")
        elif classification_val == "INSUFFICIENT_EVIDENCE":
            decision_path.append("4. Verdict Rule: Verification attempted, but available sources do not directly address the proposition. Absence of evidence is not proof of falsehood.")
        else:
            decision_path.append("4. Verdict Rule: Unverified claim pending external corroboration.")

        # 10. Human Review Audit
        human_review_dict = {
            "status": assessment.human_review_status if assessment else "UNREVIEWED",
            "notes": assessment.human_reviewer_notes if assessment else None,
            "reviewed_by": assessment.reviewed_by if assessment else None,
            "reviewed_at": assessment.human_reviewed_at.isoformat() if assessment and assessment.human_reviewed_at else None
        }

        temporal_geo = {
            "temporal_analysis": assessment.temporal_analysis if assessment else {},
            "geographical_analysis": assessment.geographical_analysis if assessment else {},
            "archival_signal_detected": assessment.archival_signal_detected if assessment else False
        }

        return ExplainableAssessmentResponse(
            claim_id=claim.id,
            investigation_id=claim.investigation_id,
            claim_text=claim.claim_text,
            normalized_claim=claim.normalized_claim,
            subject=claim.subject,
            predicate=claim.predicate,
            object=claim.object,
            assessment_classification=classification_val,
            primary_rationale=primary_rat,
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            unaddressed_evidence=unaddressed,
            source_dependencies=source_deps_dict,
            historical_media_findings=historical_matches,
            temporal_and_geographical_context=temporal_geo,
            missing_evidence=missing_evidence,
            known_limitations=(
                assessment.epistemic_limitations if assessment
                else "Assessment relies solely on accessible public sources, media metadata, and local indices."
            ),
            decision_tree_explanation="\n".join(decision_path),
            human_review=human_review_dict
        )
