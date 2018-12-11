from unittest import TestCase

from tests.util import initialize_test_config
from tests.util.mock_objects import MockRedisCacheAdapter
from walkoff.cache import make_cache, RedisCacheAdapter


class TestMakeCache(TestCase):

    @classmethod
    def setUpClass(cls):
        initialize_test_config()
        cls.mapping = {'redis': MockRedisCacheAdapter}

    def test_no_type(self):
        config = {}
        cache = make_cache(config, cache_mapping=self.mapping)
        self.assertIsInstance(cache, MockRedisCacheAdapter)

    def test_unknown_type(self):
        config = {'type': '__invalid__'}
        cache = make_cache(config, cache_mapping=self.mapping)
        self.assertIsInstance(cache, RedisCacheAdapter)

    def test_redis(self):
        config = {'type': 'redis'}
        cache = make_cache(config, cache_mapping=self.mapping)
        self.assertIsInstance(cache, MockRedisCacheAdapter)

    def test_bad_import(self):
        class CustomCacheAdapter(object):
            _requires = ['something_strange']

            def __init__(self):
                import something_strange
                self.cache = {}

            @classmethod
            def from_json(cls, json_in):
                return cls()

        mapping = self.mapping.copy()
        mapping['__something_strange'] = CustomCacheAdapter

        config = {'type': '__something_strange'}
        self.assertIsInstance(make_cache(config, cache_mapping=mapping), RedisCacheAdapter)

    def test_bad_import_no_requires(self):
        class CustomCacheAdapter(object):
            def __init__(self):
                import something_strange
                self.cache = {}

            @classmethod
            def from_json(cls, json_in):
                return cls()

        mapping = self.mapping.copy()
        mapping['__something_strange'] = CustomCacheAdapter

        config = {'type': '__something_strange'}
        self.assertIsInstance(make_cache(config, cache_mapping=mapping), RedisCacheAdapter)
