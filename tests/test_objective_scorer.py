"""TDD Test Suite for Objective Scorer & Hard Filters."""
import pytest
from app.models import Profile, Answer
from app.scoring.objective import (
    check_hard_filters,
    score_objective_koota,
    score_all_objective_kootas,
    calculate_objective_match,
    HardFilterResult,
    ObjectiveScoreResult,
)


def create_profile(
    pid: str,
    name: str,
    age: int,
    religion: str,
    caste: str = "Brahmin",
    caste_preference: str = "no_preference",
) -> Profile:
    return Profile(
        id=pid,
        name=name,
        age=age,
        religion=religion,
        caste=caste,
        caste_preference=caste_preference,
    )


def test_hard_filter_clean_pass():
    """Profiles with equal religion, age gap <= 2, and flexible caste pass hard filters."""
    p1 = create_profile("p1", "Aarav", 28, "Hindu", "Brahmin", "no_preference")
    p2 = create_profile("p2", "Ananya", 27, "Hindu", "Brahmin", "no_preference")

    res = check_hard_filters(p1, p2, max_age_gap=2)
    assert res.passed is True
    assert res.reason is None


def test_hard_filter_age_gap_fail():
    """Profiles with age gap > 2 years fail hard filter."""
    p1 = create_profile("p1", "Aarav", 32, "Hindu")
    p2 = create_profile("p2", "Ananya", 28, "Hindu")  # gap = 4

    res = check_hard_filters(p1, p2, max_age_gap=2)
    assert res.passed is False
    assert "Age gap" in res.reason


def test_hard_filter_religion_mismatch_fail():
    """Profiles with different religions fail hard filter immediately."""
    p1 = create_profile("p1", "Aarav", 28, "Hindu")
    p2 = create_profile("p2", "Zainab", 27, "Muslim")

    res = check_hard_filters(p1, p2)
    assert res.passed is False
    assert "Religion mismatch" in res.reason


def test_hard_filter_caste_required_mismatch_fail():
    """If caste is required and castes differ, hard filter fails."""
    p1 = create_profile("p1", "Aarav", 28, "Hindu", caste="Brahmin", caste_preference="same_caste_required")
    p2 = create_profile("p2", "Pooja", 27, "Hindu", caste="Kshatriya", caste_preference="no_preference")

    res = check_hard_filters(p1, p2)
    assert res.passed is False
    assert "Caste requirement" in res.reason


def test_hard_filter_short_circuit_skips_scoring(monkeypatch):
    """When hard filter fails, weighted scoring must NEVER be called."""
    p1 = create_profile("p1", "Aarav", 35, "Hindu")
    p2 = create_profile("p2", "Ananya", 26, "Hindu")  # age gap 9 -> fail

    called_weighted_scoring = False

    def mock_score_all(*args, **kwargs):
        nonlocal called_weighted_scoring
        called_weighted_scoring = True
        return {}

    monkeypatch.setattr("app.scoring.objective.score_all_objective_kootas", mock_score_all)

    result = calculate_objective_match(p1, p2, p1_answers=[], p2_answers=[], kootas_metadata={})
    assert result.is_viable is False
    assert called_weighted_scoring is False, "Hard filter short circuit failed: weighted scorer was reached!"


def test_koota_18_in_law_deference_partial_credit():
    """Verify partial credit logic on Koota 18 (In-Law deference and interaction frequency)."""
    # Q1: Interaction frequency: "Daily" vs "Weekly" -> partial credit 0.70
    score_q1 = score_objective_koota(
        koota_id=18,
        q_idx=0,
        val1="Daily",
        val2="Weekly",
    )
    assert score_q1 == pytest.approx(0.70, 0.05)

    # Q2: Traditional deference: "Yes" vs "Flexible/Depends" -> partial credit 0.70
    score_q2 = score_objective_koota(
        koota_id=18,
        q_idx=1,
        val1="Yes",
        val2="Flexible/Depends",
    )
    assert score_q2 == pytest.approx(0.70, 0.05)

    # Opposite stance: "No" vs "Yes" -> minimal credit 0.10
    score_q2_opp = score_objective_koota(
        koota_id=18,
        q_idx=1,
        val1="No",
        val2="Yes",
    )
    assert score_q2_opp <= 0.20


def test_numeric_distance_scoring():
    """Verify 1-5 scale distance scoring."""
    # Koota 23 Q2 (Ambition centrality 1-5 scale): 4 vs 5 -> diff 1 / range 4 -> 0.75
    score_scaled = score_objective_koota(
        koota_id=23,
        q_idx=2,
        val1="4",
        val2="5",
    )
    assert score_scaled == pytest.approx(0.75, 0.01)

    # Identical values: 5 vs 5 -> 1.0
    score_exact = score_objective_koota(
        koota_id=23,
        q_idx=2,
        val1="5",
        val2="5",
    )
    assert score_exact == 1.0


def test_clean_full_objective_match():
    """Verify full objective match aggregation across answers."""
    p1 = create_profile("p1", "Aarav", 28, "Hindu")
    p2 = create_profile("p2", "Ananya", 27, "Hindu")

    # Perfectly matching answers for Koota 7 (Conflict Style) and Koota 18 (In-Laws)
    p1_answers = [
        Answer(profile_id="p1", koota_id=7, question_index=0, question_type="objective", raw_value="engage immediately"),
        Answer(profile_id="p1", koota_id=7, question_index=1, question_type="objective", raw_value="same-day"),
        Answer(profile_id="p1", koota_id=18, question_index=0, question_type="objective", raw_value="Weekly"),
        Answer(profile_id="p1", koota_id=18, question_index=1, question_type="objective", raw_value="Flexible/Depends"),
    ]
    p2_answers = [
        Answer(profile_id="p2", koota_id=7, question_index=0, question_type="objective", raw_value="engage immediately"),
        Answer(profile_id="p2", koota_id=7, question_index=1, question_type="objective", raw_value="same-day"),
        Answer(profile_id="p2", koota_id=18, question_index=0, question_type="objective", raw_value="Weekly"),
        Answer(profile_id="p2", koota_id=18, question_index=1, question_type="objective", raw_value="Flexible/Depends"),
    ]

    kootas_meta = {
        7: {"weight": 9, "name": "Conflict Style"},
        18: {"weight": 14, "name": "In-Law Relationship Expectations"},
    }

    result = calculate_objective_match(
        p1, p2, p1_answers=p1_answers, p2_answers=p2_answers, kootas_metadata=kootas_meta
    )
    assert result.is_viable is True
    assert result.hard_filter_reason is None
    assert result.overall_score == 1.0
    assert 7 in result.koota_scores
    assert 18 in result.koota_scores
    assert result.koota_scores[7] == 1.0
    assert result.koota_scores[18] == 1.0
