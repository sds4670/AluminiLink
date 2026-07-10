from datetime import date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole, VerificationStatus
from app.models.connection_request import ConnectionRequest, RequestStatus
from app.models.session import Session, SessionStatus
from app.models.session_feedback import SessionFeedback
from app.models.post import Post, ModerationStatus
from app.models.match_score import MatchScore
from app.models.analytics_snapshot import AnalyticsSnapshot


async def compute_metrics(db: AsyncSession) -> dict:
    """Bronze (raw counts) -> Silver (computed rates) in one pass."""

    # --- Bronze: raw counts/aggregates straight off the tables ---
    total_students = await db.scalar(
        select(func.count()).select_from(User).where(User.role == UserRole.student)
    )
    total_alumni = await db.scalar(
        select(func.count()).select_from(User).where(User.role == UserRole.alumni)
    )
    pending_alumni = await db.scalar(
        select(func.count()).select_from(User).where(
            User.role == UserRole.alumni, User.verification_status == VerificationStatus.pending
        )
    )
    total_requests = await db.scalar(select(func.count()).select_from(ConnectionRequest))
    accepted_requests = await db.scalar(
        select(func.count()).select_from(ConnectionRequest).where(ConnectionRequest.status == RequestStatus.accepted)
    )
    rejected_requests = await db.scalar(
        select(func.count()).select_from(ConnectionRequest).where(ConnectionRequest.status == RequestStatus.rejected)
    )
    total_sessions = await db.scalar(select(func.count()).select_from(Session))
    completed_sessions = await db.scalar(
        select(func.count()).select_from(Session).where(Session.status == SessionStatus.completed)
    )
    total_posts = await db.scalar(
        select(func.count()).select_from(Post).where(Post.moderation_status == ModerationStatus.approved)
    )
    total_feedback = await db.scalar(select(func.count()).select_from(SessionFeedback))
    avg_rating = await db.scalar(select(func.avg(SessionFeedback.rating)))
    avg_match_score = await db.scalar(select(func.avg(MatchScore.cosine_similarity)))
    avg_screening_score = await db.scalar(
        select(func.avg(ConnectionRequest.screening_score)).where(ConnectionRequest.screening_score.is_not(None))
    )

    bronze = {
        "total_students": total_students or 0,
        "total_alumni": total_alumni or 0,
        "pending_alumni": pending_alumni or 0,
        "total_requests": total_requests or 0,
        "accepted_requests": accepted_requests or 0,
        "rejected_requests": rejected_requests or 0,
        "total_sessions": total_sessions or 0,
        "completed_sessions": completed_sessions or 0,
        "total_posts": total_posts or 0,
        "total_feedback": total_feedback or 0,
        "avg_rating": round(float(avg_rating), 2) if avg_rating is not None else 0.0,
        "avg_match_score": round(float(avg_match_score), 4) if avg_match_score is not None else 0.0,
        "avg_screening_score": round(float(avg_screening_score), 2) if avg_screening_score is not None else 0.0,
    }

    # --- Silver: rates derived from the bronze counts ---
    silver = {
        **bronze,
        "verified_alumni": bronze["total_alumni"] - bronze["pending_alumni"],
        "acceptance_rate": round(bronze["accepted_requests"] / bronze["total_requests"], 4) if bronze["total_requests"] > 0 else 0.0,
        "completion_rate": round(bronze["completed_sessions"] / bronze["accepted_requests"], 4) if bronze["accepted_requests"] > 0 else 0.0,
        "avg_match_score_pct": round(bronze["avg_match_score"] * 100, 1),
    }
    return silver


async def save_snapshot(db: AsyncSession, metrics: dict, snapshot_date: date | None = None) -> AnalyticsSnapshot:
    """Gold: upsert today's (or a given) snapshot_date with the computed silver metrics."""
    snapshot_date = snapshot_date or date.today()
    result = await db.execute(
        select(AnalyticsSnapshot).where(AnalyticsSnapshot.snapshot_date == snapshot_date)
    )
    snapshot = result.scalar_one_or_none()
    if snapshot:
        snapshot.metrics = metrics
    else:
        snapshot = AnalyticsSnapshot(snapshot_date=snapshot_date, metrics=metrics)
        db.add(snapshot)
    await db.flush()
    return snapshot
