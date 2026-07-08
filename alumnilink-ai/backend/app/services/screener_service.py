from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.alumni_profile import AlumniProfile
from app.models.user import User, UserRole, VerificationStatus
from app.services.ml.screener import generate_screening_report


async def screen_alumni_profile(alumni_id: int, db: AsyncSession) -> dict:
    result = await db.execute(
        select(AlumniProfile).where(AlumniProfile.id == alumni_id)
    )
    alumni = result.scalar_one_or_none()
    if not alumni:
        return {"error": "Alumni profile not found"}

    profile_data = {
        "about_me": alumni.about_me,
        "company": alumni.company,
        "designation": alumni.designation,
        "experience_years": alumni.experience_years,
        "skills": alumni.skills,
    }

    report = generate_screening_report(profile_data)
    alumni.screening_score = report["score"]
    await db.flush()
    return report


async def approve_alumni(user_id: int, db: AsyncSession) -> User:
    result = await db.execute(
        select(User).where(User.id == user_id, User.role == UserRole.alumni)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("Alumni user not found")

    user.verification_status = VerificationStatus.verified
    await db.flush()
    return user


async def reject_alumni(user_id: int, db: AsyncSession) -> User:
    result = await db.execute(
        select(User).where(User.id == user_id, User.role == UserRole.alumni)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("Alumni user not found")

    user.verification_status = VerificationStatus.rejected
    await db.flush()
    return user
