from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.post import Post, PostStatus
from app.workers.tasks import run_post_moderation

router = APIRouter(prefix="/api/feed", tags=["feed"])


class PostCreate(BaseModel):
    title: Optional[str] = None
    content: str


class PostResponse(BaseModel):
    id: int
    author_id: int
    title: Optional[str]
    content: str
    status: PostStatus
    is_pinned: bool
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/", response_model=List[PostResponse])
async def get_feed(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Post)
        .where(Post.status == PostStatus.approved)
        .order_by(Post.is_pinned.desc(), Post.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.post("/", response_model=PostResponse, status_code=201)
async def create_post(
    data: PostCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    post = Post(author_id=current_user.id, title=data.title, content=data.content)
    db.add(post)
    await db.flush()
    await db.refresh(post)
    run_post_moderation.delay(post.id)
    return post


@router.delete("/{post_id}", status_code=204)
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    await db.delete(post)
