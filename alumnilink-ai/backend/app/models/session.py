import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, DateTime, Enum as SAEnum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class SessionStatus(str, enum.Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    alumni_id: Mapped[int] = mapped_column(ForeignKey("alumni_profiles.id", ondelete="CASCADE"), nullable=False)
    slot_id: Mapped[Optional[int]] = mapped_column(ForeignKey("availability_slots.id", ondelete="SET NULL"))
    request_id: Mapped[Optional[int]] = mapped_column(ForeignKey("connection_requests.id", ondelete="SET NULL"))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(default=30)
    meeting_link: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[SessionStatus] = mapped_column(SAEnum(SessionStatus), default=SessionStatus.scheduled)
    notes: Mapped[Optional[str]] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    student: Mapped["StudentProfile"] = relationship(back_populates="sessions")  # noqa: F821
    alumni: Mapped["AlumniProfile"] = relationship(back_populates="sessions")  # noqa: F821
    slot: Mapped[Optional["AvailabilitySlot"]] = relationship(back_populates="session")  # noqa: F821
    request: Mapped[Optional["ConnectionRequest"]] = relationship(back_populates="session")  # noqa: F821
    feedbacks: Mapped[list["SessionFeedback"]] = relationship(back_populates="session")  # noqa: F821
