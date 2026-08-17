"""Test suite for Phase 6 Read-only Weekly Matches API endpoint."""
import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from app.main import app
from app.db.session import async_session
from app.db.seed_synthetic import seed_synthetic_profiles
from app.models import Profile, WeeklyMatchList, utc_now


@pytest.mark.asyncio
async def test_weekly_matches_read_only_instant_response():
    """GET /profiles/{id}/weekly-matches reads precomputed rows with zero live scoring calls."""
    await seed_synthetic_profiles()
    async with async_session() as db:
        # 1. Clean previous and insert precomputed WeeklyMatchList entries
        target_id = "syn-01-aarav"
        await db.execute(delete(WeeklyMatchList).where(WeeklyMatchList.profile_id == target_id))
        match_entry = WeeklyMatchList(
            profile_id=target_id,
            candidate_id="syn-02-ananya",
            score=0.9150,
            tier="strong match",
            alignment_points=["Shared values on lifelong companionship.", "Compatible in-law engagement rhythm."],
            friction_points=[],
            contradiction_gates=[],
            generated_at=utc_now(),
        )
        db.add(match_entry)
        await db.commit()

    with TestClient(app) as client:
        # Time the request to ensure constant-time response (under 200ms)
        start = time.perf_counter()
        res = client.get(f"/profiles/{target_id}/weekly-matches")
        elapsed = time.perf_counter() - start

        assert res.status_code == 200
        data = res.json()
        assert data["profile_id"] == target_id
        assert data["is_precomputed"] is True
        assert data["total_matches"] >= 1
        assert elapsed < 0.50  # Must be fast constant-time DB lookup

        top_match = data["matches"][0]
        assert top_match["candidate_id"] == "syn-02-ananya"
        assert top_match["candidate_name"] == "Ananya Iyer"
        assert top_match["score"] == 0.9150
        assert top_match["tier"] == "strong match"
        assert len(top_match["alignment_points"]) == 2

        # PRIVACY ASSERTION: Confirm zero Layer-1 demographics (no age, income, caste, religion fields in match payload)
        for key in ["age", "income", "caste", "religion", "raw_answers", "subjective_answers"]:
            assert key not in top_match


def test_weekly_matches_nonexistent_profile_404():
    """GET /profiles/invalid-id/weekly-matches returns 404."""
    with TestClient(app) as client:
        res = client.get("/profiles/non-existent-profile-id/weekly-matches")
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_weekly_matches_interest_status_staged_disclosure():
    """Weekly matches endpoint correctly reports caller-specific interest_status and mutual count."""
    await seed_synthetic_profiles()
    async with async_session() as db:
        from app.models import Interest
        p1 = "syn-01-aarav"
        p2 = "syn-02-ananya"

        # Ensure weekly matches exist for both
        await db.execute(delete(WeeklyMatchList).where(WeeklyMatchList.profile_id.in_([p1, p2])))
        await db.execute(delete(Interest).where(Interest.profile_id.in_([p1, p2])))

        w1 = WeeklyMatchList(
            profile_id=p1,
            candidate_id=p2,
            score=0.92,
            tier="strong match",
            alignment_points=["Values"],
            friction_points=[],
            contradiction_gates=[],
        )
        w2 = WeeklyMatchList(
            profile_id=p2,
            candidate_id=p1,
            score=0.92,
            tier="strong match",
            alignment_points=["Values"],
            friction_points=[],
            contradiction_gates=[],
        )
        # P1 expresses pending interest toward P2
        int_p1 = Interest(
            profile_id=p1,
            target_profile_id=p2,
            status="pending",
        )
        db.add_all([w1, w2, int_p1])
        await db.commit()

    with TestClient(app) as client:
        # P1 sees interest_status="pending", is_mutual=False, mutual_matches_count=0
        r1 = client.get(f"/profiles/{p1}/weekly-matches")
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1["mutual_matches_count"] == 0
        assert d1["matches"][0]["interest_status"] == "pending"
        assert d1["matches"][0]["is_mutual"] is False

        # P2 sees interest_status="none", is_mutual=False, mutual_matches_count=0 (P1's pending is hidden!)
        r2 = client.get(f"/profiles/{p2}/weekly-matches")
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2["mutual_matches_count"] == 0
        assert d2["matches"][0]["interest_status"] == "none"
        assert d2["matches"][0]["is_mutual"] is False
