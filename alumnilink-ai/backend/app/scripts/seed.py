"""
Full demo data seed for Module 2 (Profiles + SBERT Matching) and the whitelist
gate from Module 1.

Loads backend/app/scripts/students_seed.csv and alumni_seed.csv, creating:
  - a User (role=student/alumni, already verified) per row
  - the matching allowed_students / allowed_alumni whitelist row (marked used)
  - a StudentProfile / AlumniProfile with a real SBERT embedding
  - match_scores for every student-alumni combination

Usage:
    docker compose exec backend python -m app.scripts.seed

Safe to re-run: existing users (matched by email) are left untouched, and
match_scores are upserted rather than duplicated.
"""

import asyncio
import csv
from pathlib import Path

from sqlalchemy import select
from app.database import AsyncSessionLocal, create_all_tables
from app.core.security import hash_password
from app.models.user import User, UserRole, UserStatus, VerificationStatus
from app.models.allowed_student import AllowedStudent
from app.models.allowed_alumni import AllowedAlumni
from app.models.student_profile import StudentProfile
from app.models.alumni_profile import AlumniProfile
from app.services.ml.embeddings import encode_text
from app.services.matching_service import upsert_match_score

CSV_DIR = Path(__file__).parent


def _read_csv(name: str) -> list[dict]:
    with open(CSV_DIR / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


async def _seed_students(db) -> list[StudentProfile]:
    profiles = []
    for row in _read_csv("students_seed.csv"):
        result = await db.execute(select(User).where(User.email == row["email"]))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                email=row["email"],
                hashed_password=hash_password(row["password"]),
                full_name=row["full_name"],
                role=UserRole.student,
                status=UserStatus.active,
                verification_status=VerificationStatus.verified,
                roll_number=row["roll_number"],
            )
            db.add(user)
            await db.flush()

            whitelist_result = await db.execute(
                select(AllowedStudent).where(AllowedStudent.roll_number == row["roll_number"])
            )
            allowed = whitelist_result.scalar_one_or_none()
            if allowed:
                allowed.is_registered = True
                allowed.registered_user_id = user.id

        profile_result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user.id))
        profile = profile_result.scalar_one_or_none()
        skills = [s.strip() for s in row["skills"].split("|") if s.strip()]

        if profile is None:
            text = f"{row['career_goal']} {' '.join(skills)} {row['profile_description']}"
            profile = StudentProfile(
                user_id=user.id,
                department=row["department"],
                degree=row["degree"],
                graduation_year=int(row["graduation_year"]),
                career_goal=row["career_goal"],
                skills=skills,
                profile_description=row["profile_description"],
                embedding=encode_text(text),
            )
            db.add(profile)
            await db.flush()

        profiles.append(profile)

    return profiles


async def _seed_alumni(db) -> list[AlumniProfile]:
    profiles = []
    for row in _read_csv("alumni_seed.csv"):
        result = await db.execute(select(User).where(User.email == row["email"]))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                email=row["email"],
                hashed_password=hash_password(row["password"]),
                full_name=row["full_name"],
                role=UserRole.alumni,
                status=UserStatus.active,
                verification_status=VerificationStatus.verified,
                register_number=row["register_number"],
            )
            db.add(user)
            await db.flush()

            whitelist_result = await db.execute(
                select(AllowedAlumni).where(AllowedAlumni.register_number == row["register_number"])
            )
            allowed = whitelist_result.scalar_one_or_none()
            if allowed:
                allowed.is_registered = True
                allowed.registered_user_id = user.id

        profile_result = await db.execute(select(AlumniProfile).where(AlumniProfile.user_id == user.id))
        profile = profile_result.scalar_one_or_none()
        skills = [s.strip() for s in row["skills"].split("|") if s.strip()]

        if profile is None:
            text = f"{row['designation']} {row['industry']} {' '.join(skills)} {row['about_me']}"
            profile = AlumniProfile(
                user_id=user.id,
                company=row["company"],
                designation=row["designation"],
                industry=row["industry"],
                experience_years=int(row["experience_years"]),
                skills=skills,
                about_me=row["about_me"],
                embedding=encode_text(text),
            )
            db.add(profile)
            await db.flush()

        profiles.append(profile)

    return profiles


async def seed() -> None:
    await create_all_tables()

    async with AsyncSessionLocal() as db:
        students = await _seed_students(db)
        alumni = await _seed_alumni(db)
        await db.flush()

        pair_count = 0
        for student in students:
            if not student.embedding:
                continue
            for alum in alumni:
                if not alum.embedding:
                    continue
                from app.services.ml.embeddings import cosine_similarity
                sim = cosine_similarity(student.embedding, alum.embedding)
                await upsert_match_score(student.id, alum.id, sim, db)
                pair_count += 1

        await db.commit()

    print(f"Seeded {len(students)} students and {len(alumni)} alumni with profiles + embeddings.")
    print(f"Pre-computed {pair_count} match_scores.")


if __name__ == "__main__":
    asyncio.run(seed())
