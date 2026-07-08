from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.connection_request import RequestStatus


class ConnectionRequestCreate(BaseModel):
    alumni_id: int
    window_id: Optional[int] = None
    message: Optional[str] = None


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
    rejection_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConnectionWindowCreate(BaseModel):
    title: str
    opens_at: datetime
    closes_at: datetime
    max_requests: int = 5


class ConnectionWindowResponse(BaseModel):
    id: int
    alumni_id: int
    title: str
    opens_at: datetime
    closes_at: datetime
    max_requests: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
