from unittest import TestCase

import gevent

from walkoff.cache import DiskSubscription, unsubscribe_message


class TestDiskSubscription(TestCase):

    def setUp(self):
        self.pubsub = DiskSubscription('channel1')

    def test_init(self):
        self.assertEqual(self.pubsub.channel, 'channel1')

    def test_listen_push(self):
        result = []

        def listen():
            for data in self.pubsub.listen():
                result.append(data)

        def push():
            self.pubsub.push(1)
            self.pubsub.push(2)
            self.pubsub.push(10)
            self.pubsub.push(unsubscribe_message)

        thread = gevent.spawn(listen)
        push_thread = gevent.spawn(push)
        thread.join(timeout=5)
        push_thread.join(timeout=5)
        self.assertListEqual(result, [1, 2, 10])
