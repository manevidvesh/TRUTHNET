"""
TRUTHNET AI — Plan 04-04 Demonstration Scenario
Execution of Complete Claim Lineage, Evidence Relationships & Explainable Intelligence Workbench.

Demonstrates:
1. Investigation with multiple submissions, multimodal assets, and related claim variants.
2. Automated and inferred relationships (SAME_CLAIM, CLAIM_VARIANT, SUPPORTS, MISLEADING_CONTEXT).
3. Historical media rediscovery integration with privacy-preserving provenance.
4. Multi-signal source independence clustering (distinguishing independent reporting from syndication).
5. Deterministic Explainable Assessment with complete decision-tree reasoning and epistemic boundaries.
6. Evidence Drawer lookup resolving underlying evidence records.
7. Visual Lineage Explorer URL output.
"""

import asyncio
import sys
import os
import uuid
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.database import Base
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
    LineageReviewStatus
)
from app.lineage.graph_engine import LineageGraphEngine
from app.lineage.assessment_engine import ExplainableAssessmentEngine


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def run_demonstration():
    print("=" * 80)
    print("TRUTHNET AI — PLAN 04-04 DEMONSTRATION SCENARIO")
    print("Claim Lineage, Evidence Relationships & Explainable Intelligence")
    print("=" * 80)

    # 1. Setup isolated in-memory or temporary database
    db_file = Path("truthnet_lineage_demo.db")
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file.name}", echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        print("\n[Step 1] Constructing Multi-Signal Investigation Scenario...")
        now = utc_now()

        # 1. Create Investigation
        inv = Investigation(
            title="INV-2026-088: Viral Flood Devastation Report in Cyberabad Tech Corridor",
            description="Investigating viral social media claims alleging unprecedented catastrophic flooding in Cyberabad.",
            priority="HIGH",
            status="ACTIVE"
        )
        session.add(inv)
        await session.flush()
        print(f"  * Created Investigation: {inv.title} (ID: {inv.id})")

        # 2. Historical Archived Asset (from 2020 Hyderabad floods)
        archived_asset = MediaAsset(
            file_path="archives/hyderabad_floods_oct_2020.jpg",
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            mime_type="image/jpeg",
            file_size_bytes=245760
        )
        session.add(archived_asset)
        await session.flush()

        # 3. New Suspect Media Asset & Submission
        suspect_asset = MediaAsset(
            file_path="uploads/cyberabad_flood_viral_2026.jpg",
            sha256_hash="f1d2d2f924e986ac86fdf7b36c94bcdf32beec15def9b2a15e3148d8f4187077",
            mime_type="image/jpeg",
            file_size_bytes=239100
        )
        session.add(suspect_asset)
        await session.flush()

        sub1 = EvidenceSubmission(
            investigation_id=inv.id,
            media_asset_id=suspect_asset.id,
            submission_type="IMAGE",
            caption="Devastating unprecedented floods submerge Cyberabad tech corridor today!",
            claimed_event="Cyberabad Flood",
            claimed_date="2026-09-12",
            claimed_location="Cyberabad, Hyderabad",
            language="en",
            processing_status="COMPLETED"
        )
        sub2 = EvidenceSubmission(
            investigation_id=inv.id,
            submission_type="TEXT",
            raw_text="Breaking news: Tech corridor in Cyberabad flooded with waterlogging reaching 4 feet.",
            caption="Breaking news: Tech corridor in Cyberabad flooded with waterlogging reaching 4 feet.",
            claimed_event="Cyberabad Waterlogging",
            claimed_date="2026-09-12",
            claimed_location="Cyberabad, Hyderabad",
            language="en",
            processing_status="COMPLETED"
        )
        session.add_all([sub1, sub2])
        await session.flush()
        print(f"  * Created Submissions: Sub1 (Image) ID={sub1.id}, Sub2 (Text) ID={sub2.id}")

        # 4. Extracted Claims & Variants
        claim1 = ClaimRecord(
            investigation_id=inv.id,
            evidence_submission_id=sub1.id,
            claim_text="Devastating unprecedented floods submerge Cyberabad tech corridor today",
            normalized_claim="Devastating unprecedented floods submerge Cyberabad tech corridor today",
            subject="Cyberabad tech corridor",
            predicate="submerged by",
            object="unprecedented floods",
            source_modality="IMAGE_CAPTION",
            polarity_state="AFFIRMATIVE_SURFACE_SYNTAX",
            evidence_span_start=0,
            evidence_span_end=70,
            source_text_hash="hash-claim-1",
            language="en",
            language_detection_method="DETERMINISTIC_ASCII"
        )
        claim2 = ClaimRecord(
            investigation_id=inv.id,
            evidence_submission_id=sub2.id,
            claim_text="Tech corridor in Cyberabad flooded with waterlogging reaching 4 feet",
            normalized_claim="Tech corridor in Cyberabad flooded with waterlogging reaching 4 feet",
            subject="Cyberabad tech corridor",
            predicate="submerged by",
            object="waterlogging reaching 4 feet",
            source_modality="TEXT",
            polarity_state="AFFIRMATIVE_SURFACE_SYNTAX",
            evidence_span_start=0,
            evidence_span_end=68,
            source_text_hash="hash-claim-2",
            language="en",
            language_detection_method="DETERMINISTIC_ASCII"
        )
        session.add_all([claim1, claim2])
        await session.flush()
        print(f"  * Created Claim 1: '{claim1.claim_text}' (ID: {claim1.id})")
        print(f"  * Created Claim 2: '{claim2.claim_text}' (ID: {claim2.id})")

        # 5. Historical Media Rediscovery Match
        media_match = MediaMatchRecord(
            source_media_asset_id=suspect_asset.id,
            source_evidence_id=sub1.id,
            matched_media_asset_id=archived_asset.id,
            classification="SAME_PHOTOGRAPH_MODIFIED",
            method="HISTORICAL_MEDIA_REDISCOVERY",
            classification_rationale="Geometric keypoint match with October 2020 Hyderabad monsoon archives; color rebalanced and cropped.",
            raw_metrics={
                "confidence": 0.96,
                "inlier_ratio": 0.88,
                "homography_inliers": 142,
                "archived_date": "2020-10-14",
                "original_event": "Hyderabad October 2020 Flash Floods"
            },
            disclaimer="Visual match indicates geometric similarity. Requires contextual verification."
        )
        session.add(media_match)

        # 6. Retrieved External Sources
        src1 = RetrievedSourceRecord(
            investigation_id=inv.id,
            claim_id=claim1.id,
            original_url="https://timesofindia.indiatimes.com/city/hyderabad/fake-alert-2020-flood-pics-recirculated/articleshow/99881122.cms",
            canonical_url="https://timesofindia.indiatimes.com/city/hyderabad/fake-alert-2020-flood-pics-recirculated/articleshow/99881122.cms",
            article_title="Times Fact Check: Old 2020 Hyderabad Flood Photos Falsely Circulated as Current Cyberabad Flooding",
            publisher="Times of India",
            published_date=(now - timedelta(hours=3)).isoformat(),
            retrieval_timestamp=now,
            language="en",
            source_type="FACT_CHECK",
            retrieval_method="SEARCH_SCRAPE",
            content_hash="hash-toi-factcheck",
            text_excerpt="Police and weather authorities confirmed no catastrophic flooding occurred in Cyberabad today. The viral visual depicts the October 2020 deluge in Tolichowki.",
            retrieval_status="SUCCESS"
        )
        src2 = RetrievedSourceRecord(
            investigation_id=inv.id,
            claim_id=claim1.id,
            original_url="https://www.thehindu.com/news/cities/Hyderabad/light-showers-in-cyberabad-traffic-normal/article883311.ece",
            canonical_url="https://www.thehindu.com/news/cities/Hyderabad/light-showers-in-cyberabad-traffic-normal/article883311.ece",
            article_title="Light Showers in Cyberabad; Traffic Remains Normal, IT Corridor Fully Operational",
            publisher="The Hindu",
            published_date=(now - timedelta(hours=5)).isoformat(),
            retrieval_timestamp=now,
            language="en",
            source_type="NEWS",
            retrieval_method="SEARCH_SCRAPE",
            content_hash="hash-thehindu-report",
            text_excerpt="Cyberabad Traffic Police advised commuters that light showers were recorded, but all tech park underpasses and arteries remain clear and operational.",
            retrieval_status="SUCCESS"
        )
        session.add_all([src1, src2])
        await session.flush()

        # 7. Multi-Signal Source Independence
        source_dep = SourceIndependenceRecord(
            claim_id=claim1.id,
            total_sources_count=2,
            independent_sources_count=2,
            independence_assessment="INDEPENDENT_REPORTING",
            clusters=[
                {"cluster_id": 1, "publisher": "Times of India", "sources": [src1.original_url], "dependency_type": "INDEPENDENT_FACT_CHECK"},
                {"cluster_id": 2, "publisher": "The Hindu", "sources": [src2.original_url], "dependency_type": "INDEPENDENT_PRIMARY_REPORTING"}
            ],
            explanation="Both Times of India Fact Check and The Hindu published independent investigative and on-ground reporting without shared wire syndication."
        )
        session.add(source_dep)

        # 8. Contextual Assessment
        assessment = ClaimAssessmentRecord(
            investigation_id=inv.id,
            claim_id=claim1.id,
            evidence_submission_id=sub1.id,
            version=1,
            is_active=True,
            classification="MISLEADING_OR_CONTEXT_MISSING",
            primary_rationale=(
                "Genuine historical photograph from October 2020 Hyderabad floods recirculated out of context to claim "
                "unprecedented current flooding in Cyberabad. Official municipal and traffic records confirm conditions are normal."
            ),
            archival_signal_detected=True,
            epistemic_limitations="Assessment is verified against certified local meteorological reports, media rediscovery index, and verified news publications.",
            human_review_status="UNREVIEWED"
        )
        session.add(assessment)
        await session.flush()

        # 9. Evidence Relations
        rel1 = ClaimEvidenceRelationRecord(
            assessment_id=assessment.id,
            claim_id=claim1.id,
            evidence_source_id=src1.id,
            evidence_source_type="RETRIEVED_SOURCE",
            relationship_type="CONTRADICTS",
            source_location=src1.canonical_url,
            source_publisher="Times of India",
            excerpt="Police and weather authorities confirmed no catastrophic flooding occurred in Cyberabad today. The viral visual depicts the October 2020 deluge.",
            source_independence_status="INDEPENDENT",
            alignment_rationale="Explicit refutation of the claim and confirmation of 2020 photo reuse."
        )
        rel2 = ClaimEvidenceRelationRecord(
            assessment_id=assessment.id,
            claim_id=claim1.id,
            evidence_source_id=src2.id,
            evidence_source_type="RETRIEVED_SOURCE",
            relationship_type="CONTRADICTS",
            source_location=src2.canonical_url,
            source_publisher="The Hindu",
            excerpt="All tech park underpasses and arteries remain clear and operational.",
            source_independence_status="INDEPENDENT",
            alignment_rationale="Corroborates that tech corridor is not submerged."
        )
        session.add_all([rel1, rel2])

        # 10. Human Review Record
        human_rel = LineageRelationshipRecord(
            investigation_id=inv.id,
            source_entity_id=f"claim_{claim2.id}",
            source_entity_type="CLAIM",
            target_entity_id=f"claim_{claim1.id}",
            target_entity_type="CLAIM",
            relationship_type="CLAIM_VARIANT",
            edge_nature="INFERRED",
            is_inferred=True,
            evidence_summary="Textual submission reproduces identical viral claim with numerical waterlogging embellishment.",
            detection_method="HUMAN_CONFIRMATION",
            review_status="CONFIRMED",
            reviewer_notes="Confirmed by investigator. Text post accompanied the viral recirculated photo on Telegram.",
            reviewed_by="investigator_sarah",
            reviewed_at=utc_now()
        )
        session.add(human_rel)
        await session.commit()
        print("  * Persisted all relationships, historical matches, and assessment records.")

        # =====================================================================
        # [Step 2] Lineage Graph Generation
        # =====================================================================
        print("\n" + "=" * 80)
        print("[Step 2] Generating Complete Lineage Graph (NetworkX MultiDiGraph)")
        print("=" * 80)

        graph_response = await LineageGraphEngine.build_investigation_graph(
            session=session,
            investigation_id=inv.id,
            include_inferred=True
        )

        print(f"Total Graph Nodes : {graph_response.node_count}")
        print(f"Total Graph Edges : {graph_response.edge_count}")
        print("\n--- GRAPH NODES ---")
        for node in graph_response.nodes:
            print(f"  [{node.entity_type:<18}] ID: {node.id:<38} | Label: {node.label}")

        print("\n--- GRAPH EDGES (Lineage Relationships) ---")
        for edge in graph_response.edges:
            nature = f"[{edge.edge_nature}]"
            rev = f"({edge.review_status})" if edge.review_status != "UNREVIEWED" else ""
            print(f"  {edge.source_id:<36} --({edge.relationship_type:<22} {nature:<10} {rev})--> {edge.target_id}")

        # =====================================================================
        # [Step 3] Chronological Timeline Reconstruction
        # =====================================================================
        print("\n" + "=" * 80)
        print("[Step 3] Chronological Lineage Timeline Reconstruction")
        print("=" * 80)

        timeline_resp = await LineageGraphEngine.build_investigation_timeline(
            session=session,
            investigation_id=inv.id
        )
        print(f"Total Chronological Events: {timeline_resp.total_events}")
        for event in timeline_resp.events:
            print(f"  [{event.timestamp[:19]}] {event.timestamp_type:<26} | {event.label}")

        # =====================================================================
        # [Step 4] Deep Evidence Drawer Inspection
        # =====================================================================
        print("\n" + "=" * 80)
        print("[Step 4] Deep Evidence Drawer Inspection (Underlying Record Lookup)")
        print("=" * 80)

        # Inspect the historical match edge between suspect asset and archived asset
        hist_edge = next(e for e in graph_response.edges if e.relationship_type == LineageRelationshipType.SAME_PHOTOGRAPH_CANDIDATE)
        print(f"Selected Edge ID: {hist_edge.id}")
        print(f"Relationship    : {hist_edge.relationship_type} ({hist_edge.edge_nature})")
        print(f"Detection Method: {hist_edge.detection_method}")
        print(f"Evidence ID     : {hist_edge.evidence_id}")
        print(f"Summary         : {hist_edge.evidence_summary}")
        print(f"Metrics (Drawer): {json.dumps(hist_edge.metadata, indent=4)}")

        # =====================================================================
        # [Step 5] Deterministic Explainable Assessment Breakdown
        # =====================================================================
        print("\n" + "=" * 80)
        print("[Step 5] Deterministic Explainable Assessment Breakdown")
        print("=" * 80)

        explanation = await ExplainableAssessmentEngine.generate_explanation(
            session=session,
            claim_id=claim1.id
        )

        print(f"Claim Text        : {explanation.claim_text}")
        print(f"Classification    : {explanation.assessment_classification}")
        print(f"Primary Rationale : {explanation.primary_rationale}")
        print(f"\n--- Decision Tree Rationale Path ---\n{explanation.decision_tree_explanation}")
        
        print("\n--- Supporting Evidence ---")
        if explanation.supporting_evidence:
            for s in explanation.supporting_evidence:
                print(f"  * [{s['publisher']}] {s['excerpt']}")
        else:
            print("  (None)")

        print("\n--- Contradicting Evidence ---")
        for c in explanation.contradicting_evidence:
            print(f"  * [{c['publisher']}] {c['excerpt']}")

        print("\n--- Source Independence Breakdown ---")
        deps = explanation.source_dependencies
        print(f"  * Total Sources Evaluated : {deps['total_sources_evaluated']}")
        print(f"  * Independent Sources     : {deps['independent_sources_count']}")
        print(f"  * Independence Verdict    : {deps['independence_assessment']}")
        print(f"  * Synthesis Explanation   : {deps['explanation']}")

        print("\n--- Historical Media Rediscovery Findings ---")
        for m in explanation.historical_media_findings:
            print(f"  * Classification: {m['classification']} (Confidence: {m['confidence']})")
            print(f"  * Rationale     : {m['rationale']}")
            print(f"  * Archival Date : {m['raw_metrics'].get('archived_date')} | Event: {m['raw_metrics'].get('original_event')}")

        print("\n--- Epistemic Boundaries & Known Limitations ---")
        print(f"  * {explanation.known_limitations}")

        print("\n" + "=" * 80)
        print(f"Interactive Lineage Explorer UI available at:")
        print(f"http://localhost:8000/api/v1/investigations/{inv.id}/lineage/explorer")
        print("=" * 80)

    await engine.dispose()
    db_file.unlink(missing_ok=True)


if __name__ == "__main__":
    asyncio.run(run_demonstration())
