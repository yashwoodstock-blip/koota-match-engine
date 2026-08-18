"""Comprehensive test suite for On-Demand Match Refresh and Mutual-Consent Compatibility Codes."""
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.models import Profile, Answer, CompatibilityCode, MatchResult, WeeklyMatchList
from app.db.session import async_session
from app.auth.invite import generate_invite_code
from app.scoring.llm_judge import LLMJudgeResult
from app.scoring.nli import NLIResult

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_external_ai_services(monkeypatch):
    """Mock external HuggingFace and Groq LLM API calls for fast, deterministic testing."""
    async def mock_judge(answers_a, answers_b, metadata, *args, **kwargs):
        return {
            41: LLMJudgeResult(
                koota_id=41,
                agreement_score=0.90,
                contradiction=False,
                reasoning="Strong alignment on long-term life vision.",
                key_tensions=[],
            )
        }

    async def mock_nli(text1, text2, *args, **kwargs):
        return NLIResult(
            score=0.85,
            entailment=0.80,
            neutral=0.15,
            contradiction=0.05,
            is_contradiction=False,
        )

    async def mock_emb(text, *args, **kwargs):
        return [0.05] * 384

    monkeypatch.setattr("app.matching.candidates_batch.evaluate_all_top_kootas_llm_judge", mock_judge)
    monkeypatch.setattr("app.matching.candidates_batch.evaluate_nli_pair", mock_nli)
    monkeypatch.setattr("app.api.routes_on_demand.evaluate_all_top_kootas_llm_judge", mock_judge)
    monkeypatch.setattr("app.scoring.semantic.fetch_hf_embedding", mock_emb)


async def create_test_profile(
    name: str = "Test User",
    age: int = 28,
    gender: str = "male",
    religion: str = "Hindu",
    caste: str = "Brahmin",
    caste_preference: str = "no_preference",
    city: str = "Bengaluru",
) -> str:
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


async def populate_minimal_answers(profile_id: str):
    """Populate minimal answers including Koota 41 Life Purpose."""
    async with async_session() as session:
        ans1 = Answer(
            profile_id=profile_id,
            koota_id=1,
            question_index=0,
            question_type="objective",
            raw_value="nuclear_urban",
        )
        ans41_obj = Answer(
            profile_id=profile_id,
            koota_id=41,
            question_index=0,
            question_type="objective",
            raw_value="growth_equal",
        )
        ans41_sub = Answer(
            profile_id=profile_id,
            koota_id=41,
            question_index=0,
            question_type="subjective",
            raw_value="Marriage is an equal growth partnership founded on trust and personal evolution.",
            embedding=[0.05] * 384,
        )
        session.add_all([ans1, ans41_obj, ans41_sub])
        await session.commit()


@pytest.mark.asyncio
async def test_refresh_matches_on_demand_success_and_24h_cooldown():
    """POST /profiles/{id}/refresh-matches executes funnel, updates timestamp, and enforces 24h cooldown."""
    p_id = await create_test_profile(name="Kavya Iyer", age=27, gender="female", religion="Hindu", caste="Iyer")
    c_id = await create_test_profile(name="Rohan Iyer", age=28, gender="male", religion="Hindu", caste="Iyer")
    await populate_minimal_answers(p_id)
    await populate_minimal_answers(c_id)

    # 1. First refresh call should succeed
    res1 = client.post(
        f"/profiles/{p_id}/refresh-matches",
        headers={"X-Test-Profile-Id": p_id},
    )
    assert res1.status_code == 200, f"Refresh failed: {res1.text}"
    data1 = res1.json()
    assert data1["profile_id"] == p_id
    assert "refreshed_at" in data1
    assert "next_eligible_at" in data1
    assert isinstance(data1["matches"], list)

    # 2. Immediate second call should be rate-limited (HTTP 429)
    res2 = client.post(
        f"/profiles/{p_id}/refresh-matches",
        headers={"X-Test-Profile-Id": p_id},
    )
    assert res2.status_code == 429
    data2 = res2.json()["detail"]
    assert data2["error"] == "Rate limit exceeded"
    assert "next_eligible_at" in data2
    assert data2["retry_after_seconds"] > 0
    assert "Retry-After" in res2.headers

    # 3. Verify cooldown reset: simulate last_refreshed_at 25 hours ago
    async with async_session() as session:
        stmt = select(Profile).where(Profile.id == p_id)
        p = (await session.execute(stmt)).scalar_one()
        p.last_refreshed_at = datetime.now(timezone.utc) - timedelta(hours=25)
        await session.commit()

    # Now refresh should succeed again
    res3 = client.post(
        f"/profiles/{p_id}/refresh-matches",
        headers={"X-Test-Profile-Id": p_id},
    )
    assert res3.status_code == 200


@pytest.mark.asyncio
async def test_refresh_matches_ownership_forbidden():
    """POST /profiles/{id}/refresh-matches returns 403 when authenticated as a different profile."""
    p_a = await create_test_profile(name="User A", age=26)
    p_b = await create_test_profile(name="User B", age=28)

    res = client.post(
        f"/profiles/{p_a}/refresh-matches",
        headers={"X-Test-Profile-Id": p_b},
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_generate_compatibility_code_and_weekly_rate_limit():
    """POST /profiles/{id}/compatibility-code generates unguessable 24h code and caps at 5 per week."""
    p_id = await create_test_profile(name="Code Generator", age=29)

    codes = []
    # Generate 5 codes
    for _ in range(5):
        res = client.post(
            f"/profiles/{p_id}/compatibility-code",
            headers={"X-Test-Profile-Id": p_id},
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["code"]) == 7
        assert data["creator_profile_id"] == p_id
        assert "expires_at" in data
        codes.append(data["code"])

    # All generated codes should be unique
    assert len(set(codes)) == 5

    # 6th attempt should hit rate limit (429)
    res_overflow = client.post(
        f"/profiles/{p_id}/compatibility-code",
        headers={"X-Test-Profile-Id": p_id},
    )
    assert res_overflow.status_code == 429
    assert res_overflow.json()["detail"]["error"] == "Rate limit exceeded"


@pytest.mark.asyncio
async def test_redeem_compatibility_code_success():
    """POST /profiles/{id}/compatibility-check runs pairwise match and records result."""
    creator_id = await create_test_profile(name="Meera Sen", age=27, religion="Hindu")
    redeemer_id = await create_test_profile(name="Dev Malhotra", age=28, religion="Hindu")
    await populate_minimal_answers(creator_id)
    await populate_minimal_answers(redeemer_id)

    # 1. Creator generates code
    res_code = client.post(
        f"/profiles/{creator_id}/compatibility-code",
        headers={"X-Test-Profile-Id": creator_id},
    )
    assert res_code.status_code == 200
    code = res_code.json()["code"]

    # 2. Redeemer redeems code
    res_check = client.post(
        f"/profiles/{redeemer_id}/compatibility-check",
        json={"code": code},
        headers={"X-Test-Profile-Id": redeemer_id},
    )
    assert res_check.status_code == 200
    result = res_check.json()
    assert result["creator_profile_id"] == creator_id
    assert result["redeemer_profile_id"] == redeemer_id
    assert result["is_viable"] is True
    assert result["tier"] in ["strong match", "compatible with flagged friction points", "not viable"]
    assert "calculated_at" in result

    # 3. Verify code is now marked used in DB
    async with async_session() as session:
        stmt = select(CompatibilityCode).where(CompatibilityCode.code == code)
        comp = (await session.execute(stmt)).scalar_one()
        assert comp.is_used is True
        assert comp.used_by_profile_id == redeemer_id
        assert comp.used_at is not None

        # Verify MatchResult was recorded
        stmt_m = select(MatchResult).where(
            MatchResult.profile_a_id == creator_id,
            MatchResult.profile_b_id == redeemer_id,
        )
        match_rec = (await session.execute(stmt_m)).scalar_one_or_none()
        assert match_rec is not None


@pytest.mark.asyncio
async def test_redeem_compatibility_code_self_redemption_error():
    """POST /profiles/{id}/compatibility-check fails with 400 when attempting to redeem one's own code."""
    p_id = await create_test_profile(name="Self Matcher", age=30)

    res_code = client.post(
        f"/profiles/{p_id}/compatibility-code",
        headers={"X-Test-Profile-Id": p_id},
    )
    code = res_code.json()["code"]

    res_self = client.post(
        f"/profiles/{p_id}/compatibility-check",
        json={"code": code},
        headers={"X-Test-Profile-Id": p_id},
    )
    assert res_self.status_code == 400
    assert "Cannot redeem your own" in res_self.json()["detail"]


@pytest.mark.asyncio
async def test_redeem_compatibility_code_already_used_error():
    """POST /profiles/{id}/compatibility-check returns 410 if code has already been redeemed."""
    creator_id = await create_test_profile(name="Creator 1", age=26)
    redeemer1_id = await create_test_profile(name="Redeemer 1", age=27)
    redeemer2_id = await create_test_profile(name="Redeemer 2", age=28)
    await populate_minimal_answers(creator_id)
    await populate_minimal_answers(redeemer1_id)
    await populate_minimal_answers(redeemer2_id)

    # 1. Create code
    res_code = client.post(
        f"/profiles/{creator_id}/compatibility-code",
        headers={"X-Test-Profile-Id": creator_id},
    )
    code = res_code.json()["code"]

    # 2. First redemption succeeds
    res1 = client.post(
        f"/profiles/{redeemer1_id}/compatibility-check",
        json={"code": code},
        headers={"X-Test-Profile-Id": redeemer1_id},
    )
    assert res1.status_code == 200

    # 3. Second redemption fails with 410 Gone
    res2 = client.post(
        f"/profiles/{redeemer2_id}/compatibility-check",
        json={"code": code},
        headers={"X-Test-Profile-Id": redeemer2_id},
    )
    assert res2.status_code == 410
    assert "already been redeemed" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_redeem_compatibility_code_expired_error():
    """POST /profiles/{id}/compatibility-check returns 410 if code has expired."""
    creator_id = await create_test_profile(name="Creator Expired", age=26)
    redeemer_id = await create_test_profile(name="Redeemer Expired", age=27)
    await populate_minimal_answers(creator_id)
    await populate_minimal_answers(redeemer_id)

    # 1. Create code
    res_code = client.post(
        f"/profiles/{creator_id}/compatibility-code",
        headers={"X-Test-Profile-Id": creator_id},
    )
    code = res_code.json()["code"]

    # 2. Manually set expiry to in the past
    async with async_session() as session:
        stmt = select(CompatibilityCode).where(CompatibilityCode.code == code)
        comp = (await session.execute(stmt)).scalar_one()
        comp.expires_at = datetime.now(timezone.utc) - timedelta(hours=2)
        await session.commit()

    # 3. Attempt redemption
    res = client.post(
        f"/profiles/{redeemer_id}/compatibility-check",
        json={"code": code},
        headers={"X-Test-Profile-Id": redeemer_id},
    )
    assert res.status_code == 410
    assert "expired" in res.json()["detail"]


@pytest.mark.asyncio
async def test_compatibility_check_strictly_enforces_hard_filters():
    """Mutual consent compatibility check does not bypass religion or age gap hard filters."""
    creator_id = await create_test_profile(name="Hindu Creator", age=26, religion="Hindu")
    diff_religion_id = await create_test_profile(name="Jain Redeemer", age=27, religion="Jain")
    await populate_minimal_answers(creator_id)
    await populate_minimal_answers(diff_religion_id)

    res_code = client.post(
        f"/profiles/{creator_id}/compatibility-code",
        headers={"X-Test-Profile-Id": creator_id},
    )
    code = res_code.json()["code"]

    res_check = client.post(
        f"/profiles/{diff_religion_id}/compatibility-check",
        json={"code": code},
        headers={"X-Test-Profile-Id": diff_religion_id},
    )
    assert res_check.status_code == 200
    data = res_check.json()
    assert data["is_viable"] is False
    assert data["tier"] == "not viable"
    assert "Religion mismatch" in (data["hard_filter_reason"] or "")
