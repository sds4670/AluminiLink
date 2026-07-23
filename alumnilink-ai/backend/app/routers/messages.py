from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.core.dependencies import require_student_or_alumni
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.alumni_profile import AlumniProfile
from app.models.connection_request import ConnectionRequest, RequestStatus
from app.models.message import Message
from app.schemas.message import MessageCreate, MessageResponse

router = APIRouter(prefix="/api/v1/requests", tags=["messages"])


async def _get_request_as_participant(request_id: int, current_user: User, db: AsyncSession) -> ConnectionRequest:
    """
    Loads the connection_request and enforces both checks every message
    endpoint needs: the caller must be one of its two participants, and the
    request must have been accepted (translate user_id -> student_profile.id /
    alumni_profile.id the same way GET /api/v1/predict/completion/{session_id}
    does).
    """
    result = await db.execute(select(ConnectionRequest).where(ConnectionRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    student_result = await db.execute(select(StudentProfile).where(StudentProfile.id == req.student_id))
    alumni_result = await db.execute(select(AlumniProfile).where(AlumniProfile.id == req.alumni_id))
    student = student_result.scalar_one_or_none()
    alumni = alumni_result.scalar_one_or_none()
    if not student or not alumni:
        raise HTTPException(status_code=404, detail="Request participants not found")

    if current_user.id not in (student.user_id, alumni.user_id):
        raise HTTPException(status_code=403, detail="Not a participant in this request")

    if req.status != RequestStatus.accepted:
        raise HTTPException(status_code=403, detail="Messaging is only available once a request has been accepted")

    return req


@router.post("/{request_id}/messages", response_model=MessageResponse, status_code=201)
async def send_message(
    request_id: int,
    data: MessageCreate,
    current_user: User = Depends(require_student_or_alumni),
    db: AsyncSession = Depends(get_db),
):
    """
    curl -X POST http://localhost:8000/api/v1/requests/1/messages \\
      -H "Authorization: Bearer <access_token>" -H "Content-Type: application/json" \\
      -d '{"content":"Looking forward to our session!"}'
    """
    await _get_request_as_participant(request_id, current_user, db)

    message = Message(request_id=request_id, sender_id=current_user.id, content=data.content)
    db.add(message)
    await db.flush()
    await db.refresh(message)
    return message


@router.get("/{request_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    request_id: int,
    current_user: User = Depends(require_student_or_alumni),
    db: AsyncSession = Depends(get_db),
):
    """
    curl http://localhost:8000/api/v1/requests/1/messages \\
      -H "Authorization: Bearer <access_token>"
    """
    await _get_request_as_participant(request_id, current_user, db)

    result = await db.execute(
        select(Message).where(Message.request_id == request_id).order_by(Message.created_at.asc())
    )
    return result.scalars().all()
