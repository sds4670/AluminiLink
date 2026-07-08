import enum
from datetime import datetime, date, time
from sqlalchemy import ForeignKey, Date, Time, Enum as SAEnum, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class SlotStatus(str, enum.Enum):
    open = "open"
    booked = "booked"


class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    alumni_id: Mapped[int] = mapped_column(ForeignKey("alumni_profiles.id", ondelete="CASCADE"), nullable=False)
    slot_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[SlotStatus] = mapped_column(SAEnum(SlotStatus), default=SlotStatus.open, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    alumni: Mapped["AlumniProfile"] = relationship(back_populates="availability_slots")  # noqa: F821
    session: Mapped["Session | None"] = relationship(back_populates="slot")  # noqa: F821
