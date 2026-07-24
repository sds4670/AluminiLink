from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator, model_validator
from app.models.user import UserRole

# Students must prove they're currently enrolled by registering with the
# university's own domain. Alumni are NOT restricted to this (or any
# specific) domain — many no longer have an active university mailbox
# after graduating, so their identity is instead verified by an admin
# checking their register_number against the official roster (Module 9).
STUDENT_EMAIL_DOMAIN = "christuniversity.in"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole
    roll_number: Optional[str] = None
    register_number: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

    @field_validator("full_name")
    @classmethod
    def full_name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("full_name must not be blank")
        return v

    @model_validator(mode="after")
    def check_role_identifier(self) -> "RegisterRequest":
        if self.role == UserRole.student and not self.roll_number:
            raise ValueError("roll_number is required for student registration")
        if self.role == UserRole.alumni and not self.register_number:
            raise ValueError("register_number is required for alumni registration")
        if self.role == UserRole.admin:
            raise ValueError("Admin accounts cannot be self-registered")
        if self.role == UserRole.student:
            domain = self.email.split("@")[-1].lower()
            if domain != STUDENT_EMAIL_DOMAIN:
                raise ValueError(f"Students must register with a @{STUDENT_EMAIL_DOMAIN} email address")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: UserRole
    status: str
    verification_status: str
    is_verified: bool
    roll_number: Optional[str] = None
    register_number: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class AccessTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
