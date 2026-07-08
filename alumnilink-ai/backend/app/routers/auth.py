from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    AccessTokenResponse,
    UserResponse,
)
from app.services.auth_service import register_user, authenticate_user, refresh_access_token
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new student or alumni account.

    Student roll numbers and alumni register numbers must already exist in the
    `allowed_students` / `allowed_alumni` whitelist tables (see the seed script).
    Both roles can log in immediately. Students get verification_status=verified
    right away; alumni get verification_status=pending and must be verified by
    an admin (Module 9/2: profile creation and availability slots) before they
    can create a profile or list availability.

    curl -X POST http://localhost:8000/api/v1/auth/register \\
      -H "Content-Type: application/json" \\
      -d '{"email":"student1@university.edu","password":"Passw0rd!","full_name":"Aarav Mehta","role":"student","roll_number":"2024DS001"}'

    curl -X POST http://localhost:8000/api/v1/auth/register \\
      -H "Content-Type: application/json" \\
      -d '{"email":"alumni1@university.edu","password":"Passw0rd!","full_name":"Priya Nair","role":"alumni","register_number":"REG2014DS01"}'
    """
    return await register_user(data, db)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Exchange email/password credentials for an access + refresh token pair.

    curl -X POST http://localhost:8000/api/v1/auth/login \\
      -H "Content-Type: application/json" \\
      -d '{"email":"student1@university.edu","password":"Passw0rd!"}'
    """
    return await authenticate_user(data, db)


@router.post("/token", response_model=TokenResponse)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """OAuth2-compatible form login, used by FastAPI's Swagger UI 'Authorize' button."""
    data = LoginRequest(email=form_data.username, password=form_data.password)
    return await authenticate_user(data, db)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Exchange a valid, non-expired refresh token for a new access + refresh token pair.

    curl -X POST http://localhost:8000/api/v1/auth/refresh \\
      -H "Content-Type: application/json" \\
      -d '{"refresh_token":"<refresh_token from login/register response>"}'
    """
    return await refresh_access_token(data.refresh_token, db)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Return the currently authenticated user, resolved from the bearer access token.
    Unlike role-gated routes, this does not require an "active" status, so a
    pending-approval alumnus or a banned user can still see their own account state.

    curl -X GET http://localhost:8000/api/v1/auth/me \\
      -H "Authorization: Bearer <access_token from login/register response>"
    """
    return current_user
