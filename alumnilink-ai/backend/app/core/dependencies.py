from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole, VerificationStatus

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
_optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


async def get_optional_user(
    token: Optional[str] = Depends(_optional_oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """For public endpoints that personalize when a valid token happens to be present."""
    if not token:
        return None
    payload = decode_access_token(token)
    if payload is None:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    result = await db.execute(select(User).where(User.id == int(user_id)))
    return result.scalar_one_or_none()


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.status != "active":
        raise HTTPException(status_code=400, detail="Inactive user")
    # An already-issued token for a since-rejected alumnus must die immediately,
    # not just at their next login/refresh attempt (see auth_service._check_account_not_blocked).
    if current_user.role == UserRole.alumni and current_user.verification_status == VerificationStatus.rejected:
        raise HTTPException(status_code=403, detail="Your alumni application was rejected.")
    return current_user


def require_role(*roles: UserRole):
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return role_checker


require_student = require_role(UserRole.student)
require_alumni = require_role(UserRole.alumni)
require_admin = require_role(UserRole.admin)
require_student_or_alumni = require_role(UserRole.student, UserRole.alumni)
