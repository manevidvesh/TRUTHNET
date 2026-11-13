from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field

class AssessmentClassification(str, Enum):
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    MISLEADING_OR_CONTEXT_MISSING = "MISLEADING_OR_CONTEXT_MISSING"
    UNVERIFIED = "UNVERIFIED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"

class EvidenceRelationshipType(str, Enum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    PROVIDES_CONTEXT = "PROVIDES_CONTEXT"
    PARTIALLY_SUPPORTS = "PARTIALLY_SUPPORTS"
    PARTIALLY_CONTRADICTS = "PARTIALLY_CONTRADICTS"
    DOES_NOT_ADDRESS = "DOES_NOT_ADDRESS"
    TEMPORAL_CONFLICT = "TEMPORAL_CONFLICT"
    GEOGRAPHICAL_CONFLICT = "GEOGRAPHICAL_CONFLICT"

class HumanReviewStatus(str, Enum):
    UNREVIEWED = "UNREVIEWED"
    CONFIRMED = "CONFIRMED"
    DISPUTED = "DISPUTED"
    MODIFIED = "MODIFIED"

class EvidenceItem(BaseModel):
    """
    Decoupled evidence input contract consumed by the contextual verifier.
    Can be supplied by local historical matches, local artifacts, or external retrieval (04-03).
    """
    evidence_id: str = Field(..., description="Unique identifier for this evidence item")
    source_id: str = Field(..., description="URI, DOI, or internal asset ID of the source")
    source_url: Optional[str] = Field(None, description="Direct URL if retrieved from the web or archive")
    publisher: Optional[str] = Field(None, description="Publishing organization, agency, or outlet")
    author: Optional[str] = Field(None, description="Article author or content creator if known")
    title: Optional[str] = Field(None, description="Title of the source article or document")
    published_date: Optional[str] = Field(None, description="ISO 8601 string or parsed publication date")
    retrieved_date: Optional[str] = Field(None, description="ISO 8601 string of when evidence was acquired")
    content_or_passage: str = Field(..., description="Verbatim textual content, excerpt, or OCR/transcript block")
    passage_span_start: Optional[int] = Field(None, description="Character offset start in original source")
    passage_span_end: Optional[int] = Field(None, description="Character offset end in original source")
    language: str = Field(default="en", description="ISO language code of evidence text")
    source_type: str = Field(
        default="FACT_CHECK_RECORD",
        description="FACT_CHECK_RECORD, NEWS_ARTICLE, OFFICIAL_DOCUMENT, ARCHIVAL_RECORD, LOCAL_SUBMISSION, HISTORICAL_MEDIA_MATCH, USER_UPLOAD"
    )
    retrieval_method: str = Field(
        default="MANUAL_ENTRY",
        description="DATABASE_MATCH, EXTERNAL_API, LOCAL_ARCHIVE, MANUAL_ENTRY"
    )
    source_independence_status: str = Field(
        default="UNKNOWN",
        description="UNKNOWN, REPORTED_DEPENDENT, REPORTED_INDEPENDENT (default UNKNOWN pending 04-03)"
    )
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Retriever provenance, query used")
    is_available: bool = Field(default=True, description="True if evidence was successfully fetched and accessible")

class ClaimEvidenceRelationResponse(BaseModel):
    id: str
    assessment_id: str
    claim_id: str
    evidence_source_id: str
    evidence_source_type: str
    relationship_type: EvidenceRelationshipType
    excerpt: str
    passage_span_start: Optional[int] = None
    passage_span_end: Optional[int] = None
    source_location: Optional[str] = None
    source_published_date: Optional[str] = None
    source_retrieved_date: Optional[str] = None
    source_publisher: Optional[str] = None
    source_author: Optional[str] = None
    source_independence_status: str = "UNKNOWN"
    alignment_rationale: str
    uncertainty_notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ClaimAssessmentResponse(BaseModel):
    id: str
    claim_id: str
    evidence_submission_id: str
    investigation_id: str
    version: int
    is_active: bool
    supersede_reason: Optional[str] = None
    classification: AssessmentClassification
    primary_rationale: str
    contradiction_details: Optional[Dict[str, Any]] = None
    temporal_analysis: Optional[Dict[str, Any]] = None
    geographical_analysis: Optional[Dict[str, Any]] = None
    archival_signal_detected: bool = False
    epistemic_limitations: str
    recommended_investigator_actions: Optional[List[Dict[str, Any]]] = None
    evaluation_method: str = "DETERMINISTIC_RULES"
    verifier_version: str = "1.0.0"
    human_review_status: HumanReviewStatus = HumanReviewStatus.UNREVIEWED
    human_reviewer_notes: Optional[str] = None
    human_reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    created_at: datetime
    evidence_relations: List[ClaimEvidenceRelationResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class ClaimAssessmentHistoryResponse(BaseModel):
    claim_id: str
    active_assessment: Optional[ClaimAssessmentResponse] = None
    history: List[ClaimAssessmentResponse] = Field(default_factory=list)
    total_versions: int

class HumanReviewSubmission(BaseModel):
    status: HumanReviewStatus
    notes: Optional[str] = None
    reviewer_id: Optional[str] = None

class ClaimVerificationRequest(BaseModel):
    evidence_items: Optional[List[EvidenceItem]] = None
