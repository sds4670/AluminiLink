from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.session import SessionStatus
from app.models.session_feedback import FeedbackRole


class SessionResponse(BaseModel):
    id: int
    student_id: int
    alumni_id: int
    slot_id: Optional[int]
    request_id: Optional[int]
    scheduled_at: datetime
    duration_minutes: int
    meeting_link: Optional[str]
    status: SessionStatus
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionFeedbackCreate(BaseModel):
    rating: int
    comment: Optional[str] = None


class SessionFeedbackResponse(BaseModel):
    id: int
    session_id: int
    reviewer_id: int
    reviewer_role: FeedbackRole
    rating: int
    comment: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
