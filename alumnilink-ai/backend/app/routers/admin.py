from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from app.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User, UserRole, UserStatus, VerificationStatus
from app.models.post import Post, ModerationStatus
from app.models.post_moderation_log import PostModerationLog, ModerationAction
from app.models.audit_log import AuditLog
from app.schemas.auth import UserResponse
from app.schemas.feed import ModerationQueueItem, PostResponse
from app.services.screener_service import approve_alumni, reject_alumni
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/api/admin", tags=["admin"])
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
    role: str
    status: str
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/alumni/pending", response_model=List[UserResponse])
async def list_pending_alumni(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(
            User.role == UserRole.alumni,
            User.verification_status == VerificationStatus.pending,
        )
    )
    return result.scalars().all()


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
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).offset(skip).limit(limit))
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
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/reports/summary")
async def summary_report(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    user_count = await db.scalar(select(func.count()).select_from(User))
    alumni_pending = await db.scalar(
        select(func.count()).select_from(User).where(
            User.role == UserRole.alumni,
            User.verification_status == VerificationStatus.pending,
        )
    )
    posts_pending = await db.scalar(
        select(func.count()).select_from(Post).where(Post.moderation_status == ModerationStatus.pending_review)
    )
    return {
        "total_users": user_count,
        "alumni_pending_approval": alumni_pending,
        "posts_pending_moderation": posts_pending,
    }


@moderation_router.get("/queue", response_model=List[ModerationQueueItem])
async def moderation_queue(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    curl http://localhost:8000/api/v1/admin/moderation/queue \\
      -H "Authorization: Bearer <admin access_token>"
    """
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
        post_type=post.post_type, content=post.content, moderation_status=post.moderation_status,
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
        post_type=post.post_type, content=post.content, moderation_status=post.moderation_status,
        created_at=post.created_at, like_count=0, comment_count=0, liked_by_me=False,
    )
