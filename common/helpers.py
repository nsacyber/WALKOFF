import logging
from contextlib import asynccontextmanager

import aioredis
import yaml

logger = logging.getLogger("WALKOFF")


def sint(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def sfloat(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


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


def validate_app_api(api_file):
    #  TODO: Actually validate the api
    with open(api_file, 'r') as fp:
        try:
            return yaml.load(fp)
        except yaml.YAMLError as exc:
            logger.exception(exc)
