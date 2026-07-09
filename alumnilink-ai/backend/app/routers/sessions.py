from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.core.dependencies import require_student, require_alumni
from app.core.redis_client import clear_window_ttl
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.alumni_profile import AlumniProfile
from app.models.connection_window import ConnectionWindow, WindowStatus
from app.models.connection_request import ConnectionRequest
from app.models.availability_slot import AvailabilitySlot, SlotStatus
from app.models.session import Session, SessionStatus
from app.models.session_feedback import SessionFeedback, FeedbackRole
from app.schemas.session import (
    SessionBookRequest,
    SessionResponse,
    MySessionResponse,
    IncomingSessionResponse,
    SessionFeedbackCreate,
    SessionFeedbackResponse,
)

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.post("/book", response_model=SessionResponse, status_code=201)
async def book_session(
    data: SessionBookRequest,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """
    curl -X POST http://localhost:8000/api/v1/sessions/book \\
      -H "Authorization: Bearer <student access_token>" -H "Content-Type: application/json" \\
      -d '{"window_id":1,"slot_id":2}'
    """
    student_result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=400, detail="Complete your student profile first")

    window_result = await db.execute(
        select(ConnectionWindow).where(
            ConnectionWindow.id == data.window_id,
            ConnectionWindow.student_id == student.id,
        )
    )
    window = window_result.scalar_one_or_none()
    if not window:
        raise HTTPException(status_code=404, detail="Window not found")
    if window.status != WindowStatus.active:
        raise HTTPException(status_code=409, detail="Window is not active")
    if window.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=409, detail="Window has expired")

    # Lock the slot row so two concurrent booking requests against the same slot
    # can't both succeed. get_db() already manages the transaction boundary
    # (auto-begins on first statement, commits on success) — we intentionally
    # don't open a nested `db.begin()` here; the FOR UPDATE lock is simply held
    # until that outer commit/rollback happens at the end of the request.
    slot_result = await db.execute(
        select(AvailabilitySlot)
        .where(AvailabilitySlot.id == data.slot_id, AvailabilitySlot.alumni_id == window.alumni_id)
        .with_for_update()
    )
    slot = slot_result.scalar_one_or_none()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found for this alumni")
    if slot.status != SlotStatus.open:
        raise HTTPException(status_code=409, detail="Slot already booked")

    slot.status = SlotStatus.booked
    window.status = WindowStatus.booked

    request_result = await db.execute(select(ConnectionRequest).where(ConnectionRequest.window_id == window.id))
    request = request_result.scalar_one_or_none()

    scheduled_at = datetime.combine(slot.slot_date, slot.start_time, tzinfo=timezone.utc)
    end_dt = datetime.combine(slot.slot_date, slot.end_time)
    start_dt = datetime.combine(slot.slot_date, slot.start_time)
    duration_minutes = max(int((end_dt - start_dt).total_seconds() // 60), 0)

    session = Session(
        student_id=student.id,
        alumni_id=window.alumni_id,
        slot_id=slot.id,
        request_id=request.id if request else None,
        window_id=window.id,
        scheduled_at=scheduled_at,
        duration_minutes=duration_minutes,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)

    await clear_window_ttl(window.id)

    return session


@router.get("/my", response_model=List[MySessionResponse])
async def get_my_sessions(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    student_result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
    student = student_result.scalar_one_or_none()
    if not student:
        return []

    result = await db.execute(
        select(Session, AvailabilitySlot, User)
        .join(AvailabilitySlot, Session.slot_id == AvailabilitySlot.id)
        .join(AlumniProfile, Session.alumni_id == AlumniProfile.id)
        .join(User, AlumniProfile.user_id == User.id)
        .where(Session.student_id == student.id)
        .order_by(Session.scheduled_at.desc())
    )
    rows = result.all()

    reviewed_ids = set()
    session_ids = [s.id for s, _, _ in rows]
    if session_ids:
        feedback_result = await db.execute(
            select(SessionFeedback.session_id).where(
                SessionFeedback.session_id.in_(session_ids),
                SessionFeedback.reviewer_id == current_user.id,
            )
        )
        reviewed_ids = set(feedback_result.scalars().all())

    return [
        MySessionResponse(
            id=s.id,
            alumni_user_id=user.id,
            alumni_name=user.full_name,
            slot_date=slot.slot_date,
            start_time=slot.start_time,
            end_time=slot.end_time,
            status=s.status,
            has_feedback=s.id in reviewed_ids,
        )
        for s, slot, user in rows
    ]


@router.get("/incoming", response_model=List[IncomingSessionResponse])
async def get_incoming_sessions(
    current_user: User = Depends(require_alumni),
    db: AsyncSession = Depends(get_db),
):
    alumni_result = await db.execute(select(AlumniProfile).where(AlumniProfile.user_id == current_user.id))
    alumni = alumni_result.scalar_one_or_none()
    if not alumni:
        return []

    result = await db.execute(
        select(Session, AvailabilitySlot, User)
        .join(AvailabilitySlot, Session.slot_id == AvailabilitySlot.id)
        .join(StudentProfile, Session.student_id == StudentProfile.id)
        .join(User, StudentProfile.user_id == User.id)
        .where(Session.alumni_id == alumni.id)
        .order_by(Session.scheduled_at.desc())
    )
    return [
        IncomingSessionResponse(
            id=s.id,
            student_user_id=user.id,
            student_name=user.full_name,
            slot_date=slot.slot_date,
            start_time=slot.start_time,
            end_time=slot.end_time,
            status=s.status,
        )
        for s, slot, user in result.all()
    ]


@router.post("/{session_id}/feedback", response_model=SessionFeedbackResponse, status_code=201)
async def submit_feedback(
    session_id: int,
    data: SessionFeedbackCreate,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    student_result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=400, detail="Complete your student profile first")

    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.student_id == student.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != SessionStatus.completed:
        raise HTTPException(status_code=400, detail="Feedback can only be left on completed sessions")

    if not (1 <= data.rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    feedback = SessionFeedback(
        session_id=session_id,
        reviewer_id=current_user.id,
        reviewer_role=FeedbackRole.student,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(feedback)
    await db.flush()
    await db.refresh(feedback)
    return feedback
