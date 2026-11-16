"""
MediSync AI — Redis Client Factory
Provides an async Redis connection used for caching, pub/sub queue events,
and WebSocket session management.
"""
import redis.asyncio as aioredis

from app.core.config import settings

# Global async Redis connection pool
_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Return (and lazily create) the shared async Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    """Close the Redis connection (called on application shutdown)."""
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
