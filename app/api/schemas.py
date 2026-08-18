"""Pydantic schemas for request validation and secure responses."""
from datetime import datetime
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
    invite_code: Optional[str] = Field(None, json_schema_extra={"example": "A9K2M4P7"})
    invite_token: Optional[str] = Field(None, json_schema_extra={"example": "signed-token"})


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, json_schema_extra={"example": "Aarav Sharma"})
    age: Optional[int] = Field(None, ge=18, le=100, json_schema_extra={"example": 29})
    gender: Optional[str] = Field(None, json_schema_extra={"example": "male"})
    religion: Optional[str] = Field(None, json_schema_extra={"example": "Hindu"})
    caste: Optional[str] = Field(None, json_schema_extra={"example": "Brahmin"})
    caste_preference: Optional[str] = Field(None, json_schema_extra={"example": "no_preference"})
    city: Optional[str] = Field(None, json_schema_extra={"example": "Mumbai"})


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    religion: Optional[str] = None
    caste: Optional[str] = None
    caste_preference: Optional[str] = None
    city: Optional[str] = None
    is_complete: bool
    answered_kootas_count: int
    total_kootas_count: int = 42
    created_at: datetime
    updated_at: Optional[datetime] = None


class ProfileUpdateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    age: int
    gender: Optional[str] = None
    religion: str
    caste: Optional[str] = None
    caste_preference: Optional[str] = None
    city: Optional[str] = None
    stale_matches_invalidated: bool = True
    hard_filter_changed: bool = False
    warning: Optional[str] = None
    updated_at: datetime


class ProfileDeleteResponse(BaseModel):
    status: str = "success"
    message: str
    deleted_profile_id: str


class AnswerItem(BaseModel):
    koota_id: int = Field(..., ge=1, le=42)
    question_index: int = Field(..., ge=0)
    question_type: str = Field(..., json_schema_extra={"example": "objective"})
    raw_value: str = Field(..., json_schema_extra={"example": "nuclear same city"})


class BulkAnswersSubmit(BaseModel):
    answers: List[AnswerItem]


class BulkAnswersSubmitResponse(BaseModel):
    status: str
    submitted_answers_count: int
    stale_matches_invalidated: bool = True


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


class ContradictionGateDTO(BaseModel):
    koota_id: int
    koota_name: str
    pillar: str
    severity: str
    reason: str
    penalty_multiplier: float
    key_tensions: List[str] = []


class LLMJudgeInsightDTO(BaseModel):
    koota_id: int
    agreement_score: float
    contradiction: bool
    reasoning: str
    key_tensions: List[str] = []
    provider_used: str = "groq"


class MatchResponse(BaseModel):
    profile_a_id: str
    profile_b_id: str
    is_viable: bool
    tier: str  # "not viable" | "compatible with flagged friction points" | "strong match"
    overall_score: Optional[float] = None
    raw_composite_score: Optional[float] = None
    objective_score: Optional[float] = None
    semantic_score: Optional[float] = None
    tier_ceiling: Optional[str] = None
    alignment_points: List[str] = []
    friction_points: List[str] = []
    disagreement_flags: List[DisagreementFlagDTO] = []
    contradiction_gates: List[ContradictionGateDTO] = []
    llm_judge_insights: Dict[int, LLMJudgeInsightDTO] = {}
    hard_filter_reason: Optional[str] = None
    social_overlap_score: Optional[float] = 0.0
    shared_account_count: Optional[int] = 0


class CandidateMatchSummary(BaseModel):
    candidate_id: str
    candidate_name: str
    is_viable: bool
    tier: str
    overall_score: Optional[float] = None
    alignment_points: List[str] = []
    friction_points: List[str] = []
    disagreement_count: int = 0
    contradiction_count: int = 0
    social_overlap_score: Optional[float] = 0.0
    shared_account_count: Optional[int] = 0


class RefreshMatchesResponse(BaseModel):
    profile_id: str
    total_matches: int
    refreshed_at: datetime
    next_eligible_at: datetime
    matches: List[CandidateMatchSummary] = []


class CompatibilityCodeCreateResponse(BaseModel):
    code: str
    creator_profile_id: str
    created_at: datetime
    expires_at: datetime


class CompatibilityCheckRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=32)


class CompatibilityCheckResponse(BaseModel):
    creator_profile_id: str
    redeemer_profile_id: str
    code: str
    is_viable: bool
    tier: str
    overall_score: Optional[float] = None
    alignment_points: List[str] = []
    friction_points: List[str] = []
    hard_filter_reason: Optional[str] = None
    social_overlap_score: Optional[float] = 0.0
    shared_account_count: Optional[int] = 0
    calculated_at: datetime

