from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.student_profile import StudentProfile
from app.models.alumni_profile import AlumniProfile
from app.models.match_score import MatchScore
from app.models.user import User, VerificationStatus
from app.services.ml.embeddings import cosine_similarity


async def get_verified_alumni_with_embeddings(db: AsyncSession) -> List[Tuple[AlumniProfile, User]]:
    result = await db.execute(
        select(AlumniProfile, User)
        .join(User, AlumniProfile.user_id == User.id)
        .where(
            User.verification_status == VerificationStatus.verified,
            AlumniProfile.embedding.is_not(None),
        )
    )
    return result.all()


async def upsert_match_score(student_id: int, alumni_id: int, score: float, db: AsyncSession) -> MatchScore:
    result = await db.execute(
        select(MatchScore).where(
            MatchScore.student_id == student_id,
            MatchScore.alumni_id == alumni_id,
        )
    )
    match = result.scalar_one_or_none()
    if match:
        match.score = score
        match.cosine_similarity = score
    else:
        match = MatchScore(student_id=student_id, alumni_id=alumni_id, score=score, cosine_similarity=score)
        db.add(match)
    await db.flush()
    return match
