from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.connection_request import RequestStatus


class ScreenerCheckRequest(BaseModel):
    message: str


class ScreenerBreakdown(BaseModel):
    intent: float
    professional_tone: float
    personalisation: float
    message_quality: float


class ScreenerResult(BaseModel):
    score: float
    passed: bool
    breakdown: ScreenerBreakdown
    suggestions: List[str]


class ConnectionRequestCreate(BaseModel):
    alumni_id: int  # the alumni's user_id, matching the profiles/matching APIs
    message: str


class ConnectionRequestUpdate(BaseModel):
    status: RequestStatus
    rejection_reason: Optional[str] = None


class ConnectionRequestResponse(BaseModel):
    id: int
    student_id: int
    alumni_id: int
    window_id: Optional[int]
    status: RequestStatus
    message: Optional[str]
    screening_score: Optional[float]
    rejection_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RequestCreateResponse(BaseModel):
    request: ConnectionRequestResponse
    screener: ScreenerResult


class MyRequestResponse(BaseModel):
    """A student's view of a request they sent."""
    id: int
    alumni_user_id: int
    alumni_name: Optional[str] = None
    company: str
    designation: str
    status: RequestStatus
    message: Optional[str]
    screening_score: Optional[float]
    window_id: Optional[int]
    created_at: datetime


class IncomingRequestResponse(BaseModel):
    """An alumnus's view of a pending request they received."""
    id: int
    student_user_id: int
    student_name: Optional[str] = None
    department: str
    career_goal: str
    status: RequestStatus
    message: Optional[str]
    screening_score: Optional[float]
    created_at: datetime


class ConnectionWindowResponse(BaseModel):
    id: int
    alumni_id: int
    student_id: int
    expires_at: datetime
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WindowActiveResponse(BaseModel):
    id: int
    alumni_user_id: int
    alumni_name: Optional[str] = None
    company: str
    expires_at: datetime
    time_remaining_seconds: int
    status: str


class OpenSlotResponse(BaseModel):
    id: int
    slot_date: str
    start_time: str
    end_time: str


class WindowDetailResponse(WindowActiveResponse):
    available_slots: List[OpenSlotResponse]
