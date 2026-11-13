"""
Retrieval Orchestration Service.

Integrates:
- Query formulation from ClaimRecords
- Search provider discovery (Local ClaimReview, Wikipedia API, Google Fact Check, Tavily)
- Web scraping with SSRF guard and ClaimReview JSON-LD extraction
- Persistent RetrievedSourceRecord storage
- Multi-signal SourceIndependenceAnalyzer clustering & persistence
- ContextualClaimVerifier execution with retrieved evidence
"""

import time
import uuid
import hashlib
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy import select, update, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import ClaimRecord
from app.models.evidence import EvidenceSubmission
from app.models.source import RetrievedSourceRecord, SourceIndependenceRecord
from app.models.context_verification import ClaimAssessmentRecord
from app.schemas.source import (
    SourceType,
    RetrievalMethod,
    RetrievalStatus,
    IndependenceAssessment,
    SearchResultItem,
    RetrievedSourceResponse,
    SourceDependencyCluster,
    SourceIndependenceResponse,
    ClaimRetrievalAndVerificationResponse
)
from app.schemas.context_verification import EvidenceItem
from app.retrieval.adapters.local_claimreview import LocalClaimReviewAdapter
from app.retrieval.adapters.wikipedia_search import WikipediaSearchAdapter
from app.retrieval.adapters.google_factcheck import GoogleFactCheckAdapter
from app.retrieval.adapters.tavily_search import TavilySearchAdapter
from app.retrieval.scraper import WebScraper
from app.retrieval.source_independence import SourceIndependenceAnalyzer
from app.context.verifier import ContextualClaimVerifier

logger = logging.getLogger(__name__)

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RetrievalService:
    """
    Coordinates multi-provider search, robust web scraping, source independence
    analysis, and contextual claim verification.
    """

    def __init__(self):
        self.local_adapter = LocalClaimReviewAdapter()
        self.wikipedia_adapter = WikipediaSearchAdapter()
        self.google_adapter = GoogleFactCheckAdapter()
        self.tavily_adapter = TavilySearchAdapter()
        self.scraper = WebScraper()
        self.independence_analyzer = SourceIndependenceAnalyzer()

    def construct_queries(self, claim: ClaimRecord) -> List[str]:
        """
        Construct targeted search queries from a ClaimRecord:
        1. Core claim query (subject + predicate + object or normalized claim).
        2. Entity-focused query (locations, subjects, numbers).
        3. Fact-checking query variant.
        4. Multilingual representation for non-English claims.
        """
        queries: List[str] = []
        subject = (claim.subject or "").strip()
        predicate = (claim.predicate or "").strip()
        obj = (claim.object or "").strip()
        normalized = (claim.normalized_claim or claim.claim_text or "").strip()

        location = ""
        entities = claim.extracted_entities or {}
        if isinstance(entities, dict):
            locs = entities.get("locations", [])
            if locs and isinstance(locs, list):
                location = str(locs[0]).strip()
        elif isinstance(entities, list):
            for e in entities:
                if isinstance(e, dict) and e.get("type") in ["LOCATION", "GPE", "LOC"] and e.get("text"):
                    location = e["text"].strip()
                    break

        # 1. Primary claim text query
        if subject and predicate:
            core = f"{subject} {predicate}"
            if obj:
                core += f" {obj}"
            queries.append(core)
        elif normalized:
            queries.append(normalized)

        # 2. Add location if known and not already present
        if location and queries:
            loc_query = f"{queries[0]} {location}".strip()
            if loc_query not in queries:
                queries.append(loc_query)

        # 3. Entity-focused query
        entity_terms = []
        if isinstance(entities, dict):
            for k, v in entities.items():
                if isinstance(v, list):
                    entity_terms.extend([str(item) for item in v if item])
        elif isinstance(entities, list):
            entity_terms = [e.get("text") for e in entities if isinstance(e, dict) and e.get("text")]

        if entity_terms:
            entity_q = " ".join(entity_terms[:3])
            if entity_q and entity_q not in queries:
                queries.append(entity_q)

        # 4. Fact check keyword query
        if queries:
            fc_q = f"{queries[0]} fact check"
            queries.append(fc_q)

        # Deduplicate while preserving order
        deduped = []
        for q in queries:
            q_clean = q.strip()
            if q_clean and q_clean not in deduped:
                deduped.append(q_clean)

        return deduped or [normalized]

    async def search_providers(
        self,
        query: str,
        providers: Optional[List[str]] = None,
        max_results: int = 5
    ) -> List[SearchResultItem]:
        """
        Execute search across configured providers with deduplication.
        """
        active_providers = providers or ["local_claimreview", "wikipedia", "google_factcheck", "tavily"]
        results: List[SearchResultItem] = []
        seen_urls = set()

        # 1. Local ClaimReview Archive (always available, offline)
        if "local_claimreview" in active_providers:
            try:
                local_items, _, _ = await self.local_adapter.search(query, max_results=max_results)
                for item in local_items:
                    if item.url not in seen_urls:
                        seen_urls.add(item.url)
                        results.append(item)
            except Exception as e:
                logger.warning(f"Local claimreview provider error: {e}")

        # 2. Wikipedia Live API (no API key required)
        if "wikipedia" in active_providers:
            try:
                wiki_items, _, _ = await self.wikipedia_adapter.search(query, max_results=max_results)
                for item in wiki_items:
                    if item.url not in seen_urls:
                        seen_urls.add(item.url)
                        results.append(item)
            except Exception as e:
                logger.warning(f"Wikipedia provider error: {e}")

        # 3. Google Fact Check API
        if "google_factcheck" in active_providers:
            try:
                gfc_items, _, _ = await self.google_adapter.search(query, max_results=max_results)
                for item in gfc_items:
                    if item.url not in seen_urls:
                        seen_urls.add(item.url)
                        results.append(item)
            except Exception as e:
                logger.warning(f"Google Fact Check provider error: {e}")

        # 4. Tavily Search API
        if "tavily" in active_providers:
            try:
                tav_items, _, _ = await self.tavily_adapter.search(query, max_results=max_results)
                for item in tav_items:
                    if item.url not in seen_urls:
                        seen_urls.add(item.url)
                        results.append(item)
            except Exception as e:
                logger.warning(f"Tavily provider error: {e}")

        return results

    async def fetch_and_persist_source(
        self,
        session: AsyncSession,
        claim: ClaimRecord,
        search_item: SearchResultItem
    ) -> RetrievedSourceRecord:
        """
        Fetches full content for a search result item, performs SSRF validation,
        extracts ClaimReview JSON-LD and text excerpts, and persists a RetrievedSourceRecord.
        """
        # Check if already retrieved for this claim
        existing_stmt = select(RetrievedSourceRecord).where(
            RetrievedSourceRecord.claim_id == claim.id,
            RetrievedSourceRecord.canonical_url == search_item.url
        )
        existing_res = await session.execute(existing_stmt)
        existing = existing_res.scalars().first()
        if existing:
            return existing

        # Check if this item is from local ClaimReview (offline fast-path)
        if search_item.provider in ["local_claimreview", "LOCAL_CLAIMREVIEW"] or (search_item.source_type == SourceType.FACT_CHECK_ARTICLE and search_item.raw_metadata.get("claim_review")):
            raw_text = search_item.raw_metadata.get("text") or search_item.snippet
            content_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
            record = RetrievedSourceRecord(
                id=str(uuid.uuid4()),
                claim_id=claim.id,
                investigation_id=claim.investigation_id,
                canonical_url=search_item.url,
                original_url=search_item.url,
                article_title=search_item.title,
                publisher=search_item.raw_metadata.get("publisher") or "Fact Check Archive",
                author=search_item.raw_metadata.get("author"),
                published_date=search_item.published_date,
                modified_date=None,
                retrieval_timestamp=utc_now(),
                language=search_item.raw_metadata.get("language") or "en",
                source_type=search_item.source_type.value if hasattr(search_item.source_type, "value") else str(search_item.source_type),
                retrieval_method=RetrievalMethod.LOCAL_CLAIMREVIEW.value,
                search_provider=search_item.provider,
                http_status=200,
                content_hash=content_hash,
                raw_content=raw_text,
                text_excerpt=search_item.snippet[:500],
                claim_review_metadata=search_item.raw_metadata.get("claim_review"),
                retrieval_status=RetrievalStatus.SUCCESS.value,
                error_message=None
            )
            session.add(record)
            await session.flush()
            return record

        # Otherwise scrape via WebScraper with full SSRF protection
        scraped = await self.scraper.scrape_url(search_item.url)
        retrieval_method = RetrievalMethod.WIKIPEDIA_API.value if search_item.provider == "wikipedia" else RetrievalMethod.WEB_SEARCH_SCRAPER.value

        record = RetrievedSourceRecord(
            id=str(uuid.uuid4()),
            claim_id=claim.id,
            investigation_id=claim.investigation_id,
            canonical_url=scraped.canonical_url or search_item.url,
            original_url=search_item.url,
            article_title=scraped.article_title or search_item.title or "Untitled Document",
            publisher=scraped.publisher or search_item.provider,
            author=scraped.author,
            published_date=scraped.published_date or search_item.published_date,
            modified_date=scraped.modified_date,
            retrieval_timestamp=scraped.retrieval_timestamp,
            language=scraped.language or "en",
            source_type=scraped.source_type.value if hasattr(scraped.source_type, "value") else str(scraped.source_type),
            retrieval_method=retrieval_method,
            search_provider=search_item.provider,
            http_status=scraped.http_status,
            content_hash=scraped.content_hash,
            raw_content=scraped.raw_content,
            text_excerpt=scraped.text_excerpt[:500] if scraped.text_excerpt else search_item.snippet[:500],
            claim_review_metadata=scraped.claim_review_metadata or search_item.raw_metadata.get("claim_review"),
            retrieval_status=scraped.retrieval_status.value if hasattr(scraped.retrieval_status, "value") else str(scraped.retrieval_status),
            error_message=scraped.error_message
        )
        session.add(record)
        await session.flush()
        return record

    async def analyze_sources_for_claim(
        self,
        session: AsyncSession,
        claim_id: str
    ) -> SourceIndependenceRecord:
        """
        Executes multi-signal source independence analysis on all retrieved sources
        for a claim and persists a SourceIndependenceRecord.
        """
        sources_stmt = select(RetrievedSourceRecord).where(
            RetrievedSourceRecord.claim_id == claim_id,
            RetrievedSourceRecord.retrieval_status == RetrievalStatus.SUCCESS.value
        )
        sources_res = await session.execute(sources_stmt)
        sources = sources_res.scalars().all()

        source_dicts = [
            {
                "id": s.id,
                "publisher": s.publisher,
                "author": s.author,
                "text_excerpt": s.text_excerpt,
                "raw_content": s.raw_content,
                "canonical_url": s.canonical_url
            }
            for s in sources
        ]

        analysis_dict = self.independence_analyzer.analyze(claim_id, source_dicts)

        # Upsert or insert SourceIndependenceRecord
        indep_record = SourceIndependenceRecord(
            id=analysis_dict["id"],
            claim_id=claim_id,
            total_sources_count=analysis_dict["total_sources_count"],
            independent_sources_count=analysis_dict["independent_sources_count"],
            independence_assessment=analysis_dict["independence_assessment"].value if hasattr(analysis_dict["independence_assessment"], "value") else str(analysis_dict["independence_assessment"]),
            clusters=analysis_dict["clusters"],
            observable_signals=analysis_dict["observable_signals"],
            explanation=analysis_dict["explanation"],
            created_at=utc_now()
        )
        session.add(indep_record)
        await session.flush()
        return indep_record

    async def retrieve_and_verify(
        self,
        session: AsyncSession,
        claim_id: str,
        query_override: Optional[str] = None,
        providers: Optional[List[str]] = None,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Executes end-to-end evidence retrieval, source scraping, independence analysis,
        and contextual claim verification.
        """
        start_time = time.time()

        # 1. Fetch ClaimRecord
        claim_stmt = select(ClaimRecord).where(ClaimRecord.id == claim_id)
        claim_res = await session.execute(claim_stmt)
        claim = claim_res.scalars().first()
        if not claim:
            raise ValueError(f"Claim with id '{claim_id}' not found.")

        # 2. Formulate Queries & Search
        if query_override:
            queries = [query_override]
        else:
            queries = self.construct_queries(claim)

        primary_query = queries[0] if queries else (claim.normalized_claim or claim.claim_text)
        all_search_results: List[SearchResultItem] = []
        seen_urls = set()

        for q in queries:
            q_res = await self.search_providers(q, providers=providers, max_results=max_results)
            for item in q_res:
                if item.url not in seen_urls:
                    seen_urls.add(item.url)
                    all_search_results.append(item)
            if len(all_search_results) >= max_results * 2:
                break

        # 3. Retrieve and persist sources
        persisted_sources: List[RetrievedSourceRecord] = []
        for item in all_search_results[:max_results * 2]:
            try:
                rec = await self.fetch_and_persist_source(session, claim, item)
                persisted_sources.append(rec)
            except Exception as e:
                logger.error(f"Failed to fetch/persist source for {item.url}: {e}")

        # 4. Analyze Source Independence
        indep_record = await self.analyze_sources_for_claim(session, claim_id)

        # 5. Build cluster map for evidence items
        cluster_map: Dict[str, str] = {}
        if indep_record.clusters:
            for c in indep_record.clusters:
                c_type = c.get("dependency_type")
                for sid in c.get("source_ids", []):
                    cluster_map[sid] = c_type or "UNKNOWN"

        # 6. Map successful sources to EvidenceItems for ContextualClaimVerifier
        evidence_items: List[EvidenceItem] = []
        successful_sources = [s for s in persisted_sources if s.retrieval_status == RetrievalStatus.SUCCESS.value]

        for s in successful_sources:
            dep_status = cluster_map.get(s.id, "UNKNOWN_DEPENDENCY")
            content_passage = s.text_excerpt or (s.raw_content[:500] if s.raw_content else "")
            
            ev_item = EvidenceItem(
                evidence_id=f"src-{s.id}",
                source_id=s.id,
                source_url=s.canonical_url,
                publisher=s.publisher,
                author=s.author,
                published_date=s.published_date,
                retrieved_date=s.retrieval_timestamp.isoformat(),
                title=s.article_title,
                content_or_passage=content_passage,
                source_type=s.source_type,
                retrieval_method=s.retrieval_method,
                source_independence_status=dep_status,
                provenance={
                    "retrieved_source_id": s.id,
                    "content_hash": s.content_hash,
                    "claim_review": s.claim_review_metadata
                }
            )
            evidence_items.append(ev_item)

        # 7. Execute ContextualClaimVerifier
        assessment_record = await ContextualClaimVerifier.verify_claim(
            session=session,
            claim_id=claim_id,
            evidence_items=evidence_items
        )

        elapsed = round(time.time() - start_time, 3)

        # Format retrieved source responses
        source_responses = [
            RetrievedSourceResponse.model_validate(s) for s in persisted_sources
        ]

        indep_response = SourceIndependenceResponse(
            id=indep_record.id,
            claim_id=indep_record.claim_id,
            total_sources_count=indep_record.total_sources_count,
            independent_sources_count=indep_record.independent_sources_count,
            independence_assessment=IndependenceAssessment(indep_record.independence_assessment),
            clusters=[SourceDependencyCluster(**c) for c in (indep_record.clusters or [])],
            observable_signals=indep_record.observable_signals,
            explanation=indep_record.explanation,
            created_at=indep_record.created_at
        )

        return {
            "claim_id": claim_id,
            "search_query": primary_query,
            "search_status": "SUCCESS" if persisted_sources else "ZERO_RESULTS",
            "sources_discovered_count": len(all_search_results),
            "sources_retrieved_count": len(successful_sources),
            "sources": source_responses,
            "independence": indep_response,
            "assessment": {
                "id": assessment_record.id,
                "version": assessment_record.version,
                "classification": assessment_record.classification,
                "primary_rationale": assessment_record.primary_rationale,
                "contradiction_details": assessment_record.contradiction_details,
                "recommended_investigator_actions": assessment_record.recommended_investigator_actions,
                "human_review_status": assessment_record.human_review_status
            },
            "execution_time_seconds": elapsed
        }
