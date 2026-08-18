"""Score aggregation engine separating Compensatory and Non-Compensatory Continuous Ceiling scoring."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from app.scoring.llm_judge import LLMJudgeResult, TOP_WEIGHTED_JUDGE_KOOTAS


@dataclass
class ContradictionGate:
    koota_id: int
    koota_name: str
    pillar: str
    severity: str  # "critical" | "high"
    reason: str
    penalty_multiplier: float


@dataclass
class AggregateMatchResult:
    is_viable: bool
    hard_filter_reason: Optional[str] = None
    overall_score: Optional[float] = None
    raw_composite_score: Optional[float] = None
    compensatory_score: Optional[float] = None
    ceiling_applied: Optional[float] = None
    capped_by: Optional[Dict[str, Any]] = None
    objective_score: Optional[float] = None
    semantic_score: Optional[float] = None
    tier_ceiling: Optional[str] = None  # None | "compatible with flagged friction points" | "not viable"
    risk_adjusted_score: Optional[float] = None
    score_uncertainty: Optional[float] = None
    score_interval: Optional[List[float]] = None
    confidence: Optional[str] = None  # "High" | "Moderate" | "Low"
    evidence_coverage_pct: Optional[float] = None
    critical_contradictions: int = 0
    high_impact_uncertainty: List[str] = field(default_factory=list)
    koota_scores: Dict[int, float] = field(default_factory=dict)
    koota_uncertainties: Dict[int, float] = field(default_factory=dict)
    disagreement_flags: List[Dict[str, Any]] = field(default_factory=list)
    contradiction_gates: List[Dict[str, Any]] = field(default_factory=list)
    llm_judge_insights: Dict[int, Dict[str, Any]] = field(default_factory=dict)


def calculate_koota_ceiling(k_score: float, k_meta: Dict[str, Any]) -> float:
    """Compute continuous weakest-link ceiling for a non-compensatory Koota.
    
    Formula:
      ceiling_n(S_n) = 1.0 if S_n >= tau_high
                       floor_n + (1 - floor_n) * (S_n - tau_low) / (tau_high - tau_low)
                         if tau_low <= S_n < tau_high
                       floor_n if S_n < tau_low
      
      Degenerate cliff case (tau_low == tau_high):
        ceiling_n(S_n) = 1.0 if S_n >= tau_high else floor_n
    """
    agg_type = k_meta.get("aggregation_type", "compensatory")
    if agg_type != "non_compensatory":
        return 1.0

    tau_low = k_meta.get("tau_low")
    tau_high = k_meta.get("tau_high")
    floor = k_meta.get("floor", 0.30)

    if tau_low is None or tau_high is None or floor is None:
        return 1.0

    # Degenerate hard-cliff case
    if tau_low >= tau_high:
        return 1.0 if k_score >= tau_high else float(floor)

    if k_score >= tau_high:
        return 1.0
    elif k_score < tau_low:
        return float(floor)
    else:
        # Continuous linear interpolation between floor and 1.0
        normalized = (k_score - tau_low) / (tau_high - tau_low)
        return float(floor + (1.0 - floor) * normalized)


def calculate_koota_uncertainty(
    k_id: int,
    k_meta: Dict[str, Any],
    is_answered: bool,
    has_objective: bool,
    has_semantic: bool,
    llm_judge_result: Optional[LLMJudgeResult] = None,
    divergence: Optional[float] = None,
    ann_margin: Optional[float] = None,
) -> float:
    """Derive sigma_k uncertainty for a single Koota from real pipeline signals."""
    if not is_answered:
        return 0.35  # Near-total uncertainty for skipped/unanswered Kootas

    # 1. Answer modality baseline uncertainty
    if has_objective and not has_semantic:
        sigma_base = 0.04  # Deterministic discrete multiple-choice
    elif has_objective and has_semantic:
        sigma_base = 0.08  # Blended objective + subjective
    else:
        sigma_base = 0.12  # Purely subjective narrative free-text

    # 2. Objective-Subjective Divergence signal
    sigma_div = 0.0
    if divergence is not None and divergence >= 0.25:
        sigma_div = min(0.15, divergence * 0.30)

    # 3. LLM Judge confidence / disagreement signal
    sigma_llm = 0.0
    if llm_judge_result is not None:
        judge_conf = getattr(llm_judge_result, "confidence", 0.85)
        sigma_llm = 0.15 * max(0.0, 1.0 - judge_conf)

    # 4. Stage 2 ANN cosine cutoff margin signal
    sigma_ann = 0.0
    if ann_margin is not None:
        sigma_ann = 0.05 * max(0.0, 1.0 - ann_margin)

    # Combined quadrature uncertainty
    total_var = (sigma_base ** 2) + (sigma_div ** 2) + (sigma_llm ** 2) + (sigma_ann ** 2)
    return round(max(0.01, min(0.40, total_var ** 0.5)), 4)


def detect_disagreement_flags(
    objective_scores: Dict[int, float],
    semantic_scores: Dict[int, float],
    kootas_metadata: Dict[int, Dict[str, Any]],
    threshold: float = 0.35,
) -> List[Dict[str, Any]]:
    """Detect sharp divergence between objective and subjective scores on the same Koota.
    
    CRITICAL RULE: Disagreements are stored and surfaced, NEVER averaged away.
    """
    flags: List[Dict[str, Any]] = []

    for k_id, obj_score in objective_scores.items():
        if k_id in semantic_scores:
            subj_score = semantic_scores[k_id]
            divergence = round(abs(obj_score - subj_score), 4)

            if divergence >= threshold:
                k_meta = kootas_metadata.get(k_id, {})
                k_name = k_meta.get("name", f"Koota {k_id}")
                pillar = k_meta.get("pillar", "Unknown Pillar")

                if obj_score > subj_score:
                    note = (
                        f"Objective multiple-choice answers indicate alignment ({obj_score:.2f}), "
                        f"but qualitative responses show substantial underlying divergence ({subj_score:.2f})."
                    )
                else:
                    note = (
                        f"Qualitative narrative reflections show strong ideological resonance ({subj_score:.2f}), "
                        f"yet objective daily choices indicate practical misalignment ({obj_score:.2f})."
                    )

                flags.append({
                    "koota_id": k_id,
                    "koota_name": k_name,
                    "pillar": pillar,
                    "objective_score": round(obj_score, 4),
                    "subjective_score": round(subj_score, 4),
                    "divergence": divergence,
                    "delta": divergence,
                    "severity": "high" if divergence >= 0.50 else "moderate",
                    "note": note,
                })

    return flags


def detect_contradiction_gates(
    kootas_metadata: Dict[int, Dict[str, Any]],
    llm_judge_results: Optional[Dict[int, LLMJudgeResult]] = None,
    disagreement_flags: Optional[List[Dict[str, Any]]] = None,
    koota_scores: Optional[Dict[int, float]] = None,
) -> Tuple[List[Dict[str, Any]], Optional[str], float]:
    """Evaluate qualitative contradiction gates and tier ceilings."""
    gates: List[Dict[str, Any]] = []
    penalty_factor = 1.0
    tier_ceiling = None

    # 1. Check LLM Judge Contradictions
    if llm_judge_results:
        for k_id, judge_res in llm_judge_results.items():
            if judge_res.contradiction:
                k_meta = kootas_metadata.get(k_id, {})
                k_name = k_meta.get("name", f"Koota {k_id}")
                pillar = k_meta.get("pillar", "Core Pillar")

                is_critical = (k_id == 41)
                sev = "critical" if is_critical else "high"
                mult = 0.50 if is_critical else 0.80

                penalty_factor *= mult
                gates.append({
                    "koota_id": k_id,
                    "koota_name": k_name,
                    "pillar": pillar,
                    "severity": sev,
                    "reason": f"Direct value contradiction detected by LLM Judge: {judge_res.reasoning}",
                    "penalty_multiplier": mult,
                    "key_tensions": judge_res.key_tensions,
                })

    # 2. Check Severe Disagreement Flags as fallback gates
    if disagreement_flags:
        for flag in disagreement_flags:
            k_id = flag["koota_id"]
            if k_id in TOP_WEIGHTED_JUDGE_KOOTAS and flag["severity"] == "high" and flag["divergence"] >= 0.60:
                if not any(g["koota_id"] == k_id for g in gates):
                    mult = 0.85
                    penalty_factor *= mult
                    gates.append({
                        "koota_id": k_id,
                        "koota_name": flag["koota_name"],
                        "pillar": flag["pillar"],
                        "severity": "high",
                        "reason": f"Severe divergence between objective choices and narrative reflections (divergence: {flag['divergence']:.2f}).",
                        "penalty_multiplier": mult,
                        "key_tensions": [],
                    })

    # 3. Determine Tier Ceiling constraint
    critical_count = sum(1 for g in gates if g["severity"] == "critical")
    total_gates = len(gates)

    if critical_count > 0 or total_gates >= 2:
        tier_ceiling = "not viable"
    elif total_gates == 1:
        tier_ceiling = "compatible with flagged friction points"

    return gates, tier_ceiling, max(0.20, penalty_factor)


def aggregate_scores(
    is_viable: bool,
    hard_filter_reason: Optional[str],
    objective_koota_scores: Dict[int, float],
    semantic_koota_scores: Dict[int, float],
    kootas_metadata: Dict[int, Dict[str, Any]],
    llm_judge_results: Optional[Dict[int, LLMJudgeResult]] = None,
    divergence_threshold: float = 0.35,
    koota_uncertainties_override: Optional[Dict[int, float]] = None,
) -> AggregateMatchResult:
    """Merge scores separating Compensatory trade-offs, Non-Compensatory continuous ceilings, and Uncertainty Quantification."""
    if not is_viable:
        return AggregateMatchResult(
            is_viable=False,
            hard_filter_reason=hard_filter_reason,
            overall_score=None,
            raw_composite_score=None,
            compensatory_score=None,
            ceiling_applied=None,
            capped_by=None,
            objective_score=None,
            semantic_score=None,
            tier_ceiling="not viable",
            risk_adjusted_score=None,
            score_uncertainty=None,
            score_interval=None,
            confidence="Low",
            evidence_coverage_pct=0.0,
            critical_contradictions=0,
            high_impact_uncertainty=[],
            koota_scores={},
            koota_uncertainties={},
            disagreement_flags=[],
            contradiction_gates=[],
            llm_judge_insights={},
        )

    # 1. Identify Disagreements
    disagreement_flags = detect_disagreement_flags(
        objective_koota_scores,
        semantic_koota_scores,
        kootas_metadata,
        threshold=divergence_threshold,
    )
    div_map = {f["koota_id"]: f["delta"] for f in disagreement_flags}

    # 2. Combine Koota-level scores across objective, subjective, and LLM judge sources
    all_koota_ids = set(objective_koota_scores.keys()) | set(semantic_koota_scores.keys())
    if llm_judge_results:
        all_koota_ids |= set(llm_judge_results.keys())

    merged_koota_scores: Dict[int, float] = {}
    merged_koota_uncertainties: Dict[int, float] = {}

    comp_weighted_sum = 0.0
    comp_total_weight = 0.0
    comp_var_weighted_sum = 0.0

    raw_weighted_sum = 0.0
    raw_total_weight = 0.0

    non_comp_ceilings: List[Tuple[int, float, float]] = []  # (k_id, ceiling, sigma_k)
    critical_contradictions_count = 0
    high_impact_uncertainty: List[str] = []

    # Calculate evidence coverage across all 42 Kootas
    total_catalogue_weight = sum(kootas_metadata.get(k, {}).get("weight", 1) for k in kootas_metadata) or 1.0
    answered_weight = sum(kootas_metadata.get(k, {}).get("weight", 1) for k in all_koota_ids if k in kootas_metadata)
    evidence_coverage_pct = round((answered_weight / total_catalogue_weight) * 100.0, 1)

    for k_id in all_koota_ids:
        scores_for_koota = []
        has_obj = k_id in objective_koota_scores
        has_subj = k_id in semantic_koota_scores

        if has_obj:
            scores_for_koota.append(objective_koota_scores[k_id])
        if has_subj:
            scores_for_koota.append(semantic_koota_scores[k_id])
        if llm_judge_results and k_id in llm_judge_results:
            scores_for_koota.append(llm_judge_results[k_id].agreement_score)

        k_score = sum(scores_for_koota) / len(scores_for_koota) if scores_for_koota else 0.0
        merged_koota_scores[k_id] = round(k_score, 4)

        k_meta = kootas_metadata.get(k_id, {})
        weight = k_meta.get("weight", 1)
        agg_type = k_meta.get("aggregation_type", "compensatory")

        # Uncertainty derivation for k_id
        if koota_uncertainties_override and k_id in koota_uncertainties_override:
            sigma_k = koota_uncertainties_override[k_id]
        else:
            judge_res = llm_judge_results.get(k_id) if llm_judge_results else None
            sigma_k = calculate_koota_uncertainty(
                k_id=k_id,
                k_meta=k_meta,
                is_answered=True,
                has_objective=has_obj,
                has_semantic=has_subj,
                llm_judge_result=judge_res,
                divergence=div_map.get(k_id),
            )
        merged_koota_uncertainties[k_id] = sigma_k

        # Check high-impact uncertainty callout: weight >= 10 and sigma >= 0.15
        if weight >= 10 and sigma_k >= 0.15:
            k_name = k_meta.get("name", f"Koota {k_id}")
            pillar = k_meta.get("pillar", "Core Pillar")
            high_impact_uncertainty.append(f"{k_name} ({pillar})")

        raw_weighted_sum += k_score * weight
        raw_total_weight += weight

        if agg_type == "non_compensatory":
            c_val = calculate_koota_ceiling(k_score, k_meta)
            non_comp_ceilings.append((k_id, c_val, sigma_k))
            tau_low = k_meta.get("tau_low", 0.40)
            if k_score <= tau_low:
                critical_contradictions_count += 1
        else:
            comp_weighted_sum += k_score * weight
            comp_total_weight += weight
            comp_var_weighted_sum += (weight ** 2) * (sigma_k ** 2)

    raw_composite_score = round(raw_weighted_sum / raw_total_weight, 4) if raw_total_weight > 0 else 0.0

    # Compensatory Score calculation
    if comp_total_weight > 0:
        comp_score = round(comp_weighted_sum / comp_total_weight, 4)
        sigma_comp = (comp_var_weighted_sum ** 0.5) / comp_total_weight
    else:
        comp_score = raw_composite_score
        sigma_comp = 0.05

    # Weakest-link non-compensatory ceiling evaluation & ceiling variance propagation
    if non_comp_ceilings:
        # Find minimum ceiling
        min_item = min(non_comp_ceilings, key=lambda x: x[1])
        min_k_id, min_ceiling, min_sigma_k = min_item
        min_ceiling = round(min_ceiling, 4)
        k_meta = kootas_metadata.get(min_k_id, {})

        if min_ceiling < 1.0:
            capped_by = {
                "koota_id": min_k_id,
                "koota_name": k_meta.get("name", f"Koota {min_k_id}"),
                "pillar": k_meta.get("pillar", "Core Pillar"),
                "ceiling": min_ceiling,
            }
        else:
            capped_by = None

        # Calculate ceiling uncertainty sensitivity:
        t_low = k_meta.get("tau_low", 0.40)
        t_high = k_meta.get("tau_high", 0.75)
        c_floor = k_meta.get("floor", 0.40)
        k_score = merged_koota_scores.get(min_k_id, 0.5)

        if t_low < t_high and t_low <= k_score < t_high:
            slope = (1.0 - c_floor) / (t_high - t_low)
            sigma_ceiling = slope * min_sigma_k
        elif abs(k_score - t_low) <= min_sigma_k or abs(k_score - t_high) <= min_sigma_k:
            sigma_ceiling = 0.50 * min_sigma_k
        else:
            sigma_ceiling = 0.10 * min_sigma_k
    else:
        min_ceiling = 1.0
        sigma_ceiling = 0.0
        capped_by = None

    # Final overall score is CompScore scaled by weakest-link ceiling
    final_overall_score = round(comp_score * min_ceiling, 4)

    # Propagate combined final score uncertainty
    # FinalScore = CompScore * ceiling_applied
    var_final = ((min_ceiling * sigma_comp) ** 2) + ((comp_score * sigma_ceiling) ** 2)
    final_sigma = round(max(0.01, min(0.40, var_final ** 0.5)), 4)

    # 95% Confidence interval
    lower_interval = round(max(0.0, final_overall_score - (1.96 * final_sigma)), 4)
    upper_interval = round(min(1.0, final_overall_score + (1.96 * final_sigma)), 4)
    score_interval = [lower_interval, upper_interval]

    # Risk-Adjusted Ranking Score: FinalScore - 1.5 * sigma
    risk_adjusted_score = round(max(0.0, final_overall_score - (1.5 * final_sigma)), 4)

    # Confidence bucketing
    if final_sigma <= 0.05 and evidence_coverage_pct >= 85.0:
        confidence_label = "High"
    elif final_sigma <= 0.12 and evidence_coverage_pct >= 60.0:
        confidence_label = "Moderate"
    else:
        confidence_label = "Low"

    # 3. Detect Qualitative Contradiction Gates & Tier Ceilings
    gates, tier_ceiling, _ = detect_contradiction_gates(
        kootas_metadata=kootas_metadata,
        llm_judge_results=llm_judge_results,
        disagreement_flags=disagreement_flags,
        koota_scores=merged_koota_scores,
    )

    # If weakest-link ceiling is severe (<= 0.40), ensure tier is appropriately capped
    if min_ceiling <= 0.40 and tier_ceiling is None:
        tier_ceiling = "not viable"
    elif min_ceiling <= 0.70 and tier_ceiling is None:
        tier_ceiling = "compatible with flagged friction points"

    # Compute overall objective and semantic aggregates for breakdown reporting
    obj_total_w = sum(kootas_metadata.get(k, {}).get("weight", 1) for k in objective_koota_scores)
    obj_weighted = sum(objective_koota_scores[k] * kootas_metadata.get(k, {}).get("weight", 1) for k in objective_koota_scores)
    overall_obj = round(obj_weighted / obj_total_w, 4) if obj_total_w > 0 else None

    subj_total_w = sum(kootas_metadata.get(k, {}).get("weight", 1) for k in semantic_koota_scores)
    subj_weighted = sum(semantic_koota_scores[k] * kootas_metadata.get(k, {}).get("weight", 1) for k in semantic_koota_scores)
    overall_subj = round(subj_weighted / subj_total_w, 4) if subj_total_w > 0 else None

    # LLM judge insight serialization
    judge_insights_dict = {}
    if llm_judge_results:
        for k_id, j in llm_judge_results.items():
            judge_insights_dict[k_id] = {
                "koota_id": k_id,
                "agreement_score": j.agreement_score,
                "contradiction": j.contradiction,
                "confidence": getattr(j, "confidence", 0.90),
                "reasoning": j.reasoning,
                "alignment_points": getattr(j, "alignment_points", []),
                "friction_points": getattr(j, "friction_points", []),
                "key_tensions": j.key_tensions,
                "provider_used": j.provider_used,
            }

    return AggregateMatchResult(
        is_viable=True,
        hard_filter_reason=None,
        overall_score=final_overall_score,
        raw_composite_score=raw_composite_score,
        compensatory_score=comp_score,
        ceiling_applied=min_ceiling,
        capped_by=capped_by,
        objective_score=overall_obj,
        semantic_score=overall_subj,
        tier_ceiling=tier_ceiling,
        risk_adjusted_score=risk_adjusted_score,
        score_uncertainty=final_sigma,
        score_interval=score_interval,
        confidence=confidence_label,
        evidence_coverage_pct=evidence_coverage_pct,
        critical_contradictions=critical_contradictions_count,
        high_impact_uncertainty=high_impact_uncertainty,
        koota_scores=merged_koota_scores,
        koota_uncertainties=merged_koota_uncertainties,
        disagreement_flags=disagreement_flags,
        contradiction_gates=gates,
        llm_judge_insights=judge_insights_dict,
    )
