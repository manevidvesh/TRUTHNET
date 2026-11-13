from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from app.schemas.source import SearchResultItem

class BaseSearchProvider(ABC):
    """
    Abstract interface for search and retrieval discovery providers.
    Every provider implementation must handle timeouts, rate limits,
    missing credentials, and return honest status indicators without crashing.
    """

    provider_name: str = "BASE_PROVIDER"

    def is_available(self) -> bool:
        """
        Returns True if the provider is configured and ready for queries.
        """
        return True

    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 5,
        language: str = "en"
    ) -> Tuple[List[SearchResultItem], str, Optional[str]]:
        """
        Executes search discovery for a query string.
        Returns:
            Tuple[List[SearchResultItem], status_code, optional_error_message]
            status_code values: "SUCCESS", "UNCONFIGURED", "UNAVAILABLE", "RATE_LIMITED", "FAILED"
        """
        pass
