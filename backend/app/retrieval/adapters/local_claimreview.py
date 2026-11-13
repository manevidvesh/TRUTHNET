import json
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from app.retrieval.base import BaseSearchProvider
from app.schemas.source import SearchResultItem, SourceType

logger = logging.getLogger(__name__)

ARCHIVE_PATH = Path(__file__).resolve().parent.parent / "data" / "claimreview_archive.json"

class LocalClaimReviewAdapter(BaseSearchProvider):
    """
    Offline ClaimReview discovery provider querying curated local JSON-LD fact-checks.
    Always 100% available without external network or API keys.
    """
    provider_name: str = "LOCAL_CLAIMREVIEW"

    def __init__(self, archive_path: Optional[Path] = None):
        self.archive_path = archive_path or ARCHIVE_PATH
        self._data: List[dict] = []
        self._load_archive()

    def _load_archive(self) -> None:
        if self.archive_path.exists():
            try:
                with open(self.archive_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load local ClaimReview archive: {e}")
                self._data = []

    async def search(
        self,
        query: str,
        max_results: int = 5,
        language: str = "en"
    ) -> Tuple[List[SearchResultItem], str, Optional[str]]:
        if not self._data:
            return [], "UNAVAILABLE", "Local ClaimReview archive is empty or could not be loaded."

        query_terms = set(t.lower() for t in query.split() if len(t) > 2)
        matches: List[Tuple[int, dict]] = []

        for item in self._data:
            claim_text = item.get("claimReviewed", "").lower()
            text_snippet = item.get("text", "").lower()
            entities = [e.lower() for e in item.get("entities", [])]

            score = 0
            for term in query_terms:
                if term in claim_text:
                    score += 3
                if term in text_snippet:
                    score += 1
                if any(term in ent for ent in entities):
                    score += 2

            if score > 0:
                matches.append((score, item))

        # Sort by relevance score descending
        matches.sort(key=lambda x: x[0], reverse=True)
        results: List[SearchResultItem] = []

        for _, item in matches[:max_results]:
            author_info = item.get("author", {})
            publisher_name = author_info.get("name") if isinstance(author_info, dict) else str(author_info)
            rating_info = item.get("reviewRating", {})
            rating_name = rating_info.get("alternateName") or rating_info.get("ratingValue")

            result_item = SearchResultItem(
                url=item.get("url", ""),
                title=f"Fact Check: {item.get('claimReviewed', 'Claim')}",
                snippet=item.get("text", "")[:400],
                provider=self.provider_name,
                published_date=item.get("datePublished"),
                source_type=SourceType.FACT_CHECK_ARTICLE,
                raw_metadata={
                    "claimReviewed": item.get("claimReviewed"),
                    "reviewRating": rating_info,
                    "rating_verdict": rating_name,
                    "author": publisher_name,
                    "publisher": publisher_name,
                    "language": item.get("language", "en"),
                    "text": item.get("text", ""),
                    "claim_review": item
                }
            )
            results.append(result_item)

        return results, "SUCCESS", None
