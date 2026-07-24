from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date, time
from app.models.session import SessionStatus
from app.models.session_feedback import FeedbackRole


class SessionBookRequest(BaseModel):
    window_id: int
    slot_id: int


class MySessionResponse(BaseModel):
    """A student's view of one of their sessions."""
    id: int
    alumni_user_id: int
    alumni_name: Optional[str] = None
    slot_date: date
    start_time: time
    end_time: time
    status: SessionStatus
    has_feedback: bool = False
    meeting_link: Optional[str] = None


class IncomingSessionResponse(BaseModel):
    """An alumnus's view of a session where they are the mentor."""
    id: int
    student_user_id: int
    student_name: Optional[str] = None
    slot_date: date
    start_time: time
    end_time: time
    status: SessionStatus
    meeting_link: Optional[str] = None


class SessionMeetingLinkUpdate(BaseModel):
    meeting_link: str


class SessionResponse(BaseModel):
    id: int
    student_id: int
    alumni_id: int
    slot_id: Optional[int]
    request_id: Optional[int]
    window_id: Optional[int]
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
