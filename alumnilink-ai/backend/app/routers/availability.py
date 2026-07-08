from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.core.dependencies import require_alumni, require_student
from app.models.user import User, VerificationStatus
from app.models.alumni_profile import AlumniProfile
from app.models.availability_slot import AvailabilitySlot, SlotStatus
from app.schemas.availability import (
    AvailabilitySlotCreate,
    AvailabilitySlotUpdate,
    AvailabilitySlotResponse,
)

router = APIRouter(prefix="/api/v1/availability", tags=["availability"])


async def _get_own_alumni_profile(current_user: User, db: AsyncSession) -> AlumniProfile:
    result = await db.execute(select(AlumniProfile).where(AlumniProfile.user_id == current_user.id))
    alumni = result.scalar_one_or_none()
    if not alumni:
        raise HTTPException(status_code=400, detail="Alumni profile not found")
    return alumni


@router.post("/", response_model=AvailabilitySlotResponse, status_code=201)
async def create_slot(
    data: AvailabilitySlotCreate,
    current_user: User = Depends(require_alumni),
    db: AsyncSession = Depends(get_db),
):
    """
    curl -X POST http://localhost:8000/api/v1/availability/ \\
      -H "Authorization: Bearer <alumni access_token>" -H "Content-Type: application/json" \\
      -d '{"slot_date":"2026-07-10","start_time":"10:00:00","end_time":"11:00:00"}'
    """
    if current_user.verification_status != VerificationStatus.verified:
        raise HTTPException(status_code=403, detail="Alumni account must be verified before creating availability slots")

    alumni = await _get_own_alumni_profile(current_user, db)
    slot = AvailabilitySlot(alumni_id=alumni.id, status=SlotStatus.open, **data.model_dump())
    db.add(slot)
    await db.flush()
    await db.refresh(slot)
    return slot


@router.get("/my", response_model=List[AvailabilitySlotResponse])
async def my_slots(
    current_user: User = Depends(require_alumni),
    db: AsyncSession = Depends(get_db),
):
    alumni = await _get_own_alumni_profile(current_user, db)
    result = await db.execute(select(AvailabilitySlot).where(AvailabilitySlot.alumni_id == alumni.id))
    return result.scalars().all()


@router.get("/{alumni_id}", response_model=List[AvailabilitySlotResponse])
async def get_alumni_open_slots(
    alumni_id: int,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Students browse this to see what they can book. `alumni_id` is the AlumniProfile id."""
    result = await db.execute(
        select(AvailabilitySlot).where(
            AvailabilitySlot.alumni_id == alumni_id,
            AvailabilitySlot.status == SlotStatus.open,
        )
    )
    return result.scalars().all()


@router.put("/{slot_id}", response_model=AvailabilitySlotResponse)
async def update_slot(
    slot_id: int,
    data: AvailabilitySlotUpdate,
    current_user: User = Depends(require_alumni),
    db: AsyncSession = Depends(get_db),
):
    alumni = await _get_own_alumni_profile(current_user, db)
    result = await db.execute(
        select(AvailabilitySlot).where(AvailabilitySlot.id == slot_id, AvailabilitySlot.alumni_id == alumni.id)
    )
    slot = result.scalar_one_or_none()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    if slot.status != SlotStatus.open:
        raise HTTPException(status_code=400, detail="Cannot edit a booked slot")

    for field, value in data.model_dump().items():
        setattr(slot, field, value)
    await db.flush()
    await db.refresh(slot)
    return slot


@router.delete("/{slot_id}", status_code=204)
async def delete_slot(
    slot_id: int,
    current_user: User = Depends(require_alumni),
    db: AsyncSession = Depends(get_db),
):
    alumni = await _get_own_alumni_profile(current_user, db)
    result = await db.execute(
        select(AvailabilitySlot).where(AvailabilitySlot.id == slot_id, AvailabilitySlot.alumni_id == alumni.id)
    )
    slot = result.scalar_one_or_none()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    if slot.status != SlotStatus.open:
        raise HTTPException(status_code=400, detail="Cannot delete a booked slot")

    await db.delete(slot)
