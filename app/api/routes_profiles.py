"""Profile management, demographic edits, and answer submission API routes."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models import Profile, Answer, Koota, utc_now
from app.api.schemas import (
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    ProfileUpdateResponse,
    ProfileDeleteResponse,
    AnswerItem,
    BulkAnswersSubmit,
    ProfileCompletionStatus,
)
from app.auth.deps import get_current_authenticated_profile, verify_profile_ownership
from app.scoring.semantic import get_embedding
from app.scoring.invalidation import (
    invalidate_stale_matches_for_profile,
    cascade_delete_profile,
)

router = APIRouter(prefix="/profiles", tags=["Profiles"])


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(profile_in: ProfileCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user profile. Requires a valid, unused invite code or token."""
    from app.auth.invite import validate_invite_code, consume_invite_code, verify_invite_token

    code_to_consume = None
    if profile_in.invite_token:
        code_to_consume = verify_invite_token(profile_in.invite_token)
        if not code_to_consume:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invite-only registration: Invalid or expired invite session token.",
            )
    elif profile_in.invite_code:
        is_valid, msg, _ = await validate_invite_code(db, profile_in.invite_code)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Invite-only registration: {msg}",
            )
        code_to_consume = profile_in.invite_code
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invite-only registration: A valid redeemed invite code is required to sign up.",
        )

    # Consume the code
    if code_to_consume:
        await consume_invite_code(db, code_to_consume, used_by=profile_in.name)

    profile = Profile(
        name=profile_in.name,
        age=profile_in.age,
        gender=profile_in.gender,
        religion=profile_in.religion,
        caste=profile_in.caste,
        caste_preference=profile_in.caste_preference or "no_preference",
        city=profile_in.city,
        invite_code=code_to_consume,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    return ProfileResponse(
        id=profile.id,
        name=profile.name,
        age=profile.age,
        gender=profile.gender,
        religion=profile.religion,
        caste=profile.caste,
        caste_preference=profile.caste_preference,
        city=profile.city,
        is_complete=False,
        answered_kootas_count=0,
        total_kootas_count=42,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(profile_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve profile overview and completion status."""
    stmt = select(Profile).where(Profile.id == profile_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Count distinct answered kootas
    ans_stmt = select(func.count(func.distinct(Answer.koota_id))).where(Answer.profile_id == profile_id)
    ans_res = await db.execute(ans_stmt)
    answered_count = ans_res.scalar() or 0

    return ProfileResponse(
        id=profile.id,
        name=profile.name,
        age=profile.age,
        gender=profile.gender,
        religion=profile.religion,
        caste=profile.caste,
        caste_preference=profile.caste_preference,
        city=profile.city,
        is_complete=(answered_count >= 42),
        answered_kootas_count=answered_count,
        total_kootas_count=42,
        created_at=profile.created_at,
        updated_at=getattr(profile, "updated_at", profile.created_at),
    )


@router.patch("/{profile_id}", response_model=ProfileUpdateResponse)
async def update_profile(
    profile_id: str,
    payload: ProfileUpdate,
    current_profile: Profile = Depends(get_current_authenticated_profile),
    db: AsyncSession = Depends(get_db),
):
    """Partially update Layer 1 demographics with ownership gating and stale match invalidation.
    
    Hard-Filter Rules:
    - Altering religion or required-caste preferences flags hard_filter_changed=True and issues an explicit warning.
    - Purges precomputed WeeklyMatchList and MatchResult caches to guarantee no stale compatibility scores.
    """
    verify_profile_ownership(profile_id, current_profile)

    hard_filter_changed = False
    warning = None

    # Check religion modification (Universal Hard Filter)
    if payload.religion is not None and payload.religion != current_profile.religion:
        hard_filter_changed = True

    # Check caste / caste_preference modification (Koota 42 Hard Filter)
    target_caste_pref = payload.caste_preference if payload.caste_preference is not None else current_profile.caste_preference
    if target_caste_pref == "same_caste_required":
        if (payload.caste is not None and payload.caste != current_profile.caste) or (
            payload.caste_preference is not None and payload.caste_preference != current_profile.caste_preference
        ):
            hard_filter_changed = True
    elif (
        payload.caste_preference is not None
        and payload.caste_preference != current_profile.caste_preference
        and current_profile.caste_preference == "same_caste_required"
    ):
        hard_filter_changed = True

    if hard_filter_changed:
        warning = "Updating hard-filter demographic preferences (religion/caste) resets your active candidate pool."

    # Apply partial updates
    if payload.name is not None:
        current_profile.name = payload.name
    if payload.age is not None:
        current_profile.age = payload.age
    if payload.gender is not None:
        current_profile.gender = payload.gender
    if payload.religion is not None:
        current_profile.religion = payload.religion
    if payload.caste is not None:
        current_profile.caste = payload.caste
    if payload.caste_preference is not None:
        current_profile.caste_preference = payload.caste_preference
    if payload.city is not None:
        current_profile.city = payload.city

    current_profile.updated_at = utc_now()

    # Invalidate stale match caches
    await invalidate_stale_matches_for_profile(db, profile_id)

    await db.commit()
    await db.refresh(current_profile)

    return ProfileUpdateResponse(
        id=current_profile.id,
        name=current_profile.name,
        age=current_profile.age,
        gender=current_profile.gender,
        religion=current_profile.religion,
        caste=current_profile.caste,
        caste_preference=current_profile.caste_preference,
        city=current_profile.city,
        stale_matches_invalidated=True,
        hard_filter_changed=hard_filter_changed,
        warning=warning,
        updated_at=current_profile.updated_at,
    )


@router.post("/{profile_id}/answers", status_code=status.HTTP_200_OK)
async def submit_answers(
    profile_id: str,
    payload: BulkAnswersSubmit,
    db: AsyncSession = Depends(get_db),
):
    """Explicit UPSERT for 42-Koota answers with embedding recomputation and stale match invalidation."""
    stmt = select(Profile).where(Profile.id == profile_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    submitted_count = 0
    for ans_item in payload.answers:
        # Check if answer exists for this (profile, koota, question_index, question_type)
        existing_stmt = select(Answer).where(
            Answer.profile_id == profile_id,
            Answer.koota_id == ans_item.koota_id,
            Answer.question_index == ans_item.question_index,
            Answer.question_type == ans_item.question_type,
        )
        ex_res = await db.execute(existing_stmt)
        existing_ans = ex_res.scalar_one_or_none()

        # Compute embedding if subjective and not already computed or if value changed
        embedding = None
        if ans_item.question_type == "subjective":
            try:
                embedding = await get_embedding(ans_item.raw_value)
            except Exception:
                embedding = None

        if existing_ans:
            existing_ans.raw_value = ans_item.raw_value
            if embedding:
                existing_ans.embedding = embedding
            existing_ans.updated_at = utc_now()
        else:
            new_ans = Answer(
                profile_id=profile_id,
                koota_id=ans_item.koota_id,
                question_index=ans_item.question_index,
                question_type=ans_item.question_type,
                raw_value=ans_item.raw_value,
                embedding=embedding,
                created_at=utc_now(),
                updated_at=utc_now(),
            )
            db.add(new_ans)

        submitted_count += 1

    # Invalidate stale match caches for this profile
    await invalidate_stale_matches_for_profile(db, profile_id)

    await db.commit()
    return {
        "status": "success",
        "submitted_answers_count": submitted_count,
        "stale_matches_invalidated": True,
    }


@router.delete("/{profile_id}", response_model=ProfileDeleteResponse, status_code=status.HTTP_200_OK)
async def delete_profile_endpoint(
    profile_id: str,
    current_profile: Profile = Depends(get_current_authenticated_profile),
    db: AsyncSession = Depends(get_db),
):
    """Permanently delete profile and cascade all relational rows in compliance with DPDP."""
    verify_profile_ownership(profile_id, current_profile)

    await cascade_delete_profile(db, profile_id)
    await db.commit()

    return ProfileDeleteResponse(
        status="success",
        message="Profile and all associated data permanently deleted in compliance with DPDP.",
        deleted_profile_id=profile_id,
    )


@router.get("/{profile_id}/completion", response_model=ProfileCompletionStatus)
async def check_completion(profile_id: str, db: AsyncSession = Depends(get_db)):
    """Check if profile has completed questions for all 42 Kootas."""
    stmt = select(Profile).where(Profile.id == profile_id)
    res = await db.execute(stmt)
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Profile not found")

    ans_stmt = select(func.distinct(Answer.koota_id)).where(Answer.profile_id == profile_id)
    ans_res = await db.execute(ans_stmt)
    answered_koota_ids = set(ans_res.scalars().all())

    all_kootas_stmt = select(Koota.koota_id)
    all_res = await db.execute(all_kootas_stmt)
    all_koota_ids = set(all_res.scalars().all()) or set(range(1, 43))

    missing = sorted(list(all_koota_ids - answered_koota_ids))
    is_complete = len(missing) == 0

    return ProfileCompletionStatus(
        profile_id=profile_id,
        is_complete=is_complete,
        answered_kootas_count=len(answered_koota_ids),
        total_kootas_count=len(all_koota_ids),
        missing_koota_ids=missing,
    )


@router.get("/{profile_id}/candidates")
async def get_profile_candidates_alias(
    profile_id: str,
    min_score: float = 0.50,
    max_age_gap: int = 2,
    db: AsyncSession = Depends(get_db),
):
    """Alias for /match/{profile_id}/candidates."""
    from app.api.routes_match import get_ranked_candidates
    return await get_ranked_candidates(profile_id=profile_id, min_score=min_score, max_age_gap=max_age_gap, db=db)
