import logging
from contextlib import asynccontextmanager
from urllib.parse import urlparse

import aioredis
# import redis

from common.config import config, static

logger = logging.getLogger("WALKOFF")


@asynccontextmanager
async def connect_to_aioredis_pool(redis_uri) -> aioredis.Redis:
    # Redis client bound to pool of connections (auto-reconnecting).
    redis_pool = await aioredis.create_redis_pool(redis_uri, password=config.get_from_file(config.REDIS_KEY_PATH))
    try:
        yield redis_pool
    finally:
        # gracefully close pool
        redis_pool.close()
        await redis_pool.wait_closed()
        logger.info("Redis connection pool closed.")


# def connect_to_redis_pool(redis_uri) -> redis.Redis:
#     url = urlparse(redis_uri).netloc.split(":")
#     host = url[0]
#     port = 6379 if len(url) < 2 else url[1]
#     return redis.Redis(host=host, port=port, password=config.get_from_file(config.REDIS_KEY_PATH))


def deref_stream_message(message):
    try:
        key, value = message[0][-1].popitem()
        stream = message[0][0]
        id_ = message[0][1]
        return (key, value), stream, id_

    except:
        logger.exception("Stream message formatted incorrectly.")


def xlen(redis: aioredis.Redis, key):
    """Returns the number of entries inside a stream."""
    return redis.execute(b'XLEN', key)


def xdel(redis: aioredis.Redis, stream, id_):
    """ Deletes id_ from stream. Returns the number of items deleted. """
    return redis.execute(b'XDEL', stream, id_)
