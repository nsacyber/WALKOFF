import os
from datetime import timedelta
from unittest import TestCase

import walkoff.config
from tests.util import initialize_test_config
from tests.util.mock_objects import PubSubCacheSpy
from walkoff.cache import DiskCacheAdapter, unsubscribe_message


class TestDiskCacheAdapter(TestCase):

    @classmethod
    def setUpClass(cls):
        initialize_test_config()
        if not os.path.exists(walkoff.config.Config.CACHE_PATH):
            os.mkdir(walkoff.config.Config.CACHE_PATH)

    def setUp(self):
        self.cache = DiskCacheAdapter(directory=walkoff.config.Config.CACHE_PATH)

    def tearDown(self):
        self.cache.clear()
        self.cache.shutdown()

    def test_init(self):
        self.assertEqual(self.cache.directory, walkoff.config.Config.CACHE_PATH)
        self.assertTrue(self.cache.retry)

    def test_singleton(self):
        cache = DiskCacheAdapter(directory=walkoff.config.Config.CACHE_PATH)
        self.assertIs(cache, self.cache)

    def test_set_get(self):
        self.assertTrue(self.cache.set('alice', 'something'))
        self.assertEqual(self.cache.get('alice'), 'something')
        self.assertTrue(self.cache.set('count', 1))
        self.assertEqual(self.cache.get('count'), 1)
        self.assertTrue(self.cache.set('count', 2))
        self.assertEqual(self.cache.get('count'), 2)

    def test_get_key_dne(self):
        self.assertIsNone(self.cache.get('invalid_key'))

    def test_add(self):
        self.assertTrue(self.cache.add('test', 123))
        self.assertEqual(self.cache.get('test'), 123)
        self.assertFalse(self.cache.add('test', 456))
        self.assertEqual(self.cache.get('test'), 123)

    def test_delete(self):
        self.assertTrue(self.cache.set('alice', 'something'))
        self.cache.delete('alice')
        self.assertIsNone(self.cache.get('alice'))

    def test_delete_dne(self):
        self.cache.delete('alice')
        self.assertIsNone(self.cache.get('alice'))

    def test_incr(self):
        self.cache.set('count', 1)
        self.assertEqual(self.cache.incr('count'), 2)
        self.assertEqual(self.cache.get('count'), 2)

    def test_incr_multiple(self):
        self.cache.set('uid', 3)
        self.assertEqual(self.cache.incr('uid', amount=10), 13)
        self.assertEqual(self.cache.get('uid'), 13)

    def test_incr_key_dne(self):
        self.assertEqual(self.cache.incr('count'), 1)
        self.assertEqual(self.cache.get('count'), 1)

    def test_incr_multiple_key_dne(self):
        self.assertEqual(self.cache.incr('workflows', amount=10), 10)
        self.assertEqual(self.cache.get('workflows'), 10)

    def test_decr(self):
        self.cache.set('count', 0)
        self.assertEqual(self.cache.decr('count'), -1)
        self.assertEqual(self.cache.get('count'), -1)

    def test_decr_multiple(self):
        self.cache.set('uid', 3)
        self.assertEqual(self.cache.decr('uid', amount=10), -7)
        self.assertEqual(self.cache.get('uid'), -7)

    def test_decr_key_dne(self):
        self.assertEqual(self.cache.decr('count'), -1)
        self.assertEqual(self.cache.get('count'), -1)

    def test_decr_multiple_key_dne(self):
        self.assertEqual(self.cache.decr('workflows', amount=10), -10)
        self.assertEqual(self.cache.get('workflows'), -10)

    def test_r_push_pop_single_value(self):
        self.cache.rpush('queue', 10)
        self.assertEqual(self.cache.rpop('queue'), 10)
        self.assertIsNone(self.cache.rpop('queue'))

    def test_r_push_pop_multiple_values(self):
        self.cache.rpush('big', 10, 11, 12)
        self.assertEqual(self.cache.rpop('big'), 12)

    def test_l_push_pop_single_value(self):
        self.cache.lpush('queue', 10)
        self.assertEqual(self.cache.lpop('queue'), 10)
        self.assertIsNone(self.cache.lpop('queue'))

    def test_l_push_pop_multiple_values(self):
        self.cache.rpush('big2', 10, 11, 12)
        self.assertEqual(self.cache.lpop('big2'), 10)
        self.assertEqual(self.cache.lpop('big2'), 11)
        self.assertEqual(self.cache.lpop('big2'), 12)

    def test_convert_expire_to_seconds_timedelta(self):
        self.assertEqual(DiskCacheAdapter._convert_expire_to_seconds(timedelta(seconds=10, milliseconds=500)), 10.5)

    def test_convert_expire_to_seconds_int(self):
        self.assertEqual(DiskCacheAdapter._convert_expire_to_seconds(1500), 1.5)

    def test_from_json(self):
        data = {'directory': walkoff.config.Config.CACHE_PATH, 'shards': 4, 'timeout': 30, 'retry': False,
                'statistics': True}
        cache = DiskCacheAdapter.from_json(data)
        self.assertEqual(cache.directory, walkoff.config.Config.CACHE_PATH)
        self.assertEqual(cache.cache.directory, walkoff.config.Config.CACHE_PATH)
        self.assertEqual(cache.cache._count, 4)
        self.assertFalse(cache.retry)

    def test_scan_no_pattern(self):
        keys = ('a', 'b', 'c', 'd')
        for i, key in enumerate(keys):
            self.cache.set(key, i)
        ret_keys = self.cache.scan()
        self.assertSetEqual(set(ret_keys), set(keys))

    def test_scan_with_pattern(self):
        keys = ('1.a', '2.a', '3.b', 'd')
        for i, key in enumerate(keys):
            self.cache.set(key, i)
        ret_keys = self.cache.scan('*.a')
        self.assertSetEqual(set(ret_keys), {'1.a', '2.a'})

    def test_publish(self):
        self.cache.pubsub_cache = PubSubCacheSpy()
        self.cache.publish('channel1', 87)
        self.assertDictEqual(self.cache.pubsub_cache.published, {'channel1': [87]})

    def test_unsubscribe(self):
        self.cache.pubsub_cache = PubSubCacheSpy()
        self.cache.unsubscribe('channel1')
        self.assertDictEqual(self.cache.pubsub_cache.published, {'channel1': [unsubscribe_message]})

    def test_subscribe(self):
        self.cache.pubsub_cache = PubSubCacheSpy()
        self.cache.subscribe('my_channel')
        self.assertListEqual(self.cache.pubsub_cache.subscribed, ['my_channel'])
