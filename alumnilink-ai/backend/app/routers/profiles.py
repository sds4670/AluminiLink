from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.dependencies import require_student, require_alumni
from app.models.user import User, VerificationStatus
from app.models.student_profile import StudentProfile
from app.models.alumni_profile import AlumniProfile
from app.schemas.profile import (
    StudentProfileCreate, StudentProfileResponse,
    AlumniProfileCreate, AlumniProfileResponse,
)
from app.services.ml.embeddings import encode_text

router = APIRouter(prefix="/api/v1/profiles", tags=["profiles"])


def _student_response(profile: StudentProfile, user: User) -> StudentProfileResponse:
    return StudentProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        full_name=user.full_name,
        department=profile.department,
        degree=profile.degree,
        graduation_year=profile.graduation_year,
        career_goal=profile.career_goal,
        skills=profile.skills or [],
        profile_description=profile.profile_description,
        created_at=profile.created_at,
    )


def _alumni_response(profile: AlumniProfile, user: User) -> AlumniProfileResponse:
    return AlumniProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        full_name=user.full_name,
        company=profile.company,
        designation=profile.designation,
        industry=profile.industry,
        experience_years=profile.experience_years,
        skills=profile.skills or [],
        about_me=profile.about_me,
        verification_status=user.verification_status.value,
        is_accepting_mentees=profile.is_accepting_mentees,
        created_at=profile.created_at,
    )


def _student_embedding_text(data: StudentProfileCreate) -> str:
    return f"{data.career_goal} {' '.join(data.skills)} {data.profile_description}"


def _alumni_embedding_text(data: AlumniProfileCreate) -> str:
    return f"{data.designation} {data.industry} {' '.join(data.skills)} {data.about_me}"


@router.post("/student", response_model=StudentProfileResponse, status_code=201)
async def create_student_profile(
    data: StudentProfileCreate,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Profile already exists")

    embedding = encode_text(_student_embedding_text(data))
    profile = StudentProfile(user_id=current_user.id, embedding=embedding, **data.model_dump())
    db.add(profile)
    await db.flush()
    await db.refresh(profile)
    return _student_response(profile, current_user)


@router.get("/student/me", response_model=StudentProfileResponse)
async def get_my_student_profile(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return _student_response(profile, current_user)


@router.put("/student/me", response_model=StudentProfileResponse)
async def update_student_profile(
    data: StudentProfileCreate,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    for field, value in data.model_dump().items():
        setattr(profile, field, value)
    profile.embedding = encode_text(_student_embedding_text(data))
    await db.flush()
    await db.refresh(profile)
    return _student_response(profile, current_user)


@router.post("/alumni", response_model=AlumniProfileResponse, status_code=201)
async def create_alumni_profile(
    data: AlumniProfileCreate,
    current_user: User = Depends(require_alumni),
    db: AsyncSession = Depends(get_db),
):
    if current_user.verification_status != VerificationStatus.verified:
        raise HTTPException(status_code=403, detail="Alumni account must be verified before creating a profile")

    existing = await db.execute(select(AlumniProfile).where(AlumniProfile.user_id == current_user.id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Profile already exists")

    embedding = encode_text(_alumni_embedding_text(data))
    profile = AlumniProfile(user_id=current_user.id, embedding=embedding, **data.model_dump())
    db.add(profile)
    await db.flush()
    await db.refresh(profile)
    return _alumni_response(profile, current_user)


@router.get("/alumni/me", response_model=AlumniProfileResponse)
async def get_my_alumni_profile(
    current_user: User = Depends(require_alumni),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AlumniProfile).where(AlumniProfile.user_id == current_user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return _alumni_response(profile, current_user)


@router.put("/alumni/me", response_model=AlumniProfileResponse)
async def update_alumni_profile(
    data: AlumniProfileCreate,
    current_user: User = Depends(require_alumni),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AlumniProfile).where(AlumniProfile.user_id == current_user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    for field, value in data.model_dump().items():
        setattr(profile, field, value)
    profile.embedding = encode_text(_alumni_embedding_text(data))
    await db.flush()
    await db.refresh(profile)
    return _alumni_response(profile, current_user)


@router.get("/alumni/{user_id}", response_model=AlumniProfileResponse)
async def get_alumni_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    """Public endpoint — no auth required."""
    result = await db.execute(
        select(AlumniProfile, User)
        .join(User, AlumniProfile.user_id == User.id)
        .where(AlumniProfile.user_id == user_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Alumni profile not found")
    profile, user = row
    return _alumni_response(profile, user)
