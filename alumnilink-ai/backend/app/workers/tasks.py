import asyncio
from app.workers.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.services.ml.moderation import moderate_post
from sqlalchemy import select


@celery_app.task(name="app.workers.tasks.run_post_moderation", bind=True)
def run_post_moderation(self, post_id: int):
    """Run ML moderation on a newly created post."""
    async def _run():
        from app.models.post import Post, PostStatus
        from app.models.post_moderation_log import PostModerationLog, ModerationAction

        async with AsyncSessionLocal() as db:
            post_result = await db.execute(select(Post).where(Post.id == post_id))
            post = post_result.scalar_one_or_none()
            if not post:
                return

            result = moderate_post(post.content)
            post.moderation_score = result["score"]

            if result["decision"] == "approved":
                post.status = PostStatus.approved
                action = ModerationAction.auto_approved
            else:
                post.status = PostStatus.rejected
                action = ModerationAction.auto_rejected

            log = PostModerationLog(
                post_id=post_id,
                action=action,
                reason=", ".join(result.get("reasons", [])) or None,
            )
            db.add(log)
            await db.commit()

    asyncio.run(_run())


@celery_app.task(name="app.workers.tasks.screen_alumni_profile_task", bind=True)
def screen_alumni_profile_task(self, alumni_id: int):
    """Run ML screening on an alumni profile after registration."""
    async def _run():
        from app.services.screener_service import screen_alumni_profile

        async with AsyncSessionLocal() as db:
            await screen_alumni_profile(alumni_id, db)
            await db.commit()

    asyncio.run(_run())


@celery_app.task(name="app.workers.tasks.expire_window", bind=True)
def expire_window(self, window_id: int):
    """
    Fired by the Redis keyspace-notification bridge (see app.main's lifespan)
    when a `window:{id}` TTL key expires — i.e. the student never booked a
    slot within the 48-hour window.
    """
    async def _run():
        from sqlalchemy import select
        from app.models.connection_window import ConnectionWindow, WindowStatus
        from app.models.connection_request import ConnectionRequest, RequestStatus
        from app.models.audit_log import AuditLog

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(ConnectionWindow).where(ConnectionWindow.id == window_id))
            window = result.scalar_one_or_none()
            # Already booked (or already expired) in the meantime — nothing to do.
            # No slot needs "freeing": slots are only ever touched at actual booking
            # time (POST /sessions/book), never reserved just for having an active window.
            if not window or window.status != WindowStatus.active:
                return

            window.status = WindowStatus.expired

            req_result = await db.execute(
                select(ConnectionRequest).where(ConnectionRequest.window_id == window_id)
            )
            req = req_result.scalar_one_or_none()
            if req:
                req.status = RequestStatus.expired

            db.add(AuditLog(
                actor_id=None,
                action="expire_window",
                resource_type="connection_window",
                resource_id=window_id,
                details="48-hour booking window expired without a session being booked",
            ))
            await db.commit()

    asyncio.run(_run())
