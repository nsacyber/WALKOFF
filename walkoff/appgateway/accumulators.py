from walkoff.cache import make_cache


class InMemoryAccumulator(dict):
    """This accumulator is identical to a dictionary, but the copy and __cmp__ properties are disabled.
    """
    def __init__(self):
        super(InMemoryAccumulator, self).__init__()

    def copy(self):
        raise AttributeError

    def __cmp__(self, other):
        raise AttributeError


class ExternallyCachedAccumulator(object):
    """This accumulator acts as a dictionary with the values stored in an external cache (e.g. Redis)
    """
    _cache_separator = ':'

    def __init__(self, cache, workflow_execution_id, key_prefix='accumulator'):
        self._cache = cache
        self._key_prefix = key_prefix
        self.set_key(workflow_execution_id)

    def __setitem__(self, key, value):
        self._cache.set(self.format_key(key), value)


    def __getitem__(self, item):
        if self._cache.exists(self.format_key(item)):
            return self._cache.get(self.format_key(item))
        else:
            raise KeyError

    def __len__(self):
        return sum(1 for _key in self._cache.scan(self._key.format('*')))

    def __delitem__(self, key):
        key = self._key.format(key)
        if self._cache.exists(key):
            self._cache.delete(key)
        else:
            raise KeyError

    def format_key(self, key):
        return self._key.format(key)

    def extract_key(self, key):
        return key.split(self._cache_separator)[-1]

    def set_key(self, workflow_execution_id):
        self._key = '{0}{1}{2}{1}'.format(self._key_prefix, self._cache_separator, workflow_execution_id)
        self._key += '{}'
        self._scan_key = self._key.format('*')

    def clear(self):
        for key in self.keys():
            self._cache.delete(key)

    def has_key(self, key):
        return self._cache.exists(self._key.format(key))

    def update(self, *args, **kwargs):
        for arg in args:
            for key, val in arg.items():
                self._cache.set(self._key.format(key), val)
        for key, val in kwargs.items():
            self._cache.set(self._key.format(key), val)

    def keys(self):
        return self._cache.scan(self._scan_key)

    def values(self):
        return (self._cache.get(key) for key in self._cache.scan(self._scan_key))

    def items(self):
        return ((key, self._cache.get(key)) for key in self._cache.scan(self._scan_key))

    def pop(self, *args):
        if len(args) > 2:
            raise TypeError('Cannot use more than 2 arguments')
        key = self._key.format(args[0])
        if self._cache.exists(key):
            ret = self._cache.get(key)
            self._cache.delete(key)
            return ret
        elif len(args) == 2:
            return args[1]
        else:
            raise KeyError

    def __contains__(self, item):
        return self._cache.exists(self._key.format(item))

    def __iter__(self):
        return self.keys()


def make_in_memory_accumulator(config, workflow_execution_id, **kwargs):
    return InMemoryAccumulator()


def make_external_accumulator(config, workflow_execution_id, **kwargs):
    cache = make_cache(config.CACHE)
    return ExternallyCachedAccumulator(cache, workflow_execution_id)


accumulator_lookup = {
    'memory': make_in_memory_accumulator,
    'external': make_external_accumulator
}


def make_accumulator(workflow_execution_id, config=None, accumulator_map=accumulator_lookup, **kwargs):
    if not config:
        from walkoff.config import Config
        config = Config
    accumulator_type = config.ACCUMULATOR_TYPE
    try:
        return accumulator_map[accumulator_type](config, workflow_execution_id, **kwargs)
    except KeyError:
        raise ValueError('Unknown accumulator type {}'.format(accumulator_type))
