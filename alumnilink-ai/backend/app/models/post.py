import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, DateTime, Enum as SAEnum, Text, Boolean, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PostType(str, enum.Enum):
    internship = "internship"
    job = "job"
    event = "event"
    resource = "resource"
    query = "query"
    announcement = "announcement"
    general = "general"


class ModerationStatus(str, enum.Enum):
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    post_type: Mapped[PostType] = mapped_column(SAEnum(PostType), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    link_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    moderation_status: Mapped[ModerationStatus] = mapped_column(SAEnum(ModerationStatus), default=ModerationStatus.pending_review)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    toxicity_score: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    moderation_logs: Mapped[list["PostModerationLog"]] = relationship(back_populates="post")  # noqa: F821
    likes: Mapped[list["PostLike"]] = relationship(back_populates="post", cascade="all, delete-orphan")  # noqa: F821
    comments: Mapped[list["PostComment"]] = relationship(back_populates="post", cascade="all, delete-orphan")  # noqa: F821
