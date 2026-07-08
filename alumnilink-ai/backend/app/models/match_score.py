from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, Float, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class MatchScore(Base):
    __tablename__ = "match_scores"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    alumni_id: Mapped[int] = mapped_column(ForeignKey("alumni_profiles.id", ondelete="CASCADE"), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    cosine_similarity: Mapped[float] = mapped_column(Float, default=0.0)
    keyword_overlap: Mapped[float] = mapped_column(Float, default=0.0)
    industry_match: Mapped[float] = mapped_column(Float, default=0.0)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    student: Mapped["StudentProfile"] = relationship(back_populates="match_scores")  # noqa: F821
    alumni: Mapped["AlumniProfile"] = relationship(back_populates="match_scores")  # noqa: F821
