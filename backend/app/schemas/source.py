from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field

class SourceType(str, Enum):
    FACT_CHECK_ARTICLE = "FACT_CHECK_ARTICLE"
    NEWS_ARTICLE = "NEWS_ARTICLE"
    OFFICIAL_DOCUMENT = "OFFICIAL_DOCUMENT"
    ENCYCLOPEDIA = "ENCYCLOPEDIA"
    ARCHIVAL_RECORD = "ARCHIVAL_RECORD"
    USER_UPLOAD = "USER_UPLOAD"

class RetrievalMethod(str, Enum):
    WEB_SEARCH_SCRAPER = "WEB_SEARCH_SCRAPER"
    GOOGLE_FACTCHECK_API = "GOOGLE_FACTCHECK_API"
    LOCAL_CLAIMREVIEW = "LOCAL_CLAIMREVIEW"
    WIKIPEDIA_API = "WIKIPEDIA_API"
    DIRECT_URL = "DIRECT_URL"

class RetrievalStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    SSRF_BLOCKED = "SSRF_BLOCKED"

class IndependenceAssessment(str, Enum):
    INDEPENDENT_REPORTING = "INDEPENDENT_REPORTING"
    WIRE_SERVICE_DERIVED = "WIRE_SERVICE_DERIVED"
    SHARED_PRESS_RELEASE = "SHARED_PRESS_RELEASE"
    REPEATS_ORIGINAL_SOURCE = "REPEATS_ORIGINAL_SOURCE"
    POSSIBLE_CONTENT_DEPENDENCY = "POSSIBLE_CONTENT_DEPENDENCY"
    UNKNOWN_DEPENDENCY = "UNKNOWN_DEPENDENCY"

class SearchResultItem(BaseModel):
    url: str
    title: str
    snippet: str
    provider: str
    published_date: Optional[str] = None
    source_type: SourceType = SourceType.NEWS_ARTICLE
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)

class RetrievedSourceResponse(BaseModel):
    id: str
    claim_id: str
    investigation_id: str
    canonical_url: str
    original_url: str
    article_title: str
    publisher: str
    author: Optional[str] = None
    published_date: Optional[str] = None
    modified_date: Optional[str] = None
    retrieval_timestamp: datetime
    language: str
    source_type: SourceType
    retrieval_method: RetrievalMethod
    search_provider: Optional[str] = None
    http_status: Optional[int] = None
    content_hash: str
    text_excerpt: str
    claim_review_metadata: Optional[Dict[str, Any]] = None
    retrieval_status: RetrievalStatus
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SourceDependencyCluster(BaseModel):
    cluster_id: str
    dependency_type: IndependenceAssessment
    primary_source_id: str
    source_ids: List[str]
    publishers: List[str]
    wire_agency: Optional[str] = None
    rationale: str
    shared_phrases: Optional[List[str]] = None
    text_overlap_ratio: Optional[float] = None

class SourceIndependenceResponse(BaseModel):
    id: str
    claim_id: str
    total_sources_count: int
    independent_sources_count: int
    independence_assessment: IndependenceAssessment
    clusters: List[SourceDependencyCluster] = Field(default_factory=list)
    observable_signals: Optional[Dict[str, Any]] = None
    explanation: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ClaimRetrievalAndVerificationResponse(BaseModel):
    claim_id: str
    search_query: str
    search_status: str
    sources_discovered_count: int
    sources_retrieved_count: int
    sources: List[RetrievedSourceResponse]
    independence: Optional[SourceIndependenceResponse] = None
    assessment: Optional[Dict[str, Any]] = None
    execution_time_seconds: float

class ClaimSearchRequest(BaseModel):
    query: Optional[str] = None
    providers: Optional[List[str]] = None
    max_results: int = 5
