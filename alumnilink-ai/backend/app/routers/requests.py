from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.core.dependencies import require_student, require_alumni
from app.core.redis_client import set_window_ttl
from app.models.user import User, VerificationStatus
from app.models.student_profile import StudentProfile
from app.models.alumni_profile import AlumniProfile
from app.models.connection_request import ConnectionRequest, RequestStatus
from app.models.connection_window import ConnectionWindow, WindowStatus
from app.schemas.request import (
    ConnectionRequestCreate,
    ConnectionRequestResponse,
    RequestCreateResponse,
    MyRequestResponse,
    IncomingRequestResponse,
    ConnectionWindowResponse,
)
from app.services.ml.screener import screen_message

router = APIRouter(prefix="/api/v1/requests", tags=["requests"])

WINDOW_DURATION_SECONDS = 48 * 60 * 60


@router.post("/", response_model=RequestCreateResponse, status_code=201)
async def send_request(
    data: ConnectionRequestCreate,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """
    curl -X POST http://localhost:8000/api/v1/requests/ \\
      -H "Authorization: Bearer <student access_token>" -H "Content-Type: application/json" \\
      -d '{"alumni_id":17,"message":"Hi, I would love your guidance on breaking into data science. I saw your experience at your company and wanted to discuss your career journey and learn from your background. Could we schedule a short session?"}'
    """
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

    screener_result = screen_message(data.message)
    if screener_result["score"] < 0.6:
        raise HTTPException(status_code=400, detail=screener_result)

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
        message=data.message,
        screening_score=screener_result["score"],
    )
    db.add(req)
    await db.flush()
    await db.refresh(req)
    return RequestCreateResponse(request=req, screener=screener_result)


@router.get("/my", response_model=List[MyRequestResponse])
async def get_my_requests(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    student_result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
    student = student_result.scalar_one_or_none()
    if not student:
        return []

    result = await db.execute(
        select(ConnectionRequest, AlumniProfile, User)
        .join(AlumniProfile, ConnectionRequest.alumni_id == AlumniProfile.id)
        .join(User, AlumniProfile.user_id == User.id)
        .where(ConnectionRequest.student_id == student.id)
        .order_by(ConnectionRequest.created_at.desc())
    )
    return [
        MyRequestResponse(
            id=req.id,
            alumni_user_id=user.id,
            alumni_name=user.full_name,
            company=alumni.company,
            designation=alumni.designation,
            status=req.status,
            message=req.message,
            screening_score=req.screening_score,
            window_id=req.window_id,
            created_at=req.created_at,
        )
        for req, alumni, user in result.all()
    ]


@router.get("/incoming", response_model=List[IncomingRequestResponse])
async def get_incoming_requests(
    status: RequestStatus = RequestStatus.pending,
    current_user: User = Depends(require_alumni),
    db: AsyncSession = Depends(get_db),
):
    alumni_result = await db.execute(select(AlumniProfile).where(AlumniProfile.user_id == current_user.id))
    alumni = alumni_result.scalar_one_or_none()
    if not alumni:
        return []

    result = await db.execute(
        select(ConnectionRequest, StudentProfile, User)
        .join(StudentProfile, ConnectionRequest.student_id == StudentProfile.id)
        .join(User, StudentProfile.user_id == User.id)
        .where(
            ConnectionRequest.alumni_id == alumni.id,
            ConnectionRequest.status == status,
        )
        .order_by(ConnectionRequest.created_at.desc())
    )
    return [
        IncomingRequestResponse(
            id=req.id,
            student_user_id=user.id,
            student_name=user.full_name,
            department=student.department,
            career_goal=student.career_goal,
            status=req.status,
            message=req.message,
            screening_score=req.screening_score,
            created_at=req.created_at,
        )
        for req, student, user in result.all()
    ]


@router.patch("/{request_id}/accept", response_model=ConnectionWindowResponse)
async def accept_request(
    request_id: int,
    current_user: User = Depends(require_alumni),
    db: AsyncSession = Depends(get_db),
):
    """
    curl -X PATCH http://localhost:8000/api/v1/requests/1/accept \\
      -H "Authorization: Bearer <alumni access_token>"
    """
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
    if req.status != RequestStatus.pending:
        raise HTTPException(status_code=400, detail="Request has already been processed")

    req.status = RequestStatus.accepted

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=WINDOW_DURATION_SECONDS)
    window = ConnectionWindow(
        student_id=req.student_id,
        alumni_id=alumni.id,
        expires_at=expires_at,
        status=WindowStatus.active,
    )
    db.add(window)
    await db.flush()
    await db.refresh(window)

    req.window_id = window.id
    await db.flush()

    await set_window_ttl(window.id, WINDOW_DURATION_SECONDS)

    return window


@router.patch("/{request_id}/reject", response_model=ConnectionRequestResponse)
async def reject_request(
    request_id: int,
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
    if req.status != RequestStatus.pending:
        raise HTTPException(status_code=400, detail="Request has already been processed")

    req.status = RequestStatus.rejected
    await db.flush()
    await db.refresh(req)
    return req
