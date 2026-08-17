"""Weekly precomputed candidate matching funnel with SQL Hard Filter, Vector ANN, NLI Screen, and LLM Judge."""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import select, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Profile, Answer, Koota, WeeklyMatchList, FollowingList, utc_now
from app.matching.social_overlap import compute_overlap
from app.scoring.objective import calculate_objective_match
from app.scoring.semantic import score_all_subjective_kootas, cosine_similarity, get_embedding
from app.scoring.nli import evaluate_nli_pair
from app.scoring.llm_judge import evaluate_all_top_kootas_llm_judge, TOP_WEIGHTED_JUDGE_KOOTAS
from app.scoring.aggregate import aggregate_scores
from app.scoring.tiers import classify_tier


async def get_sql_hard_filtered_candidates(
    db: AsyncSession,
    target_profile: Profile,
    max_age_gap: int = 2,
) -> List[Profile]:
    """Stage 1: SQL-level Hard Filter.
    
    Filters by age gap, religion exact match, and caste requirements directly in SQL WHERE clause.
    """
    min_age = target_profile.age - max_age_gap
    max_age = target_profile.age + max_age_gap

    # Build SQL conditions
    conditions = [
        Profile.id != target_profile.id,
        Profile.age >= min_age,
        Profile.age <= max_age,
        Profile.religion == target_profile.religion,
    ]

    # Target requires same caste
    if target_profile.caste_preference == "same_caste_required" and target_profile.caste:
        conditions.append(Profile.caste == target_profile.caste)

    # Candidate cannot require same caste if castes don't match
    if target_profile.caste:
        conditions.append(
            or_(
                Profile.caste_preference != "same_caste_required",
                Profile.caste == target_profile.caste,
            )
        )

    stmt = select(Profile).where(and_(*conditions))
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def get_target_koota_41_embedding(
    db: AsyncSession,
    profile_id: str,
) -> Optional[List[float]]:
    """Retrieve or compute target profile's Koota 41 (Life Purpose) embedding."""
    stmt = select(Answer).where(
        Answer.profile_id == profile_id,
        Answer.koota_id == 41,
        Answer.question_type == "subjective",
    )
    res = await db.execute(stmt)
    ans = res.scalar_one_or_none()
    if not ans:
        return None
    if ans.embedding:
        return ans.embedding
    return await get_embedding(ans.raw_value)


async def filter_vector_ann_top_50(
    db: AsyncSession,
    target_embedding: Optional[List[float]],
    candidates: List[Profile],
    limit: int = 50,
) -> List[Profile]:
    """Stage 2: Vector ANN retrieval on Koota 41 Life Purpose embedding (LIMIT 50)."""
    if len(candidates) <= limit or target_embedding is None:
        return candidates[:limit]

    # Fetch candidate Koota 41 answers
    cand_ids = [c.id for c in candidates]
    stmt = select(Answer).where(
        Answer.profile_id.in_(cand_ids),
        Answer.koota_id == 41,
        Answer.question_type == "subjective",
    )
    res = await db.execute(stmt)
    answers = res.scalars().all()
    ans_map: Dict[str, Answer] = {a.profile_id: a for a in answers}

    scored_cands: List[Tuple[Profile, float]] = []
    for cand in candidates:
        c_ans = ans_map.get(cand.id)
        if c_ans and c_ans.embedding:
            sim = cosine_similarity(target_embedding, c_ans.embedding)
        else:
            sim = 0.50
        scored_cands.append((cand, sim))

    # Sort descending by Koota 41 vector similarity
    scored_cands.sort(key=lambda x: x[1], reverse=True)
    return [c for c, _ in scored_cands[:limit]]


async def screen_nli_top_10(
    db: AsyncSession,
    target_profile: Profile,
    candidates_50: List[Profile],
    target_answers: List[Answer],
    kootas_metadata: Dict[int, Dict[str, Any]],
    limit: int = 10,
) -> List[Tuple[Profile, List[Answer], Dict[int, float], Dict[int, float]]]:
    """Stage 3: NLI contradiction screen on Top-10 Kootas.
    
    Drops anyone with an active contradiction gate on Koota 41 outright.
    Ranks the survivors and keeps the top 10.
    """
    survivors: List[Tuple[Profile, List[Answer], Dict[int, float], Dict[int, float], float]] = []

    # Map target subjective answers
    t_subj_map: Dict[int, str] = {
        a.koota_id: a.raw_value for a in target_answers if a.question_type == "subjective"
    }

    cand_ids = [c.id for c in candidates_50]
    ans_stmt = select(Answer).where(Answer.profile_id.in_(cand_ids))
    ans_res = await db.execute(ans_stmt)
    all_cand_answers = ans_res.scalars().all()

    # Group answers by candidate_id
    cand_ans_map: Dict[str, List[Answer]] = {}
    for a in all_cand_answers:
        cand_ans_map.setdefault(a.profile_id, []).append(a)

    for cand in candidates_50:
        c_answers = cand_ans_map.get(cand.id, [])
        if not c_answers:
            continue

        # 1. Objective match calculation
        obj_res = calculate_objective_match(
            target_profile, cand, target_answers, c_answers, kootas_metadata
        )
        if not obj_res.is_viable:
            continue

        # 2. Check NLI contradictions across top subjective Kootas
        has_critical_contradiction = False
        koota_nli_scores = []
        for a in c_answers:
            if a.question_type == "subjective" and a.koota_id in t_subj_map:
                nli_res = await evaluate_nli_pair(t_subj_map[a.koota_id], a.raw_value)
                if (a.koota_id == 41 or a.koota_id in [18, 23, 41]) and nli_res.is_contradiction:
                    has_critical_contradiction = True
                    break
                koota_nli_scores.append(nli_res.score)

        # Hard drop on critical contradiction
        if has_critical_contradiction:
            continue

        # 3. Semantic scoring on remaining subjective questions
        semantic_scores, _ = await score_all_subjective_kootas(
            target_answers, c_answers, kootas_metadata
        )

        # Preliminary rank score combining objective + NLI
        obj_avg = (
            sum(obj_res.koota_scores.values()) / len(obj_res.koota_scores)
            if obj_res.koota_scores
            else 0.5
        )
        avg_nli = sum(koota_nli_scores) / len(koota_nli_scores) if koota_nli_scores else 0.5
        prelim_score = (0.6 * obj_avg) + (0.4 * avg_nli)

        survivors.append((cand, c_answers, obj_res.koota_scores, semantic_scores, prelim_score))

    # Rank by prelim score and keep top 10 shortlist
    survivors.sort(key=lambda x: x[4], reverse=True)
    shortlist_10 = [(c, ans, obj, subj) for c, ans, obj, subj, _ in survivors[:limit]]
    return shortlist_10


async def run_candidates_funnel_for_profile(
    profile_id: str,
    db: AsyncSession,
    kootas_metadata: Dict[int, Dict[str, Any]],
    max_weekly_matches: int = 5,
) -> List[WeeklyMatchList]:
    """Execute the complete 5-stage Weekly Precomputed Match Funnel for a single profile.
    
    1. SQL Hard Filter
    2. Vector ANN (Koota 41 Life Purpose, LIMIT 50)
    3. NLI Contradiction Screen (drop Koota 41 contradictions, keep top 10)
    4. Multi-Provider LLM Judge (ONLY on top 10 shortlist)
    5. Gated Aggregation & Persist top 5 into WeeklyMatchList
    """
    # 1. Fetch Target Profile & Answers
    stmt = select(Profile).where(Profile.id == profile_id)
    res = await db.execute(stmt)
    target_profile = res.scalar_one_or_none()
    if not target_profile:
        return []

    ans_stmt = select(Answer).where(Answer.profile_id == profile_id)
    ans_res = await db.execute(ans_stmt)
    target_answers = list(ans_res.scalars().all())

    # Step 1: SQL Hard Filter
    sql_candidates = await get_sql_hard_filtered_candidates(db, target_profile)
    if not sql_candidates:
        return []

    # Step 2: Vector ANN on Koota 41 embedding (LIMIT 50)
    target_k41_emb = await get_target_koota_41_embedding(db, profile_id)
    candidates_50 = await filter_vector_ann_top_50(db, target_k41_emb, sql_candidates, limit=50)

    # Step 3: NLI Screen (drop K41 contradictions, keep top 10)
    shortlist_10 = await screen_nli_top_10(
        db, target_profile, candidates_50, target_answers, kootas_metadata, limit=10
    )
    # Pre-fetch FollowingList for target and shortlist candidates
    all_shortlist_ids = [profile_id] + [cand.id for cand, _, _, _ in shortlist_10]
    stmt_f = select(FollowingList).where(FollowingList.profile_id.in_(all_shortlist_ids))
    res_f = await db.execute(stmt_f)
    f_map = {f.profile_id: f for f in res_f.scalars().all()}
    target_f = f_map.get(profile_id)

    # Step 4: LLM Judge on top 10 shortlist only (evaluated concurrently)
    async def _evaluate_single_candidate(cand_tuple):
        cand, c_answers, obj_scores, subj_scores = cand_tuple
        llm_judge_map = await evaluate_all_top_kootas_llm_judge(
            target_answers, c_answers, kootas_metadata
        )
        aggregate = aggregate_scores(
            is_viable=True,
            hard_filter_reason=None,
            objective_koota_scores=obj_scores,
            semantic_koota_scores=subj_scores,
            kootas_metadata=kootas_metadata,
            llm_judge_results=llm_judge_map,
        )
        tier_eval = classify_tier(aggregate, kootas_metadata)
        
        # Social overlap bonus signal (computed after tiering, strictly non-gating)
        cand_f = f_map.get(cand.id)
        overlap_info = compute_overlap(
            usernames_a=target_f.usernames if target_f else [],
            usernames_b=cand_f.usernames if cand_f else [],
            opted_in_a=target_f.opted_in if target_f else False,
            opted_in_b=cand_f.opted_in if cand_f else False,
        )

        return WeeklyMatchList(
            profile_id=profile_id,
            candidate_id=cand.id,
            score=aggregate.overall_score or 0.0,
            tier=tier_eval.tier,
            alignment_points=tier_eval.alignment_points,
            friction_points=tier_eval.friction_points,
            contradiction_gates=aggregate.contradiction_gates,
            social_overlap_score=overlap_info["overlap_score"],
            shared_account_count=overlap_info["shared_count"],
            generated_at=utc_now(),
        )

    evaluated_matches: List[WeeklyMatchList] = await asyncio.gather(
        *[_evaluate_single_candidate(item) for item in shortlist_10]
    )

    # Step 5: Sort by score descending and persist top 5 in same transaction
    evaluated_matches = list(evaluated_matches)
    evaluated_matches.sort(key=lambda m: m.score, reverse=True)
    top_5 = evaluated_matches[:max_weekly_matches]

    # Delete existing weekly matches for this profile and insert new top 5
    await db.execute(delete(WeeklyMatchList).where(WeeklyMatchList.profile_id == profile_id))
    for m in top_5:
        db.add(m)

    await db.commit()
    return top_5
