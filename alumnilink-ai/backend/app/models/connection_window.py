import enum
from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class WindowStatus(str, enum.Enum):
    active = "active"
    booked = "booked"
    expired = "expired"


class ConnectionWindow(Base):
    """
    Created the moment an alumnus accepts a connection request. The student has
    48 hours (`expires_at`) to book a slot before a background job expires it.
    """

    __tablename__ = "connection_windows"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    alumni_id: Mapped[int] = mapped_column(ForeignKey("alumni_profiles.id", ondelete="CASCADE"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[WindowStatus] = mapped_column(SAEnum(WindowStatus), default=WindowStatus.active, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    student: Mapped["StudentProfile"] = relationship()  # noqa: F821
    alumni: Mapped["AlumniProfile"] = relationship(back_populates="connection_windows")  # noqa: F821
    requests: Mapped[list["ConnectionRequest"]] = relationship(back_populates="window")  # noqa: F821
    sessions: Mapped[list["Session"]] = relationship(back_populates="window")  # noqa: F821
