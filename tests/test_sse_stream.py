from walkoff.sse import SseEvent, SseStream
from unittest import TestCase
from tests.util.mock_objects import MockRedisCacheAdapter
import json
import gevent
from gevent.monkey import patch_all
from tests.config import cache_path
import os
import shutil
from walkoff.cache import DiskCacheAdapter


class TestSseEvent(TestCase):
    def test_init(self):
        event = SseEvent('ev', '12345')
        self.assertEqual(event.event, 'ev')
        self.assertEqual(event.data, '12345')

    def test_format(self):
        event = SseEvent('ev', 'abc')
        self.assertEqual(event.format(42), 'id: 42\nevent: ev\ndata: abc\n\n')

    def test_format_with_retry(self):
        event = SseEvent('ev', 'abc')
        self.assertEqual(event.format(42, retry=50), 'id: 42\nevent: ev\nretry: 50\ndata: abc\n\n')

    def test_format_json_data(self):
        data = {'a': 1, 'b': 2}
        event = SseEvent('ev', data)
        self.assertEqual(event.format(11), 'id: 11\nevent: ev\ndata: {}\n\n'.format(json.dumps(data)))

    def test_format_bad_json_data(self):
        class A: pass

        data = {'a': 1, 'b': A()}
        event = SseEvent('ev', data)
        self.assertEqual(event.format(11), 'id: 11\nevent: ev\ndata: {}\n\n'.format(str(data)))


class SseStreamTestBase(object):

    def test_init(self):
        self.assertEqual(self.stream.channel, self.channel)
        self.assertEqual(self.stream.cache, self.cache)

    def assert_header_in_response(self, response, header, value):
        header_tuple = next((header_ for header_ in response.headers if header_[0] == header), None)
        self.assertIsNotNone(header_tuple)
        self.assertEqual(header_tuple[1], value)

    def test_stream_default_headers(self):
        resp = self.stream.stream()
        self.assert_header_in_response(resp, 'Connection', 'keep-alive')
        self.assert_header_in_response(resp, 'Cache-Control', 'no-cache')
        self.assert_header_in_response(resp, 'Content-Type', 'text/event-stream; charset=utf-8')

    def test_stream_custom_headers(self):
        resp = self.stream.stream(headers={'x-custom': 'yes', 'Cache-Control': 'no-store'})
        self.assert_header_in_response(resp, 'Connection', 'keep-alive')
        self.assert_header_in_response(resp, 'Cache-Control', 'no-store')
        self.assert_header_in_response(resp, 'Content-Type', 'text/event-stream; charset=utf-8')
        self.assert_header_in_response(resp, 'x-custom', 'yes')

    def test_send(self):

        @self.stream.push('event1')
        def pusher(a, ev):
            return {'a': a}, ev

        result = []

        def listen():
            for event in self.stream.send():
                result.append(event)

        args = [('event1', 1), ('event2', 2)]
        sses = [SseEvent(event, {'a': arg}) for event, arg in args]
        formatted_sses = [sse.format(i+1) for i, sse in enumerate(sses)]

        def publish():
            for event, data in args:
                pusher(data, event)
            self.stream.unsubscribe()

        thread = gevent.spawn(listen)
        thread2 = gevent.spawn(publish)
        thread.start()
        thread2.start()
        thread.join(timeout=2)
        thread2.join(timeout=2)
        self.assertListEqual(result, formatted_sses)

    def test_send_with_retry(self):

        @self.stream.push('event1')
        def pusher(a, ev):
            return {'a': a}, ev

        result = []

        def listen():
            for event in self.stream.send(retry=50):
                result.append(event)

        args = [('event1', 1), ('event2', 2)]
        sses = [SseEvent(event, {'a': arg}) for event, arg in args]
        formatted_sses = [sse.format(i+1, retry=50) for i, sse in enumerate(sses)]

        def publish():
            for event, data in args:
                pusher(data, event)
            self.stream.unsubscribe()

        thread = gevent.spawn(listen)
        thread2 = gevent.spawn(publish)
        thread.start()
        thread2.start()
        thread.join(timeout=2)
        thread2.join(timeout=2)
        self.assertListEqual(result, formatted_sses)

    def test_stream_with_data(self):
        @self.stream.push('event1')
        def pusher(a, ev):
            return {'a': a}, ev

        result = []

        def listen():
            response = self.stream.stream()
            for event in response.response:
                result.append(event)

        args = [('event1', 1), ('event2', 2)]
        sses = [SseEvent(event, {'a': arg}) for event, arg in args]
        formatted_sses = [sse.format(i+1) for i, sse in enumerate(sses)]

        def publish():
            for event, data in args:
                pusher(data, event)
            self.stream.unsubscribe()

        thread = gevent.spawn(listen)
        thread2 = gevent.spawn(publish)
        thread.start()
        thread2.start()
        thread.join(timeout=2)
        thread2.join(timeout=2)
        self.assertListEqual(result, formatted_sses)

    def test_stream_with_data_with_retry(self):
        @self.stream.push('event1')
        def pusher(a, ev):
            return {'a': a}, ev

        result = []

        def listen():
            response = self.stream.stream(retry=100)
            for event in response.response:
                result.append(event)

        args = [('event1', 1), ('event2', 2)]
        sses = [SseEvent(event, {'a': arg}) for event, arg in args]
        formatted_sses = [sse.format(i+1, retry=100) for i, sse in enumerate(sses)]

        def publish():
            for event, data in args:
                pusher(data, event)
            self.stream.unsubscribe()

        thread = gevent.spawn(listen)
        thread2 = gevent.spawn(publish)
        thread.start()
        thread2.start()
        thread.join(timeout=2)
        thread2.join(timeout=2)
        self.assertListEqual(result, formatted_sses)


class TestDiskSseStream(TestCase, SseStreamTestBase):
    @classmethod
    def setUpClass(cls):
        os.mkdir(cache_path)
        patch_all()

    def setUp(self):
        self.cache = DiskCacheAdapter(directory=cache_path)
        self.channel = 'channel1'
        self.stream = SseStream(self.channel, self.cache)

    def tearDown(self):
        self.cache.clear()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cache_path)


class TestRedisSseStream(TestCase, SseStreamTestBase):
    @classmethod
    def setUpClass(cls):
        patch_all()

    def setUp(self):
        self.cache = MockRedisCacheAdapter()
        self.channel = 'channel1'
        self.stream = SseStream(self.channel, self.cache)

    def tearDown(self):
        self.cache.clear()

    def test_push(self):

        @self.stream.push('event1')
        def pusher(a, b, c):
            if a == 1:
                return {'b': b, 'c': c}
            else:
                return {'b': b, 'c': c}, 'event2'

        sub = self.cache.subscribe(self.channel)
        self.assertDictEqual(pusher(1, 2, 3),
                         {'data': {'b': 2, 'c': 3}, 'event': 'event1'})
        result = sub._pubsub.get_message()['data']
        self.assertDictEqual(result['data'], {'b': 2, 'c': 3})
        self.assertEqual(result['event'], 'event1')
        self.assertDictEqual(pusher(2, 3, 4),
                             {'data': {'b': 3, 'c': 4}, 'event': 'event2'})
        result = sub._pubsub.get_message()['data']
        self.assertDictEqual(result['data'], {'b': 3, 'c': 4})
        self.assertEqual(result['event'], 'event2')



