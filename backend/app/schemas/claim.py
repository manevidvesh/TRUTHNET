from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field
from enum import Enum

class ExtractionState(str, Enum):
    EXTRACTED_CLAIM_CANDIDATE = "EXTRACTED_CLAIM_CANDIDATE"
    STRUCTURED_PROPOSITION = "STRUCTURED_PROPOSITION"
    PARTIAL_EXTRACTION = "PARTIAL_EXTRACTION"
    UNRESOLVED_STATEMENT = "UNRESOLVED_STATEMENT"
    NON_FACTUAL_STATEMENT = "NON_FACTUAL_STATEMENT"

class PolarityState(str, Enum):
    # Explicit surface syntax & grammatical states
    AFFIRMATIVE_SURFACE_SYNTAX = "AFFIRMATIVE_SURFACE_SYNTAX"
    NEGATIVE_SURFACE_SYNTAX = "NEGATIVE_SURFACE_SYNTAX"
    UNRESOLVED_POLARITY = "UNRESOLVED_POLARITY"
    UNSUPPORTED_LANGUAGE_POLARITY = "UNSUPPORTED_LANGUAGE_POLARITY"

    # Backward-compatible aliases
    RESOLVED_AFFIRMATIVE = "AFFIRMATIVE_SURFACE_SYNTAX"
    RESOLVED_NEGATIVE = "NEGATIVE_SURFACE_SYNTAX"
    NOT_ANALYZED = "UNSUPPORTED_LANGUAGE_POLARITY"

class ClaimBase(BaseModel):
    claim_text: str = Field(..., description="Verbatim extracted sentence or proposition from source text")
    normalized_claim: str = Field(..., description="Normalized representation of the claim")
    version: int = Field(default=1, description="Extraction version for idempotency")
    is_active: bool = Field(default=True, description="True if latest active extraction record")
    extraction_state: ExtractionState = Field(
        default=ExtractionState.EXTRACTED_CLAIM_CANDIDATE,
        description="Extraction lifecycle state"
    )
    polarity_state: PolarityState = Field(
        default=PolarityState.AFFIRMATIVE_SURFACE_SYNTAX,
        description="Surface grammatical negation polarity state"
    )
    is_attributed_assertion: bool = Field(
        default=False,
        description="True if proposition is explicitly attributed to a named speaker"
    )
    subject: Optional[str] = Field(None, description="Identified subject noun phrase")
    predicate: Optional[str] = Field(None, description="Identified predicate or relation verb")
    object: Optional[str] = Field(None, description="Identified object noun phrase or complement")
    qualifiers: Optional[Dict[str, Any]] = Field(None, description="Negation, attribution, causal, or temporal modifiers")
    source_modality: str = Field(..., description="Modality of source: CAPTION, RAW_TEXT, OCR_EXTRACTED, TRANSCRIPT")
    evidence_span_start: int = Field(..., description="0-based character start offset in original source text")
    evidence_span_end: int = Field(..., description="0-based character end offset in original source text")
    source_text_hash: str = Field(..., description="SHA-256 of originating text block")
    extracted_entities: Optional[Dict[str, Any]] = Field(None, description="Entities parsed (persons, orgs, locations, dates)")
    language: str = Field(default="en", description="Detected ISO 639-1 code or MIXED / UNKNOWN")
    language_detection_method: str = Field(..., description="Detector method used (e.g. langdetect_ngram)")
    language_detector_version: Optional[str] = Field(None, description="Version of the detector library")
    language_detector_probability: Optional[float] = Field(None, description="Raw detector probability (uncalibrated)")
    translation_provenance: Optional[Dict[str, Any]] = Field(None, description="Translation engine and provenance if applicable")
    is_factual_assertion: bool = Field(default=True, description="True if verifiable factual claim, False if subjective opinion/rhetoric")
    extraction_method: str = Field(default="HYBRID_DETERMINISTIC_SYNTACTIC", description="Extraction strategy used")
    extraction_confidence: Optional[float] = Field(None, description="Calibrated extraction confidence if provided by model")
    uncertainty_notes: Optional[str] = Field(None, description="Explicit notes detailing parse ambiguity or lack of structure")

class ClaimCreate(ClaimBase):
    investigation_id: str
    evidence_submission_id: str

class ClaimResponse(ClaimBase):
    id: str
    investigation_id: str
    evidence_submission_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ClaimListResponse(BaseModel):
    items: List[ClaimResponse]
    total: int
