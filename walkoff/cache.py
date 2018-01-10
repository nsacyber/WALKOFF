from datetime import timedelta
from diskcache import FanoutCache, Deque
from os.path import join


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

class RedisCacheAdapter(object):

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