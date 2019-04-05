import logging
from contextlib import asynccontextmanager

import aioredis

logger = logging.getLogger("WALKOFF")


def sint(value, default):
    if not isinstance(default, int):
        raise TypeError("Default value must be of integer type")
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def sfloat(value, default):
    if not isinstance(default, int):
        raise TypeError("Default value must be of float type")
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@asynccontextmanager
async def connect_to_redis_pool(redis_uri) -> aioredis.Redis:
    # Redis client bound to pool of connections (auto-reconnecting).
    redis = await aioredis.create_redis_pool(redis_uri)
    try:
        yield redis
    finally:
        # gracefully close pool
        redis.close()
        await redis.wait_closed()
        logger.info("Redis connection pool closed.")
