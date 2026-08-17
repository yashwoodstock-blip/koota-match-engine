"""Mutual-interest confirmation and staged disclosure service."""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Profile, Interest, WeeklyMatchList, utc_now


async def express_interest(
    db: AsyncSession,
    profile_id: str,
    target_profile_id: str,
    action: str = "pending",
) -> Dict[str, Any]:
    """Express interest or decline a candidate from caller's weekly matches.
    
    Atomic Mutual-Flip Guarantee:
    - If caller expresses 'pending' and target already has 'pending', both rows
      are atomically flipped to 'mutual' in the same transaction.
    - If target has 'declined', the pair never flips to 'mutual'.
    - Target must be present in caller's WeeklyMatchList.
    """
    clean_action = (action or "pending").strip().lower()
    if clean_action not in ("pending", "declined"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action must be either 'pending' or 'declined'.",
        )

    if profile_id == target_profile_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot express interest in oneself.",
        )

    # 1. Verify caller profile exists
    p_stmt = select(Profile.id).where(Profile.id == profile_id)
    p_res = await db.execute(p_stmt)
    if not p_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Caller profile '{profile_id}' not found.",
        )

    # 2. Validate target appears in caller's WeeklyMatchList
    match_stmt = select(WeeklyMatchList).where(
        WeeklyMatchList.profile_id == profile_id,
        WeeklyMatchList.candidate_id == target_profile_id,
    )
    match_res = await db.execute(match_stmt)
    weekly_match = match_res.scalar_one_or_none()
    if not weekly_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Target profile '{target_profile_id}' is not in the caller's weekly matches.",
        )

    # 3. Retrieve caller's existing Interest row (if any)
    caller_stmt = select(Interest).where(
        Interest.profile_id == profile_id,
        Interest.target_profile_id == target_profile_id,
    )
    caller_res = await db.execute(caller_stmt)
    caller_interest = caller_res.scalar_one_or_none()

    # 4. Retrieve target's reverse Interest row (if any)
    reverse_stmt = select(Interest).where(
        Interest.profile_id == target_profile_id,
        Interest.target_profile_id == profile_id,
    )
    reverse_res = await db.execute(reverse_stmt)
    reverse_interest = reverse_res.scalar_one_or_none()

    target_status = reverse_interest.status if reverse_interest else "none"

    if clean_action == "declined":
        final_caller_status = "declined"
        if caller_interest:
            caller_interest.status = "declined"
            caller_interest.expressed_at = utc_now()
        else:
            caller_interest = Interest(
                profile_id=profile_id,
                target_profile_id=target_profile_id,
                status="declined",
                expressed_at=utc_now(),
            )
            db.add(caller_interest)

        # If reverse was mutual, downgrade reverse to pending since caller declined
        if reverse_interest and reverse_interest.status == "mutual":
            reverse_interest.status = "pending"

        await db.commit()
        await db.refresh(caller_interest)

        return {
            "profile_id": profile_id,
            "target_profile_id": target_profile_id,
            "status": "declined",
            "is_mutual": False,
            "expressed_at": caller_interest.expressed_at,
        }

    # clean_action == "pending"
    # Atomic mutual flip check
    if target_status == "pending" or target_status == "mutual":
        final_caller_status = "mutual"
        if reverse_interest:
            reverse_interest.status = "mutual"
    elif target_status == "declined":
        # Target declined -> pair is never mutual
        final_caller_status = "pending"
    else:
        # Target has not acted yet ("none")
        final_caller_status = "pending"

    if caller_interest:
        caller_interest.status = final_caller_status
        caller_interest.expressed_at = utc_now()
    else:
        caller_interest = Interest(
            profile_id=profile_id,
            target_profile_id=target_profile_id,
            status=final_caller_status,
            expressed_at=utc_now(),
        )
        db.add(caller_interest)

    await db.commit()
    await db.refresh(caller_interest)

    return {
        "profile_id": profile_id,
        "target_profile_id": target_profile_id,
        "status": final_caller_status,
        "is_mutual": (final_caller_status == "mutual"),
        "expressed_at": caller_interest.expressed_at,
    }


async def get_interest_status_for_profile(
    db: AsyncSession,
    profile_id: str,
) -> List[Dict[str, Any]]:
    """Retrieve interest statuses for all candidates in caller's WeeklyMatchList.
    
    STAGED-DISCLOSURE PRIVACY RULE:
    - Never reveals whether the OTHER party has expressed interest unless
      the result is already 'mutual'.
    - If caller has no action ('none') or 'pending', the target's pending/declined
      state is completely hidden.
    """
    # 1. Fetch all weekly matches for caller
    matches_stmt = (
        select(WeeklyMatchList.candidate_id)
        .where(WeeklyMatchList.profile_id == profile_id)
        .order_by(WeeklyMatchList.score.desc())
    )
    matches_res = await db.execute(matches_stmt)
    candidate_ids = matches_res.scalars().all()

    if not candidate_ids:
        return []

    # 2. Fetch caller's interest rows for these candidates
    interests_stmt = select(Interest).where(
        Interest.profile_id == profile_id,
        Interest.target_profile_id.in_(candidate_ids),
    )
    interests_res = await db.execute(interests_stmt)
    caller_interests_map = {
        i.target_profile_id: i for i in interests_res.scalars().all()
    }

    results: List[Dict[str, Any]] = []
    for c_id in candidate_ids:
        caller_int = caller_interests_map.get(c_id)
        caller_status = caller_int.status if caller_int else "none"
        expressed_at = caller_int.expressed_at if caller_int else None

        results.append({
            "candidate_id": c_id,
            "status": caller_status,
            "is_mutual": (caller_status == "mutual"),
            "expressed_at": expressed_at,
        })

    return results
