from unittest import TestCase

import gevent
from fakeredis import FakeStrictRedis
from gevent.monkey import patch_all

from walkoff.cache import RedisSubscription, unsubscribe_message


class TestRedisSubscription(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.redis = FakeStrictRedis()
        cls.channel = 'channel1'
        patch_all()

    def setUp(self):
        redis_sub = self.redis.pubsub()
        redis_sub.subscribe(self.channel)
        self.sub = RedisSubscription(self.channel, redis_sub)

    def test_init(self):
        self.assertEqual(self.sub.channel, self.channel)

    def test_listen(self):
        result = []

        def listen():
            for x in self.sub.listen():
                result.append(x)

        def publish():
            self.redis.publish(self.channel, 1)
            self.redis.publish(self.channel, 2)
            self.redis.publish(self.channel, 10)
            self.redis.publish(self.channel, unsubscribe_message)

        thread1 = gevent.spawn(listen)
        thread1.start()
        thread2 = gevent.spawn(publish)
        thread2.start()
        thread1.join(timeout=5)
        thread2.join(timeout=5)
