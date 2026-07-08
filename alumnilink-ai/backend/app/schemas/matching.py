from typing import List, Optional
from pydantic import BaseModel

WHY_RECOMMENDED = [
    "Similar career goal",
    "Matching skills",
    "High semantic similarity",
    "Active mentor",
]


class AlumniMatchResult(BaseModel):
    user_id: int
    name: Optional[str] = None
    company: str
    designation: str
    industry: str
    experience_years: int
    skills: List[str]
    match_score: float
    why_recommended: List[str] = WHY_RECOMMENDED


class MatchScoreResponse(BaseModel):
    alumni_id: int
    match_score: float
