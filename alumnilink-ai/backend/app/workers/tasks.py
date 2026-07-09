import asyncio
from app.workers.celery_app import celery_app
from app.database import AsyncSessionLocal


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


@celery_app.task(name="app.workers.tasks.send_session_reminder", bind=True)
def send_session_reminder(self, session_id: int):
    """
    Placeholder for now — will send an email/notification reminder
    24 hours before a scheduled session.
    """
    pass
