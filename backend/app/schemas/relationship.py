"""
Pydantic Schemas for Claim Lineage, Graph Nodes, Edges, Timeline, and Explainability.
"""

from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

class LineageNodeType(str, Enum):
    INVESTIGATION = "INVESTIGATION"
    EVIDENCE_SUBMISSION = "EVIDENCE_SUBMISSION"
    MEDIA_ASSET = "MEDIA_ASSET"
    CLAIM = "CLAIM"
    CLAIM_VARIANT = "CLAIM_VARIANT"
    SOURCE = "SOURCE"
    ACCOUNT = "ACCOUNT"
    EVENT = "EVENT"
    ASSESSMENT = "ASSESSMENT"

class LineageRelationshipType(str, Enum):
    # Claim relationships
    SAME_CLAIM = "SAME_CLAIM"
    CLAIM_VARIANT = "CLAIM_VARIANT"
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    MISLEADING_CONTEXT = "MISLEADING_CONTEXT"
    ATTRIBUTED_TO = "ATTRIBUTED_TO"

    # Media relationships
    EXACT_MEDIA_MATCH = "EXACT_MEDIA_MATCH"
    NEAR_DUPLICATE_MEDIA = "NEAR_DUPLICATE_MEDIA"
    POSSIBLE_REUSED_MEDIA = "POSSIBLE_REUSED_MEDIA"
    SAME_PHOTOGRAPH_CANDIDATE = "SAME_PHOTOGRAPH_CANDIDATE"
    HISTORICAL_CONTEXT_CONFLICT = "HISTORICAL_CONTEXT_CONFLICT"

    # Source relationships
    REPEATS_SOURCE = "REPEATS_SOURCE"
    SHARED_URL = "SHARED_URL"
    SHARED_PRESS_RELEASE = "SHARED_PRESS_RELEASE"
    SHARED_WIRE_REPORT = "SHARED_WIRE_REPORT"
    SIMILAR_REPORTING = "SIMILAR_REPORTING"
    SOURCE_DEPENDENCY_UNKNOWN = "SOURCE_DEPENDENCY_UNKNOWN"

    # Timeline & Event relationships
    PUBLISHED_BEFORE = "PUBLISHED_BEFORE"
    ASSOCIATED_WITH_EVENT = "ASSOCIATED_WITH_EVENT"
    SAME_EVENT_CANDIDATE = "SAME_EVENT_CANDIDATE"

    # Distribution relationships
    SHARED_CAPTION = "SHARED_CAPTION"
    SIMILAR_CAPTION = "SIMILAR_CAPTION"
    REPEATED_DISTRIBUTION = "REPEATED_DISTRIBUTION"
    POSSIBLE_COORDINATION = "POSSIBLE_COORDINATION"

class LineageEdgeNature(str, Enum):
    OBSERVED = "OBSERVED"
    SYSTEM_DERIVED = "SYSTEM_DERIVED"
    INFERRED = "INFERRED"
    HUMAN_CONFIRMED = "HUMAN_CONFIRMED"

class LineageReviewStatus(str, Enum):
    UNREVIEWED = "UNREVIEWED"
    CONFIRMED = "CONFIRMED"
    DISPUTED = "DISPUTED"
    MODIFIED = "MODIFIED"

class LineageNode(BaseModel):
    id: str
    entity_type: LineageNodeType
    entity_id: str
    label: str
    investigation_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)

class LineageEdge(BaseModel):
    id: str
    source_id: str
    target_id: str
    relationship_type: LineageRelationshipType
    edge_nature: LineageEdgeNature
    is_inferred: bool
    evidence_id: Optional[str] = None
    evidence_summary: str
    detection_method: str
    confidence: Optional[float] = None
    review_status: LineageReviewStatus = LineageReviewStatus.UNREVIEWED
    reviewer_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    timestamps: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class LineageGraphResponse(BaseModel):
    investigation_id: str
    nodes: List[LineageNode]
    edges: List[LineageEdge]
    node_count: int
    edge_count: int
    unresolved_questions: List[Dict[str, Any]] = Field(default_factory=list)
    epistemic_notes: str

class LineageTimelineItem(BaseModel):
    timestamp: Optional[str] = None
    timestamp_type: str
    entity_id: str
    entity_type: LineageNodeType
    label: str
    details: Dict[str, Any] = Field(default_factory=dict)

class LineageTimelineResponse(BaseModel):
    investigation_id: str
    events: List[LineageTimelineItem]
    total_events: int

class CreateRelationshipRequest(BaseModel):
    source_entity_id: str
    source_entity_type: LineageNodeType
    target_entity_id: str
    target_entity_type: LineageNodeType
    relationship_type: LineageRelationshipType
    edge_nature: LineageEdgeNature = LineageEdgeNature.OBSERVED
    evidence_summary: str
    detection_method: str = "MANUAL_INVESTIGATOR_ENTRY"
    review_status: LineageReviewStatus = LineageReviewStatus.UNREVIEWED
    reviewer_notes: Optional[str] = None

class ReviewRelationshipRequest(BaseModel):
    review_status: LineageReviewStatus
    reviewer_notes: Optional[str] = None
    reviewer_id: Optional[str] = None

class ExplainableAssessmentResponse(BaseModel):
    claim_id: str
    investigation_id: str
    claim_text: str
    normalized_claim: str
    subject: Optional[str] = None
    predicate: Optional[str] = None
    object: Optional[str] = None
    assessment_classification: str
    primary_rationale: str
    supporting_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    contradicting_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    unaddressed_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    source_dependencies: Dict[str, Any] = Field(default_factory=dict)
    historical_media_findings: List[Dict[str, Any]] = Field(default_factory=list)
    temporal_and_geographical_context: Dict[str, Any] = Field(default_factory=dict)
    missing_evidence: List[str] = Field(default_factory=list)
    known_limitations: str
    decision_tree_explanation: str
    human_review: Dict[str, Any] = Field(default_factory=dict)
