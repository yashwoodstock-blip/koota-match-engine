"""Multi-Provider LLM-as-a-Judge Engine for High-Impact Subjective Kootas.

Providers: Groq (Free Tier), OpenRouter (Free Models), Google Gemini (Free Tier)
Mode: Simultaneous dispatch / Fallback cascade, Structured JSON output only.
"""
import asyncio
import json
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import httpx
from dotenv import load_dotenv

load_dotenv()

# Environment API keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3.5-lightning:free")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Top-weighted Kootas selected for deep LLM Judge evaluation
TOP_WEIGHTED_JUDGE_KOOTAS = {
    41,  # Life Purpose & Meaning of Marriage (w15)
    18,  # In-Law Relationship Expectations (w14)
    23,  # Post-Marriage Career Continuity (w13)
    22,  # Gender Roles & Division of Labor (w12)
    21,  # Living Arrangement Preference (w11)
    40,  # Long-Term Life Vision (w11)
    12,  # Commitment Philosophy (w10)
    19,  # Parental Involvement in Major Decisions (w10)
    31,  # Desire for Children & Timing (w10)
    7,   # Conflict Style (w9)
    24,  # Elder Care Responsibility (w9)
    32,  # Parenting Philosophy (w9)
}


@dataclass
class LLMJudgeResult:
    koota_id: int
    agreement_score: float
    contradiction: bool
    reasoning: str
    confidence: float = 0.90
    alignment_points: List[str] = field(default_factory=list)
    friction_points: List[str] = field(default_factory=list)
    key_tensions: List[str] = field(default_factory=list)
    provider_used: str = "none"


JUDGE_SYSTEM_PROMPT = """You are a rigorous, impartial psychological and marital compatibility judge specializing in Indian marital dynamics.
Your task is to analyze two prospective marriage candidates' responses to a foundational marriage question.
Evaluate whether their core values, boundaries, expectations, and non-negotiables are in genuine harmony, neutral divergence, or irreconcilable contradiction.

CRITICAL EVALUATION RULES:
1. Grounded Evaluation: Base your evaluation strictly on the explicit text provided; do not extrapolate, assume unstated motivations, or infer traits not directly stated.
2. Non-Compensatory Awareness: For high-stakes dimensions (conflict resolution, life purpose, desire for children, crisis habits), do not allow polite tone, affectionate language, or superficial warmth to compensate for an underlying structural disagreement.
3. Calibration Spectrum: Calibrate scores across the full 0.0 to 1.0 range:
   - 0.0 to 0.3: Fundamental incompatibility, structural opposition, or mutual hostility.
   - 0.4 to 0.6: Moderate divergence, differing life rhythms, or neutral variance.
   - 0.7 to 1.0: Strong ideological resonance, deep mutual alignment, and shared vision.
4. Uncertainty Elicitation: If either candidate provides vague, evasive, one-word, or underspecified responses, lower the 'confidence' score (< 0.50).

You MUST respond strictly with valid JSON conforming to this schema (reasoning first):
{
  "reasoning": "<concise 1-2 sentence neutral chain-of-thought analysis of alignment and tension>",
  "agreement_score": <float between 0.0 and 1.0>,
  "contradiction": <boolean true if irreconcilable contradiction or dealbreaker exists, otherwise false>,
  "confidence": <float between 0.0 (underspecified/ambiguous) and 1.0 (clear/unambiguous)>,
  "alignment_points": ["<brief key alignment point if any, or empty list>"],
  "friction_points": ["<brief key friction point if any, or empty list>"],
  "key_tensions": ["<brief key tension if any, or empty list>"]
}

Do not include any introductory or conversational text, markdown fences, or explanation outside the JSON object."""


def _clean_json_response(raw_text: str) -> Dict[str, Any]:
    """Extract and parse JSON object from LLM response text."""
    text = raw_text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    data = json.loads(text)
    
    # Handle key_tensions vs friction_points
    frictions = list(data.get("friction_points", [])) or list(data.get("key_tensions", []))
    alignments = list(data.get("alignment_points", []))

    return {
        "agreement_score": max(0.0, min(1.0, float(data.get("agreement_score", 0.5)))),
        "contradiction": bool(data.get("contradiction", False)),
        "confidence": max(0.0, min(1.0, float(data.get("confidence", 0.85)))),
        "reasoning": str(data.get("reasoning", "")).strip(),
        "alignment_points": alignments,
        "friction_points": frictions,
        "key_tensions": frictions,
    }


async def call_groq_judge(prompt: str, client: Optional[httpx.AsyncClient] = None) -> Dict[str, Any]:
    """Call Groq free tier API."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not configured")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }

    should_close = False
    if client is None:
        client = httpx.AsyncClient(timeout=10.0)
        should_close = True

    try:
        res = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        res.raise_for_status()
        content = res.json()["choices"][0]["message"]["content"]
        return _clean_json_response(content)
    finally:
        if should_close:
            await client.aclose()


async def call_openrouter_judge(prompt: str, client: Optional[httpx.AsyncClient] = None) -> Dict[str, Any]:
    """Call OpenRouter free models API."""
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not configured")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/koota-match-engine",
        "X-Title": "Koota Match Engine",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
    }

    should_close = False
    if client is None:
        client = httpx.AsyncClient(timeout=10.0)
        should_close = True

    try:
        res = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        res.raise_for_status()
        content = res.json()["choices"][0]["message"]["content"]
        return _clean_json_response(content)
    finally:
        if should_close:
            await client.aclose()


async def call_gemini_judge(prompt: str, client: Optional[httpx.AsyncClient] = None) -> Dict[str, Any]:
    """Call Google Gemini free tier REST API."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "systemInstruction": {"parts": [{"text": JUDGE_SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"},
    }

    should_close = False
    if client is None:
        client = httpx.AsyncClient(timeout=10.0)
        should_close = True

    try:
        res = await client.post(url, json=payload)
        res.raise_for_status()
        candidates = res.json().get("candidates", [])
        if not candidates:
            raise ValueError("Empty response from Gemini")
        content = candidates[0]["content"]["parts"][0]["text"]
        return _clean_json_response(content)
    finally:
        if should_close:
            await client.aclose()


async def dispatch_llm_judge(
    prompt: str,
    provider_preference: Optional[str] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> Tuple[Dict[str, Any], str]:
    """Dispatch LLM judge request across providers with automatic failover."""
    providers = ["groq", "openrouter", "gemini"]
    if provider_preference and provider_preference in providers:
        providers.remove(provider_preference)
        providers.insert(0, provider_preference)

    for p in providers:
        try:
            if p == "groq":
                data = await call_groq_judge(prompt, client=client)
                return data, "groq"
            elif p == "openrouter":
                data = await call_openrouter_judge(prompt, client=client)
                return data, "openrouter"
            elif p == "gemini":
                data = await call_gemini_judge(prompt, client=client)
                return data, "gemini"
        except Exception:
            continue

    # Heuristic fallback if all API calls fail or keys are absent
    return {
        "agreement_score": 0.50,
        "contradiction": False,
        "reasoning": "Heuristic fallback evaluation applied (offline/free-tier safe mode).",
        "key_tensions": [],
    }, "fallback_heuristic"


async def evaluate_llm_judge_koota(
    koota_id: int,
    koota_name: str,
    question: str,
    ans_a: str,
    ans_b: str,
    provider_preference: Optional[str] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> LLMJudgeResult:
    """Evaluate pairwise alignment on a specific subjective Koota."""
    prompt = f"""Koota: {koota_name} (ID: {koota_id})
Question: {question}

Candidate A's Answer:
"{ans_a}"

Candidate B's Answer:
"{ans_b}"

Evaluate agreement score, whether a direct contradiction exists, and summarize key tensions."""

    data, provider = await dispatch_llm_judge(prompt, provider_preference=provider_preference, client=client)

    return LLMJudgeResult(
        koota_id=koota_id,
        agreement_score=data["agreement_score"],
        contradiction=data["contradiction"],
        confidence=data.get("confidence", 0.90),
        reasoning=data["reasoning"],
        alignment_points=data.get("alignment_points", []),
        friction_points=data.get("friction_points", []),
        key_tensions=data.get("key_tensions", []),
        provider_used=provider,
    )


async def evaluate_all_top_kootas_llm_judge(
    p1_answers: List[Any],
    p2_answers: List[Any],
    kootas_metadata: Dict[int, Dict[str, Any]],
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[int, LLMJudgeResult]:
    """Concurrently evaluate all top-weighted subjective Kootas using LLM Judge."""
    a1_map = {
        (a.koota_id, a.question_index): a
        for a in p1_answers
        if getattr(a, "question_type", "") == "subjective"
    }
    a2_map = {
        (a.koota_id, a.question_index): a
        for a in p2_answers
        if getattr(a, "question_type", "") == "subjective"
    }

    judge_tasks = []
    task_koota_ids = []

    for (k_id, q_idx), ans1 in a1_map.items():
        if k_id in TOP_WEIGHTED_JUDGE_KOOTAS and (k_id, q_idx) in a2_map:
            ans2 = a2_map[(k_id, q_idx)]
            k_meta = kootas_metadata.get(k_id, {})
            k_name = k_meta.get("name", f"Koota {k_id}")
            subj_questions = k_meta.get("subjective_questions", [])
            q_text = subj_questions[q_idx] if q_idx < len(subj_questions) else f"Question {q_idx}"

            # Alternate provider preference across parallel tasks to balance load between Groq and OpenRouter
            pref = "groq" if len(judge_tasks) % 2 == 0 else "openrouter"

            task = evaluate_llm_judge_koota(
                koota_id=k_id,
                koota_name=k_name,
                question=q_text,
                ans_a=ans1.raw_value,
                ans_b=ans2.raw_value,
                provider_preference=pref,
                client=client,
            )
            judge_tasks.append(task)
            task_koota_ids.append(k_id)

    if not judge_tasks:
        return {}

    # Run all judge tasks simultaneously
    results = await asyncio.gather(*judge_tasks, return_exceptions=True)

    judge_dict: Dict[int, LLMJudgeResult] = {}
    for k_id, res in zip(task_koota_ids, results):
        if isinstance(res, LLMJudgeResult):
            judge_dict[k_id] = res

    return judge_dict
