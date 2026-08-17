"""Unit and integration tests for Phase 6 Invite-only Auth and Google OAuth."""
import pytest
import secrets
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.db.session import async_session
from app.models import InviteCode, Profile
from app.auth.invite import (
    generate_invite_code,
    validate_invite_code,
    consume_invite_code,
    create_invite_session_token,
    verify_invite_token,
)
from app.auth.google_oauth import get_or_create_profile_from_google


@pytest.mark.asyncio
async def test_invite_code_lifecycle_single_use():
    """An invite code succeeds once, cannot be reused, and marks consumed correctly."""
    async with async_session() as session:
        # 1. Generate code
        invite = await generate_invite_code(session, created_by="test-admin", expires_in_days=7)
        assert len(invite.code) == 8
        assert invite.used_by is None

        # 2. Validate unconsumed code
        is_valid, msg, obj = await validate_invite_code(session, invite.code)
        assert is_valid is True
        assert "valid" in msg.lower()

        # 3. Consume code
        success, consume_msg = await consume_invite_code(session, invite.code, used_by="aarav@example.com")
        assert success is True

        # 4. Attempt reuse -> must fail
        is_valid_again, reuse_msg, _ = await validate_invite_code(session, invite.code)
        assert is_valid_again is False
        assert "already been used" in reuse_msg.lower()

        # 5. Attempt second consumption -> must fail
        consume_again, _ = await consume_invite_code(session, invite.code, used_by="another@example.com")
        assert consume_again is False


@pytest.mark.asyncio
async def test_expired_invite_code_fails():
    """An expired invite code fails validation."""
    async with async_session() as session:
        expired_code = f"EXP_{secrets.token_hex(2).upper()}"
        expired_time = datetime.now(timezone.utc) - timedelta(days=2)
        expired_invite = InviteCode(
            code=expired_code,
            created_by="admin",
            used_by=None,
            used_at=None,
            expires_at=expired_time,
        )
        session.add(expired_invite)
        await session.commit()

        is_valid, msg, _ = await validate_invite_code(session, expired_code)
        assert is_valid is False
        assert "expired" in msg.lower()


@pytest.mark.asyncio
async def test_invite_session_token_signing():
    """Signed invite session token validates correctly and detects tampering."""
    code = "INVITE88"
    token = create_invite_session_token(code, valid_hours=2)

    # Valid token verification
    verified_code = verify_invite_token(token)
    assert verified_code == code

    # Tampered token verification
    tampered = token[:-4] + "abcd"
    assert verify_invite_token(tampered) is None

    # Garbage token
    assert verify_invite_token("invalid:token") is None


@pytest.mark.asyncio
async def test_google_oauth_creates_one_profile_per_email():
    """Google OAuth creates exactly one Profile per unique email upon multiple logins."""
    async with async_session() as session:
        email = "priya.sharma@gmail.com"
        name = "Priya Sharma"

        # First login -> creates profile
        p1 = await get_or_create_profile_from_google(session, email, name, invite_code="INVITE01")
        assert p1.id is not None
        assert p1.email == email
        assert p1.name == name

        # Second login with same email -> returns identical profile
        p2 = await get_or_create_profile_from_google(session, email, name, invite_code="INVITE01")
        assert p2.id == p1.id

        # Verify database count is exactly 1
        stmt = select(Profile).where(Profile.email == email)
        res = await session.execute(stmt)
        profiles = res.scalars().all()
        assert len(profiles) == 1


def test_api_invite_only_gate_enforcement():
    """API returns 403 on signup without invite code, and 201 when valid code is provided."""
    with TestClient(app) as client:
        # 1. Attempt profile creation without invite -> MUST return 403
        payload_no_invite = {
            "name": "Unauthorized User",
            "age": 27,
            "gender": "female",
            "religion": "Hindu",
            "caste": "Brahmin",
            "city": "Delhi",
        }
        res_fail = client.post("/profiles", json=payload_no_invite)
        assert res_fail.status_code == 403
        assert "invite" in res_fail.json()["detail"].lower()

        # 2. Generate invite code via API
        gen_res = client.post("/auth/invite/generate", json={"created_by": "test-admin", "expires_in_days": 10})
        assert gen_res.status_code == 201
        invite_code = gen_res.json()["code"]

        # 3. Redeem invite code
        redeem_res = client.post("/auth/invite/redeem", json={"code": invite_code})
        assert redeem_res.status_code == 200
        invite_token = redeem_res.json()["invite_token"]

        # 4. Create profile with invite_token -> SUCCESS 201
        payload_valid = {
            "name": "Authorized User",
            "age": 27,
            "gender": "female",
            "religion": "Hindu",
            "caste": "Brahmin",
            "city": "Delhi",
            "invite_token": invite_token,
        }
        res_ok = client.post("/profiles", json=payload_valid)
        assert res_ok.status_code == 201
        assert res_ok.json()["name"] == "Authorized User"
