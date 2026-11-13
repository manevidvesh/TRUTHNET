"""
Pydantic schemas for Coordinated Misinformation Intelligence.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class CoordinationClusterResponse(BaseModel):
    id: str
    investigation_id: str
    cluster_type: str
    title: str
    summary: str
    entities_involved: List[Dict[str, Any]]
    supporting_observations: Dict[str, Any]
    detection_method: str
    confidence: float
    epistemic_limitations: str
    review_status: str
    reviewer_notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CoordinationAnalysisResponse(BaseModel):
    investigation_id: str
    clusters: List[CoordinationClusterResponse]
    total_clusters: int
    signals_detected: List[str]
    epistemic_disclaimer: str

    model_config = ConfigDict(from_attributes=True)
