"""Objective scoring engine and hard-filter verification for Koota Match Engine."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
from app.models import Profile, Answer


@dataclass
class HardFilterResult:
    passed: bool
    reason: Optional[str] = None


@dataclass
class ObjectiveScoreResult:
    is_viable: bool
    hard_filter_reason: Optional[str] = None
    overall_score: Optional[float] = None
    koota_scores: Dict[int, float] = field(default_factory=dict)


# Partial credit lookup table for categorical near-misses
PARTIAL_CREDIT_TABLE: Dict[Tuple[int, int], Dict[frozenset, float]] = {
    # Koota 1: Formative Experiences
    (1, 0): {
        frozenset(["joint", "nuclear"]): 0.50,
        frozenset(["single-parent", "nuclear"]): 0.70,
        frozenset(["urban", "semi-urban"]): 0.80,
        frozenset(["semi-urban", "rural"]): 0.70,
        frozenset(["urban", "rural"]): 0.40,
    },
    (1, 1): {
        frozenset(["1 sibling, elder", "1 sibling, younger"]): 0.85,
        frozenset(["1 sibling", "2 siblings"]): 0.80,
        frozenset(["only child", "1 sibling"]): 0.70,
    },
    # Koota 2: Daily Rhythm
    (2, 0): {
        frozenset(["morning", "night"]): 0.20,
        frozenset(["morning person", "night person"]): 0.20,
        frozenset(["structured", "spontaneous"]): 0.40,
    },
    # Koota 3: Fears & Stresses
    (3, 1): {
        frozenset(["very comfortable", "somewhat"]): 0.75,
        frozenset(["somewhat", "not at all"]): 0.50,
        frozenset(["very comfortable", "not at all"]): 0.20,
    },
    # Koota 5: Expression of Appreciation
    (5, 1): {
        frozenset(["daily", "weekly"]): 0.75,
        frozenset(["weekly", "occasionally"]): 0.75,
        frozenset(["occasionally", "rarely needed"]): 0.60,
        frozenset(["daily", "rarely needed"]): 0.20,
    },
    # Koota 7: Conflict Style
    (7, 0): {
        frozenset(["engage immediately", "need space first"]): 0.30,
        frozenset(["engage immediately", "escalate then resolve"]): 0.50,
        frozenset(["engage immediately", "avoid"]): 0.20,
        frozenset(["need space first", "avoid"]): 0.50,
    },
    (7, 1): {
        frozenset(["same-day", "after a cooling-off period"]): 0.50,
    },
    # Koota 8: Feedback Handling
    (8, 0): {
        frozenset(["direct/blunt", "gentle/indirect"]): 0.30,
        frozenset(["direct/blunt", "private only"]): 0.60,
        frozenset(["gentle/indirect", "private only"]): 0.80,
        frozenset(["private only", "written"]): 0.75,
    },
    (8, 1): {
        frozenset(["comfortable", "uncomfortable"]): 0.20,
        frozenset(["comfortable", "depends"]): 0.70,
        frozenset(["uncomfortable", "depends"]): 0.70,
    },
    # Koota 11: Trust Baseline
    (11, 0): {
        frozenset(["high", "moderate"]): 0.80,
        frozenset(["moderate", "guarded"]): 0.60,
        frozenset(["high", "guarded"]): 0.40,
    },
    (11, 1): {
        frozenset(["yes", "prefer not to"]): 0.50,
        frozenset(["no", "prefer not to"]): 0.70,
        frozenset(["yes", "no"]): 0.60,
    },
    # Koota 12: Commitment Philosophy
    (12, 0): {
        frozenset(["only in extreme circumstances", "should never be considered"]): 0.70,
        frozenset(["only in extreme circumstances", "a reasonable option if unhappy"]): 0.50,
        frozenset(["should never be considered", "a reasonable option if unhappy"]): 0.10,
    },
    (12, 1): {
        frozenset(["open to it", "only as last resort"]): 0.75,
        frozenset(["only as last resort", "not for us"]): 0.60,
        frozenset(["open to it", "not for us"]): 0.20,
    },
    # Koota 13: Temperament & Stress Processing
    (13, 0): {
        frozenset(["calm/steady", "expressive/emotional"]): 0.60,
        frozenset(["calm/steady", "reserved/private"]): 0.80,
        frozenset(["expressive/emotional", "reserved/private"]): 0.40,
    },
    (13, 1): {
        frozenset(["withdraw", "push back"]): 0.30,
        frozenset(["deflect with humor", "stay composed"]): 0.75,
        frozenset(["withdraw", "deflect with humor"]): 0.60,
        frozenset(["push back", "stay composed"]): 0.50,
    },
    # Koota 14: Emotional Regulation
    (14, 0): {
        frozenset(["being left alone", "being comforted"]): 0.40,
    },
    # Koota 15: Personal Boundaries & Autonomy
    (15, 0): {
        frozenset(["high", "moderate"]): 0.80,
        frozenset(["moderate", "low"]): 0.80,
        frozenset(["high", "low"]): 0.30,
    },
    (15, 1): {
        frozenset(["comfortable", "occasional"]): 0.80,
        frozenset(["occasional", "rare"]): 0.70,
        frozenset(["rare", "not comfortable"]): 0.70,
        frozenset(["comfortable", "not comfortable"]): 0.10,
    },
    # Koota 17: Family of Origin Dynamics
    (17, 0): {
        frozenset(["hierarchical", "egalitarian"]): 0.50,
    },
    # Koota 18: In-Law Relationship Expectations (India-Critical w14)
    (18, 0): {
        frozenset(["daily", "weekly"]): 0.70,
        frozenset(["weekly", "occasional"]): 0.75,
        frozenset(["daily", "occasional"]): 0.45,
        frozenset(["occasional", "minimal"]): 0.70,
        frozenset(["daily", "minimal"]): 0.10,
    },
    (18, 1): {
        frozenset(["yes", "flexible/depends"]): 0.70,
        frozenset(["no", "flexible/depends"]): 0.70,
        frozenset(["yes", "no"]): 0.10,
    },
    # Koota 19: Parental Involvement in Major Decisions
    (19, 0): {
        frozenset(["never", "only if serious"]): 0.80,
        frozenset(["only if serious", "openly, as a norm"]): 0.50,
        frozenset(["never", "openly, as a norm"]): 0.10,
    },
    # Koota 20: Sibling & Extended Kin Obligations
    (20, 0): {
        frozenset(["yes, ongoing", "possible future"]): 0.75,
        frozenset(["possible future", "none expected"]): 0.75,
        frozenset(["yes, ongoing", "none expected"]): 0.25,
    },
    (20, 1): {
        frozenset(["yes", "no"]): 0.30,
        frozenset(["yes", "depends"]): 0.75,
    },
    # Koota 21: Living Arrangement Preference (w11)
    (21, 0): {
        frozenset(["joint family", "nuclear same city"]): 0.50,
        frozenset(["nuclear same city", "nuclear different city"]): 0.60,
        frozenset(["flexible", "joint family"]): 0.85,
        frozenset(["flexible", "nuclear same city"]): 0.85,
        frozenset(["flexible", "nuclear different city"]): 0.85,
        frozenset(["joint family", "nuclear different city"]): 0.00,
    },
    (21, 1): {
        frozenset(["yours", "partner's"]): 0.40,
        frozenset(["either", "neither"]): 0.50,
        frozenset(["either", "yours"]): 0.85,
        frozenset(["either", "partner's"]): 0.85,
    },
    # Koota 22: Gender Roles & Division of Labor (w12)
    (22, 0): {
        frozenset(["equal/shared", "traditional"]): 0.20,
    },
    (22, 1): {
        frozenset(["joint", "self"]): 0.70,
        frozenset(["joint", "partner"]): 0.70,
        frozenset(["self", "partner"]): 0.40,
    },
    # Koota 23: Post-Marriage Career Continuity (w13)
    (23, 0): {
        frozenset(["continue with full support", "continue but will need to negotiate"]): 0.70,
        frozenset(["continue but will need to negotiate", "open, decide together"]): 0.80,
        frozenset(["continue with full support", "open, decide together"]): 0.85,
        frozenset(["continue with full support", "expected to stop"]): 0.00,
        frozenset(["open, decide together", "expected to stop"]): 0.30,
    },
    (23, 1): {
        frozenset(["yes", "no"]): 0.30,
        frozenset(["yes", "depends"]): 0.80,
        frozenset(["no", "depends"]): 0.60,
    },
    # Koota 24: Elder Care Responsibility (w9)
    (24, 0): {
        frozenset(["both", "will hire help"]): 0.75,
        frozenset(["both", "yours"]): 0.65,
        frozenset(["both", "partner's"]): 0.65,
        frozenset(["yours", "partner's"]): 0.80,  # complementary
        frozenset(["both", "undecided"]): 0.70,
        frozenset(["yours", "yours"]): 0.30,      # conflicting
    },
    # Koota 26: Financial Structure & Control
    (26, 0): {
        frozenset(["joint/shared control", "hybrid"]): 0.80,
        frozenset(["separate", "hybrid"]): 0.80,
        frozenset(["joint/shared control", "separate"]): 0.30,
        frozenset(["joint/shared control", "joint/one manages"]): 0.60,
    },
    # Koota 27: Wedding Financial Transparency
    (27, 0): {
        frozenset(["yes, will disclose", "prefer to discuss privately"]): 0.85,
        frozenset(["yes, will disclose", "no"]): 0.40,
        frozenset(["prefer to discuss privately", "no"]): 0.50,
    },
    # Koota 28: Major Purchase Threshold
    (28, 0): {
        frozenset(["under ₹10k", "₹10k–50k"]): 0.75,
        frozenset(["₹10k–50k", "₹50k–1l"]): 0.75,
        frozenset(["₹50k–1l", "above ₹1l"]): 0.75,
        frozenset(["under ₹10k", "above ₹1l"]): 0.20,
    },
    # Koota 31: Desire for Children (w10)
    (31, 0): {
        frozenset(["yes", "undecided"]): 0.60,
        frozenset(["no", "undecided"]): 0.60,
        frozenset(["yes", "open to partner's strong preference"]): 0.90,
        frozenset(["no", "open to partner's strong preference"]): 0.90,
        frozenset(["yes", "no"]): 0.00,
    },
    # Koota 32: Parenting Philosophy
    (32, 0): {
        frozenset(["strict", "balanced"]): 0.70,
        frozenset(["balanced", "permissive"]): 0.70,
        frozenset(["strict", "permissive"]): 0.20,
        frozenset(["balanced", "undecided"]): 0.80,
    },
    # Koota 34: Friendship Boundaries
    (34, 0): {
        frozenset(["fully comfortable", "comfortable with transparency"]): 0.80,
        frozenset(["comfortable with transparency", "prefer minimal"]): 0.60,
        frozenset(["prefer minimal", "not comfortable"]): 0.70,
        frozenset(["fully comfortable", "not comfortable"]): 0.10,
    },
    # Koota 35: Social & Community Pace
    (35, 0): {
        frozenset(["frequent socializing", "occasional"]): 0.75,
        frozenset(["occasional", "minimal, prefer close circle"]): 0.75,
        frozenset(["frequent socializing", "minimal, prefer close circle"]): 0.30,
    },
    # Koota 36: Lifestyle Habits & Health
    (36, 0): {
        frozenset(["vegetarian", "non-vegetarian"]): 0.50,
        frozenset(["vegetarian", "eggetarian"]): 0.80,
    },
    (36, 1): {
        frozenset(["yes", "no"]): 0.20,
        frozenset(["comfortable", "not comfortable"]): 0.20,
    },
    # Koota 37: Spiritual Practice
    (37, 1): {
        frozenset(["yes", "no"]): 0.30,
        frozenset(["yes", "flexible"]): 0.80,
    },
    # Koota 39: Shared Rituals
    (39, 0): {
        frozenset(["your family's style", "blended"]): 0.80,
        frozenset(["partner's", "blended"]): 0.80,
        frozenset(["your family's style", "partner's"]): 0.40,
    },
    # Koota 40: Long-Term Life Vision
    (40, 0): {
        frozenset(["yes", "no"]): 0.30,
        frozenset(["yes", "open"]): 0.90,
    },
    # Koota 42: Caste Preference
    (42, 0): {
        frozenset(["no preference", "same caste preferred"]): 0.80,
        frozenset(["same caste preferred", "same caste required"]): 0.70,
        frozenset(["no preference", "same caste required"]): 0.50,
    },
}


def check_hard_filters(
    p1: Profile,
    p2: Profile,
    max_age_gap: int = 2,
) -> HardFilterResult:
    """Short-circuit hard filters (Age gap, Religion, Caste requirement).
    
    Returns HardFilterResult(passed=False, reason=...) immediately on failure.
    """
    # 1. Age Gap Check (default <= 2 years)
    if abs(p1.age - p2.age) > max_age_gap:
        return HardFilterResult(
            passed=False,
            reason=f"Age gap ({abs(p1.age - p2.age)} years) exceeds maximum threshold ({max_age_gap} years).",
        )

    # 2. Religion Exact Match Check
    r1 = (p1.religion or "").strip().lower()
    r2 = (p2.religion or "").strip().lower()
    if r1 != r2:
        return HardFilterResult(
            passed=False,
            reason=f"Religion mismatch: Profile A ({p1.religion}) vs Profile B ({p2.religion}).",
        )

    # 3. Koota 42: Caste & Community Hard Restriction Check
    c1 = (p1.caste or "").strip().lower()
    c2 = (p2.caste or "").strip().lower()
    pref1 = (p1.caste_preference or "").strip().lower()
    pref2 = (p2.caste_preference or "").strip().lower()

    if pref1 == "same_caste_required" and c1 != c2:
        return HardFilterResult(
            passed=False,
            reason=f"Caste requirement failed: Profile A requires same caste '{p1.caste}', but Profile B is '{p2.caste}'.",
        )
    if pref2 == "same_caste_required" and c1 != c2:
        return HardFilterResult(
            passed=False,
            reason=f"Caste requirement failed: Profile B requires same caste '{p2.caste}', but Profile A is '{p1.caste}'.",
        )

    return HardFilterResult(passed=True, reason=None)


def score_objective_koota(
    koota_id: int,
    q_idx: int,
    val1: str,
    val2: str,
) -> float:
    """Compute score for a single objective question pair in [0.0, 1.0]."""
    v1 = str(val1).strip().lower()
    v2 = str(val2).strip().lower()

    if v1 == v2:
        return 1.0

    # 1. Numeric / Scaled questions (e.g. 1-5 scale)
    try:
        n1 = float(v1)
        n2 = float(v2)
        # Assuming 1 to 5 scale if both within 1..5
        if 1.0 <= n1 <= 5.0 and 1.0 <= n2 <= 5.0:
            diff = abs(n1 - n2)
            return max(0.0, 1.0 - (diff / 4.0))
    except ValueError:
        pass

    # 2. Check Partial Credit Table
    lookup_key = (koota_id, q_idx)
    pair_set = frozenset([v1, v2])

    if lookup_key in PARTIAL_CREDIT_TABLE:
        table = PARTIAL_CREDIT_TABLE[lookup_key]
        if pair_set in table:
            return table[pair_set]
        # Check substring matches in table
        for key_set, score in table.items():
            klist = list(key_set)
            if len(klist) == 2:
                if (klist[0] in v1 and klist[1] in v2) or (klist[1] in v1 and klist[0] in v2):
                    return score

    # 3. Generic categorical fallback
    return 0.20


def score_all_objective_kootas(
    p1_answers: List[Answer],
    p2_answers: List[Answer],
    kootas_metadata: Dict[int, Dict[str, Any]],
) -> Tuple[Dict[int, float], float]:
    """Score all objective answers across matching Kootas and compute weighted total."""
    # Organize answers by (koota_id, question_index)
    a1_map: Dict[Tuple[int, int], Answer] = {
        (a.koota_id, a.question_index): a
        for a in p1_answers
        if a.question_type == "objective"
    }
    a2_map: Dict[Tuple[int, int], Answer] = {
        (a.koota_id, a.question_index): a
        for a in p2_answers
        if a.question_type == "objective"
    }

    koota_q_scores: Dict[int, List[float]] = {}

    for (k_id, q_idx), ans1 in a1_map.items():
        if (k_id, q_idx) in a2_map:
            ans2 = a2_map[(k_id, q_idx)]
            q_score = score_objective_koota(k_id, q_idx, ans1.raw_value, ans2.raw_value)
            koota_q_scores.setdefault(k_id, []).append(q_score)

    koota_scores: Dict[int, float] = {}
    weighted_sum = 0.0
    total_weight = 0.0

    for k_id, scores in koota_q_scores.items():
        mean_score = sum(scores) / len(scores)
        koota_scores[k_id] = round(mean_score, 4)

        weight = kootas_metadata.get(k_id, {}).get("weight", 1)
        weighted_sum += mean_score * weight
        total_weight += weight

    overall_objective_score = (
        round(weighted_sum / total_weight, 4) if total_weight > 0 else 0.0
    )

    return koota_scores, overall_objective_score


def calculate_objective_match(
    p1: Profile,
    p2: Profile,
    p1_answers: List[Answer],
    p2_answers: List[Answer],
    kootas_metadata: Dict[int, Dict[str, Any]],
    max_age_gap: int = 2,
) -> ObjectiveScoreResult:
    """Execute hard-filter short-circuit first; if passed, compute weighted objective scores."""
    # 1. Hard Filter Short-Circuit
    filter_result = check_hard_filters(p1, p2, max_age_gap=max_age_gap)
    if not filter_result.passed:
        return ObjectiveScoreResult(
            is_viable=False,
            hard_filter_reason=filter_result.reason,
            overall_score=None,
            koota_scores={},
        )

    # 2. Weighted Objective Scoring (only reached if hard filters passed)
    koota_scores, overall_score = score_all_objective_kootas(
        p1_answers, p2_answers, kootas_metadata
    )

    return ObjectiveScoreResult(
        is_viable=True,
        hard_filter_reason=None,
        overall_score=overall_score,
        koota_scores=koota_scores,
    )
