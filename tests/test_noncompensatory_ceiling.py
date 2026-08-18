"""Tests for non-compensatory per-Koota continuous ceiling function and compensatory scoring separation."""
import pytest
from app.scoring.aggregate import (
    calculate_koota_ceiling,
    aggregate_scores,
    AggregateMatchResult,
)


def test_ceiling_above_tau_high():
    """Score at or above tau_high enforces no penalty (ceiling = 1.0)."""
    meta = {
        "koota_id": 7,
        "name": "Conflict Style",
        "aggregation_type": "non_compensatory",
        "tau_low": 0.40,
        "tau_high": 0.75,
        "floor": 0.40,
    }
    assert calculate_koota_ceiling(0.75, meta) == 1.0
    assert calculate_koota_ceiling(0.90, meta) == 1.0
    assert calculate_koota_ceiling(1.0, meta) == 1.0


def test_ceiling_below_tau_low():
    """Score at or below tau_low enforces minimum floor."""
    meta = {
        "koota_id": 7,
        "name": "Conflict Style",
        "aggregation_type": "non_compensatory",
        "tau_low": 0.40,
        "tau_high": 0.75,
        "floor": 0.40,
    }
    assert calculate_koota_ceiling(0.40, meta) == 0.40
    assert calculate_koota_ceiling(0.25, meta) == 0.40
    assert calculate_koota_ceiling(0.0, meta) == 0.40


def test_ceiling_continuous_interpolation():
    """Score between tau_low and tau_high interpolates linearly without jumps."""
    meta = {
        "koota_id": 7,
        "name": "Conflict Style",
        "aggregation_type": "non_compensatory",
        "tau_low": 0.40,
        "tau_high": 0.75,
        "floor": 0.40,
    }
    # Midpoint: (0.40 + 0.75) / 2 = 0.575
    # Expected ceiling: 0.40 + (1.0 - 0.40) * (0.575 - 0.40) / (0.75 - 0.40) = 0.40 + 0.60 * 0.5 = 0.70
    mid = 0.575
    c_mid = calculate_koota_ceiling(mid, meta)
    assert round(c_mid, 4) == 0.7000

    # Test boundary continuity
    assert round(calculate_koota_ceiling(0.4001, meta), 3) == 0.400
    assert round(calculate_koota_ceiling(0.7499, meta), 3) == 1.000


def test_ceiling_degenerate_hard_cliff():
    """Degenerate hard-cliff step function when tau_low == tau_high."""
    meta = {
        "koota_id": 31,
        "name": "Desire for Children & Timing",
        "aggregation_type": "non_compensatory",
        "tau_low": 0.70,
        "tau_high": 0.70,
        "floor": 0.30,
    }
    assert calculate_koota_ceiling(0.70, meta) == 1.0
    assert calculate_koota_ceiling(0.85, meta) == 1.0
    assert calculate_koota_ceiling(0.699, meta) == 0.30
    assert calculate_koota_ceiling(0.30, meta) == 0.30


def test_compensatory_koota_has_no_ceiling():
    """Compensatory Kootas always return ceiling = 1.0."""
    meta = {
        "koota_id": 25,
        "name": "Financial Philosophy",
        "aggregation_type": "compensatory",
        "tau_low": None,
        "tau_high": None,
        "floor": None,
    }
    assert calculate_koota_ceiling(0.10, meta) == 1.0
    assert calculate_koota_ceiling(0.90, meta) == 1.0


def test_aggregate_scores_weakest_link_ceiling():
    """High compensatory scores suppressed by low score on non-compensatory conflict Koota."""
    kootas_meta = {
        # Compensatory Kootas (Career, Finance, Household)
        23: {"weight": 10, "name": "Career Continuity", "pillar": "PILLAR G", "aggregation_type": "compensatory"},
        25: {"weight": 10, "name": "Financial Philosophy", "pillar": "PILLAR H", "aggregation_type": "compensatory"},
        26: {"weight": 10, "name": "Financial Structure", "pillar": "PILLAR H", "aggregation_type": "compensatory"},
        # Non-compensatory Koota (Conflict Style)
        7: {
            "weight": 10,
            "name": "Conflict Style",
            "pillar": "PILLAR C — Communication & Connection",
            "aggregation_type": "non_compensatory",
            "tau_low": 0.40,
            "tau_high": 0.75,
            "floor": 0.40,
        },
    }

    # High compensatory scores = 0.90 across K23, K25, K26 -> CompScore = 0.90
    # Low non-compensatory score = 0.40 on K7 -> ceiling = 0.40
    obj_scores = {23: 0.90, 25: 0.90, 26: 0.90, 7: 0.40}
    res = aggregate_scores(
        is_viable=True,
        hard_filter_reason=None,
        objective_koota_scores=obj_scores,
        semantic_koota_scores={},
        kootas_metadata=kootas_meta,
    )

    assert res.is_viable is True
    assert res.compensatory_score == 0.90
    assert res.ceiling_applied == 0.40
    assert res.overall_score == round(0.90 * 0.40, 4)  # 0.3600
    assert res.capped_by is not None
    assert res.capped_by["koota_id"] == 7
    assert res.capped_by["koota_name"] == "Conflict Style"


def test_aggregate_scores_multiple_non_compensatory_takes_min():
    """When multiple non-compensatory dimensions are impaired, min() ceiling is applied."""
    kootas_meta = {
        25: {"weight": 10, "name": "Finance", "pillar": "PILLAR H", "aggregation_type": "compensatory"},
        7: {
            "weight": 10,
            "name": "Conflict Style",
            "pillar": "PILLAR C",
            "aggregation_type": "non_compensatory",
            "tau_low": 0.40,
            "tau_high": 0.75,
            "floor": 0.40,
        },
        41: {
            "weight": 15,
            "name": "Life Purpose",
            "pillar": "PILLAR M",
            "aggregation_type": "non_compensatory",
            "tau_low": 0.50,
            "tau_high": 0.80,
            "floor": 0.30,
        },
    }

    # K25 = 1.0 (CompScore = 1.0)
    # K7 = 0.575 (Ceiling = 0.70)
    # K41 = 0.45 (Below tau_low 0.50 -> Floor = 0.30)
    # min(0.70, 0.30) = 0.30
    obj_scores = {25: 1.0, 7: 0.575, 41: 0.45}
    res = aggregate_scores(
        is_viable=True,
        hard_filter_reason=None,
        objective_koota_scores=obj_scores,
        semantic_koota_scores={},
        kootas_metadata=kootas_meta,
    )

    assert res.compensatory_score == 1.0
    assert res.ceiling_applied == 0.30
    assert res.overall_score == 0.3000
    assert res.capped_by["koota_id"] == 41
    assert res.capped_by["koota_name"] == "Life Purpose"
