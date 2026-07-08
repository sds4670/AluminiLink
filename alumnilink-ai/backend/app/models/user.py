import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class UserRole(str, enum.Enum):
    student = "student"
    alumni = "alumni"
    admin = "admin"


class UserStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    banned = "banned"
    pending_approval = "pending_approval"


class VerificationStatus(str, enum.Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), nullable=False)
    status: Mapped[UserStatus] = mapped_column(SAEnum(UserStatus), default=UserStatus.active)
    # Alumni-only gate: can they create a profile / list availability yet? Independent of
    # `status`, which only governs whether the account can log in at all.
    verification_status: Mapped[VerificationStatus] = mapped_column(
        SAEnum(VerificationStatus), default=VerificationStatus.pending, nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    # Whitelist identifiers captured at registration; exactly one is set depending on role.
    roll_number: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True)
    register_number: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    student_profile: Mapped["StudentProfile"] = relationship(back_populates="user", uselist=False)  # noqa: F821
    alumni_profile: Mapped["AlumniProfile"] = relationship(back_populates="user", uselist=False)  # noqa: F821
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="actor")  # noqa: F821
