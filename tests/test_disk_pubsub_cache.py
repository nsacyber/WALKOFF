from unittest import TestCase
from walkoff.cache import DiskPubSubCache, unsubscribe_message
from tests.config import cache_path
import os
import shutil
import gevent
from gevent.monkey import patch_all


class TestDiskCachePubSub(TestCase):

    @classmethod
    def setUpClass(cls):
        os.mkdir(cache_path)
        patch_all()

    def setUp(self):
        self.cache = DiskPubSubCache(cache_path)

    def tearDown(self):
        self.cache.cache.clear()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cache_path)

    def test_init(self):
        self.assertEqual(self.cache.cache.directory, cache_path)

    def test_publish(self):
        self.assertEqual(self.cache.publish('channel1', '42'), 0)
        self.assertEqual(self.cache.cache.get('channel1'), '42')

    def test_subscribe(self):
        subscription = self.cache.subscribe('channel1')
        self.assertEqual(subscription.channel, 'channel1')
        self.assertEqual(len(self.cache._subscribers), 1)
    '''
    def test_pub_sub_single_sub(self):
        subscription = self.cache.subscribe('channel2')

        result = []

        def listen():
            for x in subscription.listen():
                print('appedning {}'.format(x))
                result.append(x)



        t1 = gevent.spawn(listen)
        t1.start()
        gevent.sleep(0)
        #def push():
        self.cache.publish('channel2', 10)
        gevent.sleep(0)
        self.cache.publish('channel2', 2)
        gevent.sleep(0)
        self.cache.publish('channel2', 'a')
        self.cache.publish('channel2', unsubscribe_message)


        #t2 = gevent.spawn(push)
        #t2.start()
        t1.join(timeout=2)
        #t2.join(timeout=2)
        print(result)
    '''