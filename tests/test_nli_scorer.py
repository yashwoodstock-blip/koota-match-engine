"""TDD Test Suite for NLI Contradiction Scorer."""
import pytest
from app.scoring.nli import (
    compute_nli_score,
    evaluate_nli_pair,
    NLIResult,
)


def test_nli_score_entailment():
    """High entailment probability should result in high similarity score."""
    res = compute_nli_score(entailment=0.90, neutral=0.08, contradiction=0.02)
    assert res.score >= 0.85
    assert res.is_contradiction is False


def test_nli_score_contradiction():
    """High contradiction probability should drop score to 0.0 and flag contradiction."""
    res = compute_nli_score(entailment=0.05, neutral=0.10, contradiction=0.85)
    assert res.score <= 0.10
    assert res.is_contradiction is True


@pytest.mark.asyncio
async def test_evaluate_nli_pair_with_mock(monkeypatch):
    """Mock HF NLI API call to test pair evaluation."""
    async def mock_hf_nli(premise, hypothesis, *args, **kwargs):
        if "patriarchal" in hypothesis or "refuse" in hypothesis:
            return {"labels": ["contradiction", "neutral", "entailment"], "scores": [0.88, 0.10, 0.02]}
        return {"labels": ["entailment", "neutral", "contradiction"], "scores": [0.92, 0.06, 0.02]}

    monkeypatch.setattr("app.scoring.nli.fetch_hf_nli", mock_hf_nli)

    # 1. Aligned statements
    res_aligned = await evaluate_nli_pair(
        "I value mutual career support and partnership.",
        "Both partners should actively support each other's professional dreams."
    )
    assert res_aligned.is_contradiction is False
    assert res_aligned.score >= 0.85

    # 2. Contradictory statements
    res_contra = await evaluate_nli_pair(
        "I expect complete elder deference and touching feet daily.",
        "I refuse any patriarchal interference from in-laws."
    )
    assert res_contra.is_contradiction is True
    assert res_contra.score <= 0.15
