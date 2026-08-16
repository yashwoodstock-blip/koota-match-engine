"""Score aggregation engine with Gated Aggregation Mathematics and Contradiction Overrides."""
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
    objective_score: Optional[float] = None
    semantic_score: Optional[float] = None
    tier_ceiling: Optional[str] = None  # None | "compatible with flagged friction points" | "not viable"
    koota_scores: Dict[int, float] = field(default_factory=dict)
    disagreement_flags: List[Dict[str, Any]] = field(default_factory=list)
    contradiction_gates: List[Dict[str, Any]] = field(default_factory=list)
    llm_judge_insights: Dict[int, Dict[str, Any]] = field(default_factory=dict)


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
    """Evaluate non-linear contradiction gates and tier ceilings.
    
    Returns (gates_list, tier_ceiling, cumulative_penalty_multiplier).
    """
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

                # Koota 41 (Life Purpose) is a foundational existential veto on its own
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
                # If not already gated by LLM judge
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
    """Merge scores using Gated Aggregation Mathematics with contradiction ceilings."""
    if not is_viable:
        return AggregateMatchResult(
            is_viable=False,
            hard_filter_reason=hard_filter_reason,
            overall_score=None,
            raw_composite_score=None,
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

    # 2. Combine Koota-level scores (incorporating LLM Judge scores if available)
    all_koota_ids = set(objective_koota_scores.keys()) | set(semantic_koota_scores.keys())
    if llm_judge_results:
        all_koota_ids |= set(llm_judge_results.keys())

    merged_koota_scores: Dict[int, float] = {}
    weighted_sum = 0.0
    total_weight = 0.0

    for k_id in all_koota_ids:
        scores_for_koota = []
        if k_id in objective_koota_scores:
            scores_for_koota.append(objective_koota_scores[k_id])
        if k_id in semantic_koota_scores:
            scores_for_koota.append(semantic_koota_scores[k_id])
        if llm_judge_results and k_id in llm_judge_results:
            # LLM Judge carries high fidelity weight in subjective understanding
            scores_for_koota.append(llm_judge_results[k_id].agreement_score)

        k_score = sum(scores_for_koota) / len(scores_for_koota) if scores_for_koota else 0.0
        merged_koota_scores[k_id] = round(k_score, 4)

        weight = kootas_metadata.get(k_id, {}).get("weight", 1)
        weighted_sum += k_score * weight
        total_weight += weight

    raw_composite_score = round(weighted_sum / total_weight, 4) if total_weight > 0 else 0.0

    # 3. Gated Aggregation & Contradiction Override Logic
    gates, tier_ceiling, penalty_multiplier = detect_contradiction_gates(
        kootas_metadata=kootas_metadata,
        llm_judge_results=llm_judge_results,
        disagreement_flags=disagreement_flags,
        koota_scores=merged_koota_scores,
    )

    # Apply gating penalty multiplier to composite score
    gated_overall_score = round(raw_composite_score * penalty_multiplier, 4)

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
        overall_score=gated_overall_score,
        raw_composite_score=raw_composite_score,
        objective_score=overall_obj,
        semantic_score=overall_subj,
        tier_ceiling=tier_ceiling,
        koota_scores=merged_koota_scores,
        disagreement_flags=disagreement_flags,
        contradiction_gates=gates,
        llm_judge_insights=judge_insights_dict,
    )
