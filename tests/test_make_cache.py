from unittest import TestCase

import walkoff.cache
from tests.config import cache_path
from tests.util.mock_objects import MockRedisCacheAdapter
from walkoff.cache import DiskCacheAdapter, make_cache


class TestMakeCache(TestCase):

    @classmethod
    def setUpClass(cls):
        walkoff.cache.cache_translation['redis'] = MockRedisCacheAdapter

    def test_no_type(self):
        config = {'directory': cache_path}
        cache = make_cache(config)
        self.assertIsInstance(cache, DiskCacheAdapter)
        self.assertEqual(cache.directory, cache_path)

    def test_unknown_type(self):
        config = {'type': '__invalid__', 'directory': cache_path}
        cache = make_cache(config)
        self.assertIsInstance(cache, DiskCacheAdapter)
        self.assertEqual(cache.directory, cache_path)

    def test_disk_type(self):
        config = {'type': 'disk', 'directory': cache_path}
        cache = make_cache(config)
        self.assertIsInstance(cache, DiskCacheAdapter)
        self.assertEqual(cache.directory, cache_path)

    def test_disk_type_strange_capitalization(self):
        config = {'type': 'DiSk', 'directory': cache_path}
        cache = make_cache(config)
        self.assertIsInstance(cache, DiskCacheAdapter)
        self.assertEqual(cache.directory, cache_path)

    def test_redis(self):
        config = {'type': 'redis'}
        cache = make_cache(config)
        self.assertIsInstance(cache, MockRedisCacheAdapter)

    def test_bad_import(self):
        class CustomCacheAdapter(object):
            _requires = ['something_strange']

            def __init__(self):
                self.cache ={}

            @classmethod
            def from_json(cls, json_in):
                return cls()

        walkoff.cache.cache_translation['__something_strange'] = CustomCacheAdapter

        config = {'type': '__something_strange', 'directory': cache_path}
        self.assertIsInstance(make_cache(config), DiskCacheAdapter)

    def test_bad_import_no_requires(self):
        class CustomCacheAdapter(object):
            def __init__(self):
                self.cache = {}

            @classmethod
            def from_json(cls, json_in):
                return cls()

        walkoff.cache.cache_translation['__something_strange'] = CustomCacheAdapter

        config = {'type': '__something_strange', 'directory': cache_path}
        self.assertIsInstance(make_cache(config), DiskCacheAdapter)



