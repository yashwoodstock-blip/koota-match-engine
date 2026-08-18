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
    koota_scores: Dict[int, float] = field(default_factory=dict)
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
    if tau_low == tau_high:
        return 1.0 if k_score >= tau_high else float(floor)

    if k_score >= tau_high:
        return 1.0
    elif k_score < tau_low:
        return float(floor)
    else:
        # Continuous linear interpolation between tau_low and tau_high
        ratio = (k_score - tau_low) / (tau_high - tau_low)
        return float(floor + (1.0 - floor) * ratio)


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
) -> AggregateMatchResult:
    """Merge scores separating Compensatory trade-offs and Non-Compensatory continuous ceilings."""
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
            koota_scores={},
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

    # 2. Combine Koota-level scores across objective, subjective, and LLM judge sources
    all_koota_ids = set(objective_koota_scores.keys()) | set(semantic_koota_scores.keys())
    if llm_judge_results:
        all_koota_ids |= set(llm_judge_results.keys())

    merged_koota_scores: Dict[int, float] = {}
    comp_weighted_sum = 0.0
    comp_total_weight = 0.0

    raw_weighted_sum = 0.0
    raw_total_weight = 0.0

    non_comp_ceilings: List[Tuple[int, float]] = []

    for k_id in all_koota_ids:
        scores_for_koota = []
        if k_id in objective_koota_scores:
            scores_for_koota.append(objective_koota_scores[k_id])
        if k_id in semantic_koota_scores:
            scores_for_koota.append(semantic_koota_scores[k_id])
        if llm_judge_results and k_id in llm_judge_results:
            scores_for_koota.append(llm_judge_results[k_id].agreement_score)

        k_score = sum(scores_for_koota) / len(scores_for_koota) if scores_for_koota else 0.0
        merged_koota_scores[k_id] = round(k_score, 4)

        k_meta = kootas_metadata.get(k_id, {})
        weight = k_meta.get("weight", 1)
        agg_type = k_meta.get("aggregation_type", "compensatory")

        raw_weighted_sum += k_score * weight
        raw_total_weight += weight

        if agg_type == "non_compensatory":
            c_val = calculate_koota_ceiling(k_score, k_meta)
            non_comp_ceilings.append((k_id, c_val))
        else:
            comp_weighted_sum += k_score * weight
            comp_total_weight += weight

    raw_composite_score = round(raw_weighted_sum / raw_total_weight, 4) if raw_total_weight > 0 else 0.0

    # Compensatory Score calculation
    if comp_total_weight > 0:
        comp_score = round(comp_weighted_sum / comp_total_weight, 4)
    else:
        comp_score = raw_composite_score

    # Weakest-link non-compensatory ceiling evaluation
    if non_comp_ceilings:
        # Find minimum ceiling
        min_k_id, min_ceiling = min(non_comp_ceilings, key=lambda x: x[1])
        min_ceiling = round(min_ceiling, 4)
        if min_ceiling < 1.0:
            k_meta = kootas_metadata.get(min_k_id, {})
            capped_by = {
                "koota_id": min_k_id,
                "koota_name": k_meta.get("name", f"Koota {min_k_id}"),
                "pillar": k_meta.get("pillar", "Core Pillar"),
                "ceiling": min_ceiling,
            }
        else:
            capped_by = None
    else:
        min_ceiling = 1.0
        capped_by = None

    # Final overall score is CompScore scaled by weakest-link ceiling
    final_overall_score = round(comp_score * min_ceiling, 4)

    # 3. Detect Qualitative Contradiction Gates & Tier Ceilings
    gates, tier_ceiling, _ = detect_contradiction_gates(
        kootas_metadata=kootas_metadata,
        llm_judge_results=llm_judge_results,
        disagreement_flags=disagreement_flags,
        koota_scores=merged_koota_scores,
    )

    # If weakest-link ceiling is severe (<= 0.45), ensure tier is appropriately capped
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
                "reasoning": j.reasoning,
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
        koota_scores=merged_koota_scores,
        disagreement_flags=disagreement_flags,
        contradiction_gates=gates,
        llm_judge_insights=judge_insights_dict,
    )
