"""
Seed script for TRUTHNET AI Intelligence Workbench demo data.
Populates backend/data/truthnet.db with a complete showcase investigation:
- Dual multimodal evidence submissions (recirculated flood image + claim text)
- Syntactic claim extraction with surface polarity
- Historical media rediscovery match against 2020 archive (142 ORB inliers, 0.88 ratio)
- Multi-signal source independence analysis (independent reporting without wire syndication)
- Contextual claim verification (verdict: MISLEADING_OR_CONTEXT_MISSING)
- Investigator human review determination (HUMAN_CONFIRMED)
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from sqlalchemy import select
from app.core.database import engine, async_session_factory, Base
from app.models.investigation import Investigation
from app.models.evidence import EvidenceSubmission, MediaAsset
from app.models.claim import ClaimRecord
from app.models.source import RetrievedSourceRecord, SourceIndependenceRecord
from app.models.fingerprint import MediaMatchRecord
from app.models.context_verification import ClaimAssessmentRecord, ClaimEvidenceRelationRecord
from app.models.relationship import LineageRelationshipRecord

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

async def seed_data():
    print("=" * 80)
    print("TRUTHNET AI — SEEDING DEMONSTRATION DATASET INTO APPLICATION DATABASE")
    print("=" * 80)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        # Check if already seeded
        existing = await session.execute(
            select(Investigation).where(Investigation.title.like("%INV-2026-088%"))
        )
        inv = existing.scalars().first()
        if inv:
            print(f"[*] Showcase Investigation already exists: '{inv.title}' (ID: {inv.id})")
        else:
            now = utc_now()
            today_str = now.strftime("%Y-%m-%d")

            # 1. Create Investigation
            inv = Investigation(
                title="INV-2026-088 [SIMULATED — NOT LIVE EXTERNAL EVIDENCE]: Viral Flood Devastation Report in Cyberabad Tech Corridor",
                description="[SIMULATED] Investigating recirculated 2020 imagery falsely alleged as today's catastrophic flooding in Cyberabad.",
                priority="HIGH",
                status="ACTIVE"
            )
            session.add(inv)
            await session.flush()
            print(f"[+] Created Investigation: {inv.title}")

            # 2. Historical Archived Asset
            archived_asset = MediaAsset(
                file_path="archives/hyderabad_floods_oct_2020.jpg",
                sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                mime_type="image/jpeg",
                file_size_bytes=245760
            )
            session.add(archived_asset)
            await session.flush()

            # 3. New Suspect Media Asset & Submissions
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
                claimed_date=today_str,
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
                claimed_date=today_str,
                claimed_location="Cyberabad, Hyderabad",
                language="en",
                processing_status="COMPLETED"
            )
            session.add_all([sub1, sub2])
            await session.flush()

            # 4. Extracted Claims
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

            # 5. Historical Media Rediscovery Match
            media_match = MediaMatchRecord(
                source_media_asset_id=suspect_asset.id,
                source_evidence_id=sub1.id,
                matched_media_asset_id=archived_asset.id,
                classification="SAME_PHOTOGRAPH_MODIFIED",
                method="HISTORICAL_MEDIA_REDISCOVERY",
                classification_rationale="Geometric keypoint match with October 2020 Hyderabad monsoon archives; color rebalanced and cropped.",
                raw_metrics={
                    "homography_inliers": 142,
                    "inlier_ratio": 0.88,
                    "phash_distance": 6,
                    "dhash_distance": 4,
                    "ransac_status": "CONVERGED_VALID_HOMOGRAPHY",
                    "archived_date": "2020-10-14",
                    "original_event": "Hyderabad October 2020 Flash Floods",
                    "is_candidate_match": True,
                    "requires_human_review": True
                },
                disclaimer="Candidate visual match requiring investigator review. Measurement indicates feature correspondence, not absolute identity."
            )
            session.add(media_match)

            # 6. Retrieved External Sources
            src1 = RetrievedSourceRecord(
                investigation_id=inv.id,
                claim_id=claim1.id,
                original_url="https://timesofindia.indiatimes.com/city/hyderabad/fake-alert-2020-flood-pics-recirculated/articleshow/99881122.cms",
                canonical_url="https://timesofindia.indiatimes.com/city/hyderabad/fake-alert-2020-flood-pics-recirculated/articleshow/99881122.cms",
                article_title="[SIMULATED] Times Fact Check: Old 2020 Hyderabad Flood Photos Falsely Circulated as Current Cyberabad Flooding",
                publisher="Times of India",
                published_date=(now - timedelta(hours=3)).isoformat(),
                retrieval_timestamp=now,
                language="en",
                source_type="FACT_CHECK",
                retrieval_method="SEARCH_SCRAPE",
                content_hash="hash-toi-factcheck",
                text_excerpt="[SIMULATED — NOT LIVE EXTERNAL EVIDENCE] Police and weather authorities confirmed no catastrophic flooding occurred in Cyberabad today. The viral visual depicts the October 2020 deluge in Tolichowki.",
                retrieval_status="SUCCESS"
            )
            src2 = RetrievedSourceRecord(
                investigation_id=inv.id,
                claim_id=claim1.id,
                original_url="https://www.thehindu.com/news/cities/Hyderabad/light-showers-in-cyberabad-traffic-normal/article883311.ece",
                canonical_url="https://www.thehindu.com/news/cities/Hyderabad/light-showers-in-cyberabad-traffic-normal/article883311.ece",
                article_title="[SIMULATED] Light Showers in Cyberabad; Traffic Remains Normal, IT Corridor Fully Operational",
                publisher="The Hindu",
                published_date=(now - timedelta(hours=5)).isoformat(),
                retrieval_timestamp=now,
                language="en",
                source_type="NEWS",
                retrieval_method="SEARCH_SCRAPE",
                content_hash="hash-thehindu-report",
                text_excerpt="[SIMULATED — NOT LIVE EXTERNAL EVIDENCE] Cyberabad Traffic Police advised commuters that light showers were recorded, but all tech park underpasses and arteries remain clear and operational.",
                retrieval_status="SUCCESS"
            )
            session.add_all([src1, src2])
            await session.flush()

            # 7. Source Independence
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
                edge_nature="HUMAN_CONFIRMED",
                is_inferred=False,
                evidence_summary="Textual submission reproduces identical viral claim with numerical waterlogging embellishment.",
                detection_method="HUMAN_CONFIRMATION",
                review_status="CONFIRMED",
                reviewer_notes="Confirmed by investigator. Text post accompanied the viral recirculated photo on Telegram.",
                reviewed_by="investigator_sarah",
                reviewed_at=utc_now()
            )
            session.add(human_rel)
            await session.commit()
            print("[+] Successfully seeded showcase investigation scenario!")

        print("\n" + "=" * 80)
        print("READY FOR INTERACTIVE DEMONSTRATION")
        print("=" * 80)
        print(f"Case ID: {inv.id}")
        print(f"\n1. Start the server (if not running):")
        print(f"   uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload")
        print(f"\n2. Open the Intelligence Workbench in your browser:")
        print(f"   http://localhost:8000/workbench?investigation_id={inv.id}")
        print(f"   or directly: http://localhost:8000/workbench")
        print(f"\n3. Open the Printable Case Dossier:")
        print(f"   http://localhost:8000/api/v1/investigations/{inv.id}/report/html")
        print(f"\n4. Interactive API Documentation (Swagger):")
        print(f"   http://localhost:8000/docs")
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(seed_data())
