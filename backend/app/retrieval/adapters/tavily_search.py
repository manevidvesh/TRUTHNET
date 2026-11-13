import os
import logging
from typing import List, Tuple, Optional
import httpx
from app.retrieval.base import BaseSearchProvider
from app.schemas.source import SearchResultItem, SourceType

logger = logging.getLogger(__name__)

TAVILY_ENDPOINT = "https://api.tavily.com/search"

class TavilySearchAdapter(BaseSearchProvider):
    """
    Search provider for Tavily Search API.
    If the API key is unconfigured, honestly returns UNCONFIGURED.
    """
    provider_name: str = "TAVILY_SEARCH"

    def __init__(self, api_key: Optional[str] = None, timeout_seconds: float = 8.0):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
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
            return [], "UNCONFIGURED", "TAVILY_API_KEY is not configured in environment."

        if not query or not query.strip():
            return [], "SUCCESS", None

        payload = {
            "api_key": self.api_key,
            "query": query.strip(),
            "max_results": max_results,
            "search_depth": "basic",
            "include_raw_content": False
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(TAVILY_ENDPOINT, json=payload)

                if resp.status_code == 429:
                    return [], "RATE_LIMITED", "Tavily API rate limit exceeded."
                elif resp.status_code != 200:
                    return [], "UNAVAILABLE", f"Tavily API returned HTTP status {resp.status_code}."

                data = resp.json()
                items = data.get("results", [])
                results: List[SearchResultItem] = []

                for item in items:
                    results.append(
                        SearchResultItem(
                            url=item.get("url", ""),
                            title=item.get("title", "Search Result"),
                            snippet=item.get("content", ""),
                            provider=self.provider_name,
                            published_date=item.get("published_date"),
                            source_type=SourceType.NEWS_ARTICLE,
                            raw_metadata={"score": item.get("score")}
                        )
                    )

                return results, "SUCCESS", None

        except httpx.TimeoutException:
            logger.warning(f"Tavily search timed out for query '{query}'")
            return [], "UNAVAILABLE", "Tavily search request timed out."
        except Exception as e:
            logger.warning(f"Tavily search error for query '{query}': {e}")
            return [], "FAILED", f"Tavily search error: {str(e)}"
