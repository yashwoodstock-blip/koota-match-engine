"""Invite-only authorization and single-use code verification engine."""
import hmac
import hashlib
import os
import secrets
import string
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import InviteCode, utc_now

INVITE_SECRET = os.getenv("INVITE_SECRET", "koota-invite-session-secret-key-2026")


def generate_random_code(length: int = 8) -> str:
    """Generate a clean, unambiguous 8-character uppercase alphanumeric code."""
    # Exclude ambiguous characters like 0, O, 1, I
    alphabet = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def generate_invite_code(
    db: AsyncSession,
    created_by: str = "admin",
    expires_in_days: int = 30,
) -> InviteCode:
    """Generate and persist a new single-use invite code."""
    for _ in range(10):
        code_str = generate_random_code(8)
        # Check uniqueness
        stmt = select(InviteCode).where(InviteCode.code == code_str)
        res = await db.execute(stmt)
        if res.scalar_one_or_none() is None:
            break
    else:
        code_str = secrets.token_hex(4).upper()

    expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
    invite = InviteCode(
        code=code_str,
        created_by=created_by,
        used_by=None,
        used_at=None,
        expires_at=expires_at,
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    return invite


async def validate_invite_code(
    db: AsyncSession,
    code: str,
) -> Tuple[bool, str, Optional[InviteCode]]:
    """Validate whether an invite code exists, is unconsumed, and not expired."""
    clean_code = (code or "").strip().upper()
    if not clean_code:
        return False, "Invite code cannot be empty.", None

    stmt = select(InviteCode).where(InviteCode.code == clean_code)
    res = await db.execute(stmt)
    invite = res.scalar_one_or_none()

    if not invite:
        return False, "Invalid invite code.", None

    if invite.used_by is not None:
        return False, "Invite code has already been used.", invite

    # Handle timezone-aware/naive comparisons safely
    now = datetime.now(timezone.utc)
    expires_at = invite.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if now > expires_at:
        return False, "Invite code has expired.", invite

    return True, "Invite code is valid.", invite


async def consume_invite_code(
    db: AsyncSession,
    code: str,
    used_by: str,
) -> Tuple[bool, str]:
    """Atomically consume an invite code for a specific user/email."""
    is_valid, msg, invite = await validate_invite_code(db, code)
    if not is_valid or not invite:
        return False, msg

    invite.used_by = used_by
    invite.used_at = utc_now()
    await db.commit()
    await db.refresh(invite)
    return True, "Invite code consumed successfully."


def create_invite_session_token(code: str, valid_hours: int = 24) -> str:
    """Create a signed session-ready token certifying an invite code was redeemed."""
    clean_code = code.strip().upper()
    exp = int(time.time()) + (valid_hours * 3600)
    payload = f"{clean_code}:{exp}"
    signature = hmac.new(
        INVITE_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload}:{signature}"


def verify_invite_token(token: str) -> Optional[str]:
    """Verify signed invite session token and return the validated code."""
    if not token:
        return None
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return None
        code, exp_str, sig = parts
        exp = int(exp_str)
        if time.time() > exp:
            return None

        payload = f"{code}:{exp}"
        expected_sig = hmac.new(
            INVITE_SECRET.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if hmac.compare_digest(sig, expected_sig):
            return code
        return None
    except Exception:
        return None
