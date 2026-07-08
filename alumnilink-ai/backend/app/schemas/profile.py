from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime


class StudentProfileCreate(BaseModel):
    department: str
    degree: str
    graduation_year: int
    career_goal: str
    skills: List[str]
    profile_description: str

    @field_validator("skills")
    @classmethod
    def skills_not_empty(cls, v: List[str]) -> List[str]:
        return [s.strip() for s in v if s and s.strip()]


class StudentProfileResponse(BaseModel):
    id: int
    user_id: int
    full_name: Optional[str] = None
    department: str
    degree: str
    graduation_year: int
    career_goal: str
    skills: List[str]
    profile_description: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AlumniProfileCreate(BaseModel):
    company: str
    designation: str
    industry: str
    experience_years: int
    skills: List[str]
    about_me: str

    @field_validator("skills")
    @classmethod
    def skills_not_empty(cls, v: List[str]) -> List[str]:
        return [s.strip() for s in v if s and s.strip()]


class AlumniProfileResponse(BaseModel):
    id: int
    user_id: int
    full_name: Optional[str] = None
    company: str
    designation: str
    industry: str
    experience_years: int
    skills: List[str]
    about_me: str
    verification_status: str
    is_accepting_mentees: bool
    created_at: datetime

    model_config = {"from_attributes": True}
