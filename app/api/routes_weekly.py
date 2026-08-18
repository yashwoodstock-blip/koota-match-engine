"""Read-only API routes for accessing precomputed weekly matches."""
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.auth.deps import get_current_authenticated_profile, verify_profile_ownership
from app.models import Profile, WeeklyMatchList, Interest

router = APIRouter(prefix="/profiles", tags=["Weekly Matches"])


class WeeklyMatchDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    candidate_id: str
    candidate_name: str
    score: float
    tier: str  # "strong match", "compatible with flagged friction points", etc.
    risk_adjusted_score: Optional[float] = None
    score_uncertainty: Optional[float] = None
    score_interval: Optional[List[float]] = None
    confidence: Optional[str] = None
    evidence_coverage_pct: Optional[float] = None
    critical_contradictions: Optional[int] = 0
    high_impact_uncertainty: List[str] = []
    alignment_points: List[str] = []
    friction_points: List[str] = []
    contradiction_gates: List[Dict[str, Any]] = []
    capped_by: Optional[Dict[str, Any]] = None
    ceiling_applied: Optional[float] = None
    social_overlap_score: Optional[float] = 0.0
    shared_account_count: Optional[int] = 0
    interest_status: str = "none"  # "none" | "pending" | "mutual" | "declined"
    is_mutual: bool = False
    generated_at: datetime


class WeeklyMatchListResponse(BaseModel):
    profile_id: str
    total_matches: int
    mutual_matches_count: int = 0
    matches: List[WeeklyMatchDTO]
    is_precomputed: bool = True


@router.get("/{profile_id}/weekly-matches", response_model=WeeklyMatchListResponse)
async def get_weekly_matches(
    profile_id: str,
    current_profile: Profile = Depends(get_current_authenticated_profile),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve precomputed weekly matches for a profile.
    
    CRITICAL PERFORMANCE & PRIVACY RULE:
    - Strictly READ-ONLY: Never triggers live scoring, embedding, or LLM judge calls.
    - Zero raw free-text answers or Layer-1 demographic data returned.
    - Staged-disclosure rule: interest_status exposes caller's perspective only;
      a target's pending status is hidden until mutual.
    """
    verify_profile_ownership(profile_id, current_profile)

    # 2. Fetch precomputed matches from WeeklyMatchList
    stmt = (
        select(WeeklyMatchList, Profile.name.label("candidate_name"))
        .join(Profile, WeeklyMatchList.candidate_id == Profile.id)
        .where(WeeklyMatchList.profile_id == profile_id)
        .order_by(WeeklyMatchList.score.desc())
    )
    res = await db.execute(stmt)
    rows = res.all()

    # 3. Fetch caller's Interest records for these candidates to populate caller's interest status
    candidate_ids = [m.candidate_id for m, _ in rows]
    interests_map: Dict[str, str] = {}
    if candidate_ids:
        int_stmt = select(Interest).where(
            Interest.profile_id == profile_id,
            Interest.target_profile_id.in_(candidate_ids),
        )
        int_res = await db.execute(int_stmt)
        for i_row in int_res.scalars().all():
            interests_map[i_row.target_profile_id] = i_row.status

    match_dtos: List[WeeklyMatchDTO] = []
    mutual_count = 0
    for match_record, cand_name in rows:
        caller_status = interests_map.get(match_record.candidate_id, "none")
        is_mutual = (caller_status == "mutual")
        if is_mutual:
            mutual_count += 1

        match_dtos.append(
            WeeklyMatchDTO(
                candidate_id=match_record.candidate_id,
                candidate_name=cand_name,
                score=round(match_record.score, 4),
                tier=match_record.tier,
                alignment_points=match_record.alignment_points or [],
                friction_points=match_record.friction_points or [],
                contradiction_gates=match_record.contradiction_gates or [],
                social_overlap_score=match_record.social_overlap_score or 0.0,
                shared_account_count=match_record.shared_account_count or 0,
                interest_status=caller_status,
                is_mutual=is_mutual,
                generated_at=match_record.generated_at,
            )
        )

    return WeeklyMatchListResponse(
        profile_id=profile_id,
        total_matches=len(match_dtos),
        mutual_matches_count=mutual_count,
        matches=match_dtos,
        is_precomputed=True,
    )
