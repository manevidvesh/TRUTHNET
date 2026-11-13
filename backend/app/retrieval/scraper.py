import re
import json
import hashlib
import logging
import urllib.parse
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup
from app.core.security import is_safe_url

logger = logging.getLogger(__name__)

MAX_BODY_BYTES = 5 * 1024 * 1024  # 5 MB
DEFAULT_TIMEOUT_SECONDS = 8.0
MAX_REDIRECTS = 3
MAX_EXCERPT_CHARS = 500

class ScrapedSourceData(dict):
    """Dictionary subclass supporting dot-attribute access for scraper results."""
    def __getattr__(self, item):
        if item in self:
            return self[item]
        return None

    def __setattr__(self, key, value):
        self[key] = value

class WebScraper:
    """
    SSRF-hardened webpage scraper and structured metadata extractor.
    Enforces strict IP boundaries, handles redirects securely, parses HTML,
    discovers ClaimReview JSON-LD, and extracts clean text excerpts.
    """

    @classmethod
    async def scrape_url(
        cls,
        url: str,
        target_terms: Optional[List[str]] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS
    ) -> ScrapedSourceData:
        """
        Safely fetches and parses an external URL with SSRF guards.
        Returns a ScrapedSourceData object supporting attribute and dict access.
        """
        d = await cls.fetch_and_parse(url, target_terms=target_terms, timeout=timeout)
        return ScrapedSourceData(d)

    @classmethod
    async def fetch_and_parse(
        cls,
        url: str,
        target_terms: Optional[List[str]] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS
    ) -> Dict[str, Any]:
        """
        Safely fetches an external URL and parses article text, title, publisher,
        author, published date, and ClaimReview metadata.
        Returns a structured dictionary matching RetrievedSourceRecord fields.
        """
        current_url = url.strip()

        # Step 1: Hop-by-hop SSRF validation across redirects
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            final_response = None
            redirect_count = 0

            for hop in range(MAX_REDIRECTS + 1):
                is_safe, reason = is_safe_url(current_url)
                if not is_safe:
                    logger.warning(f"SSRF guard blocked URL '{current_url}': {reason}")
                    return {
                        "canonical_url": current_url,
                        "original_url": url,
                        "article_title": "Blocked URL",
                        "publisher": "Unknown",
                        "retrieval_status": "SSRF_BLOCKED",
                        "http_status": 403,
                        "content_hash": hashlib.sha256(b"").hexdigest(),
                        "raw_content": None,
                        "text_excerpt": "",
                        "claim_review_metadata": None,
                        "error_message": f"SSRF Guard: {reason}"
                    }

                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 TRUTHNET/1.0"
                    }
                    resp = await client.get(current_url, headers=headers)

                    # Check for redirects
                    if resp.status_code in (301, 302, 303, 307, 308):
                        location = resp.headers.get("location")
                        if not location:
                            return cls._make_error_result(url, current_url, resp.status_code, "Redirect missing Location header")
                        current_url = urllib.parse.urljoin(current_url, location)
                        redirect_count += 1
                        continue

                    final_response = resp
                    break

                except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError):
                    return cls._make_error_result(url, current_url, 0, "Connection failed or timed out", status="UNAVAILABLE")
                except Exception as e:
                    return cls._make_error_result(url, current_url, 0, f"HTTP fetch error: {str(e)}", status="FAILED")

            if not final_response:
                return cls._make_error_result(url, current_url, 0, "Exceeded maximum redirect limit (3 hops)", status="FAILED")

            if final_response.status_code != 200:
                return cls._make_error_result(
                    url,
                    current_url,
                    final_response.status_code,
                    f"HTTP response status {final_response.status_code}",
                    status="FAILED"
                )

            # Step 2: Content size validation
            raw_text = final_response.text
            if len(raw_text.encode("utf-8")) > MAX_BODY_BYTES:
                raw_text = raw_text[:MAX_BODY_BYTES]

            # Step 3: Parse HTML
            return cls._parse_html_content(raw_text, original_url=url, final_url=current_url, target_terms=target_terms)

    @classmethod
    def _parse_html_content(
        cls,
        html_str: str,
        original_url: str,
        final_url: str,
        target_terms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Parses HTML DOM for title, author, date, ClaimReview JSON-LD, and prose."""
        soup = BeautifulSoup(html_str, "html.parser")

        # Canonical URL
        canonical_link = soup.find("link", rel="canonical")
        canonical_url = canonical_link["href"].strip() if canonical_link and canonical_link.get("href") else final_url

        # Publisher from domain or og:site_name
        publisher = "Web Publisher"
        og_site = soup.find("meta", property="og:site_name")
        if og_site and og_site.get("content"):
            publisher = og_site["content"].strip()
        else:
            domain_match = urllib.parse.urlparse(canonical_url).netloc
            if domain_match:
                publisher = domain_match.replace("www.", "").capitalize()

        # Page Title
        title = "Untitled Document"
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title["content"].strip()
        elif soup.title and soup.title.string:
            title = soup.title.string.strip()

        # Author
        author = None
        meta_author = soup.find("meta", attrs={"name": "author"})
        if meta_author and meta_author.get("content"):
            author = meta_author["content"].strip()

        # Published date
        published_date = None
        date_meta = (
            soup.find("meta", property="article:published_time")
            or soup.find("meta", attrs={"name": "publish-date"})
            or soup.find("meta", attrs={"name": "pubdate"})
        )
        if date_meta and date_meta.get("content"):
            published_date = date_meta["content"].strip()
        else:
            time_tag = soup.find("time")
            if time_tag and time_tag.get("datetime"):
                published_date = time_tag["datetime"].strip()

        # Modified date
        modified_date = None
        mod_meta = (
            soup.find("meta", property="article:modified_time")
            or soup.find("meta", property="og:updated_time")
            or soup.find("meta", attrs={"name": "last-modified"})
        )
        if mod_meta and mod_meta.get("content"):
            modified_date = mod_meta["content"].strip()

        # Check for ClaimReview JSON-LD
        claim_review_meta = None
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                if not script.string:
                    continue
                data = json.loads(script.string)
                # Data can be dict or list of dicts
                candidates = data if isinstance(data, list) else [data]
                for item in candidates:
                    if isinstance(item, dict):
                        item_type = item.get("@type", "")
                        if item_type == "ClaimReview" or "ClaimReview" in item_type:
                            claim_review_meta = item
                            break
                        # Check graph
                        if "@graph" in item and isinstance(item["@graph"], list):
                            for g in item["@graph"]:
                                if isinstance(g, dict) and "ClaimReview" in g.get("@type", ""):
                                    claim_review_meta = g
                                    break
                if claim_review_meta:
                    break
            except Exception:
                continue

        # Clean HTML: remove scripts, styles, header, nav, footer, aside
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "noscript", "iframe"]):
            tag.decompose()

        # Extract text from paragraphs
        paragraphs = [p.get_text().strip() for p in soup.find_all(["p", "h1", "h2", "h3", "li"])]
        clean_text = "\n\n".join(p for p in paragraphs if len(p) > 20)

        if not clean_text:
            clean_text = soup.get_text(separator="\n", strip=True)

        content_hash = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()

        # Extract targeted excerpt
        excerpt = cls._extract_excerpt(clean_text, target_terms or [])

        # Infer source type
        source_type = "NEWS_ARTICLE"
        if claim_review_meta:
            source_type = "FACT_CHECK_ARTICLE"
        elif "wikipedia.org" in canonical_url:
            source_type = "ENCYCLOPEDIA"
        elif any(g in canonical_url for g in (".gov", ".nic.in", "who.int", "un.org")):
            source_type = "OFFICIAL_DOCUMENT"

        return {
            "canonical_url": canonical_url,
            "original_url": original_url,
            "article_title": title,
            "publisher": publisher,
            "author": author,
            "published_date": published_date,
            "modified_date": modified_date,
            "retrieval_timestamp": datetime.now(timezone.utc),
            "retrieval_status": "SUCCESS",
            "http_status": 200,
            "content_hash": content_hash,
            "raw_content": clean_text,
            "text_excerpt": excerpt,
            "source_type": source_type,
            "claim_review_metadata": claim_review_meta,
            "error_message": None
        }

    @staticmethod
    def _extract_excerpt(text: str, terms: List[str], max_len: int = MAX_EXCERPT_CHARS) -> str:
        """Extracts a passage of length <= max_len centered on target terms."""
        if not text:
            return ""
        if len(text) <= max_len:
            return text

        best_pos = -1
        for term in terms:
            if not term or len(term) < 3:
                continue
            idx = text.lower().find(term.lower())
            if idx != -1:
                best_pos = idx
                break

        if best_pos == -1:
            return text[:max_len]

        half = max_len // 2
        start = max(0, best_pos - half)
        end = min(len(text), start + max_len)
        if end - start < max_len and start > 0:
            start = max(0, end - max_len)

        return text[start:end].strip()

    @staticmethod
    def _make_error_result(
        original_url: str,
        current_url: str,
        http_status: int,
        error_msg: str,
        status: str = "FAILED"
    ) -> Dict[str, Any]:
        return {
            "canonical_url": current_url,
            "original_url": original_url,
            "article_title": "Unavailable Source",
            "publisher": "Unknown",
            "retrieval_status": status,
            "http_status": http_status,
            "content_hash": hashlib.sha256(b"").hexdigest(),
            "raw_content": None,
            "text_excerpt": "",
            "retrieval_timestamp": datetime.now(timezone.utc),
            "source_type": "NEWS_ARTICLE",
            "claim_review_metadata": None,
            "error_message": error_msg
        }
