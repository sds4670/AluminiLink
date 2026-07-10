import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import create_all_tables
from app.core.redis_client import redis_client

from app.routers import auth, profiles, matching, requests, windows, sessions, availability, feed, admin, screener, predict

logger = logging.getLogger(__name__)


async def _listen_for_window_expiry():
    """
    Bridge Redis keyspace-expiry notifications to Celery: Celery has no
    built-in way to react to a Redis key expiring on its own, so this
    subscribes to Redis's `__keyevent@<db>__:expired` pub/sub channel and
    dispatches app.workers.tasks.expire_window whenever a `window:{id}` key
    (set with a 48h TTL in requests.py's accept endpoint) expires.
    """
    from app.workers.tasks import expire_window

    db_index = settings.redis_url.rsplit("/", 1)[-1] or "0"
    channel = f"__keyevent@{db_index}__:expired"

    while True:
        try:
            pubsub = redis_client.pubsub()
            await pubsub.psubscribe(channel)
            async for message in pubsub.listen():
                if message["type"] != "pmessage":
                    continue
                key = message["data"]
                if key.startswith("window:"):
                    expire_window.delay(int(key.split(":", 1)[1]))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("Redis window-expiry listener error, reconnecting: %s", exc)
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_all_tables()
    await redis_client.config_set("notify-keyspace-events", "Ex")
    listener_task = asyncio.create_task(_listen_for_window_expiry())
    yield
    listener_task.cancel()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="University alumni mentorship platform with AI-powered matching",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(matching.router)
app.include_router(requests.router)
app.include_router(windows.router)
app.include_router(sessions.router)
app.include_router(availability.router)
app.include_router(feed.router)
app.include_router(admin.router)
app.include_router(admin.moderation_router)
app.include_router(screener.router)
app.include_router(predict.router)


@app.get("/health")
async def health_check():
    try:
        from app.services.ml.embeddings import model as sbert_model
        model_status = "loaded" if sbert_model is not None else "not_loaded"
    except Exception:
        model_status = "not_loaded"

    return {"status": "ok", "app": settings.app_name, "model": model_status}
