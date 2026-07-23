from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: int
    request_id: int
    sender_id: int
    content: str
    created_at: datetime
    read_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
