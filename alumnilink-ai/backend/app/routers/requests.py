from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.core.dependencies import require_student, require_alumni, get_current_active_user
from app.models.user import User, UserRole, VerificationStatus
from app.models.student_profile import StudentProfile
from app.models.alumni_profile import AlumniProfile
from app.models.connection_request import ConnectionRequest, RequestStatus
from app.schemas.request import ConnectionRequestCreate, ConnectionRequestUpdate, ConnectionRequestResponse

router = APIRouter(prefix="/api/requests", tags=["requests"])


@router.post("/", response_model=ConnectionRequestResponse, status_code=201)
async def send_request(
    data: ConnectionRequestCreate,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    student_result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=400, detail="Complete your student profile first")

    # data.alumni_id is the alumni's user_id (the id used throughout the profile/matching APIs).
    alumni_result = await db.execute(
        select(AlumniProfile)
        .join(User, AlumniProfile.user_id == User.id)
        .where(AlumniProfile.user_id == data.alumni_id, User.verification_status == VerificationStatus.verified)
    )
    alumni = alumni_result.scalar_one_or_none()
    if not alumni:
        raise HTTPException(status_code=404, detail="Alumni not found")

    existing = await db.execute(
        select(ConnectionRequest).where(
            ConnectionRequest.student_id == student.id,
            ConnectionRequest.alumni_id == alumni.id,
            ConnectionRequest.status == RequestStatus.pending,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Pending request already exists")

    req = ConnectionRequest(
        student_id=student.id,
        alumni_id=alumni.id,
        window_id=data.window_id,
        message=data.message,
    )
    db.add(req)
    await db.flush()
    await db.refresh(req)
    return req


@router.get("/mine", response_model=List[ConnectionRequestResponse])
async def get_my_requests(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role == UserRole.student:
        student_result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
        student = student_result.scalar_one_or_none()
        if not student:
            return []
        result = await db.execute(select(ConnectionRequest).where(ConnectionRequest.student_id == student.id))
    else:
        alumni_result = await db.execute(select(AlumniProfile).where(AlumniProfile.user_id == current_user.id))
        alumni = alumni_result.scalar_one_or_none()
        if not alumni:
            return []
        result = await db.execute(select(ConnectionRequest).where(ConnectionRequest.alumni_id == alumni.id))

    return result.scalars().all()


@router.patch("/{request_id}", response_model=ConnectionRequestResponse)
async def update_request_status(
    request_id: int,
    data: ConnectionRequestUpdate,
    current_user: User = Depends(require_alumni),
    db: AsyncSession = Depends(get_db),
):
    alumni_result = await db.execute(select(AlumniProfile).where(AlumniProfile.user_id == current_user.id))
    alumni = alumni_result.scalar_one_or_none()
    if not alumni:
        raise HTTPException(status_code=400, detail="Alumni profile not found")

    result = await db.execute(
        select(ConnectionRequest).where(
            ConnectionRequest.id == request_id,
            ConnectionRequest.alumni_id == alumni.id,
        )
    )
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    req.status = data.status
    if data.rejection_reason:
        req.rejection_reason = data.rejection_reason
    await db.flush()
    return req
