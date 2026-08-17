"""Test suite for Jaccard similarity computation on social following lists."""
import pytest
from app.matching.social_overlap import compute_overlap, normalize_usernames


def test_normalize_usernames():
    """Verify usernames are trimmed, lowercased, and stripped of @ prefixes."""
    raw = [" @Virat.Kohli ", "NATGEO", "hubermanlab", "  @hubermanlab  ", "", None]
    cleaned = normalize_usernames(raw)
    assert cleaned == {"virat.kohli", "natgeo", "hubermanlab"}


def test_social_overlap_full_match():
    """Identical following lists yield 1.0 overlap score."""
    list_a = ["natgeo", "hubermanlab", "virat.kohli"]
    list_b = ["VIRAT.KOHLI", "hubermanlab", "@natgeo"]

    res = compute_overlap(list_a, list_b, opted_in_a=True, opted_in_b=True)
    assert res["overlap_score"] == 1.0
    assert res["shared_count"] == 3


def test_social_overlap_zero_match():
    """Disjoint following lists yield 0.0 overlap score."""
    list_a = ["natgeo", "nasa"]
    list_b = ["virat.kohli", "rohit.sharma"]

    res = compute_overlap(list_a, list_b, opted_in_a=True, opted_in_b=True)
    assert res["overlap_score"] == 0.0
    assert res["shared_count"] == 0


def test_social_overlap_partial_hand_computed_ratio():
    """Partial overlap yields exact Jaccard ratio |Intersection| / |Union|."""
    # A = {a, b, c, d} (len 4)
    # B = {c, d, e, f, g} (len 5)
    # Intersection = {c, d} (len 2)
    # Union = {a, b, c, d, e, f, g} (len 7)
    # Jaccard = 2 / 7 = 0.285714... -> rounded to 0.2857
    list_a = ["alpha", "beta", "gamma", "delta"]
    list_b = ["gamma", "delta", "epsilon", "zeta", "eta"]

    res = compute_overlap(list_a, list_b, opted_in_a=True, opted_in_b=True)
    assert res["shared_count"] == 2
    assert res["overlap_score"] == 0.2857


def test_social_overlap_opt_in_false_short_circuits():
    """If either party has opted_in=False, overlap is 0.0 and count is 0."""
    list_a = ["natgeo", "hubermanlab"]
    list_b = ["natgeo", "hubermanlab"]

    # Party A opted out
    res_a_out = compute_overlap(list_a, list_b, opted_in_a=False, opted_in_b=True)
    assert res_a_out["overlap_score"] == 0.0
    assert res_a_out["shared_count"] == 0

    # Party B opted out
    res_b_out = compute_overlap(list_a, list_b, opted_in_a=True, opted_in_b=False)
    assert res_b_out["overlap_score"] == 0.0
    assert res_b_out["shared_count"] == 0

    # Both opted out
    res_both_out = compute_overlap(list_a, list_b, opted_in_a=False, opted_in_b=False)
    assert res_both_out["overlap_score"] == 0.0
    assert res_both_out["shared_count"] == 0


def test_social_overlap_empty_or_none_never_raises():
    """Empty or None lists return 0.0 safely without raising exceptions."""
    assert compute_overlap([], []) == {"overlap_score": 0.0, "shared_count": 0}
    assert compute_overlap(None, ["user1"]) == {"overlap_score": 0.0, "shared_count": 0}
    assert compute_overlap(["user1"], None) == {"overlap_score": 0.0, "shared_count": 0}
    assert compute_overlap(None, None) == {"overlap_score": 0.0, "shared_count": 0}
