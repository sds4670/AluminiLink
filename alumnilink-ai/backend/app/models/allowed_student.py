from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class AllowedStudent(Base):
    """Whitelist of roll numbers permitted to self-register as a student."""

    __tablename__ = "allowed_students"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    roll_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    is_registered: Mapped[bool] = mapped_column(Boolean, default=False)
    registered_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
