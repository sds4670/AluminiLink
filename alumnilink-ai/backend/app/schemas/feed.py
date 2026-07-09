from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.post import PostType, ModerationStatus


class PostCreate(BaseModel):
    content: str
    post_type: PostType


class ModerationResult(BaseModel):
    approved: bool
    layer_failed: Optional[str] = None
    toxicity_score: float
    reason: Optional[str] = None


class PostResponse(BaseModel):
    id: int
    author_id: int
    author_name: Optional[str] = None
    author_role: str
    post_type: PostType
    content: str
    moderation_status: ModerationStatus
    created_at: datetime
    like_count: int = 0
    comment_count: int = 0
    liked_by_me: bool = False

    model_config = {"from_attributes": True}


class PostCreateResponse(BaseModel):
    post: PostResponse
    moderation: ModerationResult


class CommentCreate(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: int
    post_id: int
    author_id: int
    author_name: Optional[str] = None
    author_role: str
    content: str
    created_at: datetime


class LikeToggleResponse(BaseModel):
    liked: bool
    like_count: int


class ModerationQueueItem(BaseModel):
    id: int
    author_id: int
    author_name: Optional[str] = None
    post_type: PostType
    content: str
    toxicity_score: Optional[float] = None
    layer_failed: Optional[str] = None
    created_at: datetime
