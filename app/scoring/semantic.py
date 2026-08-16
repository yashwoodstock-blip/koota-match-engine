"""Semantic embedding and similarity scoring engine using Hugging Face Serverless API."""
import math
import os
from typing import Dict, List, Optional, Tuple, Any
import httpx
from dotenv import load_dotenv
from app.models import Answer

load_dotenv()

HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
HF_EMBEDDING_MODEL = os.getenv(
    "HF_EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
HF_API_URL = f"https://router.huggingface.co/hf-inference/models/{HF_EMBEDDING_MODEL}"


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine similarity between two float vectors, clipped to [0.0, 1.0]."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0

    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))

    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0

    sim = dot / (norm1 * norm2)
    # Clip negative similarity to 0.0 and cap at 1.0
    return float(max(0.0, min(1.0, sim)))


async def fetch_hf_embedding(
    text: str,
    model: Optional[str] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> List[float]:
    """Fetch text embedding from Hugging Face Serverless Inference API over HTTP."""
    clean_text = (text or "").strip()
    if not clean_text:
        return [0.0] * 384

    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {"inputs": clean_text, "options": {"wait_for_model": True}}

    url = (
        f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model}"
        if model
        else HF_API_URL
    )

    should_close = False
    if client is None:
        client = httpx.AsyncClient(timeout=30.0)
        should_close = True

    try:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        # Handle different response shapes from HF pipeline
        if isinstance(data, list):
            # If 2D (sequence of tokens), perform mean pooling over token embeddings
            if data and isinstance(data[0], list):
                num_tokens = len(data)
                dim = len(data[0])
                pooled = [0.0] * dim
                for token_vec in data:
                    for i in range(dim):
                        pooled[i] += token_vec[i]
                return [round(p / num_tokens, 6) for p in pooled]
            # If 1D list of floats
            elif data and isinstance(data[0], (int, float)):
                return [float(x) for x in data]

        raise ValueError(f"Unexpected embedding format from Hugging Face API: {type(data)}")
    finally:
        if should_close:
            await client.aclose()


async def get_embedding(
    text: str,
    cached_embedding: Optional[List[float]] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> List[float]:
    """Return cached embedding if available; otherwise fetch from Hugging Face."""
    if cached_embedding and isinstance(cached_embedding, list) and len(cached_embedding) > 0:
        return cached_embedding

    return await fetch_hf_embedding(text, client=client)


async def score_subjective_koota(
    ans1: Answer,
    ans2: Answer,
    client: Optional[httpx.AsyncClient] = None,
) -> float:
    """Compute semantic cosine similarity between two subjective answers."""
    v1 = await get_embedding(ans1.raw_value, cached_embedding=ans1.embedding, client=client)
    v2 = await get_embedding(ans2.raw_value, cached_embedding=ans2.embedding, client=client)

    # Cache back if missing
    if ans1.embedding is None:
        ans1.embedding = v1
    if ans2.embedding is None:
        ans2.embedding = v2

    return cosine_similarity(v1, v2)


async def score_all_subjective_kootas(
    p1_answers: List[Answer],
    p2_answers: List[Answer],
    kootas_metadata: Dict[int, Dict[str, Any]],
    client: Optional[httpx.AsyncClient] = None,
) -> Tuple[Dict[int, float], float]:
    """Score all subjective answers across matching Kootas and compute weighted total."""
    a1_map: Dict[Tuple[int, int], Answer] = {
        (a.koota_id, a.question_index): a
        for a in p1_answers
        if a.question_type == "subjective"
    }
    a2_map: Dict[Tuple[int, int], Answer] = {
        (a.koota_id, a.question_index): a
        for a in p2_answers
        if a.question_type == "subjective"
    }

    koota_q_scores: Dict[int, List[float]] = {}

    for (k_id, q_idx), ans1 in a1_map.items():
        if (k_id, q_idx) in a2_map:
            ans2 = a2_map[(k_id, q_idx)]
            q_score = await score_subjective_koota(ans1, ans2, client=client)
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

    overall_semantic_score = (
        round(weighted_sum / total_weight, 4) if total_weight > 0 else 0.0
    )

    return koota_scores, overall_semantic_score
