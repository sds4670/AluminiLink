from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.core.dependencies import require_student
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.alumni_profile import AlumniProfile
from app.models.match_score import MatchScore
from app.schemas.matching import AlumniMatchResult, MatchScoreResponse, WHY_RECOMMENDED
from app.services.ml.embeddings import cosine_similarity
from app.services.matching_service import get_verified_alumni_with_embeddings, upsert_match_score

router = APIRouter(prefix="/api/v1/matching", tags=["matching"])


async def _get_own_student_profile(current_user: User, db: AsyncSession) -> StudentProfile:
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
    student = result.scalar_one_or_none()
    if not student or not student.embedding:
        raise HTTPException(status_code=400, detail="Complete your profile first")
    return student


@router.get("/alumni", response_model=List[AlumniMatchResult])
async def browse_matches(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    student = await _get_own_student_profile(current_user, db)

    pairs = await get_verified_alumni_with_embeddings(db)
    scored = []
    for alumni, user in pairs:
        sim = cosine_similarity(student.embedding, alumni.embedding)
        await upsert_match_score(student.id, alumni.id, sim, db)
        scored.append((alumni, user, sim))

    scored.sort(key=lambda row: row[2], reverse=True)
    top = scored[:20]

    return [
        AlumniMatchResult(
            user_id=user.id,
            name=user.full_name,
            company=alumni.company,
            designation=alumni.designation,
            industry=alumni.industry,
            experience_years=alumni.experience_years,
            skills=alumni.skills or [],
            match_score=round(sim, 2),
            why_recommended=WHY_RECOMMENDED,
        )
        for alumni, user, sim in top
    ]


@router.get("/alumni/{alumni_user_id}/score", response_model=MatchScoreResponse)
async def get_match_score(
    alumni_user_id: int,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    student = await _get_own_student_profile(current_user, db)

    alumni_result = await db.execute(select(AlumniProfile).where(AlumniProfile.user_id == alumni_user_id))
    alumni = alumni_result.scalar_one_or_none()
    if not alumni or not alumni.embedding:
        raise HTTPException(status_code=404, detail="Alumni profile not found")

    score_result = await db.execute(
        select(MatchScore).where(MatchScore.student_id == student.id, MatchScore.alumni_id == alumni.id)
    )
    match = score_result.scalar_one_or_none()
    if match:
        return MatchScoreResponse(alumni_id=alumni_user_id, match_score=round(match.score, 2))

    sim = cosine_similarity(student.embedding, alumni.embedding)
    await upsert_match_score(student.id, alumni.id, sim, db)
    return MatchScoreResponse(alumni_id=alumni_user_id, match_score=round(sim, 2))
