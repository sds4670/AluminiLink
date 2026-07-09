from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.core.dependencies import require_student_or_alumni, get_optional_user
from app.models.user import User
from app.models.post import Post, PostType, ModerationStatus
from app.models.post_moderation_log import PostModerationLog, ModerationAction
from app.models.post_like import PostLike
from app.models.post_comment import PostComment
from app.schemas.feed import (
    PostCreate,
    PostResponse,
    PostCreateResponse,
    ModerationResult,
    CommentCreate,
    CommentResponse,
    LikeToggleResponse,
)
from app.services.ml.moderation import moderate_post

router = APIRouter(prefix="/api/v1/feed", tags=["feed"])


async def _post_response(post: Post, author: User, db: AsyncSession, viewer: Optional[User]) -> PostResponse:
    like_count = await db.scalar(select(func.count()).select_from(PostLike).where(PostLike.post_id == post.id))
    comment_count = await db.scalar(select(func.count()).select_from(PostComment).where(PostComment.post_id == post.id))
    liked_by_me = False
    if viewer:
        liked_result = await db.execute(
            select(PostLike).where(PostLike.post_id == post.id, PostLike.user_id == viewer.id)
        )
        liked_by_me = liked_result.scalar_one_or_none() is not None
    return PostResponse(
        id=post.id,
        author_id=post.author_id,
        author_name=author.full_name,
        author_role=author.role.value,
        post_type=post.post_type,
        content=post.content,
        moderation_status=post.moderation_status,
        created_at=post.created_at,
        like_count=like_count or 0,
        comment_count=comment_count or 0,
        liked_by_me=liked_by_me,
    )


@router.post("/posts", response_model=PostCreateResponse, status_code=201)
async def create_post(
    data: PostCreate,
    current_user: User = Depends(require_student_or_alumni),
    db: AsyncSession = Depends(get_db),
):
    """
    curl -X POST http://localhost:8000/api/v1/feed/posts \\
      -H "Authorization: Bearer <access_token>" -H "Content-Type: application/json" \\
      -d '{"content":"Excited to share that our team is hiring summer interns for a data science project this year.","post_type":"internship"}'
    """
    result = moderate_post(data.content)

    if result["approved"]:
        moderation_status = ModerationStatus.approved
    elif result["layer_failed"] == "admin_review":
        # Borderline toxicity: not an outright rejection — goes to the admin queue instead.
        moderation_status = ModerationStatus.pending_review
    else:
        moderation_status = ModerationStatus.rejected

    post = Post(
        author_id=current_user.id,
        post_type=data.post_type,
        content=data.content,
        moderation_status=moderation_status,
        toxicity_score=result["toxicity_score"],
    )
    db.add(post)
    await db.flush()
    await db.refresh(post)

    if not result["approved"]:
        action = ModerationAction.flagged if moderation_status == ModerationStatus.pending_review else ModerationAction.auto_rejected
        db.add(PostModerationLog(
            post_id=post.id,
            action=action,
            layer_failed=result["layer_failed"],
            toxicity_score=result["toxicity_score"],
            reason=result["reason"],
        ))

    if moderation_status == ModerationStatus.rejected:
        # Persist the rejected post + log before raising: get_db() rolls back
        # the session on any exception, and we want this record to survive
        # even though the request itself returns an error to the author.
        await db.commit()
        raise HTTPException(status_code=400, detail=result)

    response = await _post_response(post, current_user, db, current_user)
    return PostCreateResponse(post=response, moderation=ModerationResult(**result))


@router.get("/posts", response_model=List[PostResponse])
async def list_posts(
    post_type: Optional[PostType] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint — no auth required."""
    query = (
        select(Post, User)
        .join(User, Post.author_id == User.id)
        .where(Post.moderation_status == ModerationStatus.approved)
    )
    if post_type:
        query = query.where(Post.post_type == post_type)
    query = query.order_by(Post.is_pinned.desc(), Post.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    return [await _post_response(post, author, db, current_user) for post, author in result.all()]


@router.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: int,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint — no auth required."""
    result = await db.execute(
        select(Post, User).join(User, Post.author_id == User.id).where(Post.id == post_id)
    )
    row = result.first()
    if not row or row[0].moderation_status != ModerationStatus.approved:
        raise HTTPException(status_code=404, detail="Post not found")
    post, author = row
    return await _post_response(post, author, db, current_user)


@router.post("/posts/{post_id}/like", response_model=LikeToggleResponse)
async def toggle_like(
    post_id: int,
    current_user: User = Depends(require_student_or_alumni),
    db: AsyncSession = Depends(get_db),
):
    post_result = await db.execute(select(Post).where(Post.id == post_id))
    if not post_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Post not found")

    existing = await db.execute(
        select(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == current_user.id)
    )
    like = existing.scalar_one_or_none()
    if like:
        await db.delete(like)
        liked = False
    else:
        db.add(PostLike(post_id=post_id, user_id=current_user.id))
        liked = True
    await db.flush()

    count = await db.scalar(select(func.count()).select_from(PostLike).where(PostLike.post_id == post_id))
    return LikeToggleResponse(liked=liked, like_count=count or 0)


@router.post("/posts/{post_id}/comments", response_model=CommentResponse, status_code=201)
async def create_comment(
    post_id: int,
    data: CommentCreate,
    current_user: User = Depends(require_student_or_alumni),
    db: AsyncSession = Depends(get_db),
):
    post_result = await db.execute(select(Post).where(Post.id == post_id))
    if not post_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Post not found")

    result = moderate_post(data.content)
    if not result["approved"]:
        raise HTTPException(status_code=400, detail=result)

    comment = PostComment(post_id=post_id, user_id=current_user.id, content=data.content)
    db.add(comment)
    await db.flush()
    await db.refresh(comment)
    return CommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        author_id=current_user.id,
        author_name=current_user.full_name,
        author_role=current_user.role.value,
        content=comment.content,
        created_at=comment.created_at,
    )


@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
async def list_comments(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PostComment, User)
        .join(User, PostComment.user_id == User.id)
        .where(PostComment.post_id == post_id)
        .order_by(PostComment.created_at)
    )
    return [
        CommentResponse(
            id=c.id,
            post_id=c.post_id,
            author_id=user.id,
            author_name=user.full_name,
            author_role=user.role.value,
            content=c.content,
            created_at=c.created_at,
        )
        for c, user in result.all()
    ]
