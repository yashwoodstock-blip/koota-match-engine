"""End-to-end API tests for interest expression, mutual confirmation, and staged disclosure."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.main import app
from app.db.session import async_session
from app.models import Profile, WeeklyMatchList, Interest


async def setup_api_test_data():
    """Seed test profiles and weekly matches."""
    async with async_session() as db:
        await db.execute(delete(Interest).where(Interest.profile_id.in_(["api-prof-1", "api-prof-2"])))
        await db.execute(delete(WeeklyMatchList).where(WeeklyMatchList.profile_id.in_(["api-prof-1", "api-prof-2"])))
        await db.execute(delete(Profile).where(Profile.id.in_(["api-prof-1", "api-prof-2"])))

        p1 = Profile(
            id="api-prof-1",
            name="Aarav Sharma",
            age=28,
            gender="male",
            religion="Hindu",
            caste="Brahmin",
            caste_preference="no_preference",
            city="Bengaluru",
        )
        p2 = Profile(
            id="api-prof-2",
            name="Ananya Iyer",
            age=27,
            gender="female",
            religion="Hindu",
            caste="Brahmin",
            caste_preference="no_preference",
            city="Bengaluru",
        )
        db.add_all([p1, p2])
        await db.flush()

        w1 = WeeklyMatchList(
            profile_id=p1.id,
            candidate_id=p2.id,
            score=0.92,
            tier="strong match",
            alignment_points=["Values aligned"],
            friction_points=[],
            contradiction_gates=[],
        )
        w2 = WeeklyMatchList(
            profile_id=p2.id,
            candidate_id=p1.id,
            score=0.92,
            tier="strong match",
            alignment_points=["Values aligned"],
            friction_points=[],
            contradiction_gates=[],
        )
        db.add_all([w1, w2])
        await db.commit()
    return "api-prof-1", "api-prof-2"


@pytest.mark.asyncio
async def test_interest_api_mutual_flow_and_staged_disclosure():
    p1, p2 = await setup_api_test_data()

    with TestClient(app) as client:
        # 1. P1 expresses interest in P2
        resp1 = client.post(
            "/interest",
            json={"profile_id": p1, "target_profile_id": p2, "action": "pending"},
        )
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["status"] == "pending"
        assert data1["is_mutual"] is False

        # 2. P1 checks status -> sees "pending"
        s_resp1 = client.get(f"/interest/{p1}/status")
        assert s_resp1.status_code == 200
        s_data1 = s_resp1.json()
        assert len(s_data1["statuses"]) == 1
        assert s_data1["statuses"][0]["candidate_id"] == p2
        assert s_data1["statuses"][0]["status"] == "pending"
        assert s_data1["statuses"][0]["is_mutual"] is False

        # 3. P2 checks status BEFORE expressing interest -> sees "none", P1's pending is hidden!
        s_resp2 = client.get(f"/interest/{p2}/status")
        assert s_resp2.status_code == 200
        s_data2 = s_resp2.json()
        assert len(s_data2["statuses"]) == 1
        assert s_data2["statuses"][0]["candidate_id"] == p1
        assert s_data2["statuses"][0]["status"] == "none"
        assert s_data2["statuses"][0]["is_mutual"] is False

        # 4. P2 checks weekly matches before expressing interest -> interest_status is "none", mutual_matches_count is 0
        w_resp2 = client.get(f"/profiles/{p2}/weekly-matches")
        assert w_resp2.status_code == 200
        w_data2 = w_resp2.json()
        assert w_data2["mutual_matches_count"] == 0
        assert w_data2["matches"][0]["interest_status"] == "none"
        assert w_data2["matches"][0]["is_mutual"] is False

        # 5. P2 expresses interest in P1 -> mutual flip!
        resp2 = client.post(
            "/interest",
            json={"profile_id": p2, "target_profile_id": p1, "action": "pending"},
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["status"] == "mutual"
        assert data2["is_mutual"] is True

        # 6. Both check status -> both see "mutual"
        s_resp1_after = client.get(f"/interest/{p1}/status")
        assert s_resp1_after.json()["statuses"][0]["status"] == "mutual"
        assert s_resp1_after.json()["statuses"][0]["is_mutual"] is True

        s_resp2_after = client.get(f"/interest/{p2}/status")
        assert s_resp2_after.json()["statuses"][0]["status"] == "mutual"
        assert s_resp2_after.json()["statuses"][0]["is_mutual"] is True

        # 7. Both check weekly matches -> both see interest_status="mutual" and mutual_matches_count=1
        w_resp1_after = client.get(f"/profiles/{p1}/weekly-matches")
        assert w_resp1_after.json()["mutual_matches_count"] == 1
        assert w_resp1_after.json()["matches"][0]["interest_status"] == "mutual"
        assert w_resp1_after.json()["matches"][0]["is_mutual"] is True

        w_resp2_after = client.get(f"/profiles/{p2}/weekly-matches")
        assert w_resp2_after.json()["mutual_matches_count"] == 1
        assert w_resp2_after.json()["matches"][0]["interest_status"] == "mutual"
        assert w_resp2_after.json()["matches"][0]["is_mutual"] is True


@pytest.mark.asyncio
async def test_interest_api_rejects_unmatched_target():
    p1, _ = await setup_api_test_data()

    with TestClient(app) as client:
        resp = client.post(
            "/interest",
            json={"profile_id": p1, "target_profile_id": "non-existent-candidate", "action": "pending"},
        )
        assert resp.status_code == 400
        assert "not in the caller's weekly matches" in resp.json()["detail"]
