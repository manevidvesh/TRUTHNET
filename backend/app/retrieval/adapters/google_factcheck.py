import os
import logging
from typing import List, Tuple, Optional
import httpx
from app.retrieval.base import BaseSearchProvider
from app.schemas.source import SearchResultItem, SourceType

logger = logging.getLogger(__name__)

API_ENDPOINT = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

class GoogleFactCheckAdapter(BaseSearchProvider):
    """
    Search provider for Google Fact Check Tools API.
    Discovers existing fact-checks from verified IFCN signatories and ClaimReview publishers.
    If the API key is not configured, honestly reports UNCONFIGURED without crashing.
    """
    provider_name: str = "GOOGLE_FACTCHECK_API"

    def __init__(self, api_key: Optional[str] = None, timeout_seconds: float = 6.0):
        self.api_key = api_key or os.getenv("GOOGLE_FACTCHECK_API_KEY")
        self.timeout = timeout_seconds

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def search(
        self,
        query: str,
        max_results: int = 5,
        language: str = "en"
    ) -> Tuple[List[SearchResultItem], str, Optional[str]]:
        if not self.api_key:
            return [], "UNCONFIGURED", "GOOGLE_FACTCHECK_API_KEY is not configured in environment."

        if not query or not query.strip():
            return [], "SUCCESS", None

        params = {
            "key": self.api_key,
            "query": query.strip(),
            "pageSize": max_results,
            "languageCode": language
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(API_ENDPOINT, params=params)

                if resp.status_code == 429:
                    return [], "RATE_LIMITED", "Google Fact Check Tools API quota exceeded."
                elif resp.status_code == 400 or resp.status_code == 403:
                    return [], "UNAVAILABLE", f"Google Fact Check API authentication/permission error (HTTP {resp.status_code})."
                elif resp.status_code != 200:
                    return [], "UNAVAILABLE", f"Google Fact Check API returned HTTP {resp.status_code}."

                data = resp.json()
                claims = data.get("claims", [])
                results: List[SearchResultItem] = []

                for c in claims:
                    text = c.get("text", "")
                    claim_date = c.get("claimDate")
                    for review in c.get("claimReview", []):
                        pub_info = review.get("publisher", {})
                        publisher_name = pub_info.get("name", "Fact-Checking Outlet")
                        url = review.get("url", "")
                        title = review.get("title", f"Fact Check: {text[:80]}")
                        verdict = review.get("textualRating", "")
                        review_date = review.get("reviewDate")

                        results.append(
                            SearchResultItem(
                                url=url,
                                title=title,
                                snippet=f"Claim: {text}. Rating by {publisher_name}: {verdict}.",
                                provider=self.provider_name,
                                published_date=review_date or claim_date,
                                source_type=SourceType.FACT_CHECK_ARTICLE,
                                raw_metadata={
                                    "claimText": text,
                                    "claimant": c.get("claimant"),
                                    "publisher": pub_info,
                                    "rating_verdict": verdict,
                                    "reviewDate": review_date,
                                    "languageCode": review.get("languageCode", language)
                                }
                            )
                        )

                return results[:max_results], "SUCCESS", None

        except httpx.TimeoutException:
            logger.warning(f"Google Fact Check API timed out for query '{query}'")
            return [], "UNAVAILABLE", "Google Fact Check Tools API request timed out."
        except Exception as e:
            logger.warning(f"Google Fact Check API error for query '{query}': {e}")
            return [], "FAILED", f"Google Fact Check API error: {str(e)}"
