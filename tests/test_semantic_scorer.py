"""TDD Test Suite for Semantic Scorer & Embedding Caching."""
import pytest
import numpy as np
from app.models import Answer
from app.scoring.semantic import (
    cosine_similarity,
    get_embedding,
    score_subjective_koota,
    score_all_subjective_kootas,
)


def test_cosine_similarity_identical_vectors():
    """Identical vectors should yield cosine similarity of 1.0."""
    v1 = [0.2, 0.5, 0.8, -0.1]
    v2 = [0.2, 0.5, 0.8, -0.1]
    sim = cosine_similarity(v1, v2)
    assert sim == pytest.approx(1.0, 1e-5)


def test_cosine_similarity_orthogonal_vectors():
    """Orthogonal vectors should yield cosine similarity close to 0.0."""
    v1 = [1.0, 0.0, 0.0]
    v2 = [0.0, 1.0, 0.0]
    sim = cosine_similarity(v1, v2)
    assert sim == pytest.approx(0.0, 1e-5)


def test_cosine_similarity_opposite_vectors():
    """Opposite vectors should clip to 0.0 minimum."""
    v1 = [1.0, 0.0]
    v2 = [-1.0, 0.0]
    sim = cosine_similarity(v1, v2)
    assert sim == 0.0


@pytest.mark.asyncio
async def test_embedding_uses_cache_when_present(monkeypatch):
    """If Answer already has cached embedding, no network HTTP call should be made."""
    cached_vec = [0.1, 0.2, 0.3, 0.4]
    answer = Answer(
        profile_id="p1",
        koota_id=18,
        question_index=0,
        question_type="subjective",
        raw_value="My family is everything to me.",
        embedding=cached_vec,
    )

    called_network = False

    async def mock_network_call(*args, **kwargs):
        nonlocal called_network
        called_network = True
        return [0.9, 0.9, 0.9, 0.9]

    monkeypatch.setattr("app.scoring.semantic.fetch_hf_embedding", mock_network_call)

    vec = await get_embedding(answer.raw_value, cached_embedding=answer.embedding)
    assert vec == cached_vec
    assert called_network is False, "Network call was made despite cached embedding being present!"


@pytest.mark.asyncio
async def test_semantic_koota_scoring_with_mocked_hf(monkeypatch):
    """Semantic scoring should compute similarity between two subjective answers."""
    # Semantic vectors simulating high alignment
    vec_a = [0.5, 0.5, 0.5, 0.5]
    vec_b = [0.5, 0.5, 0.5, 0.5]

    ans_a = Answer(profile_id="p1", koota_id=41, question_index=0, question_type="subjective", raw_value="Marriage is sacred companionship.", embedding=vec_a)
    ans_b = Answer(profile_id="p2", koota_id=41, question_index=0, question_type="subjective", raw_value="Marriage is a deep lifelong partnership.", embedding=vec_b)

    score = await score_subjective_koota(ans_a, ans_b)
    assert score == pytest.approx(1.0, 1e-4)


@pytest.mark.asyncio
async def test_score_all_subjective_kootas_aggregation(monkeypatch):
    """Verify aggregation across multiple subjective questions with weights."""
    ans_a1 = Answer(profile_id="p1", koota_id=18, question_index=0, question_type="subjective", raw_value="text a1", embedding=[1.0, 0.0])
    ans_b1 = Answer(profile_id="p2", koota_id=18, question_index=0, question_type="subjective", raw_value="text b1", embedding=[1.0, 0.0])

    ans_a2 = Answer(profile_id="p1", koota_id=41, question_index=0, question_type="subjective", raw_value="text a2", embedding=[1.0, 0.0])
    ans_b2 = Answer(profile_id="p2", koota_id=41, question_index=0, question_type="subjective", raw_value="text b2", embedding=[0.0, 1.0])

    kootas_meta = {
        18: {"weight": 14, "name": "In-Law Expectations"},
        41: {"weight": 15, "name": "Life Purpose & Marriage"},
    }

    scores, overall = await score_all_subjective_kootas(
        [ans_a1, ans_a2],
        [ans_b1, ans_b2],
        kootas_meta,
    )

    assert 18 in scores
    assert 41 in scores
    assert scores[18] == pytest.approx(1.0, 1e-4)
    assert scores[41] == pytest.approx(0.0, 1e-4)
    # Expected overall: (1.0 * 14 + 0.0 * 15) / (14 + 15) = 14 / 29 ~= 0.4828
    assert overall == pytest.approx(14 / 29, 1e-3)
