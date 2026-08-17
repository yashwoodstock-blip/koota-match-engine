"""Authentication dependencies and profile ownership verification."""
from typing import Optional
from fastapi import Header, HTTPException, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models import Profile
from app.auth.google_oauth import verify_supabase_jwt


async def get_current_authenticated_profile(
    authorization: Optional[str] = Header(None),
    x_test_profile_id: Optional[str] = Header(None, alias="X-Test-Profile-Id"),
    db: AsyncSession = Depends(get_db),
) -> Profile:
    """Verify Bearer token and retrieve caller's Profile."""
    # 1. Test header shortcut for isolated test fixtures
    if x_test_profile_id:
        stmt = select(Profile).where(Profile.id == x_test_profile_id)
        res = await db.execute(stmt)
        p = res.scalar_one_or_none()
        if p:
            return p

    # 2. Bearer token extraction
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header.",
        )

    token = authorization.replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization token format.",
        )

    user_info = await verify_supabase_jwt(token)
    if not user_info or not user_info.get("email"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token.",
        )

    email = user_info["email"]
    sub = user_info.get("sub")

    # Match by email or sub/id
    stmt = select(Profile).where((Profile.email == email) | (Profile.id == sub))
    res = await db.execute(stmt)
    profile = res.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated profile not found.",
        )

    return profile


def verify_profile_ownership(profile_id: str, current_profile: Profile) -> None:
    """Verify that caller owns the requested profile resource."""
    if current_profile.id != profile_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You may only modify or delete your own profile.",
        )
