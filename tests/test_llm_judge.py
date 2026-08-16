"""TDD Test Suite for Multi-Provider LLM Judge."""
import pytest
from app.scoring.llm_judge import (
    evaluate_llm_judge_koota,
    evaluate_all_top_kootas_llm_judge,
    LLMJudgeResult,
    TOP_WEIGHTED_JUDGE_KOOTAS,
)


@pytest.mark.asyncio
async def test_llm_judge_groq_mock(monkeypatch):
    """Test LLM judge evaluation using mocked Groq response."""
    async def mock_groq_call(prompt, *args, **kwargs):
        return {
            "agreement_score": 0.90,
            "contradiction": False,
            "reasoning": "Both candidates emphasize lifelong companionship and egalitarian partnership.",
            "key_tensions": [],
        }

    monkeypatch.setattr("app.scoring.llm_judge.call_groq_judge", mock_groq_call)

    res = await evaluate_llm_judge_koota(
        koota_id=41,
        koota_name="Life Purpose & Meaning of Marriage",
        question="In your own words, what is marriage for?",
        ans_a="Marriage is a sacred lifelong journey of companionship.",
        ans_b="Marriage is a deep enduring partnership and joint growth.",
        provider_preference="groq",
    )

    assert isinstance(res, LLMJudgeResult)
    assert res.agreement_score == 0.90
    assert res.contradiction is False
    assert "companionship" in res.reasoning.lower()


@pytest.mark.asyncio
async def test_llm_judge_contradiction_detection(monkeypatch):
    """Test LLM judge correctly flags a severe contradiction."""
    async def mock_judge_contradiction(prompt, *args, **kwargs):
        return {
            "agreement_score": 0.10,
            "contradiction": True,
            "reasoning": "Candidate A demands absolute elder authority, whereas Candidate B refuses any parental interference.",
            "key_tensions": ["Elder authority vs personal spousal autonomy"],
        }, "groq"

    monkeypatch.setattr("app.scoring.llm_judge.dispatch_llm_judge", mock_judge_contradiction)

    res = await evaluate_llm_judge_koota(
        koota_id=18,
        koota_name="In-Law Relationship Expectations",
        question="How much say should parents have?",
        ans_a="Complete traditional deference, touching feet daily, parents have full veto.",
        ans_b="Zero in-law interference; strict distant boundaries.",
    )

    assert res.contradiction is True
    assert res.agreement_score <= 0.20
    assert len(res.key_tensions) > 0


@pytest.mark.asyncio
async def test_llm_judge_fallback_chain(monkeypatch):
    """Test that when Groq fails, system seamlessly falls back to OpenRouter then Gemini."""
    groq_called = False
    openrouter_called = False
    gemini_called = False

    async def mock_groq_fail(*args, **kwargs):
        nonlocal groq_called
        groq_called = True
        raise Exception("Groq rate limit 429")

    async def mock_openrouter_fail(*args, **kwargs):
        nonlocal openrouter_called
        openrouter_called = True
        raise Exception("OpenRouter busy")

    async def mock_gemini_success(*args, **kwargs):
        nonlocal gemini_called
        gemini_called = True
        return {
            "agreement_score": 0.85,
            "contradiction": False,
            "reasoning": "Fallback Gemini evaluated successfully.",
            "key_tensions": [],
        }

    monkeypatch.setattr("app.scoring.llm_judge.call_groq_judge", mock_groq_fail)
    monkeypatch.setattr("app.scoring.llm_judge.call_openrouter_judge", mock_openrouter_fail)
    monkeypatch.setattr("app.scoring.llm_judge.call_gemini_judge", mock_gemini_success)

    res = await evaluate_llm_judge_koota(
        koota_id=23,
        koota_name="Post-Marriage Career Continuity",
        question="Career priorities",
        ans_a="Mutual support",
        ans_b="Equal opportunity",
    )

    assert groq_called is True
    assert openrouter_called is True
    assert gemini_called is True
    assert res.agreement_score == 0.85


def test_top_weighted_koota_set():
    """Verify top weighted kootas include 41, 18, 23, 22, 21, 40, 12, 19, 31, 7."""
    assert 41 in TOP_WEIGHTED_JUDGE_KOOTAS
    assert 18 in TOP_WEIGHTED_JUDGE_KOOTAS
    assert 23 in TOP_WEIGHTED_JUDGE_KOOTAS
    assert 22 in TOP_WEIGHTED_JUDGE_KOOTAS
    assert 12 in TOP_WEIGHTED_JUDGE_KOOTAS
