"""Stale match invalidation and DPDP cascade deletion services."""
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    Profile,
    Answer,
    FollowingList,
    Interest,
    MatchResult,
    WeeklyMatchList,
)


async def invalidate_stale_matches_for_profile(db: AsyncSession, profile_id: str) -> int:
    """Invalidate and purge precomputed matches and scores computed against superseded profile data.
    
    Ensures the user never sees misleading compatibility scores computed against superseded data.
    """
    # 1. Purge from WeeklyMatchList where user is either the profile or the candidate
    stmt_w = delete(WeeklyMatchList).where(
        (WeeklyMatchList.profile_id == profile_id) | (WeeklyMatchList.candidate_id == profile_id)
    )
    res_w = await db.execute(stmt_w)

    # 2. Purge from MatchResult cache where user is profile_a or profile_b
    stmt_m = delete(MatchResult).where(
        (MatchResult.profile_a_id == profile_id) | (MatchResult.profile_b_id == profile_id)
    )
    res_m = await db.execute(stmt_m)

    total_purged = (res_w.rowcount or 0) + (res_m.rowcount or 0)
    return total_purged


async def cascade_delete_profile(db: AsyncSession, profile_id: str) -> None:
    """Permanently delete profile and all relational artifacts in compliance with DPDP.
    
    Cascades across:
    - answers & cached embeddings
    - following lists
    - interest records (both initiated and received)
    - cached match results
    - precomputed weekly match lists
    - profile record
    """
    # 1. Delete answers & embeddings
    await db.execute(delete(Answer).where(Answer.profile_id == profile_id))

    # 2. Delete following lists
    await db.execute(delete(FollowingList).where(FollowingList.profile_id == profile_id))

    # 3. Delete interests
    await db.execute(
        delete(Interest).where(
            (Interest.profile_id == profile_id) | (Interest.target_profile_id == profile_id)
        )
    )

    # 4. Invalidate and purge weekly match lists & match results
    await invalidate_stale_matches_for_profile(db, profile_id)

    # 5. Delete Profile
    await db.execute(delete(Profile).where(Profile.id == profile_id))
