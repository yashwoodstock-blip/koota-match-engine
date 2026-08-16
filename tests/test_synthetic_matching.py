"""Dedicated test suite for synthetic profile matching and India-critical edge cases."""
import json
import pytest
from pathlib import Path
from app.models import Profile, Answer
from app.scoring.objective import calculate_objective_match
from app.scoring.semantic import score_all_subjective_kootas, cosine_similarity
from app.scoring.aggregate import aggregate_scores
from app.scoring.tiers import classify_tier


@pytest.fixture(scope="module")
def synthetic_data():
    json_path = Path(__file__).parent / "synthetic_profiles.json"
    with open(json_path, "r", encoding="utf-8") as f:
        profiles = json.load(f)
    return {p["id"]: p for p in profiles}


@pytest.fixture(scope="module")
def kootas_metadata():
    kootas_path = Path(__file__).parent.parent / "app" / "db" / "kootas.json"
    with open(kootas_path, "r", encoding="utf-8") as f:
        kootas = json.load(f)
    return {
        k["koota_id"]: {
            "weight": k["weight"],
            "name": k["name"],
            "pillar": k["pillar"],
            "question_type": k["question_type"],
            "is_hard_filter": k["is_hard_filter"],
        }
        for k in kootas
    }


def parse_profile(p_dict: dict) -> tuple[Profile, list[Answer]]:
    p = Profile(
        id=p_dict["id"],
        name=p_dict["name"],
        age=p_dict["age"],
        gender=p_dict.get("gender"),
        religion=p_dict["religion"],
        caste=p_dict.get("caste"),
        caste_preference=p_dict.get("caste_preference", "no_preference"),
        city=p_dict.get("city"),
    )
    answers = []
    for a in p_dict.get("answers", []):
        ans = Answer(
            profile_id=p.id,
            koota_id=a["koota_id"],
            question_index=a["question_index"],
            question_type=a["question_type"],
            raw_value=a["raw_value"],
        )
        answers.append(ans)
    return p, answers


@pytest.mark.asyncio
async def test_synthetic_strong_match_aarav_ananya(synthetic_data, kootas_metadata, monkeypatch):
    """Aarav and Ananya are engineered as a comprehensive strong match."""
    p_aarav, ans_aarav = parse_profile(synthetic_data["syn-01-aarav"])
    p_ananya, ans_ananya = parse_profile(synthetic_data["syn-02-ananya"])

    # High semantic similarity mock for matching philosophies
    async def mock_emb(text, *args, **kwargs):
        return [0.8] * 384

    monkeypatch.setattr("app.scoring.semantic.fetch_hf_embedding", mock_emb)

    # 1. Objective
    obj_res = calculate_objective_match(p_aarav, p_ananya, ans_aarav, ans_ananya, kootas_metadata)
    assert obj_res.is_viable is True

    # 2. Semantic
    subj_scores, _ = await score_all_subjective_kootas(ans_aarav, ans_ananya, kootas_metadata)

    # 3. Aggregate
    agg = aggregate_scores(True, None, obj_res.koota_scores, subj_scores, kootas_metadata)
    assert agg.overall_score >= 0.75
    assert len(agg.disagreement_flags) == 0

    # 4. Tier
    tier_eval = classify_tier(agg, kootas_metadata)
    assert tier_eval.tier == "strong match"
    assert len(tier_eval.alignment_points) > 0


@pytest.mark.asyncio
async def test_synthetic_hard_filter_reject_vikram_pooja(synthetic_data, kootas_metadata):
    """Vikram (36, Rajput, required) and Pooja (25, Bania) fail on age gap (11 years) and caste constraint."""
    p_vikram, ans_vikram = parse_profile(synthetic_data["syn-03-vikram"])
    p_pooja, ans_pooja = parse_profile(synthetic_data["syn-04-pooja"])

    obj_res = calculate_objective_match(p_vikram, p_pooja, ans_vikram, ans_pooja, kootas_metadata, max_age_gap=2)
    assert obj_res.is_viable is False
    assert obj_res.hard_filter_reason is not None

    agg = aggregate_scores(False, obj_res.hard_filter_reason, {}, {}, kootas_metadata)
    tier_eval = classify_tier(agg, kootas_metadata)
    assert tier_eval.tier == "not viable"


@pytest.mark.asyncio
async def test_synthetic_disagreement_flag_koota_18_kabir_neha(synthetic_data, kootas_metadata, monkeypatch):
    """Kabir & Neha agree on multiple choice for Koota 18, but subjective narratives clash heavily."""
    p_kabir, ans_kabir = parse_profile(synthetic_data["syn-05-kabir"])
    p_neha, ans_neha = parse_profile(synthetic_data["syn-06-neha"])

    # Simulate low semantic similarity for opposing subjective stances
    async def mock_emb(text, *args, **kwargs):
        if "refuse" in text or "patriarchal" in text or "side with me" in text:
            return [1.0, 0.0, 0.0]
        return [0.0, 1.0, 0.0]

    monkeypatch.setattr("app.scoring.semantic.fetch_hf_embedding", mock_emb)

    obj_res = calculate_objective_match(p_kabir, p_neha, ans_kabir, ans_neha, kootas_metadata)
    assert obj_res.is_viable is True
    # Both chose "Weekly" and "Yes" -> obj score is 1.0
    assert obj_res.koota_scores[18] == 1.0

    subj_scores, _ = await score_all_subjective_kootas(ans_kabir, ans_neha, kootas_metadata)
    # Subjective score is 0.0
    assert subj_scores[18] == 0.0

    agg = aggregate_scores(True, None, obj_res.koota_scores, subj_scores, kootas_metadata)
    assert len(agg.disagreement_flags) == 1

    flag = agg.disagreement_flags[0]
    assert flag["koota_id"] == 18
    assert flag["severity"] == "high"
    assert flag["divergence"] == 1.0

    tier_eval = classify_tier(agg, kootas_metadata)
    assert tier_eval.tier == "compatible with flagged friction points"


@pytest.mark.asyncio
async def test_synthetic_disagreement_flag_koota_23_rohan_ishita(synthetic_data, kootas_metadata, monkeypatch):
    """Rohan & Ishita agree on objective career questions but subjective text indicates relocation / sacrifice deadlock."""
    p_rohan, ans_rohan = parse_profile(synthetic_data["syn-07-rohan"])
    p_ishita, ans_ishita = parse_profile(synthetic_data["syn-08-ishita"])

    async def mock_emb(text, *args, **kwargs):
        if "startup" in text or "not sacrifice" in text or "total career equality" in text.lower():
            return [0.0, 0.0, 1.0]
        return [1.0, 0.0, 0.0]

    monkeypatch.setattr("app.scoring.semantic.fetch_hf_embedding", mock_emb)

    obj_res = calculate_objective_match(p_rohan, p_ishita, ans_rohan, ans_ishita, kootas_metadata)
    assert obj_res.is_viable is True

    subj_scores, _ = await score_all_subjective_kootas(ans_rohan, ans_ishita, kootas_metadata)
    assert subj_scores[23] == 0.0

    agg = aggregate_scores(True, None, obj_res.koota_scores, subj_scores, kootas_metadata)
    assert any(f["koota_id"] == 23 for f in agg.disagreement_flags)

    tier_eval = classify_tier(agg, kootas_metadata)
    assert tier_eval.tier == "compatible with flagged friction points"


@pytest.mark.asyncio
async def test_synthetic_muslim_pair_matching(synthetic_data, kootas_metadata):
    """Tariq and Farida match on Islam, age gap <= 2, and common nuclear/conflict preferences."""
    p_tariq, ans_tariq = parse_profile(synthetic_data["syn-09-tariq"])
    p_farida, ans_farida = parse_profile(synthetic_data["syn-10-farida"])

    obj_res = calculate_objective_match(p_tariq, p_farida, ans_tariq, ans_farida, kootas_metadata)
    assert obj_res.is_viable is True

    agg = aggregate_scores(True, None, obj_res.koota_scores, {}, kootas_metadata)
    assert agg.overall_score == 1.0


@pytest.mark.asyncio
async def test_synthetic_sikh_pair_matching(synthetic_data, kootas_metadata):
    """Harpreet and Simran match on Sikh faith, vegetarian diet, joint family preferences."""
    p_h, ans_h = parse_profile(synthetic_data["syn-11-harpreet"])
    p_s, ans_s = parse_profile(synthetic_data["syn-12-simran"])

    obj_res = calculate_objective_match(p_h, p_s, ans_h, ans_s, kootas_metadata)
    assert obj_res.is_viable is True
    assert obj_res.overall_score == 1.0
