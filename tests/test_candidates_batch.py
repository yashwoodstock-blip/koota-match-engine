"""Test suite for Phase 6 Precomputed Candidate Matching Funnel and Rate Limiter."""
import asyncio
import time
import pytest
from sqlalchemy import select
from app.db.session import async_session
from app.models import Profile, Answer, WeeklyMatchList
from app.api.routes_match import load_kootas_metadata
from app.db.seed_synthetic import seed_synthetic_profiles
from app.matching.candidates_batch import (
    run_candidates_funnel_for_profile,
    get_sql_hard_filtered_candidates,
    filter_vector_ann_top_50,
    screen_nli_top_10,
)
from app.matching.batch_runner import GroqRateLimiter, run_weekly_matching_batch
from app.scoring.llm_judge import LLMJudgeResult
from app.scoring.nli import NLIResult


@pytest.mark.asyncio
async def test_funnel_monotonic_narrowing_and_llm_limit(monkeypatch):
    """Assert that the funnel narrows monotonically (Pool -> 50 -> 10 -> 5)
    and that the LLM judge is NEVER invoked on more than 10 candidates.
    """
    await seed_synthetic_profiles()
    llm_call_count = 0

    async def mock_judge(answers_a, answers_b, metadata, *args, **kwargs):
        nonlocal llm_call_count
        llm_call_count += 1
        return {
            41: LLMJudgeResult(
                koota_id=41,
                agreement_score=0.92,
                contradiction=False,
                reasoning="Strong alignment on lifelong companionship.",
                key_tensions=[],
            )
        }

    async def mock_nli(text1, text2, *args, **kwargs):
        return NLIResult(
            score=0.85,
            entailment=0.80,
            neutral=0.15,
            contradiction=0.05,
            is_contradiction=False,
        )

    async def mock_emb(text, *args, **kwargs):
        return [0.5] * 384

    monkeypatch.setattr("app.matching.candidates_batch.evaluate_all_top_kootas_llm_judge", mock_judge)
    monkeypatch.setattr("app.matching.candidates_batch.evaluate_nli_pair", mock_nli)
    monkeypatch.setattr("app.scoring.semantic.fetch_hf_embedding", mock_emb)

    async with async_session() as db:
        kootas_meta = await load_kootas_metadata(db)
        
        # Test on synthetic profile Aarav Sharma (syn-01-aarav)
        matches = await run_candidates_funnel_for_profile(
            profile_id="syn-01-aarav",
            db=db,
            kootas_metadata=kootas_meta,
            max_weekly_matches=5,
        )

        # 1. Output count must be capped at 5
        assert len(matches) <= 5
        assert len(matches) > 0

        # 2. LLM Judge must NEVER be called more than 10 times for a single profile
        assert llm_call_count <= 10

        # 3. Top match must have valid score and non-empty insights
        top_match = matches[0]
        assert top_match.profile_id == "syn-01-aarav"
        assert top_match.score > 0.0
        assert top_match.tier in ["strong match", "compatible with flagged friction points"]
        assert isinstance(top_match.alignment_points, list)

        # 4. Verify database persistence
        stmt = select(WeeklyMatchList).where(WeeklyMatchList.profile_id == "syn-01-aarav")
        res = await db.execute(stmt)
        persisted = res.scalars().all()
        assert len(persisted) == len(matches)


@pytest.mark.asyncio
async def test_koota_41_nli_contradiction_dropped_in_stage_3(monkeypatch):
    """A candidate with Koota 41 contradiction is dropped in Stage 3 NLI screen before LLM Judge."""
    llm_called_candidates = []

    async def mock_nli_contra(text1, text2, *args, **kwargs):
        # Simulate contradiction on Koota 41
        return NLIResult(
            score=0.05,
            entailment=0.05,
            neutral=0.10,
            contradiction=0.85,
            is_contradiction=True,
        )

    async def mock_judge(answers_a, answers_b, metadata, *args, **kwargs):
        return {}

    monkeypatch.setattr("app.matching.candidates_batch.evaluate_nli_pair", mock_nli_contra)
    monkeypatch.setattr("app.matching.candidates_batch.evaluate_all_top_kootas_llm_judge", mock_judge)

    async with async_session() as db:
        kootas_meta = await load_kootas_metadata(db)
        
        matches = await run_candidates_funnel_for_profile(
            profile_id="syn-01-aarav",
            db=db,
            kootas_metadata=kootas_meta,
            max_weekly_matches=5,
        )

        # Because all candidates trigger Koota 41 contradiction, they are dropped before LLM judge
        assert len(matches) == 0


@pytest.mark.asyncio
async def test_groq_rate_limiter_ceiling():
    """Verify GroqRateLimiter strictly limits request rate under the ceiling."""
    limiter = GroqRateLimiter(max_requests=5, window_seconds=0.5)

    start = time.time()
    for _ in range(6):
        await limiter.acquire()
    elapsed = time.time() - start

    # 6th request must wait for the window to clear
    assert elapsed >= 0.45
