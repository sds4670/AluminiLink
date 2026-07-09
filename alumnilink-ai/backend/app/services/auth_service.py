from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.config import settings
from app.models.user import User, UserRole, UserStatus, VerificationStatus
from app.models.allowed_student import AllowedStudent
from app.models.allowed_alumni import AllowedAlumni
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, AccessTokenResponse


def _issue_tokens(user: User) -> tuple[str, str]:
    claims = {"sub": str(user.id), "role": user.role.value}
    access_token = create_access_token(claims)
    refresh_token = create_refresh_token(claims)
    return access_token, refresh_token


async def register_user(data: RegisterRequest, db: AsyncSession) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    if data.role == UserRole.student:
        whitelist_result = await db.execute(
            select(AllowedStudent).where(AllowedStudent.roll_number == data.roll_number)
        )
        allowed = whitelist_result.scalar_one_or_none()
        if allowed is None:
            raise HTTPException(status_code=403, detail="Roll number not found on the student whitelist")
        if allowed.is_registered:
            raise HTTPException(status_code=409, detail="Roll number has already been registered")
        verification_status = VerificationStatus.verified  # students need no admin gate
    else:  # UserRole.alumni (admin is rejected by the request schema)
        whitelist_result = await db.execute(
            select(AllowedAlumni).where(AllowedAlumni.register_number == data.register_number)
        )
        allowed = whitelist_result.scalar_one_or_none()
        if allowed is None:
            raise HTTPException(status_code=403, detail="Register number not found on the alumni whitelist")
        if allowed.is_registered:
            raise HTTPException(status_code=409, detail="Register number has already been registered")
        # Alumni can log in immediately; an admin must separately verify them
        # before they can create a profile or list availability (Module 2/9).
        verification_status = VerificationStatus.pending

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
        status=UserStatus.active,
        verification_status=verification_status,
        roll_number=data.roll_number if data.role == UserRole.student else None,
        register_number=data.register_number if data.role == UserRole.alumni else None,
    )
    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        # The whitelist check above can go stale under concurrent requests or
        # manual data edits; never let a raw DB constraint violation surface
        # as an unhandled 500 (which also strips CORS headers on the response).
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This email or whitelist number is already registered",
        )

    allowed.is_registered = True
    allowed.registered_user_id = user.id

    await db.flush()
    await db.refresh(user)

    access_token, refresh_token = _issue_tokens(user)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=user,
    )


async def authenticate_user(data: LoginRequest, db: AsyncSession) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if user.status == UserStatus.banned:
        raise HTTPException(status_code=403, detail="Account is banned")

    access_token, refresh_token = _issue_tokens(user)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=user,
    )


async def refresh_access_token(refresh_token: str, db: AsyncSession) -> AccessTokenResponse:
    payload = decode_token(refresh_token, expected_type="refresh")
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if user.status == UserStatus.banned:
        raise HTTPException(status_code=403, detail="Account is banned")

    # Rotate both tokens so a stolen refresh token has a shrinking window of usefulness.
    new_access_token, new_refresh_token = _issue_tokens(user)
    return AccessTokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )
