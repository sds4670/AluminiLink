from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User, UserRole
from app.models.student_profile import StudentProfile
from app.models.alumni_profile import AlumniProfile
from app.models.session import Session
from app.models.session_feedback import SessionFeedback, FeedbackRole
from app.schemas.session import SessionResponse, SessionFeedbackCreate, SessionFeedbackResponse

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("/mine", response_model=List[SessionResponse])
async def get_my_sessions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role == UserRole.student:
        student_result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
        student = student_result.scalar_one_or_none()
        if not student:
            return []
        result = await db.execute(select(Session).where(Session.student_id == student.id))
    elif current_user.role == UserRole.alumni:
        alumni_result = await db.execute(select(AlumniProfile).where(AlumniProfile.user_id == current_user.id))
        alumni = alumni_result.scalar_one_or_none()
        if not alumni:
            return []
        result = await db.execute(select(Session).where(Session.alumni_id == alumni.id))
    else:
        result = await db.execute(select(Session))

    return result.scalars().all()


@router.post("/{session_id}/feedback", response_model=SessionFeedbackResponse, status_code=201)
async def submit_feedback(
    session_id: int,
    data: SessionFeedbackCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not (1 <= data.rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    reviewer_role = FeedbackRole.student if current_user.role == UserRole.student else FeedbackRole.alumni
    feedback = SessionFeedback(
        session_id=session_id,
        reviewer_id=current_user.id,
        reviewer_role=reviewer_role,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(feedback)
    await db.flush()
    await db.refresh(feedback)
    return feedback


@router.get("/{session_id}/feedback", response_model=List[SessionFeedbackResponse])
async def get_session_feedback(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SessionFeedback).where(SessionFeedback.session_id == session_id))
    return result.scalars().all()
