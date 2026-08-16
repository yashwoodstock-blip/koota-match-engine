"""Score aggregation engine with objective-subjective divergence / disagreement detection."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class AggregateMatchResult:
    is_viable: bool
    hard_filter_reason: Optional[str] = None
    overall_score: Optional[float] = None
    objective_score: Optional[float] = None
    semantic_score: Optional[float] = None
    koota_scores: Dict[int, float] = field(default_factory=dict)
    disagreement_flags: List[Dict[str, Any]] = field(default_factory=list)


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


def aggregate_scores(
    is_viable: bool,
    hard_filter_reason: Optional[str],
    objective_koota_scores: Dict[int, float],
    semantic_koota_scores: Dict[int, float],
    kootas_metadata: Dict[int, Dict[str, Any]],
    divergence_threshold: float = 0.35,
) -> AggregateMatchResult:
    """Merge objective and subjective scores using domain weights and flag divergences."""
    if not is_viable:
        return AggregateMatchResult(
            is_viable=False,
            hard_filter_reason=hard_filter_reason,
            overall_score=None,
            objective_score=None,
            semantic_score=None,
            koota_scores={},
            disagreement_flags=[],
        )

    # 1. Identify Disagreements
    disagreement_flags = detect_disagreement_flags(
        objective_koota_scores,
        semantic_koota_scores,
        kootas_metadata,
        threshold=divergence_threshold,
    )

    # 2. Combine Koota-level scores
    all_koota_ids = set(objective_koota_scores.keys()) | set(semantic_koota_scores.keys())
    merged_koota_scores: Dict[int, float] = {}
    weighted_sum = 0.0
    total_weight = 0.0

    for k_id in all_koota_ids:
        has_obj = k_id in objective_koota_scores
        has_subj = k_id in semantic_koota_scores

        if has_obj and has_subj:
            k_score = (objective_koota_scores[k_id] + semantic_koota_scores[k_id]) / 2.0
        elif has_obj:
            k_score = objective_koota_scores[k_id]
        else:
            k_score = semantic_koota_scores[k_id]

        merged_koota_scores[k_id] = round(k_score, 4)

        weight = kootas_metadata.get(k_id, {}).get("weight", 1)
        weighted_sum += k_score * weight
        total_weight += weight

    overall_score = round(weighted_sum / total_weight, 4) if total_weight > 0 else 0.0

    # Compute overall objective and semantic aggregates for breakdown reporting
    obj_total_w = sum(kootas_metadata.get(k, {}).get("weight", 1) for k in objective_koota_scores)
    obj_weighted = sum(objective_koota_scores[k] * kootas_metadata.get(k, {}).get("weight", 1) for k in objective_koota_scores)
    overall_obj = round(obj_weighted / obj_total_w, 4) if obj_total_w > 0 else None

    subj_total_w = sum(kootas_metadata.get(k, {}).get("weight", 1) for k in semantic_koota_scores)
    subj_weighted = sum(semantic_koota_scores[k] * kootas_metadata.get(k, {}).get("weight", 1) for k in semantic_koota_scores)
    overall_subj = round(subj_weighted / subj_total_w, 4) if subj_total_w > 0 else None

    return AggregateMatchResult(
        is_viable=True,
        hard_filter_reason=None,
        overall_score=overall_score,
        objective_score=overall_obj,
        semantic_score=overall_subj,
        koota_scores=merged_koota_scores,
        disagreement_flags=disagreement_flags,
    )
