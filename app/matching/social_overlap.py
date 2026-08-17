"""Pure function for Jaccard similarity computation on opted-in social following lists."""
from typing import List, Dict, Any, Optional, Set


def normalize_usernames(usernames: Optional[List[str]]) -> Set[str]:
    """Normalize username list by trimming whitespace, lowercasing, and stripping @ prefix."""
    if not usernames:
        return set()
    cleaned = set()
    for u in usernames:
        if isinstance(u, str):
            val = u.strip().lower().lstrip("@")
            if val:
                cleaned.add(val)
    return cleaned


def compute_overlap(
    usernames_a: Optional[List[str]],
    usernames_b: Optional[List[str]],
    opted_in_a: bool = True,
    opted_in_b: bool = True,
) -> Dict[str, Any]:
    """Compute Jaccard similarity between two users' social following lists.
    
    Jaccard Index = |Intersection(A, B)| / |Union(A, B)|
    
    STRICT PRIVACY & OPT-IN RULES:
    1. Returns {"overlap_score": 0.0, "shared_count": 0} if either party is not opted in.
    2. Returns {"overlap_score": 0.0, "shared_count": 0} if either list is empty.
    3. Output is purely aggregate numbers (shared_count and overlap_score) — NEVER reveals username strings.
    4. Result is always in [0.0, 1.0].
    """
    if not opted_in_a or not opted_in_b:
        return {"overlap_score": 0.0, "shared_count": 0}

    set_a = normalize_usernames(usernames_a)
    set_b = normalize_usernames(usernames_b)

    if not set_a or not set_b:
        return {"overlap_score": 0.0, "shared_count": 0}

    intersection = set_a.intersection(set_b)
    union = set_a.union(set_b)

    shared_count = len(intersection)
    union_count = len(union)

    if union_count == 0:
        return {"overlap_score": 0.0, "shared_count": 0}

    overlap_score = round(shared_count / union_count, 4)

    return {
        "overlap_score": overlap_score,
        "shared_count": shared_count,
    }
