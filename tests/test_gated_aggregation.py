"""TDD Test Suite for Gated Aggregation & Contradiction Override Logic."""
import pytest
from app.scoring.aggregate import (
    aggregate_scores,
    AggregateMatchResult,
    ContradictionGate,
)
from app.scoring.tiers import classify_tier
from app.scoring.llm_judge import LLMJudgeResult


def test_gated_override_on_koota_41_life_purpose():
    """A direct contradiction on Koota 41 (Life Purpose) must cap the tier to 'not viable'
    even if all other 41 Kootas have a perfect 1.0 match.
    """
    # 41 Kootas have score 1.0, but Koota 41 has LLM Judge contradiction
    kootas_meta = {
        k: {"weight": 10, "name": f"Koota {k}", "pillar": "Pillar", "question_type": "mixed"}
        for k in range(1, 41)
    }
    kootas_meta[41] = {
        "weight": 15,
        "name": "Life Purpose & Meaning of Marriage",
        "pillar": "PILLAR M",
        "question_type": "subjective_only",
    }

    obj_scores = {k: 1.0 for k in range(1, 41)}
    subj_scores = {k: 1.0 for k in range(1, 41)}
    subj_scores[41] = 0.10  # Complete mismatch on marriage purpose

    llm_judge_map = {
        41: LLMJudgeResult(
            koota_id=41,
            agreement_score=0.10,
            contradiction=True,
            reasoning="Fundamental irreconcilable disagreement on why they want to be married.",
            key_tensions=["Irreconcilable life purposes"],
        )
    }

    result = aggregate_scores(
        is_viable=True,
        hard_filter_reason=None,
        objective_koota_scores=obj_scores,
        semantic_koota_scores=subj_scores,
        kootas_metadata=kootas_meta,
        llm_judge_results=llm_judge_map,
    )

    assert result.is_viable is True
    assert len(result.contradiction_gates) >= 1
    gate_41 = next((g for g in result.contradiction_gates if g["koota_id"] == 41), None)
    assert gate_41 is not None
    assert gate_41["severity"] == "critical"

    # Tier classifier evaluation
    tier_eval = classify_tier(result, kootas_meta)
    # Gated math ensures Koota 41 contradiction cannot be strong match or even compatible -> not viable
    assert tier_eval.tier == "not viable"
    assert any("Life Purpose" in p or "Contradiction" in p for p in tier_eval.friction_points)


def test_gated_ceiling_on_koota_18_in_law_contradiction():
    """A direct contradiction on Koota 18 caps the tier to 'compatible with flagged friction points'
    and prevents an otherwise 0.90+ match from becoming a 'strong match'.
    """
    kootas_meta = {
        18: {"weight": 14, "name": "In-Law Relationship Expectations", "pillar": "PILLAR F", "question_type": "mixed"},
        22: {"weight": 12, "name": "Gender Roles & Division of Labor", "pillar": "PILLAR G", "question_type": "mixed"},
        41: {"weight": 15, "name": "Life Purpose", "pillar": "PILLAR M", "question_type": "subjective_only"},
    }

    obj_scores = {18: 0.95, 22: 0.95}
    subj_scores = {18: 0.10, 22: 0.95, 41: 0.95}

    llm_judge_map = {
        18: LLMJudgeResult(
            koota_id=18,
            agreement_score=0.10,
            contradiction=True,
            reasoning="Direct opposition on elder authority.",
            key_tensions=["Elder authority vs autonomy"],
        )
    }

    result = aggregate_scores(
        is_viable=True,
        hard_filter_reason=None,
        objective_koota_scores=obj_scores,
        semantic_koota_scores=subj_scores,
        kootas_metadata=kootas_meta,
        llm_judge_results=llm_judge_map,
    )

    assert result.tier_ceiling == "compatible with flagged friction points"
    tier_eval = classify_tier(result, kootas_meta)
    assert tier_eval.tier == "compatible with flagged friction points"
    assert tier_eval.tier != "strong match"
