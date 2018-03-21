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
import threading
import walkoff.config
import pickle
from copy import deepcopy
logger = logging.getLogger(__name__)

try:
    from io import BytesIO
except ImportError:
    from cStringIO import StringIO as BytesIO


unsubscribe_message = '__UNSUBSCRIBE__'
"""(str): The message used to unsubscribe from and close a PubSub channel
"""


class DiskSubscription(object):
    """A Subscription used by a PubSub channel backed by DiskCache

    Attributes:
        channel (str): The channel name associated with this subscription
        _listener (generator): The generator which yields the new values in the channel
        _result (AsyncResult): The result of the latest value in the channel
        _sync (Event): A synchronization event used to block the channel from yielding new values

    Args:
        channel (str): The channel name associated with this subscription
    """
    def __init__(self, channel):
        self.channel = channel
        self._listener = None
        self._result = AsyncResult()
        self._sync = Event()

    def listen(self):
        """Listen for updates in this channel

        Returns:
            (generator): A generator which yields new values in the channel
        """
        if self._listener is None:
            self._listener = self._listen()
        return self._listener

    def _listen(self):
        """Listen for updates in this channel and yield the results

        Yields:
            The new values in this channel
        """
        while True:
            self._sync.wait()
            result = self._result.get()
            if result == unsubscribe_message:
                break
            else:
                yield result
                sleep(0)

    def push(self, value):
        """Push a new value to the channel

        Args:
            value: The value to push to the channel
        """
        if self._listener is not None:
            self._result.set(value)
            sleep(0)
            self._sync.set()
            sleep(0)
            self._sync.clear()


class DiskPubSubCache(object):
    """A DiskCache-backed cache used for PubSub channels

    Attributes:
        cache (Cache): The cache which backs this pubsub cache
        _insert_func_name (str): The name of the function to be called when an insert occurs on the cache
        _udpate_func_name (str): The name of the function to be called when an update occurs on the cache
        _subscribers (dict{str: DiskSubscription}): The subscriptions tracked by this cache
        _threads_registered (set(str)): The names of the threads which have registered triggers on the database
        _push_partial (func): The function called when an insert or update happens on the cache

    Args:
        directory (str): The path to the directory used by this cache
        timeout (float, optional): The number of seconds to wait before an operation times out. Defaults to 0.01 seconds
    """
    _insert_func_name = 'push_on_insert'
    _update_func_name = 'push_on_update'

    def __init__(self, directory, timeout=0.01):
        self.cache = Cache(directory, timeout=timeout)
        self._subscribers = {}  # Would be nice to use a weakref to a set so that keys with no subscribers are
        self._threads_registered = set()
        self._insert_triggers()
        self._push_partial = partial(self.__push_to_subscribers)

    def publish(self, channel, data):
        """Publish data to a channel

        Args:
            channel (str): Channel to publish the data to
            data: The data to publish the data to. The data will arrive in the same format as it was set

        Returns:
            (int): The number of subscribers which received the published data
        """
        self.cache.set(channel, data)
        return len(self._subscribers.get(channel, []))

    def register_callbacks(self):
        """Registers the trigger functions for the current thread.

        A thread must have trigger functions registered before it can publish data
        """
        if threading.current_thread().name not in self._threads_registered:
            con = self._con
            for func_name in (self._insert_func_name, self._update_func_name):
                con.create_function(func_name, 2, self._push_partial)
            self._threads_registered.add(threading.current_thread().name)

    def _insert_triggers(self):
        """Inserts the original triggers into the cache, but does not create or the functions which receive the triggers
        """
        con = self._con
        for func_name, operation in [(self._insert_func_name, 'INSERT'), (self._update_func_name, 'UPDATE')]:
            con.execute('CREATE TRIGGER IF NOT EXISTS {0} AFTER {1} ON Cache BEGIN '
                        'SELECT {0}(NEW.key, NEW.value); END;'.format(func_name, operation))

    def subscribe(self, channel):
        """Subscribe to a channel

        Args:
            channel (str): The name of the channel to subscribe to

        Returns:
            (DiskSubscription): The subscription to this channel
        """
        subscription = DiskSubscription(channel)
        if channel not in self._subscribers:
            self._subscribers[channel] = WeakSet([subscription])
        else:
            self._subscribers[channel].add(subscription)
        return subscription

    def __push_to_subscribers(self, channel, value):
        try:
            value = pickle.load(BytesIO(value))
        except KeyError:
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
    """Adapter for a DiskCache backed cache

    This cache provides a wrapper for a FanoutCache which is backed by SQLite with the same interface as the
    RedisCacheAdapter. This cache provides automatic sharding and is process and thread-safe; however it should not be
    used in production for performance reasons.

    Attributes:
        directory (str): The directory to the SQLite database backing this cache
        retry (bool, optional): Should this database retry timed out transactions? Default to True
        cache (FanoutCache): The cache which is wrapped by this adapter
        pubsub_cache (DiskPubSubCache): The cache which provides pubsub capabilities to this adapter

    Args:
        directory (str): The directory to the SQLite database backing this cache
        shards (int, optional): The number of shards to split the cache into. Defaults to 8.
        timeout (float, optional): The number of seconds to wait before an operation times out. Defaults to 0.01 seconds
        retry (bool, optional): Should this database retry timed out transactions? Default to True
        **settings: Other setting which will be passsed to the `cache` attribute on initialization
    """
    def __init__(self, directory, shards=8, timeout=0.01, retry=True, **settings):
        self.directory = directory
        self.retry = retry
        self.cache = FanoutCache(directory, shards=shards, timeout=timeout, **settings)
        self.pubsub_cache = DiskPubSubCache(directory=os.path.join(directory, 'channels'), timeout=timeout)

    def set(self, key, value, expire=None, **opts):
        """Set a value for a key in the cache

        Args:
            key: The key to use for this data
            value: The value to set this key to
            expire (int|datetime.timedelta, optional): The expiration for this value. If `int` is passed, it indicates
                milliseconds
            **opts: Additional options to use. See `FanoutCache` for more details

        Returns:
            (bool): Was this key set?
        """
        if expire is not None:
            expire = self._convert_expire_to_seconds(expire)
        return self.cache.set(key, value, expire=expire, retry=opts.get('retry', self.retry), **opts)

    def get(self, key, **opts):
        """Gets the value stored in the key

        Args:
            key: The key to get the value from
            **opts: Additional options to use. See `FanoutCache` for more details.

        Returns:
            The value stored in the key
        """
        return self.cache.get(key, default=None, retry=opts.get('retry', self.retry), **opts)

    def add(self, key, value, expire=None, **opts):
        """Add a key and a value to the cache if the key is not already in the cache

        Args:
            key: The key to store the value to
            value: Teh value to store in the key
            expire (int|datetime.timedelta, optional): The expiration for this value. If `int` is passed, it indicates
                milliseconds
            **opts: Additional options to use. See `FanoutCache` for more details

        Returns:
            (bool): Was the key set?
        """
        if expire is not None:
            expire = self._convert_expire_to_seconds(expire)
        return self.cache.add(key, value, expire=expire, retry=opts.get('retry', self.retry), **opts)

    def incr(self, key, amount=1, retry=None):
        """Increments a key by an amount.

        If the key is not found, then its value becomes the increment amount specified

        Args:
            key: The key to increment
            amount (int, optional): The amount to increment the key by. Defaults to 1
            retry (bool, optional): Should this operation be retried if the transaction times out? Defaults to
                `self.retry`

        Returns:
            (int): The incremented value
        """
        retry = retry if retry is not None else self.retry
        return self.cache.incr(key, delta=amount, default=0, retry=retry)

    def decr(self, key, amount=1, retry=None):
        """Decrements a key by an amount.

        If the key is not found, then its value becomes the decrement amount specified

        Args:
            key: The key to decrement
            amount (int, optional): The amount to decrement the key by. Defaults to 1
            retry (bool, optional): Should this operation be retried if the transaction times out? Defaults to
                `self.retry`

        Returns:
            (int): The decremented value
        """
        retry = retry if retry is not None else self.retry
        return self.cache.decr(key, delta=amount, default=0, retry=retry)

    def rpush(self, key, *values):
        """Pushes a value to the right of a deque.

        This operation also creates a deque for a given key if one was not already created. Otherwise it uses the
        existing deque

        Args:
            key: The key of the deque to push the values to
            *values: The values to push to the deque
        """
        deque = self.cache.deque(key)
        deque.extend(values)

    def rpop(self, key):
        """Pops a value from the right of a deque.

        If this key is not a deque then this function will return None.

        Args:
            key: The key of the deque to push the values to
            *values: The values to push to the deque

        Returns:
            The rightmost value on the deque or None if the key is not a deque or the deque is empty
        """
        deque = self.cache.deque(key)
        try:
            return deque.pop()
        except IndexError:
            return None

    def lpush(self, key, *values):
        """Pushes a value to the left of a deque.

        This operation also creates a deque for a given key if one was not already created. Otherwise it uses the
        existing deque

        Args:
            key: The key of the deque to push the values to
            *values: The values to push to the deque
        """
        deque = self.cache.deque(key)
        deque.extendleft(values)

    def lpop(self, key):
        """Pops a value from the left of a deque.

        If this key is not a deque then this function will return None.

        Args:
            key: The key of the deque to push the values to
            *values: The values to push to the deque

        Returns:
            The leftmost value on the deque or None if the key is not a deque or the deque is empty
        """
        deque = self.cache.deque(key)
        try:
            return deque.popleft()
        except IndexError:
            return None

    def subscribe(self, channel):
        """Subscribe to a channel

        Args:
            channel (str): The name of the channel to subscribe to

        Returns:
            (DiskSubscription): The subscription for this channel
        """
        return self.pubsub_cache.subscribe(channel)

    def unsubscribe(self, channel):
        """Unsubscribe to a channel

        Args:
            channel (str): The name of the channel to subscribe to

        Returns:
            (int): The number of subscribers unsubscribed ffrom this channel
        """
        return self.pubsub_cache.publish(channel, unsubscribe_message)

    def publish(self, channel, data):
        """Publish some data to a channel

        Args:
            channel (str): The name of the channel to publish the data to
            data: The data to publish

        Returns:
            The number of subscriptions which received the data
        """
        return self.pubsub_cache.publish(channel, data)

    def register_callbacks(self):
        """Registers callbacks for the PubSubs for the current thread.

        This must be done before publishing data to any channel from this thread,
        """
        self.pubsub_cache.register_callbacks()

    @staticmethod
    def _convert_expire_to_seconds(time):
        """Converts values passed as expire time to a float seconds

        Args:
            time (int| datetime.timedelta): The expiration for this value. If `int` is passed, it indicates milliseconds

        Returns:
            (float): The expiration time in seconds
        """
        return time.total_seconds() if isinstance(time, timedelta) else float(time)/1000.

    def shutdown(self):
        """Shuts down the connection to the cache
        """
        self.cache.close()

    def clear(self):
        """Clears all values in the cache
        """
        self.cache.clear()

    @classmethod
    def from_json(cls, json_in):
        """Constructs this cache from its JSON representation

        Args:
            json_in (dict): The JSON representation of this cache configuration

        Returns:
            (DiskCacheAdapter): A DiskCacheAdapter with a configuration reflecting the values in the JSON
        """
        directory = json_in.pop('directory', walkoff.config.Config.CACHE_PATH)
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
        """Listen for updates in this channel

        Returns:
            (generator): A generator which yields new values in the channel
        """
        return self._listen()

    def _listen(self):
        """Listen for updates in this channel and yield the results

        Yields:
            The new values in this channel
        """
        for message in self._pubsub.listen():
            data = message['data']
            if data == unsubscribe_message:
                self._pubsub.unsubscribe()
                break
            else:
                yield data


class RedisCacheAdapter(object):
    _requires = ['redis']

    def __init__(self, **opts):
        from redis import StrictRedis
        self.cache = StrictRedis(**opts)

    def set(self, key, value, expire=None, **opts):
        """Set a value for a key in the cache

        Args:
            key: The key to use for this data
            value: The value to set this key to
            expire (int|datetime.timedelta, optional): The expiration for this value. If `int` is passed, it indicates
                milliseconds
            **opts: Additional options to use. See `FanoutCache` for more details

        Returns:
            (bool): Was this key set?
        """
        return self.cache.set(key, value, px=expire, **opts)

    def get(self, key, **opts):
        """Gets the value stored in the key

        Args:
            key: The key to get the value from
            **opts: Additional options to use. See `FanoutCache` for more details.

        Returns:
            The value stored in the key
        """
        return self.cache.get(key)

    def add(self, key, value, expire=None, **opts):
        """Add a key and a value to the cache if the key is not already in the cache

        Args:
            key: The key to store the value to
            value: Teh value to store in the key
            expire (int|datetime.timedelta, optional): The expiration for this value. If `int` is passed, it indicates
                milliseconds
            **opts: Additional options to use. See `FanoutCache` for more details

        Returns:
            (bool): Was the key set?
        """
        return self.cache.set(key, value, px=expire, nx=True, **opts)

    def incr(self, key, amount=1):
        """Increments a key by an amount.

        If the key is not found, then its value becomes the increment amount specified

        Args:
            key: The key to increment
            amount (int, optional): The amount to increment the key by. Defaults to 1
            retry (bool, optional): Should this operation be retried if the transaction times out? Defaults to
                `self.retry`

        Returns:
            (int): The incremented value
        """
        return self.cache.incr(key, amount)

    def decr(self, key, amount=1):
        """Decrements a key by an amount.

        If the key is not found, then its value becomes the decrement amount specified

        Args:
            key: The key to decrement
            amount (int, optional): The amount to decrement the key by. Defaults to 1
            retry (bool, optional): Should this operation be retried if the transaction times out? Defaults to
                `self.retry`

        Returns:
            (int): The decremented value
        """
        return self.cache.decr(key, amount)

    def rpush(self, key, *values):
        """Pushes a value to the right of a deque.

        This operation also creates a deque for a given key if one was not already created. Otherwise it uses the
        existing deque

        Args:
            key: The key of the deque to push the values to
            *values: The values to push to the deque
        """
        return self.cache.rpush(key, *values)

    def rpop(self, key):
        """Pops a value from the right of a deque.

        If this key is not a deque then this function will return None.

        Args:
            key: The key of the deque to push the values to
            *values: The values to push to the deque

        Returns:
            The rightmost value on the deque or None if the key is not a deque or the deque is empty
        """
        return self.cache.rpop(key)

    def lpush(self, key, *values):
        """Pushes a value to the left of a deque.

        This operation also creates a deque for a given key if one was not already created. Otherwise it uses the
        existing deque

        Args:
            key: The key of the deque to push the values to
            *values: The values to push to the deque
        """
        return self.cache.lpush(key, *values)

    def lpop(self, key):
        """Pops a value from the left of a deque.

        If this key is not a deque then this function will return None.

        Args:
            key: The key of the deque to push the values to
            *values: The values to push to the deque

        Returns:
            The leftmost value on the deque or None if the key is not a deque or the deque is empty
        """
        return self.cache.lpop(key)

    def subscribe(self, channel):
        """Subscribe to a channel

        Args:
            channel (str): The name of the channel to subscribe to

        Returns:
            (RedisSubscription): The subscription for this channel
        """
        subscription = self.cache.pubsub()
        subscription.subscribe(channel)
        subscription.get_message()
        return RedisSubscription(channel, subscription)

    def unsubscribe(self, channel):
        """Unsubscribe to a channel

        Args:
            channel (str): The name of the channel to subscribe to

        Returns:
            (int): The number of subscribers unsubscribed ffrom this channel
        """
        return self.cache.publish(channel, unsubscribe_message)

    def publish(self, channel, data):
        """Publish some data to a channel

        Args:
            channel (str): The name of the channel to publish the data to
            data: The data to publish

        Returns:
            The number of subscriptions which received the data
        """
        return self.cache.publish(channel, data)

    def shutdown(self):
        """Shuts down the connection to the cache

        For the Redis cache, this is not necessary. Redis's ConnectionPool should handle it
        """
        pass

    def clear(self):
        """Clears all values in the cache
        """
        self.cache.flushdb()

    def register_callbacks(self):
        """Registers callbacks for the PubSubs for the current thread.

        For the RedisCacheAdapter, this is not necessary
        """
        pass

    @classmethod
    def from_json(cls, json_in):
        """Constructs this cache from its JSON representation

        Args:
            json_in (dict): The JSON representation of this cache configuration

        Returns:
            (RedisCacheAdapter): A RedisCacheAdapter with a configuration reflecting the values in the JSON
        """
        password = os.getenv('WALKOFF_REDIS_PASSWORD')
        if password is not None:
            json_in['password'] = password
        if 'timeout' in json_in and json_in['timeout'] > 0:
            json_in['socket_timeout'] = json_in.pop('timeout')
        return cls(**json_in)


cache_translation = {'disk': DiskCacheAdapter, 'redis': RedisCacheAdapter}
"""(dict): A mapping between a string type and the corresponding cache adapter
"""

# Ideally this global is replaced entirely by the running_context
# This is needed currently to get this cache into the blueprints, so there are two cache connections in the apps now
cache = None
""" (RedisCacheAdapter|DiskCacheAdapter): The cache used throughout Walkoff 
"""


def make_cache(config=None):
    """Factory method for constructing Cache Adapters from configuration JSON

    Args:
        config (dict): The JSON configuration of the cache adapter

    Returns:
        (RedisCacheAdapter|DiskCacheAdapter): The constructed cache
    """
    if config is None:
        config = {}
    config = deepcopy(config)
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
