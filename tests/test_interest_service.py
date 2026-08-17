"""Tests for mutual-interest confirmation service, atomic flips, and decline logic."""
import pytest
from sqlalchemy import select, delete
from fastapi import HTTPException

from app.db.session import async_session
from app.models import Profile, WeeklyMatchList, Interest
from app.interest.interest_service import express_interest, get_interest_status_for_profile


async def setup_sample_profiles_and_matches():
    """Seed test profiles and weekly match list."""
    async with async_session() as db:
        await db.execute(delete(Interest).where(Interest.profile_id.in_(["test-prof-01", "test-prof-02", "test-prof-03"])))
        await db.execute(delete(WeeklyMatchList).where(WeeklyMatchList.profile_id.in_(["test-prof-01", "test-prof-02", "test-prof-03"])))
        await db.execute(delete(Profile).where(Profile.id.in_(["test-prof-01", "test-prof-02", "test-prof-03"])))

        p1 = Profile(
            id="test-prof-01",
            name="Aarav Sharma",
            age=28,
            gender="male",
            religion="Hindu",
            caste="Brahmin",
            caste_preference="no_preference",
            city="Bengaluru",
        )
        p2 = Profile(
            id="test-prof-02",
            name="Ananya Iyer",
            age=27,
            gender="female",
            religion="Hindu",
            caste="Brahmin",
            caste_preference="no_preference",
            city="Bengaluru",
        )
        p3 = Profile(
            id="test-prof-03",
            name="Pooja Gupta",
            age=26,
            gender="female",
            religion="Hindu",
            caste="Bania",
            caste_preference="no_preference",
            city="Delhi",
        )
        db.add_all([p1, p2, p3])
        await db.flush()

        w1 = WeeklyMatchList(
            profile_id=p1.id,
            candidate_id=p2.id,
            score=0.91,
            tier="strong match",
            alignment_points=["Philosophy"],
            friction_points=[],
            contradiction_gates=[],
        )
        w2 = WeeklyMatchList(
            profile_id=p2.id,
            candidate_id=p1.id,
            score=0.91,
            tier="strong match",
            alignment_points=["Philosophy"],
            friction_points=[],
            contradiction_gates=[],
        )
        db.add_all([w1, w2])
        await db.commit()
    return "test-prof-01", "test-prof-02", "test-prof-03"


@pytest.mark.asyncio
async def test_express_interest_one_sided_stays_pending():
    p1, p2, _ = await setup_sample_profiles_and_matches()

    async with async_session() as db:
        res = await express_interest(db, profile_id=p1, target_profile_id=p2, action="pending")
        assert res["status"] == "pending"
        assert res["is_mutual"] is False

        # Check DB state
        stmt = select(Interest).where(Interest.profile_id == p1, Interest.target_profile_id == p2)
        r = await db.execute(stmt)
        row = r.scalar_one_or_none()
        assert row is not None
        assert row.status == "pending"


@pytest.mark.asyncio
async def test_express_interest_second_party_flips_both_to_mutual_atomically():
    p1, p2, _ = await setup_sample_profiles_and_matches()

    # 1. P1 expresses interest -> pending
    async with async_session() as db:
        res1 = await express_interest(db, profile_id=p1, target_profile_id=p2, action="pending")
        assert res1["status"] == "pending"
        assert res1["is_mutual"] is False

    # 2. P2 expresses interest -> both become mutual atomically
    async with async_session() as db:
        res2 = await express_interest(db, profile_id=p2, target_profile_id=p1, action="pending")
        assert res2["status"] == "mutual"
        assert res2["is_mutual"] is True

        # 3. Verify DB shows BOTH rows as mutual
        stmt1 = select(Interest).where(Interest.profile_id == p1, Interest.target_profile_id == p2)
        r1 = await db.execute(stmt1)
        row1 = r1.scalar_one()
        assert row1.status == "mutual"

        stmt2 = select(Interest).where(Interest.profile_id == p2, Interest.target_profile_id == p1)
        r2 = await db.execute(stmt2)
        row2 = r2.scalar_one()
        assert row2.status == "mutual"


@pytest.mark.asyncio
async def test_express_interest_idempotent_reexpression():
    p1, p2, _ = await setup_sample_profiles_and_matches()

    async with async_session() as db:
        # Express once
        res1 = await express_interest(db, profile_id=p1, target_profile_id=p2, action="pending")
        assert res1["status"] == "pending"

        # Express again (idempotent upsert)
        res2 = await express_interest(db, profile_id=p1, target_profile_id=p2, action="pending")
        assert res2["status"] == "pending"

        # Confirm exactly 1 row exists
        stmt = select(Interest).where(Interest.profile_id == p1, Interest.target_profile_id == p2)
        r = await db.execute(stmt)
        rows = r.scalars().all()
        assert len(rows) == 1


@pytest.mark.asyncio
async def test_express_interest_rejected_if_target_not_in_weekly_matches():
    p1, _, p3 = await setup_sample_profiles_and_matches()

    async with async_session() as db:
        # P1 tries to express interest in P3 who is NOT in P1's weekly matches
        with pytest.raises(HTTPException) as exc_info:
            await express_interest(db, profile_id=p1, target_profile_id=p3, action="pending")

        assert exc_info.value.status_code == 400
        assert "not in the caller's weekly matches" in exc_info.value.detail


@pytest.mark.asyncio
async def test_express_interest_declined_before_other_acts():
    p1, p2, _ = await setup_sample_profiles_and_matches()

    async with async_session() as db:
        res = await express_interest(db, profile_id=p1, target_profile_id=p2, action="declined")
        assert res["status"] == "declined"
        assert res["is_mutual"] is False


@pytest.mark.asyncio
async def test_express_interest_declined_after_pending_never_becomes_mutual():
    p1, p2, _ = await setup_sample_profiles_and_matches()

    async with async_session() as db:
        # P1 expresses pending
        await express_interest(db, profile_id=p1, target_profile_id=p2, action="pending")

        # P2 declines
        res2 = await express_interest(db, profile_id=p2, target_profile_id=p1, action="declined")
        assert res2["status"] == "declined"
        assert res2["is_mutual"] is False

        # P1 expresses pending again -> target is declined so does NOT become mutual
        res1_re = await express_interest(db, profile_id=p1, target_profile_id=p2, action="pending")
        assert res1_re["status"] == "pending"
        assert res1_re["is_mutual"] is False


@pytest.mark.asyncio
async def test_staged_disclosure_one_sided_pending_is_hidden_from_other_party():
    p1, p2, _ = await setup_sample_profiles_and_matches()

    async with async_session() as db:
        # P1 expresses pending interest
        await express_interest(db, profile_id=p1, target_profile_id=p2, action="pending")

        # P1 views status -> sees "pending"
        status_p1 = await get_interest_status_for_profile(db, profile_id=p1)
        assert len(status_p1) == 1
        assert status_p1[0]["candidate_id"] == p2
        assert status_p1[0]["status"] == "pending"
        assert status_p1[0]["is_mutual"] is False

        # P2 views status -> sees "none", P1's pending is COMPLETELY HIDDEN
        status_p2 = await get_interest_status_for_profile(db, profile_id=p2)
        assert len(status_p2) == 1
        assert status_p2[0]["candidate_id"] == p1
        assert status_p2[0]["status"] == "none"
        assert status_p2[0]["is_mutual"] is False
