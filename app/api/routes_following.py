"""API routes for managing opt-in social following lists."""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models import Profile, FollowingList, utc_now
from app.matching.social_overlap import normalize_usernames

router = APIRouter(prefix="/profiles", tags=["Social Following Overlap"])


class FollowingUploadRequest(BaseModel):
    usernames: List[str] = Field(
        ...,
        description="Plain array of username strings extracted client-side from following.json",
        json_schema_extra={"example": ["natgeo", "virat.kohli", "hubermanlab"]},
    )


class FollowingUploadResponse(BaseModel):
    status: str = "success"
    profile_id: str
    account_count: int
    opted_in: bool
    uploaded_at: datetime


class FollowingDeleteResponse(BaseModel):
    status: str = "success"
    profile_id: str
    opted_in: bool = False
    message: str


@router.post(
    "/{profile_id}/following",
    response_model=FollowingUploadResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_following_list(
    profile_id: str,
    payload: FollowingUploadRequest,
    db: AsyncSession = Depends(get_db),
):
    """Upload or update an opt-in following list for a profile.
    
    STRICT PRIVACY & ARCHITECTURAL BOUNDARIES:
    - Never accepts ZIP or binary archives.
    - Only receives pre-extracted username strings.
    - Normalizes, lowercases, and deduplicates.
    - Overwrites any prior list in the same transaction (does not append).
    """
    # 1. Verify profile exists
    stmt_p = select(Profile).where(Profile.id == profile_id)
    res_p = await db.execute(stmt_p)
    profile = res_p.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found.")

    # 2. Normalize and deduplicate usernames
    cleaned_set = normalize_usernames(payload.usernames)
    cleaned_list = sorted(list(cleaned_set))

    # 3. Upsert FollowingList row
    stmt_f = select(FollowingList).where(FollowingList.profile_id == profile_id)
    res_f = await db.execute(stmt_f)
    following_entry = res_f.scalar_one_or_none()

    now = utc_now()
    if following_entry:
        following_entry.usernames = cleaned_list
        following_entry.opted_in = True
        following_entry.uploaded_at = now
    else:
        following_entry = FollowingList(
            profile_id=profile_id,
            usernames=cleaned_list,
            opted_in=True,
            uploaded_at=now,
        )
        db.add(following_entry)

    await db.commit()
    await db.refresh(following_entry)

    return FollowingUploadResponse(
        status="success",
        profile_id=profile_id,
        account_count=len(cleaned_list),
        opted_in=True,
        uploaded_at=following_entry.uploaded_at,
    )


@router.delete(
    "/{profile_id}/following",
    response_model=FollowingDeleteResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_following_list(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Opt-out and completely purge following list data for a profile.
    
    Idempotent: succeeds even if no following list exists.
    """
    # Verify profile exists
    stmt_p = select(Profile).where(Profile.id == profile_id)
    res_p = await db.execute(stmt_p)
    profile = res_p.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found.")

    # Delete following list entry completely
    await db.execute(delete(FollowingList).where(FollowingList.profile_id == profile_id))
    await db.commit()

    return FollowingDeleteResponse(
        status="success",
        profile_id=profile_id,
        opted_in=False,
        message="Following list removed and opted out of social overlap signal.",
    )
