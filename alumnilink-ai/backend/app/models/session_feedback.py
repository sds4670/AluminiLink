import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, DateTime, Enum as SAEnum, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class FeedbackRole(str, enum.Enum):
    student = "student"
    alumni = "alumni"


class SessionFeedback(Base):
    __tablename__ = "session_feedbacks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reviewer_role: Mapped[FeedbackRole] = mapped_column(SAEnum(FeedbackRole), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    comment: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["Session"] = relationship(back_populates="feedbacks")  # noqa: F821
