import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, DateTime, Enum as SAEnum, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ModerationAction(str, enum.Enum):
    approved = "approved"
    rejected = "rejected"
    flagged = "flagged"
    auto_approved = "auto_approved"
    auto_rejected = "auto_rejected"


class PostModerationLog(Base):
    __tablename__ = "post_moderation_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    moderator_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[ModerationAction] = mapped_column(SAEnum(ModerationAction), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    post: Mapped["Post"] = relationship(back_populates="moderation_logs")  # noqa: F821
