import redis.asyncio as redis
from app.config import settings

# Shared async client for app-level Redis usage (connection windows, TTL keys).
# Separate from the Celery broker/backend DBs (redis_url uses db 0 by default).
redis_client = redis.from_url(settings.redis_url, decode_responses=True)


def window_key(window_id: int) -> str:
    return f"window:{window_id}"


async def set_window_ttl(window_id: int, ttl_seconds: int) -> None:
    await redis_client.set(window_key(window_id), "active", ex=ttl_seconds)


async def clear_window_ttl(window_id: int) -> None:
    await redis_client.delete(window_key(window_id))
