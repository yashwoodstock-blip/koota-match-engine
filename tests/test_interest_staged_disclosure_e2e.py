"""End-to-end integration test for interest staged disclosure and atomic mutual confirmation."""
import pytest
from app.main import app
from fastapi.testclient import TestClient
from app.db.session import async_session
from app.models import WeeklyMatchList, utc_now
from tests.test_on_demand_refresh_and_compatibility import create_test_profile, populate_minimal_answers

client = TestClient(app)


@pytest.mark.asyncio
async def test_interest_staged_disclosure_and_mutual_flip_e2e():
    """Verify staged disclosure: 'none' visible until both express pending, then atomically flips to 'mutual'."""
    p_a = await create_test_profile(name="Candidate Ananya", age=26, gender="female", religion="Hindu")
    p_b = await create_test_profile(name="Candidate Rohan", age=27, gender="male", religion="Hindu")
    await populate_minimal_answers(p_a)
    await populate_minimal_answers(p_b)

    # 1. Place each candidate in each other's WeeklyMatchList
    async with async_session() as session:
        wml_a = WeeklyMatchList(
            profile_id=p_a,
            candidate_id=p_b,
            score=0.88,
            tier="strong match",
            generated_at=utc_now(),
        )
        wml_b = WeeklyMatchList(
            profile_id=p_b,
            candidate_id=p_a,
            score=0.88,
            tier="strong match",
            generated_at=utc_now(),
        )
        session.add_all([wml_a, wml_b])
        await session.commit()

    # 2. Before any interest: both see status 'none'
    res_status_a0 = client.get(f"/interest/{p_a}/status", headers={"X-Test-Profile-Id": p_a})
    assert res_status_a0.status_code == 200
    st_a0 = next(s for s in res_status_a0.json()["statuses"] if s["candidate_id"] == p_b)
    assert st_a0["status"] == "none"
    assert st_a0["is_mutual"] is False

    res_status_b0 = client.get(f"/interest/{p_b}/status", headers={"X-Test-Profile-Id": p_b})
    assert res_status_b0.status_code == 200
    st_b0 = next(s for s in res_status_b0.json()["statuses"] if s["candidate_id"] == p_a)
    assert st_b0["status"] == "none"
    assert st_b0["is_mutual"] is False

    # 3. Ananya expresses 'pending' interest in Rohan
    res_exp_a = client.post(
        "/interest",
        json={"profile_id": p_a, "target_profile_id": p_b, "action": "pending"},
        headers={"X-Test-Profile-Id": p_a},
    )
    assert res_exp_a.status_code == 200
    assert res_exp_a.json()["status"] == "pending"
    assert res_exp_a.json()["is_mutual"] is False

    # 4. Staged-disclosure privacy verification:
    # Ananya sees 'pending'
    res_status_a1 = client.get(f"/interest/{p_a}/status", headers={"X-Test-Profile-Id": p_a})
    st_a1 = next(s for s in res_status_a1.json()["statuses"] if s["candidate_id"] == p_b)
    assert st_a1["status"] == "pending"
    assert st_a1["is_mutual"] is False

    # CRITICAL: Rohan still sees 'none' (zero knowledge leak before mutual expression)
    res_status_b1 = client.get(f"/interest/{p_b}/status", headers={"X-Test-Profile-Id": p_b})
    st_b1 = next(s for s in res_status_b1.json()["statuses"] if s["candidate_id"] == p_a)
    assert st_b1["status"] == "none"
    assert st_b1["is_mutual"] is False

    # 5. Rohan expresses 'pending' interest in Ananya -> Atomic mutual flip!
    res_exp_b = client.post(
        "/interest",
        json={"profile_id": p_b, "target_profile_id": p_a, "action": "pending"},
        headers={"X-Test-Profile-Id": p_b},
    )
    assert res_exp_b.status_code == 200
    assert res_exp_b.json()["status"] == "mutual"
    assert res_exp_b.json()["is_mutual"] is True

    # 6. Both now see 'mutual'
    res_status_a2 = client.get(f"/interest/{p_a}/status", headers={"X-Test-Profile-Id": p_a})
    st_a2 = next(s for s in res_status_a2.json()["statuses"] if s["candidate_id"] == p_b)
    assert st_a2["status"] == "mutual"
    assert st_a2["is_mutual"] is True

    res_status_b2 = client.get(f"/interest/{p_b}/status", headers={"X-Test-Profile-Id": p_b})
    st_b2 = next(s for s in res_status_b2.json()["statuses"] if s["candidate_id"] == p_a)
    assert st_b2["status"] == "mutual"
    assert st_b2["is_mutual"] is True
