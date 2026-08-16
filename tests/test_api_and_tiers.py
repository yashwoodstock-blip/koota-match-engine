"""Test suite for Phase 4: Tier classification and API endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import Profile, Answer, Koota
from app.scoring.aggregate import AggregateMatchResult
from app.scoring.tiers import classify_tier, ALIGNMENT_TEMPLATES, FRICTION_TEMPLATES


def test_tier_classification_strong_match():
    """A high score (>= 0.75) with no high disagreement flags classifies as 'strong match'."""
    agg = AggregateMatchResult(
        is_viable=True,
        hard_filter_reason=None,
        overall_score=0.88,
        objective_score=0.90,
        semantic_score=0.86,
        koota_scores={18: 0.90, 22: 0.85, 23: 0.92, 41: 0.88},
        disagreement_flags=[],
    )
    kootas_meta = {
        18: {"weight": 14, "name": "In-Laws"},
        22: {"weight": 12, "name": "Gender Roles"},
        23: {"weight": 13, "name": "Career Continuity"},
        41: {"weight": 15, "name": "Life Purpose"},
    }

    tier_res = classify_tier(agg, kootas_meta)
    assert tier_res.tier == "strong match"
    assert len(tier_res.alignment_points) > 0
    # Confirm no raw text
    for p in tier_res.alignment_points:
        assert isinstance(p, str)


def test_tier_classification_flagged_friction():
    """A high score with a high disagreement flag classifies as 'compatible with flagged friction points'."""
    agg = AggregateMatchResult(
        is_viable=True,
        hard_filter_reason=None,
        overall_score=0.80,
        objective_score=0.90,
        semantic_score=0.70,
        koota_scores={18: 0.50, 22: 0.90},
        disagreement_flags=[{
            "koota_id": 18,
            "koota_name": "In-Law Relationship Expectations",
            "pillar": "PILLAR F",
            "objective_score": 0.95,
            "subjective_score": 0.05,
            "divergence": 0.90,
            "severity": "high",
            "note": "Severe divergence",
        }],
    )
    kootas_meta = {
        18: {"weight": 14, "name": "In-Laws"},
        22: {"weight": 12, "name": "Gender Roles"},
    }

    tier_res = classify_tier(agg, kootas_meta)
    assert tier_res.tier == "compatible with flagged friction points"
    assert any("[Divergence Flagged]" in f for f in tier_res.friction_points)


def test_tier_classification_not_viable():
    """Hard filter failure or very low score classifies as 'not viable'."""
    agg = AggregateMatchResult(
        is_viable=False,
        hard_filter_reason="Religion mismatch: Hindu vs Muslim.",
        overall_score=None,
        koota_scores={},
        disagreement_flags=[],
    )
    tier_res = classify_tier(agg, {})
    assert tier_res.tier == "not viable"
    assert "Religion mismatch" in tier_res.friction_points[0]


def test_api_profile_and_match_lifecycle(monkeypatch):
    """End-to-end API test: create profiles, submit answers, check completion, and execute match."""
    # Mock embedding function so no external HF API call occurs during test
    async def mock_emb(text, *args, **kwargs):
        return [0.5] * 384

    async def mock_judge(prompt, *args, **kwargs):
        return {
            "agreement_score": 0.90,
            "contradiction": False,
            "reasoning": "High alignment on values.",
            "key_tensions": [],
        }, "groq"

    monkeypatch.setattr("app.scoring.semantic.fetch_hf_embedding", mock_emb)
    monkeypatch.setattr("app.api.routes_profiles.get_embedding", mock_emb)
    monkeypatch.setattr("app.scoring.llm_judge.dispatch_llm_judge", mock_judge)

    with TestClient(app) as client:
        # 1. Create Profile A
        res_a = client.post("/profiles", json={
            "name": "Rohan Patel",
            "age": 29,
            "gender": "male",
            "religion": "Hindu",
            "caste": "Patel",
            "caste_preference": "no_preference",
            "city": "Ahmedabad",
        })
        assert res_a.status_code == 201
        p_a = res_a.json()
        p_a_id = p_a["id"]
        assert p_a["is_complete"] is False

        # 2. Create Profile B
        res_b = client.post("/profiles", json={
            "name": "Pooja Patel",
            "age": 28,
            "gender": "female",
            "religion": "Hindu",
            "caste": "Patel",
            "caste_preference": "no_preference",
            "city": "Mumbai",
        })
        assert res_b.status_code == 201
        p_b = res_b.json()
        p_b_id = p_b["id"]

        # 3. Submit Answers for Profile A & B
        answers_a = [
            {"koota_id": 7, "question_index": 0, "question_type": "objective", "raw_value": "engage immediately"},
            {"koota_id": 7, "question_index": 1, "question_type": "objective", "raw_value": "same-day"},
            {"koota_id": 18, "question_index": 0, "question_type": "objective", "raw_value": "Weekly"},
            {"koota_id": 18, "question_index": 1, "question_type": "objective", "raw_value": "Flexible/Depends"},
            {"koota_id": 18, "question_index": 0, "question_type": "subjective", "raw_value": "Respecting parents while keeping nuclear space."},
            {"koota_id": 41, "question_index": 0, "question_type": "subjective", "raw_value": "Lifelong companionship and joint purpose."},
        ]
        answers_b = [
            {"koota_id": 7, "question_index": 0, "question_type": "objective", "raw_value": "engage immediately"},
            {"koota_id": 7, "question_index": 1, "question_type": "objective", "raw_value": "same-day"},
            {"koota_id": 18, "question_index": 0, "question_type": "objective", "raw_value": "Weekly"},
            {"koota_id": 18, "question_index": 1, "question_type": "objective", "raw_value": "Flexible/Depends"},
            {"koota_id": 18, "question_index": 0, "question_type": "subjective", "raw_value": "Respecting parents while keeping nuclear space."},
            {"koota_id": 41, "question_index": 0, "question_type": "subjective", "raw_value": "Lifelong companionship and joint purpose."},
        ]

        sub_a = client.post(f"/profiles/{p_a_id}/answers", json={"answers": answers_a})
        assert sub_a.status_code == 200
        assert sub_a.json()["submitted_answers_count"] == 6

        sub_b = client.post(f"/profiles/{p_b_id}/answers", json={"answers": answers_b})
        assert sub_b.status_code == 200

        # 4. Check completion endpoint
        comp_res = client.get(f"/profiles/{p_a_id}/completion")
        assert comp_res.status_code == 200
        comp_data = comp_res.json()
        assert comp_data["answered_kootas_count"] == 3
        assert comp_data["is_complete"] is False

        # 5. POST /match/{p_a_id}/{p_b_id}
        match_res = client.post(f"/match/{p_a_id}/{p_b_id}")
        assert match_res.status_code == 200
        match_data = match_res.json()

        assert match_data["is_viable"] is True
        assert match_data["tier"] in ["strong match", "compatible with flagged friction points"]
        assert match_data["overall_score"] is not None
        assert match_data["overall_score"] >= 0.75
        assert len(match_data["alignment_points"]) > 0
        # Assert NO raw free text or sensitive demographic leaked in response
        assert "caste" not in match_data
        assert "religion" not in match_data
        assert "Respecting parents while keeping nuclear space." not in str(match_data)
        assert "Lifelong companionship" not in str(match_data)

        # 6. GET /match/{p_a_id}/candidates
        cand_res = client.get(f"/match/{p_a_id}/candidates")
        assert cand_res.status_code == 200
        candidates = cand_res.json()
        assert len(candidates) >= 1
        assert any(c["candidate_id"] == p_b_id for c in candidates)
