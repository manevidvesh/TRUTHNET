"""
Comprehensive Test Suite for Plan 04-03:
Real-Time Evidence Retrieval, Web Scraping, and Multi-Signal Source Independence.

Covers 26 deterministic test scenarios:
- Search provider discovery, missing credentials, rate limits, timeouts, deduplication.
- Web scraping, SSRF guards, date extraction, metadata absence, ClaimReview LD-JSON.
- Proposition-level claim alignment, support, contradiction, incident-only context distinction.
- Multi-signal source independence: wire service (PTI/ANI/Reuters), shared press release,
  content syndication/near-duplicate, uncorroborated repetition, independent reporting, unknown dependency.
- Conflicting reports synthesis, multilingual queries, partial provider resilience.
- End-to-end FastAPI integration, version immutability, and API routes.
"""

import pytest
import uuid
import httpx
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from app.models.investigation import Investigation
from app.models.evidence import EvidenceSubmission
from app.models.claim import ClaimRecord
from app.models.source import RetrievedSourceRecord, SourceIndependenceRecord
from app.models.context_verification import ClaimAssessmentRecord
from app.schemas.source import (
    SourceType,
    RetrievalMethod,
    RetrievalStatus,
    IndependenceAssessment,
    SearchResultItem
)
from app.schemas.context_verification import (
    EvidenceItem,
    AssessmentClassification,
    EvidenceRelationshipType
)
from app.retrieval.adapters.local_claimreview import LocalClaimReviewAdapter
from app.retrieval.adapters.wikipedia_search import WikipediaSearchAdapter
from app.retrieval.adapters.google_factcheck import GoogleFactCheckAdapter
from app.retrieval.adapters.tavily_search import TavilySearchAdapter
from app.retrieval.scraper import WebScraper
from app.retrieval.source_independence import SourceIndependenceAnalyzer
from app.retrieval.service import RetrievalService
from app.context.evidence_aligner import EvidenceAligner
from app.context.verifier import ContextualClaimVerifier

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

async def create_test_claim(
    db: AsyncSession,
    claim_text: str = "Dam collapsed near Hyderabad killing 40 people",
    normalized_claim: str = "Dam collapsed near Hyderabad killing 40 people",
    subject: str = "Dam",
    predicate: str = "collapsed",
    obj: str = "killing 40 people",
    location: str = "Hyderabad",
    language: str = "en"
) -> tuple[Investigation, EvidenceSubmission, ClaimRecord]:
    inv = Investigation(
        title="Retrieval Test Investigation",
        description="Testing retrieval and source independence",
        priority="MEDIUM",
        status="ACTIVE"
    )
    db.add(inv)
    await db.flush()

    sub = EvidenceSubmission(
        investigation_id=inv.id,
        submission_type="TEXT",
        raw_text=claim_text,
        caption=claim_text,
        claimed_date="2026-06-15",
        claimed_location=location,
        language=language,
        processing_status="COMPLETED"
    )
    db.add(sub)
    await db.flush()

    claim = ClaimRecord(
        investigation_id=inv.id,
        evidence_submission_id=sub.id,
        claim_text=claim_text,
        normalized_claim=normalized_claim,
        subject=subject,
        predicate=predicate,
        object=obj,
        polarity_state="AFFIRMATIVE_SURFACE_SYNTAX",
        is_attributed_assertion=False,
        source_modality="TEXT",
        evidence_span_start=0,
        evidence_span_end=len(claim_text),
        source_text_hash=f"hash-{uuid.uuid4()}",
        extracted_entities={"locations": [location]},
        language=language,
        language_detection_method="statistical_test"
    )
    db.add(claim)
    await db.commit()
    return inv, sub, claim

# ==============================================================================
# 1. SEARCH PROVIDER TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_search_provider_success():
    """1. Local ClaimReview and Wikipedia providers return structured SearchResultItems."""
    adapter = LocalClaimReviewAdapter()
    results, status, err = await adapter.search("Hyderabad floods")
    assert len(results) > 0
    assert status == "SUCCESS"
    item = results[0]
    assert isinstance(item, SearchResultItem)
    assert item.url
    assert item.title
    assert item.provider == "LOCAL_CLAIMREVIEW"
    assert item.source_type == SourceType.FACT_CHECK_ARTICLE

@pytest.mark.asyncio
async def test_search_provider_missing_credentials():
    """2. Providers without credentials gracefully report UNCONFIGURED without crashing."""
    gfc = GoogleFactCheckAdapter(api_key=None)
    assert gfc.is_available() is False
    results, status, err = await gfc.search("test claim")
    assert results == []
    assert status == "UNCONFIGURED"

    tav = TavilySearchAdapter(api_key=None)
    assert tav.is_available() is False
    tav_results, tav_status, tav_err = await tav.search("test claim")
    assert tav_results == []
    assert tav_status == "UNCONFIGURED"

@pytest.mark.asyncio
async def test_search_provider_rate_limited():
    """3. Provider handles HTTP 429 response cleanly by returning empty list with RATE_LIMITED status."""
    tav = TavilySearchAdapter(api_key="mock-key")
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = httpx.Response(
            status_code=429,
            content=b'{"error": "Rate limit exceeded"}'
        )
        mock_post.return_value = mock_response
        results, status, err = await tav.search("test claim")
        assert results == []
        assert status == "RATE_LIMITED"

@pytest.mark.asyncio
async def test_search_provider_timeout():
    """4. Provider handles network timeout without hanging or unhandled exception."""
    wiki = WikipediaSearchAdapter()
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Read timeout")):
        results, status, err = await wiki.search("test claim")
        assert results == []
        assert status == "UNAVAILABLE"

@pytest.mark.asyncio
async def test_search_provider_zero_results():
    """5. Provider handles queries with no matching results gracefully."""
    adapter = LocalClaimReviewAdapter()
    results, status, err = await adapter.search("random_unmatched_gibberish_string_99881122")
    assert results == []
    assert status == "SUCCESS"

@pytest.mark.asyncio
async def test_search_deduplication():
    """6. Results from multiple providers with duplicate URLs are deduplicated."""
    service = RetrievalService()
    item1 = SearchResultItem(url="https://example.com/same-news", title="Article 1", snippet="Snippet 1", provider="provider1")
    item2 = SearchResultItem(url="https://example.com/same-news", title="Article 2", snippet="Snippet 2", provider="provider2")
    item3 = SearchResultItem(url="https://example.com/other-news", title="Article 3", snippet="Snippet 3", provider="provider1")

    with patch.object(service.local_adapter, "search", return_value=([item1, item3], "SUCCESS", None)):
        with patch.object(service.wikipedia_adapter, "search", return_value=([item2], "SUCCESS", None)):
            combined = await service.search_providers("query", providers=["local_claimreview", "wikipedia"])
            urls = [c.url for c in combined]
            assert len(urls) == 2
            assert urls.count("https://example.com/same-news") == 1

# ==============================================================================
# 2. WEB SCRAPER & CONTENT RETRIEVAL TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_source_retrieval_success():
    """7. Valid HTML page is retrieved, title, author, publisher, and excerpt extracted."""
    scraper = WebScraper()
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Heavy Rains Inundate Hyderabad Lowlands</title>
        <meta property="og:site_name" content="Deccan Chronicle" />
        <meta name="author" content="S. Ramanathan" />
        <meta property="article:published_time" content="2026-06-15T09:00:00Z" />
    </head>
    <body>
        <main>
            <p>Hyderabad witnessed unprecedented rainfall over the past 24 hours, inundating key residential colonies.</p>
        </main>
    </body>
    </html>
    """
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = httpx.Response(
            status_code=200,
            text=html_content,
            request=httpx.Request("GET", "https://deccanchronicle.com/hyderabad-rain")
        )
        data = await scraper.scrape_url("https://deccanchronicle.com/hyderabad-rain")
        assert data.retrieval_status in [RetrievalStatus.SUCCESS, RetrievalStatus.SUCCESS.value]
        assert data.article_title == "Heavy Rains Inundate Hyderabad Lowlands"
        assert data.publisher == "Deccan Chronicle"
        assert data.author == "S. Ramanathan"
        assert data.published_date == "2026-06-15T09:00:00Z"
        assert "unprecedented rainfall" in data.text_excerpt

@pytest.mark.asyncio
async def test_source_retrieval_inaccessible():
    """8. Handles HTTP 404, 500, and connection error without unhandled crash."""
    scraper = WebScraper()
    with patch("httpx.AsyncClient.get") as mock_get:
        # 404
        mock_get.return_value = httpx.Response(status_code=404, text="Not Found", request=httpx.Request("GET", "https://example.com/not-found"))
        res_404 = await scraper.scrape_url("https://example.com/not-found")
        assert res_404.retrieval_status in [RetrievalStatus.FAILED, RetrievalStatus.FAILED.value]
        assert res_404.http_status == 404

        # Connection error
        mock_get.side_effect = httpx.ConnectError("Connection refused")
        res_conn = await scraper.scrape_url("https://example.com/down")
        assert res_conn.retrieval_status in [RetrievalStatus.UNAVAILABLE, RetrievalStatus.UNAVAILABLE.value]

@pytest.mark.asyncio
async def test_source_retrieval_ssrf_blocked():
    """9. Localhost, 127.0.0.1, 169.254.169.254, and RFC 1918 private IPs are strictly blocked."""
    scraper = WebScraper()
    dangerous_urls = [
        "http://127.0.0.1:8000/internal",
        "http://localhost/admin",
        "http://169.254.169.254/latest/meta-data",
        "http://192.168.1.10/secrets",
        "http://10.0.0.1/private",
        "ftp://example.com/file"
    ]
    for url in dangerous_urls:
        data = await scraper.scrape_url(url)
        assert data.retrieval_status in [RetrievalStatus.SSRF_BLOCKED, RetrievalStatus.SSRF_BLOCKED.value]
        assert "SSRF" in (data.error_message or "")

@pytest.mark.asyncio
async def test_source_retrieval_date_extraction():
    """10. Article publication and modified timestamps extracted from meta tags."""
    scraper = WebScraper()
    html = """
    <html>
    <head>
        <meta property="article:published_time" content="2026-04-10T11:22:33Z" />
        <meta property="article:modified_time" content="2026-04-10T15:00:00Z" />
    </head>
    <body><p>News body text here.</p></body>
    </html>
    """
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = httpx.Response(status_code=200, text=html, request=httpx.Request("GET", "https://example.com/dates"))
        data = await scraper.scrape_url("https://example.com/dates")
        assert data.published_date == "2026-04-10T11:22:33Z"
        assert data.modified_date == "2026-04-10T15:00:00Z"

@pytest.mark.asyncio
async def test_source_retrieval_missing_metadata():
    """11. Page without metadata parsed gracefully with fallback title and None authors."""
    scraper = WebScraper()
    html = "<html><body><p>Bare paragraph without any head metadata or author tags.</p></body></html>"
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = httpx.Response(status_code=200, text=html, request=httpx.Request("GET", "https://example.com/bare"))
        data = await scraper.scrape_url("https://example.com/bare")
        assert data.retrieval_status in [RetrievalStatus.SUCCESS, RetrievalStatus.SUCCESS.value]
        assert data.article_title == "Untitled Document"
        assert data.author is None
        assert data.published_date is None

@pytest.mark.asyncio
async def test_claimreview_ldjson_parsing():
    """12. Schema.org ClaimReview JSON-LD extracted, validated, and structured."""
    scraper = WebScraper()
    html = """
    <html>
    <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "ClaimReview",
            "claimReviewed": "Old dam collapsed near Hyderabad",
            "reviewRating": {
                "@type": "Rating",
                "ratingValue": "1",
                "alternateName": "False"
            },
            "itemReviewed": {
                "@type": "CreativeWork",
                "author": {"@type": "Organization", "name": "Social Media User"}
            }
        }
        </script>
    </head>
    <body><p>Fact-checking team analyzed the video and confirmed the dam is intact.</p></body>
    </html>
    """
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = httpx.Response(status_code=200, text=html, request=httpx.Request("GET", "https://factcheck.org/dam-claim"))
        data = await scraper.scrape_url("https://factcheck.org/dam-claim")
        assert data.claim_review_metadata is not None
        rating_info = data.claim_review_metadata.get("reviewRating") or {}
        assert rating_info.get("alternateName") == "False"
        assert data.claim_review_metadata.get("claimReviewed") == "Old dam collapsed near Hyderabad"

# ==============================================================================
# 3. CLAIM-TO-EVIDENCE ALIGNMENT & PROPOSITION RELEVANCE TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_claim_relevance_filtering(db_session: AsyncSession):
    """13. Irrelevant external pages are filtered out as DOES_NOT_ADDRESS."""
    inv, sub, claim = await create_test_claim(
        db_session,
        claim_text="ISRO launched Aditya-L1 solar observatory successfully",
        subject="ISRO",
        predicate="launched",
        obj="Aditya-L1"
    )
    irrelevant_evidence = EvidenceItem(
        evidence_id="ev-irrelevant",
        source_id="src-irrelevant",
        publisher="Bollywood Hungama",
        title="Movie Box Office Collection",
        content_or_passage="The newly released romantic comedy crossed 50 crores on its opening weekend in Mumbai.",
        source_type="NEWS_ARTICLE"
    )
    relation = EvidenceAligner.evaluate_evidence_item(claim, irrelevant_evidence)
    assert relation["relationship_type"] == EvidenceRelationshipType.DOES_NOT_ADDRESS

@pytest.mark.asyncio
async def test_supporting_evidence_corroboration(db_session: AsyncSession):
    """14. Evidence matching proposition predicate and subject classified as SUPPORTS."""
    inv, sub, claim = await create_test_claim(
        db_session,
        claim_text="ISRO launched Chandrayaan-3 successfully from Sriharikota",
        subject="ISRO",
        predicate="launched",
        obj="Chandrayaan-3"
    )
    supporting_evidence = EvidenceItem(
        evidence_id="ev-sup",
        source_id="src-sup",
        publisher="The Hindu",
        title="Chandrayaan-3 Mission",
        content_or_passage="ISRO successfully launched Chandrayaan-3 spacecraft from the Satish Dhawan Space Centre in Sriharikota.",
        source_type="NEWS_ARTICLE"
    )
    relation = EvidenceAligner.evaluate_evidence_item(claim, supporting_evidence)
    assert relation["relationship_type"] == EvidenceRelationshipType.SUPPORTS

@pytest.mark.asyncio
async def test_contradictory_evidence_identification(db_session: AsyncSession):
    """15. Authoritative fact-check refuting claim classified as CONTRADICTS."""
    inv, sub, claim = await create_test_claim(
        db_session,
        claim_text="Himayat Sagar dam collapsed near Hyderabad",
        subject="Himayat Sagar dam",
        predicate="collapsed"
    )
    contradicting_evidence = EvidenceItem(
        evidence_id="ev-contra",
        source_id="src-contra",
        publisher="Boom Live Fact Check",
        title="Fact Check on Himayat Sagar Dam",
        content_or_passage="Fact Check: Claims that Himayat Sagar dam collapsed are false. Officials inspected the reservoir and confirmed the dam is intact with zero damage.",
        source_type="FACT_CHECK_RECORD"
    )
    relation = EvidenceAligner.evaluate_evidence_item(claim, contradicting_evidence)
    assert relation["relationship_type"] == EvidenceRelationshipType.CONTRADICTS

@pytest.mark.asyncio
async def test_incident_only_context_vs_proposition_evidence(db_session: AsyncSession):
    """16. Article mentioning incident/location does NOT corroborate an unmentioned predicate (dam collapse)."""
    inv, sub, claim = await create_test_claim(
        db_session,
        claim_text="Himayat Sagar dam collapsed killing 40 people",
        subject="Himayat Sagar dam",
        predicate="collapsed",
        obj="killing 40 people",
        location="Hyderabad"
    )
    incident_only_evidence = EvidenceItem(
        evidence_id="ev-incident-only",
        source_id="src-incident-only",
        publisher="Local Daily",
        title="Heavy Rains in Hyderabad",
        content_or_passage="Incessant heavy rains lashed Hyderabad on Thursday, submerging low-lying residential areas and disrupting traffic across the city.",
        source_type="NEWS_ARTICLE"
    )
    relation = EvidenceAligner.evaluate_evidence_item(claim, incident_only_evidence)
    # Must NOT be SUPPORTS because the predicate (dam collapse / 40 deaths) is not addressed
    assert relation["relationship_type"] != EvidenceRelationshipType.SUPPORTS
    assert relation["relationship_type"] in [EvidenceRelationshipType.DOES_NOT_ADDRESS, EvidenceRelationshipType.PROVIDES_CONTEXT]

# ==============================================================================
# 4. MULTI-SIGNAL SOURCE INDEPENDENCE TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_source_independence_identical_articles_different_urls():
    """17. Identical prose on distinct URLs/domains grouped into POSSIBLE_CONTENT_DEPENDENCY."""
    analyzer = SourceIndependenceAnalyzer()
    src1 = {
        "id": "s1",
        "publisher": "DomainAlpha.com",
        "canonical_url": "https://domainalpha.com/news/123",
        "text_excerpt": "The state administration announced immediate emergency compensation for disaster victims across all flood-hit taluks.",
        "raw_content": "The state administration announced immediate emergency compensation for disaster victims across all flood-hit taluks."
    }
    src2 = {
        "id": "s2",
        "publisher": "DomainBeta.org",
        "canonical_url": "https://domainbeta.org/post/456",
        "text_excerpt": "The state administration announced immediate emergency compensation for disaster victims across all flood-hit taluks.",
        "raw_content": "The state administration announced immediate emergency compensation for disaster victims across all flood-hit taluks."
    }
    res = analyzer.analyze("claim-1", [src1, src2])
    assert res["independence_assessment"] == IndependenceAssessment.POSSIBLE_CONTENT_DEPENDENCY
    assert len(res["clusters"]) == 1
    assert res["clusters"][0]["dependency_type"] == IndependenceAssessment.POSSIBLE_CONTENT_DEPENDENCY

@pytest.mark.asyncio
async def test_source_independence_wire_service_attribution():
    """18. Articles with PTI/ANI/Reuters byline grouped into WIRE_SERVICE_DERIVED cluster."""
    analyzer = SourceIndependenceAnalyzer()
    src1 = {
        "id": "s1",
        "publisher": "NDTV",
        "author": "PTI",
        "text_excerpt": "New Delhi: (PTI) - The Union Cabinet chaired by the Prime Minister approved the semiconductor incentive package on Wednesday."
    }
    src2 = {
        "id": "s2",
        "publisher": "Times of India",
        "author": "Staff",
        "text_excerpt": "New Delhi (PTI) -- Union Cabinet approved the semiconductor incentive package during Wednesday morning session."
    }
    res = analyzer.analyze("claim-wire", [src1, src2])
    assert res["independence_assessment"] == IndependenceAssessment.WIRE_SERVICE_DERIVED
    assert len(res["clusters"]) == 1
    cluster = res["clusters"][0]
    assert cluster["dependency_type"] == IndependenceAssessment.WIRE_SERVICE_DERIVED
    assert "Press Trust of India (PTI)" in cluster["wire_agency"]
    assert res["independent_sources_count"] == 1

@pytest.mark.asyncio
async def test_source_independence_shared_press_release():
    """19. Articles reciting official government/corporate press release grouped into SHARED_PRESS_RELEASE."""
    analyzer = SourceIndependenceAnalyzer()
    src1 = {
        "id": "s1",
        "publisher": "Financial Daily",
        "text_excerpt": "According to a press release issued by the Ministry of External Affairs, bilateral talks concluded successfully in Geneva."
    }
    src2 = {
        "id": "s2",
        "publisher": "National Wire",
        "text_excerpt": "In an official statement released by the Ministry of External Affairs, bilateral talks concluded successfully in Geneva."
    }
    res = analyzer.analyze("claim-pr", [src1, src2])
    assert res["independence_assessment"] == IndependenceAssessment.SHARED_PRESS_RELEASE
    assert res["clusters"][0]["dependency_type"] == IndependenceAssessment.SHARED_PRESS_RELEASE

@pytest.mark.asyncio
async def test_source_independence_unknown_dependency():
    """20. Inadequate metadata or single source recorded as UNKNOWN_DEPENDENCY (never false independent)."""
    analyzer = SourceIndependenceAnalyzer()
    src1 = {
        "id": "s1",
        "publisher": "BlogSpot User",
        "text_excerpt": "Water levels rose near the old bridge yesterday evening."
    }
    res = analyzer.analyze("claim-unknown", [src1])
    assert res["independence_assessment"] == IndependenceAssessment.UNKNOWN_DEPENDENCY
    assert "external source" in res["explanation"].lower() or "single source" in res["explanation"].lower()

@pytest.mark.asyncio
async def test_source_independence_multiple_independent():
    """21. Truly distinct newsrooms with independent bylines, low text overlap classified as INDEPENDENT_REPORTING."""
    analyzer = SourceIndependenceAnalyzer()
    src1 = {
        "id": "s1",
        "publisher": "BBC News",
        "author": "Alice Henderson",
        "text_excerpt": "Our investigative correspondents visited the reservoir site directly, interviewing local hydrologists and verifying telemetry sensors."
    }
    src2 = {
        "id": "s2",
        "publisher": "Reuters",
        "author": "Pravin Kumar",
        "text_excerpt": "Satellite radar imagery analyzed by spatial experts shows normal water reservoir levels with no embankment breach."
    }
    res = analyzer.analyze("claim-indep", [src1, src2])
    assert res["independence_assessment"] == IndependenceAssessment.INDEPENDENT_REPORTING
    assert res["independent_sources_count"] == 2
    assert len(res["clusters"]) == 2

@pytest.mark.asyncio
async def test_conflicting_external_reports(db_session: AsyncSession):
    """22. Conflicting external reports produce CONFLICTING_EVIDENCE assessment."""
    inv, sub, claim = await create_test_claim(
        db_session,
        claim_text="Bridge collapse caused 50 fatalities",
        subject="Bridge collapse",
        predicate="caused",
        obj="50 fatalities"
    )
    ev_support = EvidenceItem(
        evidence_id="ev-sup-conf",
        source_id="src-sup-conf",
        publisher="Channel 1 News",
        title="Bridge Tragedy",
        content_or_passage="Officials confirm the bridge collapse caused 50 fatalities on Sunday morning.",
        source_type="NEWS_ARTICLE",
        source_independence_status="INDEPENDENT_REPORTING"
    )
    ev_contradict = EvidenceItem(
        evidence_id="ev-contra-conf",
        source_id="src-contra-conf",
        publisher="FactCheck Registry",
        title="Fatalities Disputed",
        content_or_passage="Fact Check: Claims that the bridge collapse caused 50 fatalities are false. Hospital records confirm 0 fatalities and 3 minor injuries.",
        source_type="FACT_CHECK_RECORD",
        source_independence_status="INDEPENDENT_REPORTING"
    )
    assessment = await ContextualClaimVerifier.verify_claim(
        session=db_session,
        claim_id=claim.id,
        evidence_items=[ev_support, ev_contradict]
    )
    assert assessment.classification == AssessmentClassification.CONFLICTING_EVIDENCE.value

# ==============================================================================
# 5. MULTILINGUAL & INTEGRATION RESILIENCE TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_multilingual_search_query_generation(db_session: AsyncSession):
    """23. Hindi and Telugu claims generate search queries preserving native script entities."""
    service = RetrievalService()

    # Hindi claim
    inv_hi, sub_hi, claim_hi = await create_test_claim(
        db_session,
        claim_text="दिल्ली में भारी बारिश के कारण लाल किला जलमग्न हुआ",
        normalized_claim="दिल्ली में भारी बारिश के कारण लाल किला जलमग्न हुआ",
        subject="लाल किला",
        predicate="जलमग्न हुआ",
        location="दिल्ली",
        language="hi"
    )
    queries_hi = service.construct_queries(claim_hi)
    assert any("लाल किला" in q for q in queries_hi)

    # Telugu claim
    inv_te, sub_te, claim_te = await create_test_claim(
        db_session,
        claim_text="హైదరాబాద్‌లో హుస్సేన్ సాగర్ కట్ట తెగిపోయింది",
        normalized_claim="హైదరాబాద్‌లో హుస్సేన్ సాగర్ కట్ట తెగిపోయింది",
        subject="హుస్సేన్ సాగర్ కట్ట",
        predicate="తెగిపోయింది",
        location="హైదరాబాద్",
        language="te"
    )
    queries_te = service.construct_queries(claim_te)
    assert any("హుస్సేన్ సాగర్" in q for q in queries_te)

@pytest.mark.asyncio
async def test_partial_provider_failure_resilience():
    """24. If one provider fails or times out, other providers continue without failure."""
    service = RetrievalService()
    # Mock Google Fact Check to throw exception, Tavily to throw timeout
    with patch.object(service.google_adapter, "search", return_value=([], "FAILED", "Service down")):
        with patch.object(service.tavily_adapter, "search", return_value=([], "UNAVAILABLE", "timeout")):
            # Local ClaimReview should still return results
            results = await service.search_providers("Hyderabad floods")
            assert len(results) > 0
            assert any(r.provider == "LOCAL_CLAIMREVIEW" for r in results)

# ==============================================================================
# 6. END-TO-END PIPELINE & REST API TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_full_retrieval_and_verification_pipeline(async_client: AsyncClient, db_session: AsyncSession):
    """25. End-to-end API: POST /claims/{id}/retrieve-and-verify runs search, scrape, independence, and verifier."""
    inv, sub, claim = await create_test_claim(
        db_session,
        claim_text="Himayat Sagar dam collapsed during Hyderabad floods",
        subject="Himayat Sagar dam",
        predicate="collapsed",
        location="Hyderabad"
    )

    # Call POST /api/v1/claims/{claim_id}/retrieve-and-verify
    resp = await async_client.post(
        f"/api/v1/claims/{claim.id}/retrieve-and-verify",
        json={"providers": ["local_claimreview"], "max_results": 5}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["claim_id"] == claim.id
    assert data["search_status"] == "SUCCESS"
    assert data["sources_retrieved_count"] > 0
    assert "independence" in data
    assert "assessment" in data
    assert data["assessment"]["classification"] in [
        AssessmentClassification.CONTRADICTED.value,
        AssessmentClassification.MISLEADING_OR_CONTEXT_MISSING.value,
        AssessmentClassification.SUPPORTED.value
    ]

    # Verify GET /api/v1/claims/{claim_id}/sources
    sources_resp = await async_client.get(f"/api/v1/claims/{claim.id}/sources")
    assert sources_resp.status_code == 200
    sources_data = sources_resp.json()
    assert len(sources_data) > 0
    first_source_id = sources_data[0]["id"]

    # Verify GET /api/v1/sources/{source_id}
    single_source_resp = await async_client.get(f"/api/v1/sources/{first_source_id}")
    assert single_source_resp.status_code == 200
    assert single_source_resp.json()["id"] == first_source_id

    # Verify POST /api/v1/claims/{claim_id}/analyze-sources
    analyze_resp = await async_client.post(f"/api/v1/claims/{claim.id}/analyze-sources")
    assert analyze_resp.status_code == 200
    indep_data = analyze_resp.json()
    assert indep_data["total_sources_count"] > 0
    assert "clusters" in indep_data

@pytest.mark.asyncio
async def test_re_verification_with_new_evidence(async_client: AsyncClient, db_session: AsyncSession):
    """26. Re-running verification with new evidence creates a new immutable assessment version."""
    inv, sub, claim = await create_test_claim(
        db_session,
        claim_text="Bridge collapsed near Vijayawada",
        subject="Bridge",
        predicate="collapsed",
        location="Vijayawada"
    )

    # Initial verification
    resp1 = await async_client.post(
        f"/api/v1/claims/{claim.id}/verify",
        json={"evidence_items": []}
    )
    assert resp1.status_code == 200
    v1_data = resp1.json()
    assert v1_data["version"] == 1

    # Second verification with newly retrieved evidence
    new_ev = EvidenceItem(
        evidence_id="ev-v2",
        source_id="src-v2",
        publisher="Andhra News",
        title="Bridge Intact",
        content_or_passage="Authorities confirmed the bridge is fully intact with no damage.",
        source_type="NEWS_ARTICLE"
    )
    resp2 = await async_client.post(
        f"/api/v1/claims/{claim.id}/verify",
        json={"evidence_items": [new_ev.model_dump()]}
    )
    assert resp2.status_code == 200
    v2_data = resp2.json()
    assert v2_data["version"] == 2

    # Verify version history via API
    hist_resp = await async_client.get(f"/api/v1/claims/{claim.id}/assessment/history")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert hist_data["total_versions"] == 2
    assert hist_data["active_assessment"]["version"] == 2
