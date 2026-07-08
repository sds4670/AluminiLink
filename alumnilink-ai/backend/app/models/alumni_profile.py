from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, DateTime, Text, Boolean, Float, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.database import Base


class AlumniProfile(Base):
    __tablename__ = "alumni_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    designation: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str] = mapped_column(String(255), nullable=False)
    experience_years: Mapped[int] = mapped_column(Integer, nullable=False)
    skills: Mapped[list] = mapped_column(JSON, default=list)
    about_me: Mapped[str] = mapped_column(Text, nullable=False)
    is_accepting_mentees: Mapped[bool] = mapped_column(Boolean, default=True)
    screening_score: Mapped[Optional[float]] = mapped_column(Float)
    embedding: Mapped[Optional[list]] = mapped_column(Vector(384))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="alumni_profile")  # noqa: F821
    availability_slots: Mapped[list["AvailabilitySlot"]] = relationship(back_populates="alumni")  # noqa: F821
    received_requests: Mapped[list["ConnectionRequest"]] = relationship(back_populates="alumni", foreign_keys="ConnectionRequest.alumni_id")  # noqa: F821
    sessions: Mapped[list["Session"]] = relationship(back_populates="alumni")  # noqa: F821
    match_scores: Mapped[list["MatchScore"]] = relationship(back_populates="alumni")  # noqa: F821
    connection_windows: Mapped[list["ConnectionWindow"]] = relationship(back_populates="alumni")  # noqa: F821
