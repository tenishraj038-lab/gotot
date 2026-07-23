import json
import logging
from typing import Optional
import redis.asyncio as aioredis
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger("gotot.cache")

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> Optional[aioredis.Redis]:
    global _redis
    if _redis is not None:
        return _redis
    if not settings.redis_url or settings.redis_url.startswith("fake"):
        return None
    try:
        _redis = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2,
        )
        await _redis.ping()
        logger.info("Redis cache connected")
    except Exception as e:
        logger.warning(f"Redis unavailable, caching disabled: {e}")
        _redis = None
    return _redis


async def cache_get(key: str) -> Optional[str]:
    try:
        r = await get_redis()
        if r:
            return await r.get(key)
    except Exception as e:
        logger.debug(f"Cache get error: {e}")
    return None


async def cache_set(key: str, value: str, ttl: int = 3600):
    try:
        r = await get_redis()
        if r:
            await r.setex(key, ttl, value)
    except Exception as e:
        logger.debug(f"Cache set error: {e}")


async def cache_delete(key: str):
    try:
        r = await get_redis()
        if r:
            await r.delete(key)
    except Exception as e:
        logger.debug(f"Cache delete error: {e}")


async def get_cached_video_info(url: str) -> Optional[dict]:
    data = await cache_get(f"vinfo:{url}")
    if data:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            pass
    return None


async def set_cached_video_info(url: str, info: dict, ttl: Optional[int] = None):
    await cache_set(
        f"vinfo:{url}",
        json.dumps(info, default=str),
        ttl or settings.cache_ttl,
    )


async def invalidate_video_info(url: str):
    await cache_delete(f"vinfo:{url}")
