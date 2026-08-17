"""Read-only API routes for accessing precomputed weekly matches."""
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models import Profile, WeeklyMatchList

router = APIRouter(prefix="/profiles", tags=["Weekly Matches"])


class WeeklyMatchDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    candidate_id: str
    candidate_name: str
    score: float
    tier: str  # "strong match", "compatible with flagged friction points", etc.
    alignment_points: List[str] = []
    friction_points: List[str] = []
    contradiction_gates: List[Dict[str, Any]] = []
    social_overlap_score: Optional[float] = 0.0
    shared_account_count: Optional[int] = 0
    generated_at: datetime


class WeeklyMatchListResponse(BaseModel):
    profile_id: str
    total_matches: int
    matches: List[WeeklyMatchDTO]
    is_precomputed: bool = True


@router.get("/{profile_id}/weekly-matches", response_model=WeeklyMatchListResponse)
async def get_weekly_matches(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve precomputed weekly matches for a profile.
    
    CRITICAL PERFORMANCE & PRIVACY RULE:
    - Strictly READ-ONLY: Never triggers live scoring, embedding, or LLM judge calls.
    - Zero raw free-text answers or Layer-1 demographic data returned.
    """
    # 1. Verify Profile exists
    stmt_p = select(Profile).where(Profile.id == profile_id)
    res_p = await db.execute(stmt_p)
    profile = res_p.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    # 2. Fetch precomputed matches from WeeklyMatchList
    stmt = (
        select(WeeklyMatchList, Profile.name.label("candidate_name"))
        .join(Profile, WeeklyMatchList.candidate_id == Profile.id)
        .where(WeeklyMatchList.profile_id == profile_id)
        .order_by(WeeklyMatchList.score.desc())
    )
    res = await db.execute(stmt)
    rows = res.all()

    match_dtos: List[WeeklyMatchDTO] = []
    for match_record, cand_name in rows:
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
                generated_at=match_record.generated_at,
            )
        )

    return WeeklyMatchListResponse(
        profile_id=profile_id,
        total_matches=len(match_dtos),
        matches=match_dtos,
        is_precomputed=True,
    )
