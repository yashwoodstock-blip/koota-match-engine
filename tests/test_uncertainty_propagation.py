"""Tests for Uncertainty Quantification, Variance Propagation, and Risk-Adjusted Ranking."""
import pytest
from app.scoring.aggregate import (
    aggregate_scores,
    calculate_koota_uncertainty,
    calculate_koota_ceiling,
)
from app.scoring.tiers import classify_tier


@pytest.fixture
def sample_kootas_metadata():
    """Mock metadata for 42 Kootas with weights and non-compensatory attributes."""
    meta = {}
    for i in range(1, 43):
        is_non_comp = i in [7, 8, 9, 10, 13, 14, 15, 16, 31, 32, 33, 36, 38, 39, 40, 41]
        weight = 15 if i == 41 else (10 if i in [7, 12, 18, 19, 21, 22, 23, 31] else 5)
        meta[i] = {
            "name": f"Koota {i}",
            "pillar": f"Pillar {i % 6}",
            "weight": weight,
            "aggregation_type": "non_compensatory" if is_non_comp else "compensatory",
            "tau_low": 0.40 if is_non_comp else None,
            "tau_high": 0.75 if is_non_comp else None,
            "floor": 0.40 if is_non_comp else None,
        }
    return meta


def test_motivating_example_risk_adjusted_ranking_flip(sample_kootas_metadata):
    """Test the motivating specification example:
    Candidate A: Raw score 0.82 ± 0.02
    Candidate B: Raw score 0.84 ± 0.15
    Assert Candidate A ranks above Candidate B under Risk-Adjusted Score.
    """
    # Build candidate A (clean, consistent objective answers)
    obj_scores_a = {k: 0.82 for k in range(1, 43)}
    override_uncertainties_a = {k: 0.02 for k in range(1, 43)}
    res_a = aggregate_scores(
        is_viable=True,
        hard_filter_reason=None,
        objective_koota_scores=obj_scores_a,
        semantic_koota_scores={},
        kootas_metadata=sample_kootas_metadata,
        koota_uncertainties_override=override_uncertainties_a,
    )
    tier_a = classify_tier(res_a, sample_kootas_metadata)

    # Build candidate B (noisy / volatile answers)
    obj_scores_b = {k: 0.84 for k in range(1, 43)}
    override_uncertainties_b = {k: 0.15 for k in range(1, 43)}
    res_b = aggregate_scores(
        is_viable=True,
        hard_filter_reason=None,
        objective_koota_scores=obj_scores_b,
        semantic_koota_scores={},
        kootas_metadata=sample_kootas_metadata,
        koota_uncertainties_override=override_uncertainties_b,
    )
    tier_b = classify_tier(res_b, sample_kootas_metadata)

    # Verify raw scores
    assert res_a.overall_score == 0.82
    assert res_b.overall_score == 0.84

    # Verify uncertainty terms
    assert res_a.score_uncertainty < 0.03
    assert res_b.score_uncertainty > 0.05

    # Verify risk-adjusted ranking flip
    assert res_a.risk_adjusted_score > res_b.risk_adjusted_score

    # Verify confidence labeling
    assert res_a.confidence == "High"
    assert res_b.confidence in ["Moderate", "Low"]

    # Verify tier assignment
    assert tier_a.tier == "strong match"
    assert tier_b.tier == "compatible with flagged friction points"


def test_evidence_coverage_percentage_calculation(sample_kootas_metadata):
    """Verify evidence coverage pct reflects the answered weighted proportion of 42 Kootas."""
    # 1. Full questionnaire answered
    full_obj = {k: 0.80 for k in range(1, 43)}
    res_full = aggregate_scores(
        is_viable=True,
        hard_filter_reason=None,
        objective_koota_scores=full_obj,
        semantic_koota_scores={},
        kootas_metadata=sample_kootas_metadata,
    )
    assert res_full.evidence_coverage_pct == 100.0

    # 2. Half questionnaire answered
    half_obj = {k: 0.80 for k in range(1, 22)}
    res_half = aggregate_scores(
        is_viable=True,
        hard_filter_reason=None,
        objective_koota_scores=half_obj,
        semantic_koota_scores={},
        kootas_metadata=sample_kootas_metadata,
    )
    assert 40.0 <= res_half.evidence_coverage_pct <= 60.0
    assert res_half.confidence == "Low"  # Coverage < 60% forces Low confidence


def test_confidence_interval_bounds_safety(sample_kootas_metadata):
    """Verify 95% confidence interval [lower, upper] is strictly bounded in [0.0, 1.0]."""
    # Extremely high score with high uncertainty
    high_obj = {k: 0.98 for k in range(1, 43)}
    high_unc = {k: 0.30 for k in range(1, 43)}
    res = aggregate_scores(
        is_viable=True,
        hard_filter_reason=None,
        objective_koota_scores=high_obj,
        semantic_koota_scores={},
        kootas_metadata=sample_kootas_metadata,
        koota_uncertainties_override=high_unc,
    )
    assert res.score_interval is not None
    lower, upper = res.score_interval
    assert 0.0 <= lower <= upper <= 1.0
    assert upper == 1.0  # Clamped at 1.0


def test_high_impact_uncertainty_callouts(sample_kootas_metadata):
    """Verify high-impact uncertainty callout triggers for high-weight Kootas with high sigma."""
    obj_scores = {k: 0.80 for k in range(1, 43)}
    # Inject high uncertainty on Koota 41 (weight 15) and Koota 1 (weight 5)
    unc_map = {k: 0.03 for k in range(1, 43)}
    unc_map[41] = 0.25  # High weight (15) & High sigma (0.25) -> SHOULD appear
    unc_map[1] = 0.25   # Low weight (5) & High sigma (0.25) -> should NOT appear

    res = aggregate_scores(
        is_viable=True,
        hard_filter_reason=None,
        objective_koota_scores=obj_scores,
        semantic_koota_scores={},
        kootas_metadata=sample_kootas_metadata,
        koota_uncertainties_override=unc_map,
    )

    assert any("Koota 41" in callout for callout in res.high_impact_uncertainty)
    assert not any("Koota 1" in callout for callout in res.high_impact_uncertainty)


def test_koota_uncertainty_signal_derivation():
    """Verify calculate_koota_uncertainty behavior across modalities and signals."""
    meta = {"weight": 10}

    # 1. Unanswered
    sigma_unanswered = calculate_koota_uncertainty(1, meta, is_answered=False, has_objective=False, has_semantic=False)
    assert sigma_unanswered == 0.35

    # 2. Pure objective
    sigma_obj = calculate_koota_uncertainty(1, meta, is_answered=True, has_objective=True, has_semantic=False)
    assert sigma_obj == 0.04

    # 3. Pure subjective
    sigma_subj = calculate_koota_uncertainty(1, meta, is_answered=True, has_objective=False, has_semantic=True)
    assert sigma_subj == 0.12

    # 4. Objective with high divergence
    sigma_div = calculate_koota_uncertainty(1, meta, is_answered=True, has_objective=True, has_semantic=True, divergence=0.60)
    assert sigma_div > sigma_obj
