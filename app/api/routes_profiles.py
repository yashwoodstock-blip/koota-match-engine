"""Profile management and answer submission API routes."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models import Profile, Answer, Koota
from app.api.schemas import (
    ProfileCreate,
    ProfileResponse,
    AnswerItem,
    BulkAnswersSubmit,
    ProfileCompletionStatus,
)
from app.scoring.semantic import get_embedding

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
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    return ProfileResponse(
        id=profile.id,
        name=profile.name,
        is_complete=False,
        answered_kootas_count=0,
        total_kootas_count=42,
        created_at=profile.created_at,
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
        is_complete=(answered_count >= 42),
        answered_kootas_count=answered_count,
        total_kootas_count=42,
        created_at=profile.created_at,
    )


@router.post("/{profile_id}/answers", status_code=status.HTTP_200_OK)
async def submit_answers(
    profile_id: str,
    payload: BulkAnswersSubmit,
    db: AsyncSession = Depends(get_db),
):
    """Submit or update answers for a profile. Caches embeddings for subjective answers."""
    stmt = select(Profile).where(Profile.id == profile_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    submitted_count = 0
    for ans_item in payload.answers:
        # Check if answer exists
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
                # Fallback to None if external HF is temporarily unavailable; will compute on match
                embedding = None

        if existing_ans:
            existing_ans.raw_value = ans_item.raw_value
            if embedding:
                existing_ans.embedding = embedding
        else:
            new_ans = Answer(
                profile_id=profile_id,
                koota_id=ans_item.koota_id,
                question_index=ans_item.question_index,
                question_type=ans_item.question_type,
                raw_value=ans_item.raw_value,
                embedding=embedding,
            )
            db.add(new_ans)

        submitted_count += 1

    await db.commit()
    return {"status": "success", "submitted_answers_count": submitted_count}


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
