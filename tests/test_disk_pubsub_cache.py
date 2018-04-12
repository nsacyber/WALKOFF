from unittest import TestCase
from walkoff.cache import DiskPubSubCache, unsubscribe_message
from tests.config import CACHE_PATH
import os
import shutil
import gevent
import threading
from gevent.monkey import patch_all


class TestDiskCachePubSub(TestCase):

    @classmethod
    def setUpClass(cls):
        os.mkdir(CACHE_PATH)
        patch_all()

    def setUp(self):
        self.cache = DiskPubSubCache(CACHE_PATH)

    def tearDown(self):
        self.cache.cache.clear()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(CACHE_PATH)

    def test_init(self):
        self.assertEqual(self.cache.cache.directory, CACHE_PATH)

    def test_publish(self):
        self.cache.register_callbacks()
        self.assertEqual(self.cache.publish('channel1', '42'), 0)
        self.assertEqual(self.cache.cache.get('channel1'), '42')

    def test_subscribe(self):
        subscription = self.cache.subscribe('channel1')
        self.assertEqual(subscription.channel, 'channel1')
        self.assertEqual(len(self.cache._subscribers), 1)

    def test_pub_sub_single_sub(self):
        subscription = self.cache.subscribe('channel2')

        result = []

        def listen():
            for x in subscription.listen():
                result.append(x)

        t1 = gevent.spawn(listen)
        t1.start()
        gevent.sleep(0, ref=t1)

        def publish():
            self.cache.register_callbacks()
            self.cache.publish('channel2', 10)
            self.cache.publish('channel2', 2)
            self.cache.publish('channel2', 'a')
            self.cache.publish('channel2', unsubscribe_message)

        t2 = gevent.spawn(publish)
        t2.start()
        t2.join(timeout=2)
        t1.join(timeout=2)
        self.assertListEqual(result, [10, 2, 'a'])
