from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class InvestigationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Investigation headline or case title")
    description: str | None = Field(None, description="Detailed case background, notes, or investigation objective")
    priority: str = Field("MEDIUM", description="Priority level: LOW, MEDIUM, HIGH, URGENT")

class InvestigationCreate(InvestigationBase):
    pass

class InvestigationUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    status: str | None = Field(None, description="ACTIVE, CLOSED, ARCHIVED")
    priority: str | None = Field(None, description="LOW, MEDIUM, HIGH, URGENT")

class InvestigationResponse(InvestigationBase):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime
    evidence_count: int = 0

    model_config = ConfigDict(from_attributes=True)

class InvestigationReportResponse(BaseModel):
    investigation: Dict[str, Any]
    is_simulated_scenario: bool
    simulation_disclaimer: Optional[str] = None
    executive_summary: str
    metrics: Dict[str, int]
    submissions: List[Dict[str, Any]]
    media_assets: List[Dict[str, Any]]
    claims: List[Dict[str, Any]]
    historical_media_matches: List[Dict[str, Any]]
    retrieved_sources: List[Dict[str, Any]]
    source_independence_evaluations: List[Dict[str, Any]]
    contextual_assessments: List[Dict[str, Any]]
    epistemic_limitations: List[str]
    human_review_log: List[Dict[str, Any]]
    generated_at: str
