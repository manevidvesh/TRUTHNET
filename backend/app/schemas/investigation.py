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
