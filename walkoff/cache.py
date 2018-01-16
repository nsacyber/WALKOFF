from datetime import timedelta
from diskcache import FanoutCache, DEFAULT_SETTINGS
import logging
import os
from walkoff.config.paths import cache_path

logger = logging.getLogger(__name__)


class DiskCacheAdapter(object):
    def __init__(self, directory, shards=8, timeout=60, retry=True, **settings):
        self.directory = directory
        self.retry = retry
        self.cache = FanoutCache(directory, shards=shards, timeout=timeout, **settings)

    def set(self, key, value, expire=None, **opts):
        if expire is not None:
            expire = self._convert_expire_to_seconds(expire)
        return self.cache.set(key, value, expire=expire, retry=opts.get('retry', self.retry), **opts)

    def get(self, key, **opts):
        return self.cache.get(key, default=None, retry=opts.get('retry', self.retry), **opts)

    def add(self, key, value, expire=None, **opts):
        if expire is not None:
            expire = self._convert_expire_to_seconds(expire)
        return self.cache.add(key, value, expire=expire, retry=opts.get('retry', self.retry), **opts)

    def incr(self, key, amount=1, retry=None):
        retry = retry if retry is not None else self.retry
        return self.cache.incr(key, delta=amount, default=0, retry=retry)

    def decr(self, key, amount=1, retry=None):
        retry = retry if retry is not None else self.retry
        return self.cache.decr(key, delta=amount, default=0, retry=retry)

    def rpush(self, key, *values):
        deque = self.cache.deque(key)
        deque.extend(values)

    def rpop(self, key):
        deque = self.cache.deque(key)
        return deque.pop()

    def lpush(self, key, *values):
        deque = self.cache.deque(key)
        deque.extendleft(values)

    def lpop(self, key):
        deque = self.cache.deque(key)
        return deque.popleft()

    @staticmethod
    def _convert_expire_to_seconds(time):
        return time.total_seconds() if isinstance(time, timedelta) else float(time)/1000.

    def shutdown(self):
        self.cache.close()

    def clear(self):
        self.cache.clear()

    @classmethod
    def from_json(cls, json_in):
        directory = json_in.pop('directory', cache_path)
        shards = json_in.pop('shards', 8)
        timeout = json_in.pop('timeout', 60)
        retry = json_in.pop('retry', True)
        settings = {key: value for key, value in json_in.items() if key in DEFAULT_SETTINGS}
        return cls(directory, shards=shards, timeout=timeout, retry=retry, **settings)


class RedisCacheAdapter(object):
    _requires = ['redis']

    def __init__(self, **opts):
        from redis import StrictRedis
        self.cache = StrictRedis(**opts)

    def set(self, key, value, expire=None, **opts):  # expire can be datetime or ms
        return self.cache.set(key, value, px=expire, **opts)

    def get(self, key, **opts):
        return self.cache.get(key)

    def add(self, key, value, expire=None, **opts):
        return self.cache.set(key, value, px=expire, nx=True, **opts)

    def incr(self, key, amount=1):
        return self.cache.incr(key, amount)

    def decr(self, key, amount=1):
        return self.cache.decr(key, amount)

    def rpush(self, key, *values):
        return self.cache.rpush(key, *values)

    def rpop(self, key):
        return self.cache.rpop(key)

    def lpush(self, key, *values):
        return self.cache.lpush(key, *values)

    def lpop(self, key):
        return self.cache.lpop(key)

    def shutdown(self):
        pass  # Redis's ConnectionPool should handle it

    def clear(self):
        self.cache.flushdb()

    @classmethod
    def from_json(cls, json_in):
        password = os.getenv('WALKOFF_REDIS_PASS')
        if password is not None:
            json_in['password'] = password
        return cls(**json_in)


cache_translation = {'disk': DiskCacheAdapter, 'redis': RedisCacheAdapter}

cache = None


def make_cache(config=None):
    if config is None:
        config = {}
    global cache
    cache_type = config.pop('type', 'disk').lower()
    try:
        cache = cache_translation[cache_type].from_json(config)
    except KeyError:
        logger.error('Unknown cache type {} selected. Creating default DiskCache'.format(cache_type))
        cache = DiskCacheAdapter.from_json(config)
    except ImportError:
        logger.error(
            'Could not import required packages to create cache type {0}. '
            'Cache type requires the following packages {1}. '
            'Using default DiskCache'.format(cache_type, getattr(cache_translation[cache_type], '_requires', [])))
        cache = DiskCacheAdapter.from_json(config)

    logger.info('Created {} cache connection'.format(cache_type))
    return cache
