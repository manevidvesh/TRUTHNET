import logging
import urllib.parse
from typing import List, Tuple, Optional
import httpx
from app.retrieval.base import BaseSearchProvider
from app.schemas.source import SearchResultItem, SourceType

logger = logging.getLogger(__name__)

class WikipediaSearchAdapter(BaseSearchProvider):
    """
    Live external search provider querying the public Wikimedia Search API.
    Provides real live search discovery for people, events, landmarks,
    disasters, and organizations across English, Hindi, and Telugu.
    Requires no paid API keys.
    """
    provider_name: str = "WIKIPEDIA_SEARCH"

    def __init__(self, timeout_seconds: float = 6.0):
        self.timeout = timeout_seconds

    async def search(
        self,
        query: str,
        max_results: int = 5,
        language: str = "en"
    ) -> Tuple[List[SearchResultItem], str, Optional[str]]:
        if not query or not query.strip():
            return [], "SUCCESS", None

        # Choose wiki subdomain based on language code
        lang_subdomain = "en"
        if language in ("hi", "hindi"):
            lang_subdomain = "hi"
        elif language in ("te", "telugu"):
            lang_subdomain = "te"

        endpoint = f"https://{lang_subdomain}.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query.strip(),
            "format": "json",
            "srlimit": max_results,
            "utf8": "1"
        }
        headers = {
            "User-Agent": "TRUTHNET-Misinformation-Workbench/1.0 (https://truthnet.ai; research@truthnet.ai)"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(endpoint, params=params, headers=headers)

                if resp.status_code == 429:
                    return [], "RATE_LIMITED", "Wikimedia API rate limit exceeded."
                elif resp.status_code != 200:
                    return [], "UNAVAILABLE", f"Wikimedia API returned HTTP status {resp.status_code}."

                data = resp.json()
                search_hits = data.get("query", {}).get("search", [])
                results: List[SearchResultItem] = []

                for hit in search_hits:
                    title = hit.get("title", "")
                    page_id = hit.get("pageid")
                    raw_snippet = hit.get("snippet", "")
                    # Clean simple HTML tags in snippet
                    clean_snippet = raw_snippet.replace('<span class="searchmatch">', '').replace('</span>', '')
                    page_url = f"https://{lang_subdomain}.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                    timestamp = hit.get("timestamp")

                    results.append(
                        SearchResultItem(
                            url=page_url,
                            title=title,
                            snippet=clean_snippet,
                            provider=self.provider_name,
                            published_date=timestamp,
                            source_type=SourceType.ENCYCLOPEDIA,
                            raw_metadata={
                                "pageid": page_id,
                                "language": lang_subdomain,
                                "wordcount": hit.get("wordcount")
                            }
                        )
                    )

                return results, "SUCCESS", None

        except httpx.TimeoutException:
            logger.warning(f"Wikipedia search timed out for query '{query}'")
            return [], "UNAVAILABLE", "Wikimedia search request timed out."
        except Exception as e:
            logger.warning(f"Wikipedia search failed for query '{query}': {e}")
            return [], "FAILED", f"Wikimedia search error: {str(e)}"
