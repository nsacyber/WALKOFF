import logging
import os
import os.path
import sqlite3
from datetime import timedelta
from functools import partial
from weakref import WeakSet

from diskcache import FanoutCache, DEFAULT_SETTINGS, Cache
from diskcache.core import DBNAME
from gevent import sleep
from gevent.event import AsyncResult, Event

from walkoff.config.paths import cache_path

logger = logging.getLogger(__name__)

unsubscribe_message = '__UNSUBSCRIBE__'


class DiskSubscription(object):
    def __init__(self, channel):
        self.channel = channel
        self._listener = None
        self._result = AsyncResult()
        self._sync = Event()

    def listen(self):
        self._listener = self._listen()
        return self._listener

    def _listen(self):
        while True:
            result = self._result.get()
            if result == unsubscribe_message:
                break
            else:
                yield result
            self._sync.wait()

    def push(self, value):
        if self._listener is not None:
            self._result.set(value)
            sleep(0)
            self._sync.set()
            self._sync.clear()


class DiskPubSubCache(object):
    def __init__(self, directory, timeout=0.01):
        self.cache = Cache(directory, timeout=timeout)
        self._subscribers = {}  # Would be nice to use a weakref to a set so that keys with no subscribers are
        # removed from dict
        push_partial = partial(self.__push_to_subscribers)
        con = self._con
        con.create_function('push', 2, push_partial)
        con.execute('CREATE TRIGGER IF NOT EXISTS push AFTER INSERT ON Cache BEGIN '
                    'SELECT push(NEW.key, NEW.value); END;')
        con.execute('CREATE TRIGGER IF NOT EXISTS push AFTER UPDATE ON Cache BEGIN '
                    'SELECT push(NEW.key, NEW.value); END;')

    def publish(self, channel, data):
        self.cache.set(channel, data)
        return len(self._subscribers.get(channel, []))

    def subscribe(self, channel):
        subscription = DiskSubscription(channel)
        if channel not in self._subscribers:
            self._subscribers[channel] = WeakSet([subscription])
        else:
            self._subscribers[channel].add(subscription)
        return subscription

    def __push_to_subscribers(self, channel, value):
        value = str(value)
        for subscriber in self._subscribers.get(str(channel), []):
            subscriber.push(value)

    @property
    def _con(self):
        con = getattr(self.cache._local, 'con', None)

        if con is None:
            con = self.cache._local.con = sqlite3.connect(
                os.path.join(self.cache._directory, DBNAME),
                timeout=self.cache._timeout,
                isolation_level=None,
            )

            # Some SQLite pragmas work on a per-connection basis so query the
            # Settings table and reset the pragmas. The Settings table may not
            # exist so catch and ignore the OperationalError that may occur.

            try:
                select = 'SELECT key, value FROM Settings'
                settings = con.execute(select).fetchall()
            except sqlite3.OperationalError:
                pass
            else:
                for key, value in settings:
                    if key.startswith('sqlite_'):
                        self.cache.reset(key, value, update=False)

        return con


class DiskCacheAdapter(object):
    def __init__(self, directory, shards=8, timeout=0.01, retry=True, **settings):
        self.directory = directory
        self.retry = retry
        self.cache = FanoutCache(directory, shards=shards, timeout=timeout, **settings)
        self.pubsub_cache = DiskPubSubCache(directory=os.path.join(directory, 'channels'), timeout=timeout)

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

    def subscribe(self, channel):
        return self.pubsub_cache.subscribe(channel)

    def unsubscribe(self, channel):
        return self.pubsub_cache.publish(channel, unsubscribe_message)

    def publish(self, channel, data):
        return self.pubsub_cache.publish(channel, data)

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
        timeout = json_in.pop('timeout', 0.01)
        retry = json_in.pop('retry', True)
        settings = {key: value for key, value in json_in.items() if key in DEFAULT_SETTINGS}
        return cls(directory, shards=shards, timeout=timeout, retry=retry, **settings)


class RedisSubscription(object):
    def __init__(self, channel, pubsub):
        self.channel = channel
        self._pubsub = pubsub

    def listen(self):
        return self._listen()

    def _listen(self):
        for message in self._pubsub.listen():
            data = message['data']
            if data == unsubscribe_message:
                self._pubsub.unsubscribe()
                break
            else:
                yield data
                sleep(0)


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

    def subscribe(self, channel):
        subscription = self.cache.pubsub()
        subscription.subscribe(channel)
        subscription.get_message()
        return RedisSubscription(channel, subscription)

    def unsubscribe(self, channel):
        return self.cache.publish(channel, unsubscribe_message)

    def publish(self, channel, data):
        return self.cache.publish(channel, data)

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
