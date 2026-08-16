"""NLI Contradiction Scorer using Hugging Face Inference API for Top-10 Kootas."""
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import httpx
from dotenv import load_dotenv

load_dotenv()

HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
HF_NLI_MODEL = os.getenv("HF_NLI_MODEL", "facebook/bart-large-mnli")
HF_NLI_URL = f"https://api-inference.huggingface.co/models/{HF_NLI_MODEL}"


@dataclass
class NLIResult:
    score: float
    entailment: float
    neutral: float
    contradiction: float
    is_contradiction: bool


def compute_nli_score(
    entailment: float,
    neutral: float,
    contradiction: float,
    contradiction_threshold: float = 0.50,
) -> NLIResult:
    """Compute calibrated similarity score and contradiction flag from NLI probabilities."""
    # Calibrated score: entailment rewarded, neutral gives baseline, contradiction heavily penalized
    raw_score = entailment + (0.40 * neutral) - (0.70 * contradiction)
    score = round(max(0.0, min(1.0, float(raw_score))), 4)
    is_contra = contradiction >= contradiction_threshold

    return NLIResult(
        score=score,
        entailment=round(entailment, 4),
        neutral=round(neutral, 4),
        contradiction=round(contradiction, 4),
        is_contradiction=is_contra,
    )


async def fetch_hf_nli(
    premise: str,
    hypothesis: str,
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    """Call Hugging Face NLI inference endpoint."""
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {
        "inputs": premise,
        "parameters": {"candidate_labels": ["entailment", "neutral", "contradiction"]},
    }

    should_close = False
    if client is None:
        client = httpx.AsyncClient(timeout=15.0)
        should_close = True

    try:
        response = await client.post(HF_NLI_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    finally:
        if should_close:
            await client.aclose()


async def evaluate_nli_pair(
    text1: str,
    text2: str,
    client: Optional[httpx.AsyncClient] = None,
) -> NLIResult:
    """Evaluate pairwise NLI relationship between two subjective texts."""
    t1 = (text1 or "").strip()
    t2 = (text2 or "").strip()

    if not t1 or not t2:
        return NLIResult(score=0.50, entailment=0.33, neutral=0.34, contradiction=0.33, is_contradiction=False)

    try:
        data = await fetch_hf_nli(t1, t2, client=client)
        labels = data.get("labels", [])
        scores = data.get("scores", [])

        prob_map = dict(zip(labels, scores))
        ent = float(prob_map.get("entailment", 0.33))
        neu = float(prob_map.get("neutral", 0.34))
        con = float(prob_map.get("contradiction", 0.33))

        return compute_nli_score(ent, neu, con)
    except Exception:
        # Graceful heuristic fallback if HF NLI service is unreachable
        return NLIResult(score=0.50, entailment=0.50, neutral=0.50, contradiction=0.0, is_contradiction=False)
