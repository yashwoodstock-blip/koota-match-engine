"""On-demand matching routes: 24h cooldown match refresh and mutual-consent compatibility codes."""
import asyncio
import secrets
import string
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models import (
    Profile,
    Answer,
    Koota,
    MatchResult,
    WeeklyMatchList,
    FollowingList,
    CompatibilityCode,
    utc_now,
)
from app.auth.deps import get_current_authenticated_profile, verify_profile_ownership
from app.api.schemas import (
    RefreshMatchesResponse,
    CandidateMatchSummary,
    CompatibilityCodeCreateResponse,
    CompatibilityCheckRequest,
    CompatibilityCheckResponse,
)
from app.matching.candidates_batch import run_candidates_funnel_for_profile
from app.matching.social_overlap import compute_overlap
from app.scoring.objective import calculate_objective_match
from app.scoring.semantic import score_all_subjective_kootas
from app.scoring.llm_judge import evaluate_all_top_kootas_llm_judge
from app.scoring.aggregate import aggregate_scores, AggregateMatchResult
from app.scoring.tiers import classify_tier

router = APIRouter(tags=["On-Demand Matching"])

UNAMBIGUOUS_CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


async def load_kootas_metadata(db: AsyncSession) -> Dict[int, Dict[str, Any]]:
    """Load metadata for all 42 Kootas into a fast lookup dict."""
    stmt = select(Koota)
    res = await db.execute(stmt)
    kootas = res.scalars().all()
    return {
        k.koota_id: {
            "weight": k.weight,
            "name": k.name,
            "pillar": k.pillar,
            "question_type": k.question_type,
            "is_hard_filter": k.is_hard_filter,
            "subjective_questions": k.subjective_questions,
            "objective_questions": k.objective_questions,
        }
        for k in kootas
    }


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime has UTC timezone."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


@router.post("/profiles/{profile_id}/refresh-matches", response_model=RefreshMatchesResponse)
async def refresh_matches_on_demand(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
    current_profile: Profile = Depends(get_current_authenticated_profile),
):
    """Execute the full 5-stage funnel on demand for the caller's profile.
    
    RATE LIMIT: Strict 24-hour cooldown per profile. Returns 429 with next_eligible_at if called early.
    CEILING: ≤10 LLM judge calls per run.
    INDEPENDENCE: Completely replaces existing WeeklyMatchList entries for this profile.
    """
    verify_profile_ownership(profile_id, current_profile)

    now = utc_now()
    if current_profile.last_refreshed_at:
        last_refreshed = ensure_utc(current_profile.last_refreshed_at)
        elapsed_seconds = (now - last_refreshed).total_seconds()
        cooldown_seconds = 24 * 3600  # 86400 seconds

        if elapsed_seconds < cooldown_seconds:
            remaining_seconds = int(cooldown_seconds - elapsed_seconds)
            next_eligible = last_refreshed + timedelta(hours=24)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": "Matches can only be refreshed once every 24 hours.",
                    "next_eligible_at": next_eligible.isoformat(),
                    "retry_after_seconds": max(1, remaining_seconds),
                },
                headers={"Retry-After": str(max(1, remaining_seconds))},
            )

    # 1. Load Kootas Metadata
    kootas_meta = await load_kootas_metadata(db)

    # 2. Run single-profile 5-stage funnel
    new_weekly_matches = await run_candidates_funnel_for_profile(
        profile_id=profile_id,
        db=db,
        kootas_metadata=kootas_meta,
        max_weekly_matches=5,
    )

    # 3. Update last_refreshed_at on Profile
    current_profile.last_refreshed_at = now
    await db.commit()

    # 4. Fetch candidate details for summary response
    candidate_ids = [m.candidate_id for m in new_weekly_matches]
    cand_map: Dict[str, Profile] = {}
    if candidate_ids:
        c_stmt = select(Profile).where(Profile.id.in_(candidate_ids))
        c_res = await db.execute(c_stmt)
        for c in c_res.scalars().all():
            cand_map[c.id] = c

    matches_summary: List[CandidateMatchSummary] = [
        CandidateMatchSummary(
            candidate_id=m.candidate_id,
            candidate_name=cand_map.get(m.candidate_id).name if cand_map.get(m.candidate_id) else "Candidate",
            is_viable=True,
            tier=m.tier,
            overall_score=m.score,
            alignment_points=m.alignment_points or [],
            friction_points=m.friction_points or [],
            disagreement_count=0,
            contradiction_count=len(m.contradiction_gates or []),
            social_overlap_score=m.social_overlap_score or 0.0,
            shared_account_count=m.shared_account_count or 0,
        )
        for m in new_weekly_matches
    ]

    return RefreshMatchesResponse(
        profile_id=profile_id,
        total_matches=len(new_weekly_matches),
        refreshed_at=now,
        next_eligible_at=now + timedelta(hours=24),
        matches=matches_summary,
    )


@router.post("/profiles/{profile_id}/compatibility-code", response_model=CompatibilityCodeCreateResponse)
async def generate_compatibility_code(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
    current_profile: Profile = Depends(get_current_authenticated_profile),
):
    """Generate a single-use, 24-hour mutual consent compatibility code.
    
    RATE LIMIT: Maximum 5 generated codes per 7 days per profile.
    SECURITY: Cryptographically random 7-character token from unambiguous character set.
    """
    verify_profile_ownership(profile_id, current_profile)

    now = utc_now()
    one_week_ago = now - timedelta(days=7)

    # 1. Check weekly rate limit
    stmt_count = select(func.count(CompatibilityCode.id)).where(
        CompatibilityCode.creator_profile_id == profile_id,
        CompatibilityCode.created_at >= one_week_ago,
    )
    res_count = await db.execute(stmt_count)
    active_count = res_count.scalar() or 0

    if active_count >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "message": "Weekly limit of 5 compatibility codes reached.",
            },
        )

    # 2. Generate secure unguessable 7-char code
    for _ in range(10):
        candidate_code = "".join(secrets.choice(UNAMBIGUOUS_CODE_ALPHABET) for _ in range(7))
        # Verify code uniqueness
        dup_stmt = select(CompatibilityCode).where(CompatibilityCode.code == candidate_code)
        dup_res = await db.execute(dup_stmt)
        if not dup_res.scalar_one_or_none():
            break
    else:
        candidate_code = secrets.token_hex(4).upper()

    expires_at = now + timedelta(hours=24)
    code_record = CompatibilityCode(
        code=candidate_code,
        creator_profile_id=profile_id,
        created_at=now,
        expires_at=expires_at,
        is_used=False,
    )
    db.add(code_record)
    await db.commit()

    return CompatibilityCodeCreateResponse(
        code=candidate_code,
        creator_profile_id=profile_id,
        created_at=now,
        expires_at=expires_at,
    )


@router.post("/profiles/{profile_id}/compatibility-check", response_model=CompatibilityCheckResponse)
async def check_compatibility_via_code(
    profile_id: str,
    payload: CompatibilityCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_profile: Profile = Depends(get_current_authenticated_profile),
):
    """Redeem a shared compatibility code to compute mutual compatibility.
    
    RATE LIMIT: Maximum 5 redemptions per 7 days per profile.
    VALIDATION:
    - Code exists
    - Redeemer cannot redeem own code (400 Bad Request)
    - Code is not already used (410 Gone)
    - Code is not expired (410 Gone)
    HARD FILTERS: Strictly enforced (Age gap, Religion, Caste rules) — no bypass.
    TRANSPARENCY: Saves MatchResult for immediate mutual visibility by both parties.
    """
    verify_profile_ownership(profile_id, current_profile)

    now = utc_now()
    one_week_ago = now - timedelta(days=7)

    # 1. Check weekly redemption rate limit for redeemer
    stmt_count = select(func.count(CompatibilityCode.id)).where(
        CompatibilityCode.used_by_profile_id == profile_id,
        CompatibilityCode.used_at >= one_week_ago,
    )
    res_count = await db.execute(stmt_count)
    redeem_count = res_count.scalar() or 0

    if redeem_count >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "message": "Weekly limit of 5 compatibility redemptions reached.",
            },
        )

    # 2. Look up code
    clean_code = payload.code.strip().upper()
    code_stmt = select(CompatibilityCode).where(CompatibilityCode.code == clean_code)
    code_res = await db.execute(code_stmt)
    comp_code = code_res.scalar_one_or_none()

    if not comp_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid compatibility code.",
        )

    # 3. Validate code constraints
    if comp_code.creator_profile_id == profile_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot redeem your own compatibility code.",
        )

    if comp_code.is_used:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This compatibility code has already been redeemed.",
        )

    code_expiry = ensure_utc(comp_code.expires_at)
    if code_expiry < now:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This compatibility code has expired.",
        )

    # 4. Fetch Creator Profile and Answers
    creator_stmt = select(Profile).where(Profile.id == comp_code.creator_profile_id)
    creator_res = await db.execute(creator_stmt)
    creator_profile = creator_res.scalar_one_or_none()
    if not creator_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Code creator profile no longer exists.",
        )

    ans_a_stmt = select(Answer).where(Answer.profile_id == comp_code.creator_profile_id)
    ans_b_stmt = select(Answer).where(Answer.profile_id == profile_id)
    res_ans_a = await db.execute(ans_a_stmt)
    res_ans_b = await db.execute(ans_b_stmt)
    answers_creator = list(res_ans_a.scalars().all())
    answers_redeemer = list(res_ans_b.scalars().all())

    # 5. Load Kootas Metadata & Calculate Objective/Hard-Filter Match
    kootas_meta = await load_kootas_metadata(db)
    obj_result = calculate_objective_match(
        creator_profile, current_profile, answers_creator, answers_redeemer, kootas_meta, max_age_gap=2
    )

    # Pre-fetch social following lists
    stmt_f = select(FollowingList).where(
        FollowingList.profile_id.in_([comp_code.creator_profile_id, profile_id])
    )
    res_f = await db.execute(stmt_f)
    f_map = {f.profile_id: f for f in res_f.scalars().all()}
    f_creator = f_map.get(comp_code.creator_profile_id)
    f_redeemer = f_map.get(profile_id)
    overlap_info = compute_overlap(
        usernames_a=f_creator.usernames if f_creator else [],
        usernames_b=f_redeemer.usernames if f_redeemer else [],
        opted_in_a=f_creator.opted_in if f_creator else False,
        opted_in_b=f_redeemer.opted_in if f_redeemer else False,
    )

    if not obj_result.is_viable:
        # Non-viable due to Hard Filter failure
        aggregate = AggregateMatchResult(
            is_viable=False,
            hard_filter_reason=obj_result.hard_filter_reason,
            overall_score=None,
            raw_composite_score=None,
            objective_score=None,
            semantic_score=None,
            tier_ceiling="not viable",
            koota_scores={},
            disagreement_flags=[],
            contradiction_gates=[],
            llm_judge_insights={},
        )
        tier_eval = classify_tier(aggregate, kootas_meta)

        # Save MatchResult for mutual history
        match_record = MatchResult(
            profile_a_id=comp_code.creator_profile_id,
            profile_b_id=profile_id,
            is_viable=False,
            hard_filter_reason=obj_result.hard_filter_reason,
            overall_score=None,
            tier=tier_eval.tier,
            objective_score=None,
            semantic_score=None,
            disagreement_flags=[],
            alignment_points=tier_eval.alignment_points,
            friction_points=tier_eval.friction_points,
            social_overlap_score=overlap_info["overlap_score"],
            shared_account_count=overlap_info["shared_count"],
            created_at=now,
        )
        db.add(match_record)

        # Mark code as consumed
        comp_code.is_used = True
        comp_code.used_by_profile_id = profile_id
        comp_code.used_at = now
        await db.commit()

        return CompatibilityCheckResponse(
            creator_profile_id=comp_code.creator_profile_id,
            redeemer_profile_id=profile_id,
            code=clean_code,
            is_viable=False,
            tier=tier_eval.tier,
            overall_score=None,
            alignment_points=tier_eval.alignment_points,
            friction_points=tier_eval.friction_points,
            hard_filter_reason=obj_result.hard_filter_reason,
            social_overlap_score=overlap_info["overlap_score"],
            shared_account_count=overlap_info["shared_count"],
            calculated_at=now,
        )

    # 6. Hard filter passed -> Full subjective semantic scoring & LLM judge
    (semantic_koota_scores, _), llm_judge_map = await asyncio.gather(
        score_all_subjective_kootas(answers_creator, answers_redeemer, kootas_meta),
        evaluate_all_top_kootas_llm_judge(answers_creator, answers_redeemer, kootas_meta),
    )

    aggregate = aggregate_scores(
        is_viable=True,
        hard_filter_reason=None,
        objective_koota_scores=obj_result.koota_scores,
        semantic_koota_scores=semantic_koota_scores,
        kootas_metadata=kootas_meta,
        llm_judge_results=llm_judge_map,
    )
    tier_eval = classify_tier(aggregate, kootas_meta)

    match_record = MatchResult(
        profile_a_id=comp_code.creator_profile_id,
        profile_b_id=profile_id,
        is_viable=True,
        hard_filter_reason=None,
        overall_score=aggregate.overall_score,
        tier=tier_eval.tier,
        objective_score=aggregate.objective_score,
        semantic_score=aggregate.semantic_score,
        disagreement_flags=[df.model_dump() for df in aggregate.disagreement_flags],
        alignment_points=tier_eval.alignment_points,
        friction_points=tier_eval.friction_points,
        social_overlap_score=overlap_info["overlap_score"],
        shared_account_count=overlap_info["shared_count"],
        created_at=now,
    )
    db.add(match_record)

    # Mark code as consumed
    comp_code.is_used = True
    comp_code.used_by_profile_id = profile_id
    comp_code.used_at = now
    await db.commit()

    return CompatibilityCheckResponse(
        creator_profile_id=comp_code.creator_profile_id,
        redeemer_profile_id=profile_id,
        code=clean_code,
        is_viable=True,
        tier=tier_eval.tier,
        overall_score=aggregate.overall_score,
        alignment_points=tier_eval.alignment_points,
        friction_points=tier_eval.friction_points,
        hard_filter_reason=None,
        social_overlap_score=overlap_info["overlap_score"],
        shared_account_count=overlap_info["shared_count"],
        calculated_at=now,
    )
