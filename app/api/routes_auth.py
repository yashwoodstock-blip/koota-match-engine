"""Authentication and Invite Code verification API routes."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models import Profile, InviteCode
from app.auth.invite import (
    generate_invite_code,
    validate_invite_code,
    consume_invite_code,
    create_invite_session_token,
    verify_invite_token,
)
from app.auth.google_oauth import verify_supabase_jwt, get_or_create_profile_from_google

router = APIRouter(prefix="/auth", tags=["Authentication & Invites"])


class InviteGenerateRequest(BaseModel):
    created_by: str = Field("admin", json_schema_extra={"example": "admin"})
    expires_in_days: int = Field(30, ge=1, le=365)


class InviteRedeemRequest(BaseModel):
    code: str = Field(..., json_schema_extra={"example": "A9K2M4P7"})
    email: Optional[str] = Field(None, json_schema_extra={"example": "user@example.com"})


class InviteRedeemResponse(BaseModel):
    status: str
    message: str
    invite_code: str
    invite_token: str


class AuthSessionResponse(BaseModel):
    authenticated: bool
    email: Optional[str] = None
    name: Optional[str] = None
    profile_id: Optional[str] = None
    invite_code: Optional[str] = None


@router.post("/invite/generate", status_code=201)
async def create_invite(
    req: InviteGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Admin endpoint: Generate a single-use invite code for new cohorts."""
    invite = await generate_invite_code(
        db,
        created_by=req.created_by,
        expires_in_days=req.expires_in_days,
    )
    return {
        "status": "success",
        "code": invite.code,
        "expires_at": invite.expires_at.isoformat(),
        "created_by": invite.created_by,
    }


@router.post("/invite/redeem", response_model=InviteRedeemResponse)
async def redeem_invite(
    req: InviteRedeemRequest,
    db: AsyncSession = Depends(get_db),
):
    """Validate single-use invite code and generate a signed session token.
    
    If email is provided, consumes the code immediately; otherwise validates and issues a 24h token.
    """
    is_valid, msg, invite = await validate_invite_code(db, req.code)
    if not is_valid or not invite:
        raise HTTPException(status_code=400, detail=msg)

    if req.email:
        await consume_invite_code(db, req.code, used_by=req.email)

    invite_token = create_invite_session_token(req.code)
    return InviteRedeemResponse(
        status="valid",
        message="Invite code verified successfully.",
        invite_code=invite.code,
        invite_token=invite_token,
    )


@router.get("/google/callback")
async def google_oauth_callback(
    token: Optional[str] = Query(None, description="Supabase Auth access_token / JWT"),
    invite_token: Optional[str] = Query(None, description="Redeemed invite session token"),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """OAuth callback endpoint: Verifies Supabase Google JWT and creates/retrieves Profile.
    
    Requires a valid redeemed invite token or existing profile.
    """
    raw_jwt = token or (authorization.replace("Bearer ", "") if authorization else "")
    if not raw_jwt:
        raise HTTPException(status_code=401, detail="Missing Google OAuth authorization token.")

    user_info = await verify_supabase_jwt(raw_jwt)
    if not user_info or not user_info.get("email"):
        raise HTTPException(status_code=401, detail="Invalid or expired Google authorization token.")

    email = user_info["email"]
    name = user_info.get("name", email.split("@")[0])

    # Check if profile already exists for this email
    stmt = select(Profile).where(Profile.email == email)
    res = await db.execute(stmt)
    existing_profile = res.scalar_one_or_none()

    if existing_profile:
        return {
            "status": "success",
            "message": "Welcome back.",
            "profile_id": existing_profile.id,
            "email": existing_profile.email,
            "name": existing_profile.name,
            "is_new_user": False,
        }

    # If new user: Invite code is MANDATORY
    validated_code = verify_invite_token(invite_token) if invite_token else None
    if not validated_code:
        raise HTTPException(
            status_code=403,
            detail="Invite-only registration: A valid redeemed invite code is required to sign up.",
        )

    # Consume the invite code with the user's verified Google email
    await consume_invite_code(db, validated_code, used_by=email)

    # Create profile
    profile = await get_or_create_profile_from_google(
        db,
        email=email,
        name=name,
        invite_code=validated_code,
    )

    return {
        "status": "success",
        "message": "Profile created successfully via Google OAuth & Invite.",
        "profile_id": profile.id,
        "email": profile.email,
        "name": profile.name,
        "is_new_user": True,
    }


@router.get("/session", response_model=AuthSessionResponse)
async def get_session(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve session details for authenticated Google user."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header.")

    token = authorization.replace("Bearer ", "").strip()
    user_info = await verify_supabase_jwt(token)
    if not user_info or not user_info.get("email"):
        raise HTTPException(status_code=401, detail="Invalid session token.")

    email = user_info["email"]
    stmt = select(Profile).where(Profile.email == email)
    res = await db.execute(stmt)
    profile = res.scalar_one_or_none()

    return AuthSessionResponse(
        authenticated=True,
        email=email,
        name=profile.name if profile else user_info.get("name"),
        profile_id=profile.id if profile else None,
        invite_code=profile.invite_code if profile else None,
    )
