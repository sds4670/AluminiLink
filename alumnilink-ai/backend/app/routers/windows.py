from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.core.dependencies import require_alumni, get_current_active_user
from app.models.user import User
from app.models.alumni_profile import AlumniProfile
from app.models.connection_window import ConnectionWindow
from app.schemas.request import ConnectionWindowCreate, ConnectionWindowResponse

router = APIRouter(prefix="/api/windows", tags=["windows"])


@router.post("/", response_model=ConnectionWindowResponse, status_code=201)
async def create_window(
    data: ConnectionWindowCreate,
    current_user: User = Depends(require_alumni),
    db: AsyncSession = Depends(get_db),
):
    alumni_result = await db.execute(select(AlumniProfile).where(AlumniProfile.user_id == current_user.id))
    alumni = alumni_result.scalar_one_or_none()
    if not alumni:
        raise HTTPException(status_code=400, detail="Alumni profile not found")

    window = ConnectionWindow(alumni_id=alumni.id, **data.model_dump())
    db.add(window)
    await db.flush()
    await db.refresh(window)
    return window


@router.get("/", response_model=List[ConnectionWindowResponse])
async def list_windows(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ConnectionWindow))
    return result.scalars().all()


@router.get("/mine", response_model=List[ConnectionWindowResponse])
async def my_windows(
    current_user: User = Depends(require_alumni),
    db: AsyncSession = Depends(get_db),
):
    alumni_result = await db.execute(select(AlumniProfile).where(AlumniProfile.user_id == current_user.id))
    alumni = alumni_result.scalar_one_or_none()
    if not alumni:
        return []
    result = await db.execute(select(ConnectionWindow).where(ConnectionWindow.alumni_id == alumni.id))
    return result.scalars().all()
