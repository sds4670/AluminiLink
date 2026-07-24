from datetime import datetime, date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User, UserRole, UserStatus, VerificationStatus
from app.models.alumni_profile import AlumniProfile
from app.models.post import Post, ModerationStatus
from app.models.post_moderation_log import PostModerationLog, ModerationAction
from app.models.audit_log import AuditLog
from app.models.analytics_snapshot import AnalyticsSnapshot
from app.schemas.auth import UserResponse
from app.schemas.feed import ModerationQueueItem, PostResponse
from app.services.screener_service import approve_alumni, reject_alumni
from app.services.analytics_service import compute_metrics, save_snapshot

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
# Kept as a distinct object for main.py's existing `admin.moderation_router` include;
# both routers now share the same /api/v1/admin prefix.
moderation_router = APIRouter(prefix="/api/v1/admin/moderation", tags=["moderation"])


class AuditLogResponse(BaseModel):
    id: int
    actor_id: Optional[int]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[int]
    details: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class UserAdminResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: str
    status: str
    verification_status: str
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SnapshotResponse(BaseModel):
    snapshot_date: date
    metrics: dict


class PendingAlumniResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    register_number: Optional[str] = None
    created_at: datetime
    # None when the alumnus hasn't filled in their profile yet — an admin
    # can't meaningfully verify someone with nothing to review.
    company: Optional[str] = None
    designation: Optional[str] = None
    industry: Optional[str] = None
    experience_years: Optional[int] = None
    skills: Optional[List[str]] = None
    about_me: Optional[str] = None


@router.get("/alumni/pending", response_model=List[PendingAlumniResponse])
async def list_pending_alumni(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User, AlumniProfile)
        .outerjoin(AlumniProfile, AlumniProfile.user_id == User.id)
        .where(
            User.role == UserRole.alumni,
            User.verification_status == VerificationStatus.pending,
        )
    )
    return [
        PendingAlumniResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            register_number=user.register_number,
            created_at=user.created_at,
            company=profile.company if profile else None,
            designation=profile.designation if profile else None,
            industry=profile.industry if profile else None,
            experience_years=profile.experience_years if profile else None,
            skills=profile.skills if profile else None,
            about_me=profile.about_me if profile else None,
        )
        for user, profile in result.all()
    ]


@router.post("/alumni/{user_id}/approve", response_model=UserResponse)
async def approve(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await approve_alumni(user_id, db)
        log = AuditLog(actor_id=current_user.id, action="approve_alumni", resource_type="user", resource_id=user_id)
        db.add(log)
        return user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/alumni/{user_id}/reject", response_model=UserResponse)
async def reject(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await reject_alumni(user_id, db)
        log = AuditLog(actor_id=current_user.id, action="reject_alumni", resource_type="user", resource_id=user_id)
        db.add(log)
        return user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/users", response_model=List[UserAdminResponse])
async def list_users(
    role: Optional[UserRole] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(User)
    if role:
        query = query.where(User.role == role)
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()


@router.patch("/users/{user_id}/ban")
async def ban_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.status = UserStatus.banned
    log = AuditLog(actor_id=current_user.id, action="ban_user", resource_type="user", resource_id=user_id)
    db.add(log)
    return {"message": "User banned"}


@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    action: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(AuditLog)
    if action:
        query = query.where(AuditLog.action == action)
    result = await db.execute(query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/analytics/summary")
async def analytics_summary(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    curl http://localhost:8000/api/v1/admin/analytics/summary \\
      -H "Authorization: Bearer <admin access_token>"
    """
    metrics = await compute_metrics(db)
    await save_snapshot(db, metrics)
    return metrics


@router.get("/analytics/snapshots", response_model=List[SnapshotResponse])
async def analytics_snapshots(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    cutoff = date.today() - timedelta(days=30)
    result = await db.execute(
        select(AnalyticsSnapshot)
        .where(AnalyticsSnapshot.snapshot_date >= cutoff)
        .order_by(AnalyticsSnapshot.snapshot_date)
    )
    return result.scalars().all()


@moderation_router.get("/queue", response_model=List[ModerationQueueItem])
async def moderation_queue(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Post, User)
        .join(User, Post.author_id == User.id)
        .where(Post.moderation_status == ModerationStatus.pending_review)
        .order_by(Post.created_at)
    )
    return [
        ModerationQueueItem(
            id=post.id,
            author_id=author.id,
            author_name=author.full_name,
            post_type=post.post_type,
            content=post.content,
            toxicity_score=post.toxicity_score,
            layer_failed=None,
            created_at=post.created_at,
        )
        for post, author in result.all()
    ]


async def _get_pending_post(post_id: int, db: AsyncSession) -> Post:
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@moderation_router.patch("/{post_id}/approve", response_model=PostResponse)
async def approve_post(
    post_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    post = await _get_pending_post(post_id, db)
    post.moderation_status = ModerationStatus.approved
    db.add(PostModerationLog(
        post_id=post.id,
        moderator_id=current_user.id,
        action=ModerationAction.approved,
        toxicity_score=post.toxicity_score,
        reason="Approved by admin after manual review",
    ))
    await db.flush()

    author_result = await db.execute(select(User).where(User.id == post.author_id))
    author = author_result.scalar_one()
    return PostResponse(
        id=post.id, author_id=author.id, author_name=author.full_name, author_role=author.role.value,
        post_type=post.post_type, content=post.content, link_url=post.link_url, moderation_status=post.moderation_status,
        created_at=post.created_at, like_count=0, comment_count=0, liked_by_me=False,
    )


@moderation_router.patch("/{post_id}/reject", response_model=PostResponse)
async def reject_post(
    post_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    post = await _get_pending_post(post_id, db)
    post.moderation_status = ModerationStatus.rejected
    db.add(PostModerationLog(
        post_id=post.id,
        moderator_id=current_user.id,
        action=ModerationAction.rejected,
        toxicity_score=post.toxicity_score,
        reason="Rejected by admin after manual review",
    ))
    await db.flush()

    author_result = await db.execute(select(User).where(User.id == post.author_id))
    author = author_result.scalar_one()
    return PostResponse(
        id=post.id, author_id=author.id, author_name=author.full_name, author_role=author.role.value,
        post_type=post.post_type, content=post.content, link_url=post.link_url, moderation_status=post.moderation_status,
        created_at=post.created_at, like_count=0, comment_count=0, liked_by_me=False,
    )
