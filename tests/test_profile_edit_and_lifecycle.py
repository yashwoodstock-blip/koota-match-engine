"""Comprehensive test suite for profile editing, answer upserts, stale match invalidation, and DPDP cascade deletion."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.models import (
    Profile,
    Answer,
    FollowingList,
    Interest,
    MatchResult,
    WeeklyMatchList,
)
from app.db.session import async_session
from app.auth.invite import generate_invite_code

client = TestClient(app)


async def create_test_profile(name="Test User", age=28, gender="male", religion="Hindu", caste="Brahmin", caste_preference="no_preference", city="Bengaluru") -> str:
    async with async_session() as session:
        invite = await generate_invite_code(session, created_by="test-admin", expires_in_days=7)
        code = invite.code

    res = client.post(
        "/profiles",
        json={
            "name": name,
            "age": age,
            "gender": gender,
            "religion": religion,
            "caste": caste,
            "caste_preference": caste_preference,
            "city": city,
            "invite_code": code,
        },
    )
    assert res.status_code == 201, f"Failed to create profile: {res.text}"
    return res.json()["id"]


@pytest.mark.asyncio
async def test_partial_patch_profile():
    """PATCH /profiles/{id} allows partial updates and updates timestamp."""
    # 1. Create Profile
    profile_id = await create_test_profile(name="Arjun Singhania", age=28, city="Bengaluru")

    # 2. Patch only age and city using X-Test-Profile-Id
    res_patch = client.patch(
        f"/profiles/{profile_id}",
        json={"age": 29, "city": "Mumbai"},
        headers={"X-Test-Profile-Id": profile_id},
    )
    assert res_patch.status_code == 200
    data = res_patch.json()
    assert data["age"] == 29
    assert data["city"] == "Mumbai"
    assert data["name"] == "Arjun Singhania"
    assert data["religion"] == "Hindu"
    assert data["stale_matches_invalidated"] is True
    assert data["hard_filter_changed"] is False
    assert data["warning"] is None


@pytest.mark.asyncio
async def test_patch_profile_auth_gates():
    """PATCH /profiles/{id} returns 401 without auth and 403 on mismatched user ID."""
    # 1. Create two profiles
    id_a = await create_test_profile(name="User Alpha", age=27)
    id_b = await create_test_profile(name="User Beta", age=30)

    # 2. Try without any auth -> 401
    res_unauth = client.patch(f"/profiles/{id_a}", json={"age": 28})
    assert res_unauth.status_code == 401

    # 3. User B tries to update User A -> 403 Forbidden
    res_forbid = client.patch(
        f"/profiles/{id_a}",
        json={"age": 28},
        headers={"X-Test-Profile-Id": id_b},
    )
    assert res_forbid.status_code == 403
    assert "You may only modify or delete your own profile" in res_forbid.json()["detail"]


@pytest.mark.asyncio
async def test_patch_hard_filter_alteration_warning():
    """Changing religion or caste_preference to same_caste_required returns an explicit warning."""
    # 1. Create Profile
    profile_id = await create_test_profile(name="Priya Nair", religion="Hindu", caste="Nair", caste_preference="no_preference")

    # 2. Change religion -> returns warning
    res_rel = client.patch(
        f"/profiles/{profile_id}",
        json={"religion": "Jain"},
        headers={"X-Test-Profile-Id": profile_id},
    )
    assert res_rel.status_code == 200
    assert res_rel.json()["hard_filter_changed"] is True
    assert "resets your active candidate pool" in res_rel.json()["warning"]

    # 3. Change caste_preference to same_caste_required -> returns warning
    res_caste = client.patch(
        f"/profiles/{profile_id}",
        json={"caste_preference": "same_caste_required"},
        headers={"X-Test-Profile-Id": profile_id},
    )
    assert res_caste.status_code == 200
    assert res_caste.json()["hard_filter_changed"] is True
    assert "resets your active candidate pool" in res_caste.json()["warning"]


@pytest.mark.asyncio
async def test_answer_upsert_and_embedding_update():
    """POST /profiles/{id}/answers cleanly upserts without IntegrityError and updates values."""
    # 1. Create Profile
    profile_id = await create_test_profile(name="Vikram Patel", age=31)

    # 2. Initial answer submission
    payload_initial = {
        "answers": [
            {
                "koota_id": 1,
                "question_index": 0,
                "question_type": "objective",
                "raw_value": "living with parents",
            },
            {
                "koota_id": 1,
                "question_index": 0,
                "question_type": "subjective",
                "raw_value": "I value family harmony and close-knit living.",
            },
        ]
    }
    res_ans1 = client.post(f"/profiles/{profile_id}/answers", json=payload_initial)
    assert res_ans1.status_code == 200
    assert res_ans1.json()["submitted_answers_count"] == 2
    assert res_ans1.json()["stale_matches_invalidated"] is True

    # 3. Resubmit updated answers for the same koota & question indices
    payload_updated = {
        "answers": [
            {
                "koota_id": 1,
                "question_index": 0,
                "question_type": "objective",
                "raw_value": "independent nuclear apartment",
            },
            {
                "koota_id": 1,
                "question_index": 0,
                "question_type": "subjective",
                "raw_value": "We prefer living independently in the same city for personal space.",
            },
        ]
    }
    res_ans2 = client.post(f"/profiles/{profile_id}/answers", json=payload_updated)
    assert res_ans2.status_code == 200
    assert res_ans2.json()["submitted_answers_count"] == 2

    # 4. Verify in DB that only 2 total answers exist (no duplicates) and values are updated
    async with async_session() as session:
        ans_rows = await session.execute(select(Answer).where(Answer.profile_id == profile_id))
        answers = ans_rows.scalars().all()
        assert len(answers) == 2
        raw_vals = [a.raw_value for a in answers]
        assert "independent nuclear apartment" in raw_vals
        assert "We prefer living independently in the same city for personal space." in raw_vals


@pytest.mark.asyncio
async def test_stale_match_invalidation_purges_precomputed_matches():
    """Editing profile or answers purges existing WeeklyMatchList and MatchResult caches."""
    # 1. Create Profiles A & B
    id_a = await create_test_profile(name="Kavita", age=27)
    id_b = await create_test_profile(name="Rohan", age=29)

    # 2. Insert mock weekly match list and match result directly
    async with async_session() as session:
        match_res = MatchResult(
            profile_a_id=id_a,
            profile_b_id=id_b,
            is_viable=True,
            overall_score=0.88,
            tier="strong match",
        )
        weekly_m = WeeklyMatchList(
            profile_id=id_a,
            candidate_id=id_b,
            score=0.88,
            tier="strong match",
        )
        session.add_all([match_res, weekly_m])
        await session.commit()

        # Verify rows exist
        w_stmt = select(WeeklyMatchList).where(WeeklyMatchList.profile_id == id_a)
        res = await session.execute(w_stmt)
        assert len(res.scalars().all()) == 1

    # 3. Patch Profile A
    res_patch = client.patch(
        f"/profiles/{id_a}",
        json={"city": "Hyderabad"},
        headers={"X-Test-Profile-Id": id_a},
    )
    assert res_patch.status_code == 200

    # 4. Verify WeeklyMatchList and MatchResult have been purged
    async with async_session() as session:
        w_res = await session.execute(select(WeeklyMatchList).where(WeeklyMatchList.profile_id == id_a))
        assert len(w_res.scalars().all()) == 0

        m_res = await session.execute(select(MatchResult).where(MatchResult.profile_a_id == id_a))
        assert len(m_res.scalars().all()) == 0


@pytest.mark.asyncio
async def test_cascade_delete_profile_zero_orphans():
    """DELETE /profiles/{id} permanently removes profile and all associated data with zero orphans."""
    # 1. Create Profiles
    id_a = await create_test_profile(name="Dev", age=28)
    id_b = await create_test_profile(name="Mira", age=27)

    # 2. Add answer, following list, interest, match result, and weekly match list
    async with async_session() as session:
        ans = Answer(
            profile_id=id_a,
            koota_id=1,
            question_index=0,
            question_type="objective",
            raw_value="nuclear",
        )
        fol = FollowingList(
            profile_id=id_a,
            usernames=["nature_org", "tech_insider"],
            opted_in=True,
        )
        intr = Interest(
            profile_id=id_a,
            target_profile_id=id_b,
            status="pending",
        )
        mr = MatchResult(
            profile_a_id=id_a,
            profile_b_id=id_b,
            is_viable=True,
            tier="strong match",
            overall_score=0.85,
        )
        wml = WeeklyMatchList(
            profile_id=id_a,
            candidate_id=id_b,
            score=0.85,
            tier="strong match",
        )
        session.add_all([ans, fol, intr, mr, wml])
        await session.commit()

    # 3. Call DELETE /profiles/{id_a}
    res_del = client.delete(f"/profiles/{id_a}", headers={"X-Test-Profile-Id": id_a})
    assert res_del.status_code == 200
    assert res_del.json()["status"] == "success"
    assert res_del.json()["deleted_profile_id"] == id_a

    # 4. Verify ZERO orphaned rows across all tables for id_a
    async with async_session() as session:
        p = await session.execute(select(Profile).where(Profile.id == id_a))
        assert p.scalar_one_or_none() is None

        a = await session.execute(select(Answer).where(Answer.profile_id == id_a))
        assert len(a.scalars().all()) == 0

        f = await session.execute(select(FollowingList).where(FollowingList.profile_id == id_a))
        assert len(f.scalars().all()) == 0

        i = await session.execute(select(Interest).where((Interest.profile_id == id_a) | (Interest.target_profile_id == id_a)))
        assert len(i.scalars().all()) == 0

        m = await session.execute(select(MatchResult).where((MatchResult.profile_a_id == id_a) | (MatchResult.profile_b_id == id_a)))
        assert len(m.scalars().all()) == 0

        w = await session.execute(select(WeeklyMatchList).where((WeeklyMatchList.profile_id == id_a) | (WeeklyMatchList.candidate_id == id_a)))
        assert len(w.scalars().all()) == 0
