from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.dependencies import require_student, require_student_or_alumni
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.alumni_profile import AlumniProfile
from app.models.connection_request import ConnectionRequest
from app.models.session import Session
from app.models.availability_slot import AvailabilitySlot
from app.services.matching_service import get_or_compute_match_score
from app.services.ml.predict import (
    predict_response_likelihood,
    predict_completion_likelihood,
    interpret,
)

router = APIRouter(prefix="/api/v1/predict", tags=["predict"])

DEFAULT_SCREENING_SCORE = 0.7


@router.get("/response/{alumni_id}")
async def predict_response(
    alumni_id: int,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """
    curl http://localhost:8000/api/v1/predict/response/17 \\
      -H "Authorization: Bearer <student access_token>"
    """
    student_result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=400, detail="Complete your student profile first")

    alumni_result = await db.execute(select(AlumniProfile).where(AlumniProfile.user_id == alumni_id))
    alumni = alumni_result.scalar_one_or_none()
    if not alumni:
        raise HTTPException(status_code=404, detail="Alumni profile not found")

    match_score = await get_or_compute_match_score(student, alumni, db)

    last_request_result = await db.execute(
        select(ConnectionRequest)
        .where(ConnectionRequest.student_id == student.id, ConnectionRequest.screening_score.is_not(None))
        .order_by(ConnectionRequest.created_at.desc())
    )
    last_request = last_request_result.scalars().first()
    screening_score = last_request.screening_score if last_request else DEFAULT_SCREENING_SCORE

    likelihood = predict_response_likelihood(
        screening_score=screening_score,
        match_score=match_score,
        experience_years=alumni.experience_years,
    )
    return {
        "response_likelihood": likelihood,
        "interpretation": interpret(likelihood),
    }


@router.get("/completion/{session_id}")
async def predict_completion(
    session_id: int,
    current_user: User = Depends(require_student_or_alumni),
    db: AsyncSession = Depends(get_db),
):
    """
    curl http://localhost:8000/api/v1/predict/completion/1 \\
      -H "Authorization: Bearer <access_token>"
    """
    session_result = await db.execute(select(Session).where(Session.id == session_id))
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    student_result = await db.execute(select(StudentProfile).where(StudentProfile.id == session.student_id))
    alumni_result = await db.execute(select(AlumniProfile).where(AlumniProfile.id == session.alumni_id))
    student = student_result.scalar_one_or_none()
    alumni = alumni_result.scalar_one_or_none()
    if not student or not alumni:
        raise HTTPException(status_code=404, detail="Session participants not found")

    # Only the two participants may query this.
    if current_user.id not in (student.user_id, alumni.user_id):
        raise HTTPException(status_code=403, detail="Not a participant in this session")

    match_score = await get_or_compute_match_score(student, alumni, db)

    screening_score = DEFAULT_SCREENING_SCORE
    if session.request_id:
        request_result = await db.execute(select(ConnectionRequest).where(ConnectionRequest.id == session.request_id))
        request = request_result.scalar_one_or_none()
        if request and request.screening_score is not None:
            screening_score = request.screening_score

    session_hour = 10
    if session.slot_id:
        slot_result = await db.execute(select(AvailabilitySlot).where(AvailabilitySlot.id == session.slot_id))
        slot = slot_result.scalar_one_or_none()
        if slot:
            session_hour = slot.start_time.hour

    likelihood = predict_completion_likelihood(
        match_score=match_score,
        screening_score=screening_score,
        experience_years=alumni.experience_years,
        session_hour=session_hour,
    )
    return {
        "completion_likelihood": likelihood,
        "interpretation": interpret(likelihood),
    }
