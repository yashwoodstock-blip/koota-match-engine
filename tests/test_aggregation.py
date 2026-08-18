"""TDD Test Suite for Score Aggregation & Disagreement Flagging."""
import pytest
from app.models import Profile, Answer
from app.scoring.aggregate import (
    aggregate_scores,
    detect_disagreement_flags,
    AggregateMatchResult,
)


def test_clean_aggregation_without_divergence():
    """When objective and subjective scores align, overall score combines them accurately."""
    objective_scores = {
        7: 0.80,   # Conflict Style (w9)
        18: 0.85,  # In-Law Expectations (w14)
    }
    semantic_scores = {
        18: 0.80,  # In-Law Expectations (w14)
        41: 0.90,  # Life Purpose (w15)
    }

    kootas_meta = {
        7: {"weight": 9, "name": "Conflict Style", "pillar": "PILLAR C", "question_type": "mixed", "aggregation_type": "non_compensatory", "tau_low": 0.40, "tau_high": 0.75, "floor": 0.40},
        18: {"weight": 14, "name": "In-Law Relationship Expectations", "pillar": "PILLAR F", "question_type": "mixed", "aggregation_type": "compensatory"},
        41: {"weight": 15, "name": "Life Purpose & Meaning of Marriage", "pillar": "PILLAR M", "question_type": "subjective_only", "aggregation_type": "non_compensatory", "tau_low": 0.50, "tau_high": 0.80, "floor": 0.30},
    }

    result = aggregate_scores(
        is_viable=True,
        hard_filter_reason=None,
        objective_koota_scores=objective_scores,
        semantic_koota_scores=semantic_scores,
        kootas_metadata=kootas_meta,
    )

    assert result.is_viable is True
    assert result.hard_filter_reason is None
    assert len(result.disagreement_flags) == 0

    # Compensatory Koota 18 combined = (0.85 + 0.80) / 2 = 0.825
    # Non-compensatory Koota 7 (0.80 >= 0.75) -> ceiling 1.0
    # Non-compensatory Koota 41 (0.90 >= 0.80) -> ceiling 1.0
    assert result.compensatory_score == 0.825
    assert result.ceiling_applied == 1.0
    assert result.capped_by is None
    assert result.overall_score == 0.8250


def test_disagreement_flag_on_koota_18_in_laws():
    """When objective score is high (0.90) but subjective score is low (0.15) on Koota 18,
    a disagreement flag must be raised and preserved, NEVER averaged away.
    """
    objective_scores = {
        18: 0.90,  # In-Laws: Both chose 'Weekly visits' on multiple choice
        22: 0.85,  # Gender roles
    }
    semantic_scores = {
        18: 0.15,  # In-Laws: Deep free-text reveals severe underlying hostility vs traditional obedience
        22: 0.80,
    }

    kootas_meta = {
        18: {"weight": 14, "name": "In-Law Relationship Expectations", "pillar": "PILLAR F — Family of Origin", "question_type": "mixed"},
        22: {"weight": 12, "name": "Gender Roles & Division of Labor", "pillar": "PILLAR G — Household Structure", "question_type": "mixed"},
    }

    result = aggregate_scores(
        is_viable=True,
        hard_filter_reason=None,
        objective_koota_scores=objective_scores,
        semantic_koota_scores=semantic_scores,
        kootas_metadata=kootas_meta,
        divergence_threshold=0.35,
    )

    assert result.is_viable is True
    assert len(result.disagreement_flags) == 1

    flag = result.disagreement_flags[0]
    assert flag["koota_id"] == 18
    assert flag["koota_name"] == "In-Law Relationship Expectations"
    assert flag["objective_score"] == 0.90
    assert flag["subjective_score"] == 0.15
    assert flag["divergence"] == pytest.approx(0.75, 1e-2)
    assert flag["severity"] == "high"
    assert "disagreement" in flag["note"].lower() or "friction" in flag["note"].lower() or "divergence" in flag["note"].lower()


def test_multiple_disagreement_flags():
    """Test flagging across multiple critical India-context Kootas (18, 22, 23)."""
    objective_scores = {
        18: 0.95,
        22: 0.90,
        23: 0.85,
    }
    semantic_scores = {
        18: 0.20,  # Divergence 0.75
        22: 0.30,  # Divergence 0.60
        23: 0.40,  # Divergence 0.45
    }

    kootas_meta = {
        18: {"weight": 14, "name": "In-Law Relationship Expectations", "pillar": "PILLAR F", "question_type": "mixed"},
        22: {"weight": 12, "name": "Gender Roles & Division of Labor", "pillar": "PILLAR G", "question_type": "mixed"},
        23: {"weight": 13, "name": "Post-Marriage Career Continuity", "pillar": "PILLAR G", "question_type": "mixed"},
    }

    flags = detect_disagreement_flags(objective_scores, semantic_scores, kootas_meta, threshold=0.35)
    assert len(flags) == 3
    flagged_ids = [f["koota_id"] for f in flags]
    assert 18 in flagged_ids
    assert 22 in flagged_ids
    assert 23 in flagged_ids
