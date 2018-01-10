from unittest import TestCase
from walkoff.cache import RedisCacheAdapter
from tests.config import cache_path
from fakeredis import FakeStrictRedis

import os
import shutil
from datetime import timedelta


class TestRedisCacheAdapter(TestCase):

    def setUp(self):
        redis_cache = FakeStrictRedis()
        self.cache = RedisCacheAdapter(redis_cache=redis_cache)

    def tearDown(self):
        self.cache.clear()
        self.cache.shutdown()

    def test_set_get(self):
        self.assertTrue(self.cache.set('alice', 'something'))
        self.assertEqual(self.cache.get('alice'), 'something')
        self.assertTrue(self.cache.set('count', 1))
        self.assertEqual(self.cache.get('count'), '1')
        self.assertTrue(self.cache.set('count', 2))
        self.assertEqual(self.cache.get('count'), '2')

    def test_get_key_dne(self):
        self.assertIsNone(self.cache.get('invalid_key'))

    def test_add(self):
        self.assertTrue(self.cache.add('test', 123))
        self.assertEqual(self.cache.get('test'), '123')
        self.assertFalse(self.cache.add('test', 456))
        self.assertEqual(self.cache.get('test'), '123')

    def test_incr(self):
        self.cache.set('count', 1)
        self.assertEqual(self.cache.incr('count'), 2)
        self.assertEqual(self.cache.get('count'), '2')

    def test_incr_multiple(self):
        self.cache.set('uid', 3)
        self.assertEqual(self.cache.incr('uid', amount=10), 13)
        self.assertEqual(self.cache.get('uid'), '13')

    def test_incr_key_dne(self):
        self.assertEqual(self.cache.incr('count'), 1)
        self.assertEqual(self.cache.get('count'), '1')

    def test_incr_multiple_key_dne(self):
        self.assertEqual(self.cache.incr('workflows', amount=10), 10)
        self.assertEqual(self.cache.get('workflows'), '10')

    def test_decr(self):
        self.cache.set('count', 0)
        self.assertEqual(self.cache.decr('count'), -1)
        self.assertEqual(self.cache.get('count'), '-1')

    def test_decr_multiple(self):
        self.cache.set('uid', 3)
        self.assertEqual(self.cache.decr('uid', amount=10), -7)
        self.assertEqual(self.cache.get('uid'), '-7')

    def test_decr_key_dne(self):
        self.assertEqual(self.cache.decr('count'), -1)
        self.assertEqual(self.cache.get('count'), '-1')

    def test_decr_multiple_key_dne(self):
        self.assertEqual(self.cache.decr('workflows', amount=10), -10)
        self.assertEqual(self.cache.get('workflows'), '-10')

    def test_r_push_pop_single_value(self):
        self.cache.rpush('queue', 10)
        self.assertEqual(self.cache.rpop('queue'), '10')

    def test_r_push_pop_multiple_values(self):
        self.cache.rpush('big', 10, 11, 12)
        self.assertEqual(self.cache.rpop('big'), '12')

    def test_l_push_pop_single_value(self):
        self.cache.lpush('queue', 10)
        self.assertEqual(self.cache.lpop('queue'), '10')

    def test_r_push_pop_multiple_values(self):
        self.cache.rpush('big', 10, 11, 12)
        self.assertEqual(self.cache.lpop('big'), '10')
        self.assertEqual(self.cache.rpop('big'), '12')
