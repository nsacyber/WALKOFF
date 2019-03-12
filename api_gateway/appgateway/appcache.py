import logging
import json

_logger = logging.getLogger(__name__)


class AppCache:
    """ Object which caches app apis in redis"""

    # TODO: Add config options when decided
    def __init__(self, redis, api_key="app-apis"):
        self.redis = redis
        self.api_key = api_key

    def __setitem__(self, key, value):
        self.redis.hset(self.api_key, key, json.dumps(value))

    def __getitem__(self, key):
        if key in self:
            return json.loads(self.redis.hget(self.api_key, key))
        else:
            raise KeyError

    def __len__(self):
        return sum(1 for _key in self.redis.hscan_iter(self.api_key))

    def __delitem__(self, key):
        if key in self:
            self.redis.hdel(self.api_key, key)
        else:
            raise KeyError

    def __contains__(self, key):
        return self.redis.hexists(self.api_key, key)

    def __iter__(self):
        return self.keys()

    def clear(self):
        for key in self.keys():
            self.redis.hdelete(self.api_key, key)

    def update(self, other, **kwargs):
        try:
            iter(other)
            keys_method = getattr(other, "items")
            if callable(keys_method):  # it's a dictionary
                for key, val in other.items():
                    self.redis.hset(self.api_key, key, json.dumps(val))
            else:  # it's a different iterable
                for key, val in other:
                    self.redis.hset(self.api_key, key, json.dumps(val))
            for key, val in kwargs.items():
                self.redis.hset(self.api_key, key, json.dumps(val))
        except TypeError:
            return

    def keys(self):
        return (key for key, val in self.redis.hscan_iter(self.api_key))

    def values(self):
        return (json.loads(val) for key, val in self.redis.hscan_iter(self.api_key))

    def items(self):
        return ((key, json.loads(val)) for key, val in self.redis.hscan_iter(self.api_key))

    def pop(self, key):
        ret = self[key]
        del self[key]
        return ret

    @classmethod
    def initialize(cls, redis):
        self = cls(redis)
        self.validate()
        return self

    def validate(self):
        for app, api in self.items():
            # TODO: validate these things
            print(app, api)
