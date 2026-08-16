"""Matching API routes for pairwise compatibility scoring and candidate discovery."""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models import Profile, Answer, Koota, MatchResult
from app.api.schemas import MatchResponse, CandidateMatchSummary, DisagreementFlagDTO
from app.scoring.objective import calculate_objective_match
from app.scoring.semantic import score_all_subjective_kootas
from app.scoring.aggregate import aggregate_scores, AggregateMatchResult
from app.scoring.tiers import classify_tier

router = APIRouter(prefix="/match", tags=["Matching"])


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
        }
        for k in kootas
    }


@router.post("/{profile_a_id}/{profile_b_id}", response_model=MatchResponse)
async def score_match(
    profile_a_id: str,
    profile_b_id: str,
    max_age_gap: int = Query(2, description="Maximum allowable age gap (default 2 years)"),
    db: AsyncSession = Depends(get_db),
):
    """Calculate full 42-Koota compatibility between two profiles.
    
    CRITICAL PRIVACY RULE: Zero raw answer text or Layer-1 demographics are returned.
    """
    if profile_a_id == profile_b_id:
        raise HTTPException(status_code=400, detail="Cannot match a profile with itself.")

    # 1. Fetch Profiles
    stmt_a = select(Profile).where(Profile.id == profile_a_id)
    stmt_b = select(Profile).where(Profile.id == profile_b_id)
    res_a = await db.execute(stmt_a)
    res_b = await db.execute(stmt_b)
    p_a = res_a.scalar_one_or_none()
    p_b = res_b.scalar_one_or_none()

    if not p_a or not p_b:
        raise HTTPException(status_code=404, detail="One or both profiles not found.")

    # 2. Fetch Answers
    ans_stmt_a = select(Answer).where(Answer.profile_id == profile_a_id)
    ans_stmt_b = select(Answer).where(Answer.profile_id == profile_b_id)
    ans_res_a = await db.execute(ans_stmt_a)
    ans_res_b = await db.execute(ans_stmt_b)
    answers_a = list(ans_res_a.scalars().all())
    answers_b = list(ans_res_b.scalars().all())

    # 3. Load Kootas Metadata
    kootas_meta = await load_kootas_metadata(db)

    # 4. Objective Scorer + Hard Filter Short-Circuit
    obj_result = calculate_objective_match(
        p_a, p_b, answers_a, answers_b, kootas_meta, max_age_gap=max_age_gap
    )

    if not obj_result.is_viable:
        # Fails hard filter -> Non-viable
        aggregate = AggregateMatchResult(
            is_viable=False,
            hard_filter_reason=obj_result.hard_filter_reason,
            overall_score=None,
            objective_score=None,
            semantic_score=None,
            koota_scores={},
            disagreement_flags=[],
        )
        tier_eval = classify_tier(aggregate, kootas_meta)

        # Store match result in DB
        match_record = MatchResult(
            profile_a_id=profile_a_id,
            profile_b_id=profile_b_id,
            is_viable=False,
            hard_filter_reason=obj_result.hard_filter_reason,
            overall_score=None,
            tier=tier_eval.tier,
            objective_score=None,
            semantic_score=None,
            disagreement_flags=[],
            alignment_points=tier_eval.alignment_points,
            friction_points=tier_eval.friction_points,
        )
        db.add(match_record)
        await db.commit()

        return MatchResponse(
            profile_a_id=profile_a_id,
            profile_b_id=profile_b_id,
            is_viable=False,
            tier=tier_eval.tier,
            overall_score=None,
            objective_score=None,
            semantic_score=None,
            alignment_points=tier_eval.alignment_points,
            friction_points=tier_eval.friction_points,
            disagreement_flags=[],
            hard_filter_reason=obj_result.hard_filter_reason,
        )

    # 5. Semantic Scorer for Subjective Answers
    semantic_koota_scores, overall_semantic = await score_all_subjective_kootas(
        answers_a, answers_b, kootas_meta
    )

    # 6. Score Aggregator with Disagreement Detection
    aggregate = aggregate_scores(
        is_viable=True,
        hard_filter_reason=None,
        objective_koota_scores=obj_result.koota_scores,
        semantic_koota_scores=semantic_koota_scores,
        kootas_metadata=kootas_meta,
    )

    # 7. Tier Classifier & Templated Generator
    tier_eval = classify_tier(aggregate, kootas_meta)

    # 8. Persist Match Result
    match_record = MatchResult(
        profile_a_id=profile_a_id,
        profile_b_id=profile_b_id,
        is_viable=True,
        hard_filter_reason=None,
        overall_score=aggregate.overall_score,
        tier=tier_eval.tier,
        objective_score=aggregate.objective_score,
        semantic_score=aggregate.semantic_score,
        disagreement_flags=aggregate.disagreement_flags,
        alignment_points=tier_eval.alignment_points,
        friction_points=tier_eval.friction_points,
    )
    db.add(match_record)
    await db.commit()

    return MatchResponse(
        profile_a_id=profile_a_id,
        profile_b_id=profile_b_id,
        is_viable=True,
        tier=tier_eval.tier,
        overall_score=aggregate.overall_score,
        objective_score=aggregate.objective_score,
        semantic_score=aggregate.semantic_score,
        alignment_points=tier_eval.alignment_points,
        friction_points=tier_eval.friction_points,
        disagreement_flags=[DisagreementFlagDTO(**flag) for flag in aggregate.disagreement_flags],
        hard_filter_reason=None,
    )


@router.get("/{profile_id}/candidates", response_model=List[CandidateMatchSummary])
async def get_ranked_candidates(
    profile_id: str,
    min_score: float = Query(0.50, description="Minimum compatibility score threshold"),
    max_age_gap: int = Query(2, description="Maximum allowable age gap"),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve ranked candidate profiles for a given profile above a score threshold."""
    stmt_target = select(Profile).where(Profile.id == profile_id)
    res_target = await db.execute(stmt_target)
    target = res_target.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target profile not found.")

    # Fetch all candidate profiles (excluding target)
    stmt_candidates = select(Profile).where(Profile.id != profile_id)
    res_candidates = await db.execute(stmt_candidates)
    candidates = res_candidates.scalars().all()

    # Load target answers
    ans_stmt_t = select(Answer).where(Answer.profile_id == profile_id)
    res_t_ans = await db.execute(ans_stmt_t)
    target_answers = list(res_t_ans.scalars().all())

    kootas_meta = await load_kootas_metadata(db)
    ranked_list: List[CandidateMatchSummary] = []

    for cand in candidates:
        ans_stmt_c = select(Answer).where(Answer.profile_id == cand.id)
        res_c_ans = await db.execute(ans_stmt_c)
        cand_answers = list(res_c_ans.scalars().all())

        # Objective & Hard filters
        obj_res = calculate_objective_match(
            target, cand, target_answers, cand_answers, kootas_meta, max_age_gap=max_age_gap
        )
        if not obj_res.is_viable:
            continue

        # Semantic
        semantic_scores, _ = await score_all_subjective_kootas(
            target_answers, cand_answers, kootas_meta
        )

        # Aggregate
        agg = aggregate_scores(
            is_viable=True,
            hard_filter_reason=None,
            objective_koota_scores=obj_res.koota_scores,
            semantic_koota_scores=semantic_scores,
            kootas_metadata=kootas_meta,
        )

        if agg.overall_score is not None and agg.overall_score >= min_score:
            tier_eval = classify_tier(agg, kootas_meta)
            ranked_list.append(
                CandidateMatchSummary(
                    candidate_id=cand.id,
                    candidate_name=cand.name,
                    is_viable=True,
                    tier=tier_eval.tier,
                    overall_score=agg.overall_score,
                    alignment_points=tier_eval.alignment_points,
                    friction_points=tier_eval.friction_points,
                    disagreement_count=len(agg.disagreement_flags),
                )
            )

    # Sort candidates by overall_score descending
    ranked_list.sort(key=lambda c: c.overall_score or 0.0, reverse=True)
    return ranked_list
