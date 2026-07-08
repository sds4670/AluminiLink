import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, DateTime, Enum as SAEnum, Integer, func, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class WindowStatus(str, enum.Enum):
    upcoming = "upcoming"
    active = "active"
    closed = "closed"


class ConnectionWindow(Base):
    __tablename__ = "connection_windows"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    alumni_id: Mapped[int] = mapped_column(ForeignKey("alumni_profiles.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    opens_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closes_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_requests: Mapped[int] = mapped_column(Integer, default=5)
    status: Mapped[WindowStatus] = mapped_column(SAEnum(WindowStatus), default=WindowStatus.upcoming)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    alumni: Mapped["AlumniProfile"] = relationship(back_populates="connection_windows")  # noqa: F821
    requests: Mapped[list["ConnectionRequest"]] = relationship(back_populates="window")  # noqa: F821
