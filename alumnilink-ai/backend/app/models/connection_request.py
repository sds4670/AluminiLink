import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, DateTime, Enum as SAEnum, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class RequestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    withdrawn = "withdrawn"
    expired = "expired"


class ConnectionRequest(Base):
    __tablename__ = "connection_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    alumni_id: Mapped[int] = mapped_column(ForeignKey("alumni_profiles.id", ondelete="CASCADE"), nullable=False)
    window_id: Mapped[Optional[int]] = mapped_column(ForeignKey("connection_windows.id", ondelete="SET NULL"))
    status: Mapped[RequestStatus] = mapped_column(SAEnum(RequestStatus), default=RequestStatus.pending)
    message: Mapped[Optional[str]] = mapped_column(Text)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    student: Mapped["StudentProfile"] = relationship(back_populates="sent_requests", foreign_keys=[student_id])  # noqa: F821
    alumni: Mapped["AlumniProfile"] = relationship(back_populates="received_requests", foreign_keys=[alumni_id])  # noqa: F821
    window: Mapped[Optional["ConnectionWindow"]] = relationship(back_populates="requests")  # noqa: F821
    session: Mapped[Optional["Session"]] = relationship(back_populates="request")  # noqa: F821
