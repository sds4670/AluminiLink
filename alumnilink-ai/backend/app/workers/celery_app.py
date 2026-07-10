import logging
import redis
from celery import Celery
from celery.schedules import crontab
from app.config import settings

logger = logging.getLogger(__name__)

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
        "app.workers.tasks.screen_alumni_profile_task": {"queue": "screening"},
        "app.workers.tasks.expire_window": {"queue": "windows"},
        "app.workers.tasks.send_session_reminder": {"queue": "reminders"},
        "app.workers.tasks.run_nightly_etl": {"queue": "analytics"},
    },
    beat_schedule={
        "nightly-analytics-etl": {
            "task": "app.workers.tasks.run_nightly_etl",
            "schedule": crontab(hour=2, minute=0),
        },
    },
)

# Enable keyspace notifications for key-expiry events ("Ex") so the
# Redis pub/sub bridge in app.main can react when a `window:{id}` TTL key
# expires and dispatch the expire_window task above.
try:
    redis_client = redis.Redis.from_url(settings.redis_url)
    redis_client.config_set("notify-keyspace-events", "Ex")
except Exception as exc:
    logger.warning("Could not enable Redis keyspace notifications: %s", exc)
