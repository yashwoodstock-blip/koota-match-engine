"""Tier classification and templated alignment / friction generator for Koota Match Engine.

Zero raw answer text is exposed. Only templated insights keyed by koota_id are generated.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from app.scoring.aggregate import AggregateMatchResult


# Curated, India-focused domain templates keyed by koota_id
ALIGNMENT_TEMPLATES: Dict[int, str] = {
    1: "Shared appreciation for formative upbringing and family background perspectives.",
    2: "Complementary daily rhythms and harmonious weekend lifestyle pacing.",
    3: "Compatible stress-coping strategies and emotional support expectations.",
    4: "Mutual encouragement of individual dreams, personal passions, and personal autonomy.",
    5: "Synchronized appreciation styles and love languages.",
    6: "Strong mutual respect language and admiration values.",
    7: "Compatible conflict resolution rhythms and cooling-off pacing.",
    8: "Aligned feedback handling styles and comfort with constructive communication.",
    9: "High emotional responsiveness and mutual attentiveness to bids for connection.",
    10: "Effective post-disagreement repair mechanisms and mutual reassurance.",
    11: "Strong baseline trust readiness and transparency on personal history.",
    12: "Unified commitment philosophy and resilience toward long-term marital hurdles.",
    13: "Complementary individual temperaments and social pressure processing.",
    14: "Compatible emotional regulation windows when processing distress.",
    15: "Harmonious personal space boundaries and respect for individual independence.",
    16: "Comfort with emotional vulnerability and safe disclosure.",
    17: "Balanced perspectives on family of origin hierarchy and decision-making norms.",
    18: "High resonance on in-law engagement rhythm and balanced filial boundaries.",
    19: "Agreed-upon healthy boundaries regarding parental involvement in marital matters.",
    20: "Clarity and mutual agreement on extended family obligations and kin support.",
    21: "Unified living arrangement preference and spatial boundary vision.",
    22: "Shared egalitarian vision for domestic labor, finances, and household responsibilities.",
    23: "Mutual dedication to bilateral career continuity, ambitions, and relocation adaptability.",
    24: "Reciprocal and cooperative strategy for multi-generational elder care.",
    25: "Harmonious financial mindset balancing future wealth accumulation with lifestyle.",
    26: "Compatible approach to bank account structure and financial transparency.",
    27: "Mutual openness regarding marriage-onset expectations and financial customs.",
    28: "Aligned consultation thresholds for major discretionary purchases and debt comfort.",
    29: "Comfortable pre-marital dialogue on intimacy expectations and physical affection.",
    30: "Shared expression of small daily gestures and affection languages.",
    31: "Aligned intentions regarding children, family expansion, and parenthood timing.",
    32: "Harmonious parenting philosophy, discipline approach, and linguistic heritage.",
    33: "Shared educational values and broad openness to diverse career paths for children.",
    34: "Clear and mutually comfortable social and opposite-sex friendship boundaries.",
    35: "Harmonious social circle pace and balance of independent friendships.",
    36: "Compatible dietary choices, health habits, and substance boundaries.",
    37: "Synchronized spiritual practice intensity and ritual participation expectations.",
    38: "Deep philosophical resonance on meaning-making and existential outlook.",
    39: "Shared enthusiasm for cultural festivals, rituals, and family traditions.",
    40: "Cohesive 10-year life vision spanning geography, career, and lifestyle shape.",
    41: "Deep philosophical consensus on the transcendent purpose and companionship of marriage.",
    42: "Fully aligned community and social boundary preferences.",
}

FRICTION_TEMPLATES: Dict[int, str] = {
    1: "Divergent upbringing backgrounds that may require intentional cultural bridging.",
    2: "Different daily energy cycles (morning vs night) or weekend pace preferences.",
    3: "Contrasting ways of handling stress and asking for help during hardship.",
    4: "Different long-term personal aspirations outside the domestic sphere.",
    5: "Mismatched expectations around the expression and frequency of verbal appreciation.",
    6: "Differing standards and vocabularies of verbal respect and admiration.",
    7: "Mismatched conflict resolution styles (immediate confrontation vs need for space).",
    8: "Contrasting preferences for direct vs indirect feedback in front of family.",
    9: "Different expectations regarding daily check-in frequency and emotional bids.",
    10: "Varying cooling-off timelines and preferred repair gestures after arguments.",
    11: "Different levels of initial trust readiness or comfort discussing past experiences.",
    12: "Contrasting viewpoints on marital permanence and openness to counseling.",
    13: "Differing emotional reactivity under elder criticism or social gatherings.",
    14: "Asymmetric time needed to talk through upset feelings.",
    15: "Different expectations for alone time and independent solo travel.",
    16: "Varying comfort with vulnerability and emotional disclosure.",
    17: "Contrasting familial models of hierarchy versus egalitarian decision-making.",
    18: "Differing expectations regarding in-law involvement and traditional elder deference.",
    19: "Disagreement on when and how much to involve parents in marital conflicts.",
    20: "Differing expectations around financial support for extended kin and siblings.",
    21: "Contrasting preferences regarding joint family living vs independent nuclear household.",
    22: "Divergence on domestic chore distribution and day-to-day household budget management.",
    23: "Potential conflict between career ambition pacing and extended family expectations.",
    24: "Unresolved allocation of caregiving obligations and career priority for aging parents.",
    25: "Contrasting saver vs spender orientations and debt comfort levels.",
    26: "Differing preferences for joint vs strictly separate financial accounts.",
    27: "Unspoken family expectations surrounding wedding costs and financial transparency.",
    28: "Discrepancy in the monetary threshold for consulting before making major purchases.",
    29: "Different comfort levels discussing physical affection and intimate health topics.",
    30: "Mismatched expressions of daily non-intimate physical and verbal affection.",
    31: "Misalignment on family expansion timeline or openness to alternative conception paths.",
    32: "Contrasting parenting discipline styles (strict vs permissive/balanced).",
    33: "Differing pressure thresholds on academic achievement vs unconventional careers.",
    34: "Different comfort levels regarding partner's pre-existing opposite-sex friendships.",
    35: "Disparity in preferred frequency of external socializing vs quiet home time.",
    36: "Meaningfully different dietary lifestyles or comfort with alcohol/non-veg at home.",
    37: "Differing intensity of daily spiritual practice and mandatory ritual attendance.",
    38: "Contrasting philosophical coping frameworks when navigating existential hardship.",
    39: "Disagreement over how cultural and religious festivals are observed post-marriage.",
    40: "Divergent geographical willingness to relocate or live abroad.",
    41: "Contrasting foundational definitions of what marriage fundamentally accomplishes.",
    42: "Unmatched caste or community preference constraints.",
}


@dataclass
class TierEvaluationResult:
    tier: str  # "not viable" | "compatible with flagged friction points" | "strong match"
    alignment_points: List[str]
    friction_points: List[str]
    capped_by: Optional[Dict[str, Any]] = None
    ceiling_applied: Optional[float] = None
    compensatory_score: Optional[float] = None
    risk_adjusted_score: Optional[float] = None
    score_uncertainty: Optional[float] = None
    score_interval: Optional[List[float]] = None
    confidence: Optional[str] = None
    evidence_coverage_pct: Optional[float] = None
    critical_contradictions: int = 0
    high_impact_uncertainty: List[str] = field(default_factory=list)


def classify_tier(
    aggregate: AggregateMatchResult,
    kootas_metadata: Dict[int, Dict[str, Any]],
    high_alignment_threshold: float = 0.78,
    friction_threshold: float = 0.55,
) -> TierEvaluationResult:
    """Classify into one of 3 tiers and generate templated alignment & friction points."""
    # 1. Non-viable check
    if not aggregate.is_viable or aggregate.overall_score is None:
        return TierEvaluationResult(
            tier="not viable",
            alignment_points=[],
            friction_points=[aggregate.hard_filter_reason or "Failed essential compatibility requirements."],
            capped_by=aggregate.capped_by,
            ceiling_applied=aggregate.ceiling_applied,
            compensatory_score=aggregate.compensatory_score,
            risk_adjusted_score=aggregate.risk_adjusted_score,
            score_uncertainty=aggregate.score_uncertainty,
            score_interval=aggregate.score_interval,
            confidence=aggregate.confidence or "Low",
            evidence_coverage_pct=aggregate.evidence_coverage_pct or 0.0,
            critical_contradictions=aggregate.critical_contradictions,
            high_impact_uncertainty=aggregate.high_impact_uncertainty,
        )

    # Risk-adjusted score is used for tier decisions and ranking
    effective_score = aggregate.risk_adjusted_score if aggregate.risk_adjusted_score is not None else aggregate.overall_score
    koota_scores = aggregate.koota_scores
    flags = aggregate.disagreement_flags

    # Gather Alignment Points (top performing kootas)
    alignments: List[str] = []
    sorted_by_alignment = sorted(
        koota_scores.items(),
        key=lambda item: kootas_metadata.get(item[0], {}).get("weight", 1) * item[1],
        reverse=True,
    )

    for k_id, k_score in sorted_by_alignment:
        if k_score >= high_alignment_threshold:
            template = ALIGNMENT_TEMPLATES.get(k_id)
            if template and template not in alignments:
                alignments.append(template)

    # Gather Friction Points (low scores, disagreement flags, and non-compensatory ceiling limitations)
    frictions: List[str] = []

    # Add friction from non-compensatory ceiling caps first
    if aggregate.capped_by:
        cap_k_id = aggregate.capped_by.get("koota_id")
        cap_name = aggregate.capped_by.get("koota_name", "Core Dimension")
        cap_val = aggregate.capped_by.get("ceiling", 1.0)
        template = FRICTION_TEMPLATES.get(cap_k_id, f"Significant boundary tension in {cap_name}")
        cap_str = f"{template} [Non-Compensatory Ceiling: {cap_name} capped at {int(cap_val * 100)}%]"
        if cap_str not in frictions:
            frictions.append(cap_str)

    # Add friction from contradiction gates
    for gate in aggregate.contradiction_gates:
        template = FRICTION_TEMPLATES.get(gate["koota_id"], f"Critical conflict in {gate['koota_name']}")
        gate_str = f"{template} [Contradiction Override: {gate['severity'].upper()}]"
        if gate_str not in frictions:
            frictions.append(gate_str)

    # Add friction from explicit disagreement flags
    for flag in flags:
        k_id = flag["koota_id"]
        template = FRICTION_TEMPLATES.get(k_id)
        if template and template not in frictions:
            frictions.append(f"{template} [Divergence Flagged]")

    # Add friction from low scoring kootas
    sorted_by_friction = sorted(
        koota_scores.items(),
        key=lambda item: item[1],
    )
    for k_id, k_score in sorted_by_friction:
        if k_score <= friction_threshold:
            template = FRICTION_TEMPLATES.get(k_id)
            if template and template not in frictions:
                frictions.append(template)

    # Determine Tier with Gated Overrides based on Risk-Adjusted Score
    has_high_disagreements = any(f.get("severity") == "high" for f in flags)
    has_critical_koota_friction = any(
        k_id in [18, 22, 23, 41] and koota_scores.get(k_id, 1.0) < 0.60
        for k_id in koota_scores
    )

    if effective_score < 0.50:
        tier = "not viable"
    elif effective_score >= 0.75 and not has_high_disagreements and not has_critical_koota_friction:
        tier = "strong match"
    else:
        tier = "compatible with flagged friction points"

    # Enforce Gated Math Tier Ceilings
    if aggregate.tier_ceiling == "not viable":
        tier = "not viable"
    elif aggregate.tier_ceiling == "compatible with flagged friction points" and tier == "strong match":
        tier = "compatible with flagged friction points"

    return TierEvaluationResult(
        tier=tier,
        alignment_points=alignments[:5],  # Top 5 most prominent alignments
        friction_points=frictions[:5],    # Top 5 most prominent friction areas
        capped_by=aggregate.capped_by,
        ceiling_applied=aggregate.ceiling_applied,
        compensatory_score=aggregate.compensatory_score,
        risk_adjusted_score=aggregate.risk_adjusted_score,
        score_uncertainty=aggregate.score_uncertainty,
        score_interval=aggregate.score_interval,
        confidence=aggregate.confidence,
        evidence_coverage_pct=aggregate.evidence_coverage_pct,
        critical_contradictions=aggregate.critical_contradictions,
        high_impact_uncertainty=aggregate.high_impact_uncertainty,
    )
