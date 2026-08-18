"""API routes for mutual-interest confirmation and staged disclosure."""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.auth.deps import get_current_authenticated_profile, verify_profile_ownership
from app.models import Profile
from app.interest.interest_service import express_interest, get_interest_status_for_profile

router = APIRouter(prefix="/interest", tags=["Mutual Interest"])


class ExpressInterestRequest(BaseModel):
    profile_id: str
    target_profile_id: str
    action: Optional[str] = "pending"  # "pending" | "declined"


class InterestResponse(BaseModel):
    profile_id: str
    target_profile_id: str
    status: str  # "pending" | "mutual" | "declined"
    is_mutual: bool
    expressed_at: Optional[datetime] = None


class CandidateInterestStatus(BaseModel):
    candidate_id: str
    status: str  # "pending" | "mutual" | "declined" | "none"
    is_mutual: bool
    expressed_at: Optional[datetime] = None


class InterestStatusListResponse(BaseModel):
    profile_id: str
    statuses: List[CandidateInterestStatus]


@router.post("", response_model=InterestResponse, status_code=status.HTTP_200_OK)
async def handle_express_interest(
    payload: ExpressInterestRequest,
    current_profile: Profile = Depends(get_current_authenticated_profile),
    db: AsyncSession = Depends(get_db),
):
    """Express interest or decline a candidate from caller's weekly matches.
    
    Atomic Mutual-Flip Guarantee:
    - If caller expresses 'pending' and target has 'pending', both rows flip to
      'mutual' in the exact same transaction.
    - If target has 'declined', the pair never flips to 'mutual'.
    - Target must be present in caller's WeeklyMatchList.
    """
    verify_profile_ownership(payload.profile_id, current_profile)
    result = await express_interest(
        db=db,
        profile_id=payload.profile_id,
        target_profile_id=payload.target_profile_id,
        action=payload.action or "pending",
    )
    return InterestResponse(**result)


@router.get("/{profile_id}/status", response_model=InterestStatusListResponse)
async def handle_get_interest_status(
    profile_id: str,
    current_profile: Profile = Depends(get_current_authenticated_profile),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve caller's interest status for all candidates in their WeeklyMatchList.
    
    STAGED-DISCLOSURE PRIVACY RULE:
    - Never reveals whether the target has expressed interest unless the status is 'mutual'.
    - One-sided 'pending' or 'declined' is visible only to the expressing party.
    """
    verify_profile_ownership(profile_id, current_profile)
    statuses = await get_interest_status_for_profile(db=db, profile_id=profile_id)
    return InterestStatusListResponse(
        profile_id=profile_id,
        statuses=[CandidateInterestStatus(**s) for s in statuses],
    )

