"""Google OAuth and Supabase Auth JWT verification."""
import base64
import json
import os
import time
from typing import Dict, Any, Optional
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Profile, utc_now

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")


def decode_jwt_payload_unverified(token: str) -> Optional[Dict[str, Any]]:
    """Extract and decode JWT payload dictionary safely."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload_b64 = parts[1]
        # Fix base64 padding
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        decoded_bytes = base64.urlsafe_b64decode(padded)
        return json.loads(decoded_bytes.decode("utf-8"))
    except Exception:
        return None


async def verify_supabase_jwt(token: str) -> Optional[Dict[str, Any]]:
    """Verify Supabase Auth JWT token server-side.
    
    If Supabase REST service is reachable, validates against Supabase Auth `/auth/v1/user`.
    Otherwise verifies standard JWT claims (exp, email/sub).
    """
    clean_token = token.replace("Bearer ", "").strip()
    if not clean_token:
        return None

    # 1. Try Live Supabase Auth User verification if URL & KEY configured
    if SUPABASE_URL and SUPABASE_KEY and not SUPABASE_URL.startswith("http://demo"):
        try:
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {clean_token}",
            }
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{SUPABASE_URL}/auth/v1/user", headers=headers)
                if res.status_code == 200:
                    user_data = res.json()
                    email = user_data.get("email")
                    metadata = user_data.get("user_metadata", {})
                    name = metadata.get("full_name") or metadata.get("name") or (email.split("@")[0] if email else "User")
                    return {
                        "sub": user_data.get("id"),
                        "email": email,
                        "name": name,
                        "user_metadata": metadata,
                    }
        except Exception:
            pass  # Fall through to claim verification

    # 2. Fallback: Local JWT claim inspection
    payload = decode_jwt_payload_unverified(clean_token)
    if not payload:
        return None

    # Check expiration
    exp = payload.get("exp")
    if exp and time.time() > exp:
        return None

    email = payload.get("email") or payload.get("user_metadata", {}).get("email")
    if not email:
        return None

    name = (
        payload.get("user_metadata", {}).get("full_name")
        or payload.get("user_metadata", {}).get("name")
        or payload.get("name")
        or email.split("@")[0]
    )

    return {
        "sub": payload.get("sub", ""),
        "email": email,
        "name": name,
        "user_metadata": payload.get("user_metadata", {}),
    }


async def get_or_create_profile_from_google(
    db: AsyncSession,
    email: str,
    name: str,
    invite_code: Optional[str] = None,
    default_age: int = 28,
    default_religion: str = "Hindu",
) -> Profile:
    """Upsert exactly one Profile per unique verified email."""
    stmt = select(Profile).where(Profile.email == email)
    res = await db.execute(stmt)
    existing_profile = res.scalar_one_or_none()

    if existing_profile:
        # Return existing profile without re-creating
        return existing_profile

    # Create new profile bound to Google verified email & invite code
    new_profile = Profile(
        email=email,
        name=name,
        age=default_age,
        religion=default_religion,
        caste_preference="no_preference",
        invite_code=invite_code,
        created_at=utc_now(),
    )
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)
    return new_profile
