from unittest import TestCase

import gevent
from gevent.monkey import patch_all

from tests.util.mock_objects import MockRedisCacheAdapter
from walkoff.sse import FilteredSseStream, SseEvent, create_interface_channel_name, FilteredInterfaceSseStream


class TestSimpleFilteredSseStream(TestCase):
    @classmethod
    def setUpClass(cls):
        patch_all()

    def setUp(self):
        self.cache = MockRedisCacheAdapter()
        self.channel = 'channel1'
        self.stream = FilteredSseStream(self.channel, self.cache)

    def tearDown(self):
        self.cache.clear()

    def test_init(self):
        self.assertEqual(self.stream.channel, self.channel)
        self.assertEqual(self.stream.cache, self.cache)

    def test_create_channel_name(self):
        self.assertEqual(self.stream.create_subchannel_name('a'), '{}.a'.format(self.channel))
        self.assertEqual(self.stream.create_subchannel_name(14), '{}.14'.format(self.channel))

    def assert_header_in_response(self, response, header, value):
        header_tuple = next((header_ for header_ in response.headers if header_[0] == header), None)
        self.assertIsNotNone(header_tuple)
        self.assertEqual(header_tuple[1], value)

    def test_stream_default_headers(self):
        resp = self.stream.stream(subchannel='a')
        self.assert_header_in_response(resp, 'Connection', 'keep-alive')
        self.assert_header_in_response(resp, 'Cache-Control', 'no-cache')
        self.assert_header_in_response(resp, 'Content-Type', 'text/event-stream; charset=utf-8')

    def test_stream_custom_headers(self):
        resp = self.stream.stream(subchannel='a', headers={'x-custom': 'yes', 'Cache-Control': 'no-store'})
        self.assert_header_in_response(resp, 'Connection', 'keep-alive')
        self.assert_header_in_response(resp, 'Cache-Control', 'no-store')
        self.assert_header_in_response(resp, 'Content-Type', 'text/event-stream; charset=utf-8')
        self.assert_header_in_response(resp, 'x-custom', 'yes')

    def test_send(self):

        @self.stream.push('event1')
        def pusher(a, ev, sub):
            return {'a': a}, sub, ev

        subs = ('aaa', 'bbb')

        result = {sub: [] for sub in subs}

        def listen(sub):
            for event in self.stream.send(subchannel=sub):
                result[sub].append(event)

        base_args = [('event1', 1), ('event2', 2)]
        args = {sub: [(event, data + i) for (event, data) in base_args] for i, sub in enumerate(subs)}

        def publish(sub):
            for event, data in args[sub]:
                pusher(data, event, sub)
            self.stream.unsubscribe(sub)

        sses = {sub: [SseEvent(event, {'a': arg}) for event, arg in args[sub]] for sub in subs}
        formatted_sses = {sub: [sse.format(i + 1) for i, sse in enumerate(sse_vals)] for sub, sse_vals in sses.items()}

        listen_threads = [gevent.spawn(listen, sub) for sub in subs]
        publish_threads = [gevent.spawn(publish, sub) for sub in subs]
        gevent.joinall(listen_threads, timeout=2)
        gevent.joinall(publish_threads, timeout=2)
        for sub in subs:
            self.assertListEqual(result[sub], formatted_sses[sub])

    def test_send_publish_multiple(self):

        subs = ('a', 'bbb')

        @self.stream.push('event1')
        def pusher(a, ev):
            return {'a': a}, subs, ev

        result = {sub: [] for sub in subs}

        def listen(sub):
            for event in self.stream.send(subchannel=sub):
                result[sub].append(event)

        base_args = [('event1', 1), ('event2', 2)]

        def publish():
            for event, data in base_args:
                pusher(data, event)
            for sub in subs:
                self.stream.unsubscribe(sub)

        sses = {sub: [SseEvent(event, {'a': arg}) for event, arg in base_args] for sub in subs}
        formatted_sses = {sub: [sse.format(i + 1) for i, sse in enumerate(sse_vals)] for sub, sse_vals in sses.items()}

        listen_threads = [gevent.spawn(listen, sub) for sub in subs]
        publish_thread = gevent.spawn(publish)
        gevent.joinall(listen_threads, timeout=2)
        publish_thread.join(timeout=2)
        for sub in subs:
            self.assertListEqual(result[sub], formatted_sses[sub])

    def test_send_with_retry(self):

        @self.stream.push('event1')
        def pusher(a, ev, sub):
            return {'a': a}, sub, ev

        subs = ('a', 'b')

        result = {'a': [], 'b': []}

        def listen(sub):
            for event in self.stream.send(subchannel=sub, retry=50):
                result[sub].append(event)

        base_args = [('event1', 1), ('event2', 2)]
        args = {sub: [(event, data + i) for (event, data) in base_args] for i, sub in enumerate(subs)}

        def publish(sub):
            for event, data in args[sub]:
                pusher(data, event, sub)
            self.stream.unsubscribe(sub)

        sses = {sub: [SseEvent(event, {'a': arg}) for event, arg in args[sub]] for sub in subs}
        formatted_sses = {sub: [sse.format(i + 1, retry=50) for i, sse in enumerate(sse_vals)] for sub, sse_vals in
                          sses.items()}

        listen_threads = [gevent.spawn(listen, sub) for sub in subs]
        publish_threads = [gevent.spawn(publish, sub) for sub in subs]
        gevent.joinall(listen_threads, timeout=2)
        gevent.joinall(publish_threads, timeout=2)
        for sub in subs:
            self.assertListEqual(result[sub], formatted_sses[sub])


class TestFilteredInterfaceSseStream(TestCase):

    def test_init(self):
        stream = FilteredInterfaceSseStream('HelloWorld3', 'random_filtered')
        self.assertEqual(stream.interface, 'HelloWorld3')
        self.assertEqual(stream.channel, create_interface_channel_name('HelloWorld3', 'random_filtered'))
