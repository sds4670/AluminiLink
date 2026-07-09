from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.core.dependencies import require_student
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.alumni_profile import AlumniProfile
from app.models.connection_window import ConnectionWindow, WindowStatus
from app.models.availability_slot import AvailabilitySlot, SlotStatus
from app.schemas.request import WindowActiveResponse, WindowDetailResponse, OpenSlotResponse

router = APIRouter(prefix="/api/v1/windows", tags=["windows"])


def _time_remaining(expires_at: datetime) -> int:
    delta = expires_at - datetime.now(timezone.utc)
    return max(0, int(delta.total_seconds()))


async def _get_own_student(current_user: User, db: AsyncSession) -> StudentProfile:
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=400, detail="Complete your student profile first")
    return student


@router.get("/active", response_model=List[WindowActiveResponse])
async def list_active_windows(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    student = await _get_own_student(current_user, db)

    result = await db.execute(
        select(ConnectionWindow, AlumniProfile, User)
        .join(AlumniProfile, ConnectionWindow.alumni_id == AlumniProfile.id)
        .join(User, AlumniProfile.user_id == User.id)
        .where(ConnectionWindow.student_id == student.id, ConnectionWindow.status == WindowStatus.active)
        .order_by(ConnectionWindow.expires_at)
    )
    return [
        WindowActiveResponse(
            id=window.id,
            alumni_user_id=user.id,
            alumni_name=user.full_name,
            company=alumni.company,
            expires_at=window.expires_at,
            time_remaining_seconds=_time_remaining(window.expires_at),
            status=window.status.value,
        )
        for window, alumni, user in result.all()
    ]


@router.get("/{window_id}", response_model=WindowDetailResponse)
async def get_window_detail(
    window_id: int,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    student = await _get_own_student(current_user, db)

    result = await db.execute(
        select(ConnectionWindow, AlumniProfile, User)
        .join(AlumniProfile, ConnectionWindow.alumni_id == AlumniProfile.id)
        .join(User, AlumniProfile.user_id == User.id)
        .where(ConnectionWindow.id == window_id, ConnectionWindow.student_id == student.id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Window not found")
    window, alumni, user = row

    slots_result = await db.execute(
        select(AvailabilitySlot).where(
            AvailabilitySlot.alumni_id == alumni.id,
            AvailabilitySlot.status == SlotStatus.open,
        )
    )
    slots = [
        OpenSlotResponse(id=s.id, slot_date=s.slot_date.isoformat(), start_time=s.start_time.isoformat(), end_time=s.end_time.isoformat())
        for s in slots_result.scalars().all()
    ]

    return WindowDetailResponse(
        id=window.id,
        alumni_user_id=user.id,
        alumni_name=user.full_name,
        company=alumni.company,
        expires_at=window.expires_at,
        time_remaining_seconds=_time_remaining(window.expires_at),
        status=window.status.value,
        available_slots=slots,
    )
