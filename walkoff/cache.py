import logging
import os
from copy import deepcopy

import os.path

logger = logging.getLogger(__name__)

try:
    from io import BytesIO
except ImportError:
    from cStringIO import StringIO as BytesIO

unsubscribe_message = b'__UNSUBSCRIBE__'
"""(str): The message used to unsubscribe from and close a PubSub channel
"""

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

    instance = None

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super(RedisCacheAdapter, cls).__new__(cls)
            logger.info('Created redis cache connection')
        return cls.instance

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
            **opts: Additional options to use.

        Returns:
            The value stored in the key
        """
        return self._decode_response(self.cache.get(key))

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

    def delete(self, key):
        """Deletes a key
        """
        return self.cache.delete(key)

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
        return int(self.cache.incr(key, amount))

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
        return int(self.cache.decr(key, amount))

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
        return self._decode_response(self.cache.rpop(key))

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
        return self._decode_response(self.cache.lpop(key))

    @staticmethod
    def _decode_response(response):
        if response is None:
            return response
        try:
            return response.decode('utf-8')
        except UnicodeDecodeError:
            return response

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

    def check(self):
        self.cache.info()

    def register_callbacks(self):
        """Registers callbacks for the PubSubs for the current thread.

        For the RedisCacheAdapter, this is not necessary
        """
        pass

    def ping(self):
        """Pings the Redis cache to test the connection

        Returns:
            (Bool): True if the ping was successful, False otherwise.
        """
        return self.cache.ping()

    def scan(self, pattern=None):
        """Scans through all keys in the cache

        Args:
            pattern (str, optional): Regex Pattern to search for

        Returns:
            Iterator(str): The keys in the cache matching the pattern if specified. Else all the keys in the cache
        """
        return (key.decode('utf-8') for key in self.cache.scan_iter(pattern))

    def exists(self, key):
        """Checks to see if a key exists in the cache

        Args:
            key: The key to check

        Returns:
            bool: Does the key exist?
        """
        return bool(self.cache.exists(key))

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


cache_translation = {'redis': RedisCacheAdapter}
"""(dict): A mapping between a string type and the corresponding cache adapter
"""


def make_cache(config=None, cache_mapping=cache_translation):
    """Factory method for constructing Cache Adapters from configuration JSON

    Args:
        config (dict): The JSON configuration of the cache adapter
        cache_mapping(dict{str:cls}): A mapping from a string describing the type of cache to make and the class to make
    Returns:
        The constructed cache object
    """
    if config is None:
        config = {}
    config = deepcopy(config)
    cache_type = config.pop('type', 'redis').lower()
    default_cache = cache_mapping.get('redis', RedisCacheAdapter)
    try:
        cache = cache_mapping[cache_type].from_json(config)
    except KeyError:
        logger.error('Unknown cache type {} selected. Creating default Redis Cache'.format(cache_type))
        cache = default_cache.from_json(config)
    except ImportError:
        logger.error(
            'Could not import required packages to create cache type {0}. '
            'Cache type requires the following packages {1}. '
            'Using default Redis Cache'.format(cache_type, getattr(cache_mapping[cache_type], '_requires', [])))
        cache = default_cache.from_json(config)
    return cache
