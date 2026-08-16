"""Pydantic schemas for request validation and secure responses."""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class ProfileCreate(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Aarav Sharma"})
    age: int = Field(..., ge=18, le=100, json_schema_extra={"example": 28})
    gender: Optional[str] = Field(None, json_schema_extra={"example": "male"})
    religion: str = Field(..., json_schema_extra={"example": "Hindu"})
    caste: Optional[str] = Field(None, json_schema_extra={"example": "Brahmin"})
    caste_preference: Optional[str] = Field("no_preference", json_schema_extra={"example": "no_preference"})
    city: Optional[str] = Field(None, json_schema_extra={"example": "Bengaluru"})


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    is_complete: bool
    answered_kootas_count: int
    total_kootas_count: int = 42
    created_at: datetime


class AnswerItem(BaseModel):
    koota_id: int = Field(..., ge=1, le=42)
    question_index: int = Field(..., ge=0)
    question_type: str = Field(..., json_schema_extra={"example": "objective"})
    raw_value: str = Field(..., json_schema_extra={"example": "nuclear same city"})


class BulkAnswersSubmit(BaseModel):
    answers: List[AnswerItem]


class ProfileCompletionStatus(BaseModel):
    profile_id: str
    is_complete: bool
    answered_kootas_count: int
    total_kootas_count: int = 42
    missing_koota_ids: List[int] = []


class DisagreementFlagDTO(BaseModel):
    koota_id: int
    koota_name: str
    pillar: str
    objective_score: float
    subjective_score: float
    divergence: float
    severity: str
    note: str


class MatchResponse(BaseModel):
    profile_a_id: str
    profile_b_id: str
    is_viable: bool
    tier: str  # "not viable" | "compatible with flagged friction points" | "strong match"
    overall_score: Optional[float] = None
    objective_score: Optional[float] = None
    semantic_score: Optional[float] = None
    alignment_points: List[str] = []
    friction_points: List[str] = []
    disagreement_flags: List[DisagreementFlagDTO] = []
    hard_filter_reason: Optional[str] = None


class CandidateMatchSummary(BaseModel):
    candidate_id: str
    candidate_name: str
    is_viable: bool
    tier: str
    overall_score: Optional[float] = None
    alignment_points: List[str] = []
    friction_points: List[str] = []
    disagreement_count: int = 0
