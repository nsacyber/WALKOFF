import unittest

from apps import Event


class TestAppEvent(unittest.TestCase):

    def test_constructor_default(self):
        event = Event()
        self.assertSetEqual(event.receivers, set())
        self.assertEqual(event.name, '')

    def test_constructor_with_name(self):
        event = Event('test')
        self.assertSetEqual(event.receivers, set())
        self.assertEqual(event.name, 'test')

    def test_connect_one(self):
        event = Event()

        @event.connect
        def test1():
            pass

        self.assertSetEqual(event.receivers, {test1})

    def test_connect_two(self):
        event = Event()

        @event.connect
        def test1(data):
            pass

        @event.connect
        def test2(data):
            pass

        self.assertSetEqual(event.receivers, {test1, test2})

    def test_connect_redefined_function(self):
        event = Event()

        @event.connect
        def test1():
            pass

        @event.connect
        def test2(a, b, c):
            pass

        self.assertSetEqual(event.receivers, {test1, test2})

    def test_disconnect(self):
        event = Event()

        @event.connect
        def test1():
            pass

        event.disconnect(test1)
        self.assertSetEqual(event.receivers, set())

    def test_disconnect_invalid(self):
        event = Event()

        @event.connect
        def test1():
            pass

        def test2(a, b, c):
            pass

        event.disconnect(test2)
        self.assertSetEqual(event.receivers, {test1})

    def test_trigger(self):
        event = Event()
        result = {}

        @event.connect
        def test1(data):
            result['x'] = data

        event.trigger({1: 2})

        self.assertDictEqual(result, {'x': {1: 2}})

    def test_multiple_triggers(self):
        event = Event()
        result = {}

        @event.connect
        def test1(data):
            result['x'] = data

        @event.connect
        def test2(a):
            result['y'] = a

        event.trigger({1: 2})

        self.assertDictEqual(result, {'x': {1: 2}, 'y': {1: 2}})
