"""
Full pilot data seed for the AlumniLink AI demo dataset.

Loads, in order, from backend/app/scripts/:
  - students_seed.csv           -> 20 student Users + StudentProfiles (real SBERT embeddings)
  - alumni_seed.csv              -> 10 alumni Users + AlumniProfiles (real SBERT embeddings, verified)
  - (all 20 x 10 = 200 student-alumni match_scores, real cosine similarities)
  - connection_requests_seed.csv -> 30 connection_requests (20 accepted, 10 rejected)
  - sessions_seed.csv            -> 20 sessions for the accepted requests (15 completed, 4 upcoming, 1 cancelled),
                                     each completed session gets a student-authored session_feedback (rating 4-5)
  - 5 hardcoded sample posts, one per post_type

Usage:
    docker compose exec backend python -m app.scripts.seed

Safe to re-run: existing users/profiles/requests/sessions/posts (matched by natural
keys - email, student+alumni pair, etc.) are left untouched rather than duplicated.
"""

import asyncio
import csv
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path

from sqlalchemy import select

from app.database import AsyncSessionLocal, create_all_tables
from app.core.security import hash_password
from app.models.user import User, UserRole, UserStatus, VerificationStatus
from app.models.allowed_student import AllowedStudent
from app.models.allowed_alumni import AllowedAlumni
from app.models.student_profile import StudentProfile
from app.models.alumni_profile import AlumniProfile
from app.models.connection_request import ConnectionRequest, RequestStatus
from app.models.connection_window import ConnectionWindow, WindowStatus
from app.models.availability_slot import AvailabilitySlot, SlotStatus
from app.models.session import Session, SessionStatus
from app.models.session_feedback import SessionFeedback, FeedbackRole
from app.models.post import Post, PostType, ModerationStatus
from app.services.ml.embeddings import encode_text, cosine_similarity
from app.services.matching_service import upsert_match_score

CSV_DIR = Path(__file__).parent

# sessions_seed.csv uses "upcoming" as a friendlier label for a not-yet-happened
# session; the actual SessionStatus enum calls that state "scheduled".
SESSION_STATUS_MAP = {
    "completed": SessionStatus.completed,
    "upcoming": SessionStatus.scheduled,
    "cancelled": SessionStatus.cancelled,
}


def _read_csv(name: str) -> list[dict]:
    with open(CSV_DIR / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


async def _seed_students(db) -> dict[str, StudentProfile]:
    """Returns {roll_number: StudentProfile}."""
    profiles: dict[str, StudentProfile] = {}
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

        profiles[row["roll_number"]] = profile

    return profiles


async def _seed_alumni(db) -> dict[str, AlumniProfile]:
    """Returns {register_number: AlumniProfile}."""
    profiles: dict[str, AlumniProfile] = {}
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

        profiles[row["register_number"]] = profile

    return profiles


async def _seed_match_scores(db, students: dict[str, StudentProfile], alumni: dict[str, AlumniProfile]) -> int:
    pair_count = 0
    for student in students.values():
        if student.embedding is None:
            continue
        for alum in alumni.values():
            if alum.embedding is None:
                continue
            sim = cosine_similarity(student.embedding, alum.embedding)
            await upsert_match_score(student.id, alum.id, sim, db)
            pair_count += 1
    return pair_count


async def _seed_requests(
    db, students: dict[str, StudentProfile], alumni: dict[str, AlumniProfile]
) -> dict[str, ConnectionRequest]:
    """Returns {ref: ConnectionRequest} for every row in connection_requests_seed.csv."""
    requests: dict[str, ConnectionRequest] = {}
    for row in _read_csv("connection_requests_seed.csv"):
        student = students[row["student_roll_number"]]
        alum = alumni[row["alumni_register_number"]]

        result = await db.execute(
            select(ConnectionRequest).where(
                ConnectionRequest.student_id == student.id, ConnectionRequest.alumni_id == alum.id
            )
        )
        req = result.scalar_one_or_none()

        if req is None:
            status = RequestStatus.accepted if row["outcome"] == "PASS" else RequestStatus.rejected
            req = ConnectionRequest(
                student_id=student.id,
                alumni_id=alum.id,
                message=row["message"],
                screening_score=float(row["screening_score"]),
                status=status,
            )
            db.add(req)
            await db.flush()

            if status == RequestStatus.accepted:
                window = ConnectionWindow(
                    student_id=student.id,
                    alumni_id=alum.id,
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
                    status=WindowStatus.booked,
                )
                db.add(window)
                await db.flush()
                req.window_id = window.id

        requests[row["ref"]] = req

    return requests


async def _seed_sessions(
    db, requests: dict[str, ConnectionRequest], students: dict[str, StudentProfile]
) -> tuple[int, int]:
    """Creates sessions + (for completed ones) session_feedback. Returns (session_count, feedback_count)."""
    session_count = 0
    feedback_count = 0
    student_user_id_by_profile_id = {s.id: s.user_id for s in students.values()}

    for row in _read_csv("sessions_seed.csv"):
        req = requests[row["request_ref"]]

        result = await db.execute(select(Session).where(Session.request_id == req.id))
        session = result.scalar_one_or_none()

        scheduled_at = datetime.fromisoformat(row["scheduled_at"]).replace(tzinfo=timezone.utc)
        status = SESSION_STATUS_MAP[row["status"]]

        if session is None:
            slot = AvailabilitySlot(
                alumni_id=req.alumni_id,
                slot_date=scheduled_at.date(),
                start_time=scheduled_at.time(),
                end_time=(scheduled_at + timedelta(minutes=int(row["duration_minutes"]))).time(),
                status=SlotStatus.booked,
            )
            db.add(slot)
            await db.flush()

            session = Session(
                student_id=req.student_id,
                alumni_id=req.alumni_id,
                slot_id=slot.id,
                request_id=req.id,
                window_id=req.window_id,
                scheduled_at=scheduled_at,
                duration_minutes=int(row["duration_minutes"]),
                status=status,
            )
            db.add(session)
            await db.flush()
            session_count += 1

        if status == SessionStatus.completed:
            student_user_id = student_user_id_by_profile_id[req.student_id]

            fb_result = await db.execute(
                select(SessionFeedback).where(
                    SessionFeedback.session_id == session.id, SessionFeedback.reviewer_id == student_user_id
                )
            )
            if fb_result.scalar_one_or_none() is None:
                feedback = SessionFeedback(
                    session_id=session.id,
                    reviewer_id=student_user_id,
                    reviewer_role=FeedbackRole.student,
                    rating=random.choice([4, 5]),
                    comment="Great conversation, really helpful advice!",
                )
                db.add(feedback)
                feedback_count += 1

    return session_count, feedback_count


SAMPLE_POSTS = [
    (PostType.internship, "We're hiring 3 summer data science interns at Google's recommendations team. Strong Python + ML fundamentals a plus. DM if interested!"),
    (PostType.job, "Deutsche Bank's risk analytics team is hiring a junior data analyst. SQL + Tableau experience preferred. Happy to refer strong candidates."),
    (PostType.event, "Hosting a virtual AMA on breaking into NLP research next Friday at 6pm. Bring your questions about transformers, research careers, and grad school."),
    (PostType.resource, "Sharing my favourite free resource for learning distributed data pipelines: the Airflow official docs + the 'Designing Data-Intensive Applications' book."),
    (PostType.query, "Curious how others approached the transition from a generalist SWE role into MLOps - any course or project recommendations?"),
]


async def _seed_posts(db, students: dict[str, StudentProfile], alumni: dict[str, AlumniProfile]) -> int:
    created = 0
    result = await db.execute(select(Post.content))
    existing_content = {row[0] for row in result.all()}

    alumni_user_ids = [a.user_id for a in list(alumni.values())[:4]]
    student_user_id = list(students.values())[0].user_id
    authors = alumni_user_ids + [student_user_id]

    for (post_type, content), author_id in zip(SAMPLE_POSTS, authors):
        if content in existing_content:
            continue
        db.add(
            Post(
                author_id=author_id,
                post_type=post_type,
                content=content,
                moderation_status=ModerationStatus.approved,
            )
        )
        created += 1

    return created


async def seed() -> None:
    await create_all_tables()

    async with AsyncSessionLocal() as db:
        students = await _seed_students(db)
        alumni = await _seed_alumni(db)
        await db.flush()

        pair_count = await _seed_match_scores(db, students, alumni)
        requests = await _seed_requests(db, students, alumni)
        session_count, feedback_count = await _seed_sessions(db, requests, students)
        post_count = await _seed_posts(db, students, alumni)

        await db.commit()

    print(f"Seeded {len(students)} students and {len(alumni)} alumni with profiles + embeddings.")
    print(f"Pre-computed {pair_count} match_scores.")
    print(f"Seeded {len(requests)} connection_requests.")
    print(f"Seeded {session_count} sessions and {feedback_count} session_feedback rows.")
    print(f"Seeded {post_count} posts.")


if __name__ == "__main__":
    asyncio.run(seed())
