"""Semantic embedding and similarity scoring engine using Hugging Face Serverless API."""
import asyncio
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
HF_SIMILARITY_URL = f"https://router.huggingface.co/hf-inference/models/{HF_EMBEDDING_MODEL}"


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
    return float(max(0.0, min(1.0, sim)))


async def fetch_hf_similarity(
    text1: str,
    text2: str,
    client: Optional[httpx.AsyncClient] = None,
) -> float:
    """Compute direct sentence similarity via Hugging Face Serverless API."""
    t1 = (text1 or "").strip()
    t2 = (text2 or "").strip()
    if not t1 or not t2:
        return 0.0

    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {
        "inputs": {
            "source_sentence": t1,
            "sentences": [t2],
        }
    }

    should_close = False
    if client is None:
        client = httpx.AsyncClient(timeout=15.0)
        should_close = True

    try:
        response = await client.post(HF_SIMILARITY_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            return float(max(0.0, min(1.0, data[0])))
        return 0.50
    except Exception:
        # Fallback if offline/mocked
        return 0.50
    finally:
        if should_close:
            await client.aclose()


async def fetch_hf_embedding(
    text: str,
    model: Optional[str] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> List[float]:
    """Fetch text embedding vector (fallback/caching)."""
    clean_text = (text or "").strip()
    if not clean_text:
        return [0.0] * 384

    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    m = model or "sentence-transformers/all-MiniLM-L6-v2"
    url = f"https://router.huggingface.co/hf-inference/models/{m}"
    payload = {"inputs": clean_text}

    should_close = False
    if client is None:
        client = httpx.AsyncClient(timeout=15.0)
        should_close = True

    try:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            if data and isinstance(data[0], list):
                num_tokens = len(data)
                dim = len(data[0])
                pooled = [0.0] * dim
                for token_vec in data:
                    for i in range(dim):
                        pooled[i] += token_vec[i]
                return [round(p / num_tokens, 6) for p in pooled]
            elif data and isinstance(data[0], (int, float)):
                return [float(x) for x in data]
        return [0.5] * 384
    except Exception:
        return [0.5] * 384
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
    """Compute semantic similarity between two subjective answers."""
    # If both have cached vector embeddings, compute cosine similarity in-memory
    if ans1.embedding and ans2.embedding:
        return cosine_similarity(ans1.embedding, ans2.embedding)

    # Otherwise query the live Hugging Face sentence similarity endpoint
    return await fetch_hf_similarity(ans1.raw_value, ans2.raw_value, client=client)


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

    # Gather all pairs to score concurrently
    pairs_to_score: List[Tuple[int, int, Answer, Answer]] = []
    for (k_id, q_idx), ans1 in a1_map.items():
        if (k_id, q_idx) in a2_map:
            ans2 = a2_map[(k_id, q_idx)]
            pairs_to_score.append((k_id, q_idx, ans1, ans2))

    if not pairs_to_score:
        return {}, 0.0

    async def _eval_pair(k_id: int, a1: Answer, a2: Answer) -> Tuple[int, float]:
        score = await score_subjective_koota(a1, a2, client=client)
        return k_id, score

    scored_results = await asyncio.gather(
        *[_eval_pair(k, a1, a2) for k, _, a1, a2 in pairs_to_score]
    )

    koota_q_scores: Dict[int, List[float]] = {}
    for k_id, q_score in scored_results:
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
