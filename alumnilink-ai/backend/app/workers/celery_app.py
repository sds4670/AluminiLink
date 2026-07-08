from celery import Celery
from app.config import settings

celery_app = Celery(
    "alumnilink",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_routes={
        "app.workers.tasks.run_post_moderation": {"queue": "moderation"},
        "app.workers.tasks.screen_alumni_profile_task": {"queue": "screening"},
    },
)
