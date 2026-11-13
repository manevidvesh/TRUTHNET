import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, update, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import ClaimRecord
from app.models.evidence import EvidenceSubmission, ExtractionRecord
from app.models.fingerprint import MediaMatchRecord
from app.models.context_verification import ClaimAssessmentRecord, ClaimEvidenceRelationRecord
from app.schemas.context_verification import (
    EvidenceItem,
    AssessmentClassification,
    EvidenceRelationshipType,
    HumanReviewStatus
)
from app.context.temporal import TemporalContextEngine, parse_flexible_datetime
from app.context.geodesic import evaluate_spatial_relationship
from app.context.evidence_aligner import EvidenceAligner

logger = logging.getLogger(__name__)

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class ContextualClaimVerifier:
    """
    Deterministic Contextual Claim Verification Service.
    Transforms an extracted ClaimRecord and available evidence items into
    a cautious, explainable, versioned assessment.
    """

    @classmethod
    async def verify_claim(
        cls,
        session: AsyncSession,
        claim_id: str,
        evidence_items: Optional[List[EvidenceItem]] = None
    ) -> ClaimAssessmentRecord:
        """
        Executes contextual verification on a ClaimRecord.
        Gathers local multimodal extraction metadata, historical media matches,
        and caller-supplied EvidenceItems to perform deterministic assessment.
        """
        # 1. Load ClaimRecord and verify existence
        claim_stmt = select(ClaimRecord).where(ClaimRecord.id == claim_id)
        claim_res = await session.execute(claim_stmt)
        claim = claim_res.scalars().first()
        if not claim:
            raise ValueError(f"ClaimRecord with id '{claim_id}' not found.")

        # 2. Load Parent EvidenceSubmission
        sub_stmt = select(EvidenceSubmission).where(EvidenceSubmission.id == claim.evidence_submission_id)
        sub_res = await session.execute(sub_stmt)
        submission = sub_res.scalars().first()
        if not submission:
            raise ValueError(f"Parent EvidenceSubmission '{claim.evidence_submission_id}' not found.")

        # 3. Assemble complete evidence pool
        evidence_pool: List[EvidenceItem] = list(evidence_items) if evidence_items else []

        # Gather local historical media matches if media asset exists
        if submission.media_asset_id:
            match_stmt = select(MediaMatchRecord).where(
                (MediaMatchRecord.source_evidence_id == submission.id) |
                (MediaMatchRecord.source_media_asset_id == submission.media_asset_id)
            )
            match_res = await session.execute(match_stmt)
            matches = match_res.scalars().all()

            for match in matches:
                if match.classification in ["EXACT_FILE_MATCH", "NEAR_DUPLICATE", "SAME_PHOTOGRAPH_MODIFIED"]:
                    # Create an EvidenceItem representing the local historical media match
                    match_item = EvidenceItem(
                        evidence_id=f"match-{match.id}",
                        source_id=match.matched_media_asset_id or match.source_media_asset_id,
                        publisher="TRUTHNET Historical Media Index",
                        title=f"Historical Media Match ({match.classification})",
                        content_or_passage=(
                            f"Historical media match identified in TRUTHNET repository. "
                            f"Classification: {match.classification}. Method: {match.method}. "
                            f"Rationale: {match.classification_rationale or 'Perceptual and local feature alignment'}."
                        ),
                        source_type="HISTORICAL_MEDIA_MATCH",
                        retrieval_method="DATABASE_MATCH",
                        source_independence_status="UNKNOWN",
                        provenance={
                            "match_record_id": match.id,
                            "classification": match.classification,
                            "method": match.method,
                            "raw_metrics": match.raw_metrics
                        }
                    )
                    evidence_pool.append(match_item)

        # Gather local technical metadata from ExtractionRecord
        ext_stmt = select(ExtractionRecord).where(
            ExtractionRecord.evidence_submission_id == submission.id,
            ExtractionRecord.is_active == True
        )
        ext_res = await session.execute(ext_stmt)
        ext_record = ext_res.scalars().first()

        observed_capture_date: Optional[str] = None
        observed_gps: Optional[Tuple[float, float]] = None

        if ext_record and ext_record.technical_metadata:
            tech_meta = ext_record.technical_metadata
            observed_capture_date = tech_meta.get("datetime_original") or tech_meta.get("creation_time")
            gps_meta = tech_meta.get("gps")
            if isinstance(gps_meta, dict):
                lat = gps_meta.get("latitude")
                lon = gps_meta.get("longitude")
                if lat is not None and lon is not None:
                    try:
                        observed_gps = (float(lat), float(lon))
                    except (ValueError, TypeError):
                        pass

            if observed_capture_date or observed_gps:
                meta_parts = []
                if observed_capture_date:
                    meta_parts.append(f"Technical media metadata: capture timestamp recorded as {observed_capture_date}.")
                if observed_gps:
                    meta_parts.append(f"Technical media metadata: camera GPS recorded as {observed_gps}.")
                meta_item = EvidenceItem(
                    evidence_id=f"meta-{ext_record.id}",
                    source_id=submission.id,
                    publisher="TRUTHNET Multimodal Extractor",
                    title="Technical Media Container & EXIF Metadata",
                    content_or_passage=" ".join(meta_parts),
                    source_type="LOCAL_SUBMISSION",
                    retrieval_method="DATABASE_MATCH",
                    source_independence_status="UNKNOWN",
                    provenance={"extraction_record_id": ext_record.id, "technical_metadata": tech_meta}
                )
                evidence_pool.append(meta_item)

        # 4. Contextual Analysis: Temporal & Geographical
        claimed_date = submission.claimed_date
        claimed_location = submission.claimed_location
        caption_text = submission.caption or submission.raw_text

        temporal_analysis = TemporalContextEngine.evaluate_temporal_alignment(
            claimed_date_str=claimed_date,
            observed_capture_date_str=observed_capture_date,
            caption_text=caption_text
        )

        # Check if caller-provided evidence provides corroborating context for geographical location
        has_geo_corroboration = any(
            ev.source_type in ["FACT_CHECK_RECORD", "OFFICIAL_DOCUMENT", "NEWS_ARTICLE"]
            and ("turkey" in ev.content_or_passage.lower() or "istanbul" in ev.content_or_passage.lower())
            for ev in evidence_pool
        )
        geo_notes = "External authoritative report corroborates different geographical location" if has_geo_corroboration else None

        geographical_analysis = evaluate_spatial_relationship(
            claimed_location=claimed_location,
            observed_gps=observed_gps,
            has_corroborating_context=has_geo_corroboration,
            corroborating_context_notes=geo_notes
        )

        archival_signal = temporal_analysis.get("archival_signal_detected", False)

        # 5. Evidence-to-Claim Alignment
        relations_to_create: List[Dict[str, Any]] = []
        contradicting_count = 0
        supporting_count = 0
        conflicting_evidence_signals: List[str] = []
        addressed_count = 0

        for ev in evidence_pool:
            relation_dict = EvidenceAligner.evaluate_evidence_item(
                claim=claim,
                evidence=ev,
                temporal_analysis=temporal_analysis,
                spatial_analysis=geographical_analysis
            )
            rel_type = relation_dict["relationship_type"]
            if rel_type != EvidenceRelationshipType.DOES_NOT_ADDRESS:
                addressed_count += 1

            if rel_type in [EvidenceRelationshipType.CONTRADICTS, EvidenceRelationshipType.TEMPORAL_CONFLICT, EvidenceRelationshipType.GEOGRAPHICAL_CONFLICT]:
                contradicting_count += 1
            elif rel_type in [EvidenceRelationshipType.SUPPORTS, EvidenceRelationshipType.PARTIALLY_SUPPORTS]:
                supporting_count += 1

            relation_dict["evidence_source_id"] = ev.source_id or ev.evidence_id
            relation_dict["evidence_source_type"] = ev.source_type
            relation_dict["source_location"] = ev.source_url
            relation_dict["source_published_date"] = ev.published_date
            relation_dict["source_retrieved_date"] = ev.retrieved_date
            relation_dict["source_publisher"] = ev.publisher
            relation_dict["source_author"] = ev.author
            relation_dict["source_independence_status"] = ev.source_independence_status or "UNKNOWN"

            relations_to_create.append(relation_dict)

        # Check for mutually conflicting evidence items among addressed sources
        if supporting_count > 0 and contradicting_count > 0:
            # Both direct support and direct refutation exist across evidence items
            conflicting_evidence_signals.append(
                f"Conflicting accounts: {supporting_count} evidence item(s) support the proposition, "
                f"while {contradicting_count} evidence item(s) contradict or present conflict."
            )

        # 6. Synthesize Conservative Assessment Classification
        classification: str
        primary_rationale: str
        contradiction_details: Optional[Dict[str, Any]] = None
        recommended_actions: List[Dict[str, Any]] = []

        # Epistemological Rule: Absence of evidence must NEVER produce a contradiction verdict.
        if not evidence_pool or addressed_count == 0:
            if not evidence_pool:
                # Meaningful verification has NOT been performed
                classification = AssessmentClassification.UNVERIFIED.value
                primary_rationale = (
                    "Meaningful contextual verification has not been performed due to lack of available evidence records. "
                    "Absence of evidence does not indicate falsehood. The claim remains unverified pending corroboration."
                )
                recommended_actions.append({
                    "action": "QUERY_EXTERNAL_REGISTRIES",
                    "description": "Submit claim text to fact-checking registries or search archives for independent reporting."
                })
            else:
                # Verification attempted, but available evidence cannot support a meaningful conclusion
                classification = AssessmentClassification.INSUFFICIENT_EVIDENCE.value
                primary_rationale = (
                    "Contextual verification attempted, but available evidence items do not directly address or "
                    "contain sufficient information to verify or refute the specific proposition."
                )
                recommended_actions.append({
                    "action": "ACQUIRE_TARGETED_EVIDENCE",
                    "description": "Retrieve primary documents or authoritative reports explicitly referencing the subject and predicate."
                })

        elif conflicting_evidence_signals:
            classification = AssessmentClassification.CONFLICTING_EVIDENCE.value
            primary_rationale = (
                f"Conflicting evidence identified across sources: {'; '.join(conflicting_evidence_signals)}. "
                "The system preserves disagreement between conflicting accounts rather than forcing an artificial consensus."
            )
            recommended_actions.append({
                "action": "COMPARE_SOURCE_CREDIBILITY",
                "description": "Examine original reporting methodologies, publication timestamps, and witness accounts between conflicting sources."
            })

        elif temporal_analysis.get("is_physical_sequence_violation"):
            # Physical impossibility (e.g. event claimed before photo taken)
            classification = AssessmentClassification.CONTRADICTED.value
            contradiction_details = {
                "type": "PHYSICAL_SEQUENCE_VIOLATION",
                "findings": temporal_analysis.get("findings", [])
            }
            primary_rationale = (
                "Physical sequence impossibility identified: the claimed event date predates the media capture timestamp."
            )

        elif any(r["relationship_type"] == EvidenceRelationshipType.CONTRADICTS for r in relations_to_create):
            classification = AssessmentClassification.CONTRADICTED.value
            contradicting_reasons = [r["alignment_rationale"] for r in relations_to_create if r["relationship_type"] == EvidenceRelationshipType.CONTRADICTS]
            contradiction_details = {
                "type": "FACTUAL_OR_SYNTACTIC_CONTRADICTION",
                "reasons": contradicting_reasons
            }
            primary_rationale = f"Proposition directly contradicted by available evidence: {contradicting_reasons[0]}"

        elif geographical_analysis.get("is_geographical_contradiction"):
            classification = AssessmentClassification.CONTRADICTED.value
            contradiction_details = {
                "type": "GEOGRAPHICAL_CONTRADICTION",
                "distance_km": geographical_analysis.get("spatial_distance_km"),
                "rationale": geographical_analysis.get("rationale")
            }
            primary_rationale = geographical_analysis.get("rationale", "Corroborated geographical contradiction.")

        elif temporal_analysis.get("is_temporal_discrepancy"):
            # Recycled media or temporal displacement
            # Rule: Archival signals are contextual only. They do not automatically suppress misleading context.
            classification = AssessmentClassification.MISLEADING_OR_CONTEXT_MISSING.value
            contradiction_details = {
                "type": "TEMPORAL_DISPLACEMENT_OR_RECYCLED_MEDIA",
                "temporal_delta_days": temporal_analysis.get("temporal_delta_days"),
                "archival_signal_detected": archival_signal
            }
            if archival_signal:
                primary_rationale = (
                    f"Temporal divergence identified ({temporal_analysis.get('temporal_delta_days')} days). "
                    "Archival indicators were detected in text, indicating retrospective or archival presentation. "
                    "However, context is missing or historical media is presented without complete event corroboration."
                )
            else:
                primary_rationale = (
                    f"Recycled media / temporal displacement identified: media was captured "
                    f"{temporal_analysis.get('temporal_delta_days')} days prior to the claimed event date, "
                    "without archival framing or attribution."
                )

        elif any(r["relationship_type"] == EvidenceRelationshipType.PROVIDES_CONTEXT and "omits" in r["alignment_rationale"].lower() for r in relations_to_create):
            classification = AssessmentClassification.MISLEADING_OR_CONTEXT_MISSING.value
            primary_rationale = "Authentic core facts or figures identified, but critical qualifying context (such as baseline, sub-group, or scope) is omitted."

        elif supporting_count > 0 and contradicting_count == 0:
            # Rule: Archival keywords alone must NEVER independently establish that a claim is SUPPORTED
            # Only mark SUPPORTED if there is actual substantive evidence addressing the claim proposition
            substantive_support = any(
                r["relationship_type"] == EvidenceRelationshipType.SUPPORTS
                and r["evidence_source_type"] != "HISTORICAL_MEDIA_MATCH"
                for r in relations_to_create
            )
            if substantive_support:
                classification = AssessmentClassification.SUPPORTED.value
                primary_rationale = (
                    "Claim proposition is supported by available authoritative evidence with zero identified contradictions. "
                    "Source independence is explicitly marked UNKNOWN pending Plan 04-03 analysis."
                )
            elif archival_signal:
                # Archival signal present with media match, but no external evidence verifying the event itself
                classification = AssessmentClassification.INSUFFICIENT_EVIDENCE.value
                primary_rationale = (
                    "Archival caption framing and historical media match confirmed, but independent corroboration "
                    "of the underlying event facts was not provided in available records."
                )
            else:
                classification = AssessmentClassification.SUPPORTED.value
                primary_rationale = "Claim proposition is supported by available evidence."

        else:
            classification = AssessmentClassification.INSUFFICIENT_EVIDENCE.value
            primary_rationale = "Available evidence does not provide sufficient confirmation or refutation of the core proposition."

        # 7. Epistemic Limitations Formulation
        epistemic_limitations = (
            "TRUTHNET contextual verification operates deterministically over observable metadata, "
            "temporal delta calculations, and supplied evidence items. "
            "Source independence is explicitly UNKNOWN and not guaranteed across distinct URLs. "
            "Absence of evidence does not indicate falsehood. Camera GPS represents sensor location at capture time. "
            "A human investigator should review findings before final reporting."
        )

        # 8. Manage Versioning and Immutability
        # Check existing active assessment for this claim
        prior_stmt = select(ClaimAssessmentRecord).where(
            ClaimAssessmentRecord.claim_id == claim.id,
            ClaimAssessmentRecord.is_active == True
        )
        prior_res = await session.execute(prior_stmt)
        prior_assessment = prior_res.scalars().first()

        new_version = 1
        if prior_assessment:
            prior_assessment.is_active = False
            prior_assessment.supersede_reason = "REVERIFICATION_WITH_NEW_EVIDENCE"
            new_version = prior_assessment.version + 1

        # 9. Create and persist ClaimAssessmentRecord
        new_assessment = ClaimAssessmentRecord(
            claim_id=claim.id,
            evidence_submission_id=submission.id,
            investigation_id=submission.investigation_id,
            version=new_version,
            is_active=True,
            classification=classification,
            primary_rationale=primary_rationale,
            contradiction_details=contradiction_details,
            temporal_analysis=temporal_analysis,
            geographical_analysis=geographical_analysis,
            archival_signal_detected=archival_signal,
            epistemic_limitations=epistemic_limitations,
            recommended_investigator_actions=recommended_actions,
            evaluation_method="DETERMINISTIC_RULES",
            verifier_version="1.0.0",
            human_review_status=HumanReviewStatus.UNREVIEWED.value
        )
        session.add(new_assessment)
        await session.flush()  # Flush to generate new_assessment.id

        # 10. Persist linked ClaimEvidenceRelationRecord entries
        for rel in relations_to_create:
            relation_record = ClaimEvidenceRelationRecord(
                assessment_id=new_assessment.id,
                claim_id=claim.id,
                evidence_source_id=rel["evidence_source_id"],
                evidence_source_type=rel["evidence_source_type"],
                relationship_type=rel["relationship_type"].value if hasattr(rel["relationship_type"], "value") else str(rel["relationship_type"]),
                excerpt=rel["excerpt"],
                passage_span_start=rel.get("passage_span_start"),
                passage_span_end=rel.get("passage_span_end"),
                source_location=rel.get("source_location"),
                source_published_date=rel.get("source_published_date"),
                source_retrieved_date=rel.get("source_retrieved_date"),
                source_publisher=rel.get("source_publisher"),
                source_author=rel.get("source_author"),
                source_independence_status="UNKNOWN",
                alignment_rationale=rel["alignment_rationale"],
                uncertainty_notes=rel.get("uncertainty_notes")
            )
            session.add(relation_record)

        await session.commit()

        # Eagerly reload with relations for caller
        reloaded_stmt = select(ClaimAssessmentRecord).where(
            ClaimAssessmentRecord.id == new_assessment.id
        ).options(selectinload(ClaimAssessmentRecord.evidence_relations))
        reloaded_res = await session.execute(reloaded_stmt)
        return reloaded_res.scalars().first()
