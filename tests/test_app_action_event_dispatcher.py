from unittest import TestCase

from interfaces.disatchers import CallbackContainer, AppActionEventDispatcher


def func(): pass


def func2(): pass


class TestAppActionEventDispatcher(TestCase):
    def setUp(self):
        self.router = AppActionEventDispatcher('app', 'action')

    def assert_router_equals(self, expected_router):
        self.assertDictEqual(self.router._event_router, expected_router)

    def test_init(self):
        self.assertEqual(self.router.app, 'app')
        self.assertEqual(self.router.action, 'action')
        self.assertDictEqual(self.router._event_router, {})

    def test_register_event_for_device_device_not_in_router(self):
        self.router._event_router = {'event1': {}}
        self.router._register_event_for_device_id('event1', 'all', func, False)
        self.assertSetEqual(set(self.router._event_router), {'event1'})
        self.assertSetEqual(set(self.router._event_router['event1']), {'all'})
        self.assertIsInstance(self.router._event_router['event1']['all'], CallbackContainer)
        self.assertSetEqual(set(self.router._event_router['event1']['all']), {func})

    def test_register_event_for_device_device_in_router(self):
        self.router._event_router = {'event1': {'all': CallbackContainer()}}
        self.router._register_event_for_device_id('event1', 'all', func, False)
        self.assertSetEqual(set(self.router._event_router), {'event1'})
        self.assertSetEqual(set(self.router._event_router['event1']), {'all'})
        self.assertIsInstance(self.router._event_router['event1']['all'], CallbackContainer)
        self.assertSetEqual(set(self.router._event_router['event1']['all']), {func})

    def test_register_event_event_in_router_all_devices_strong(self):
        container = CallbackContainer()
        container.register(func, weak=False)
        self.router._event_router = {'event1': {'all': container}}
        self.router.register_event('event1', 'all', func2, weak=False)
        self.assertSetEqual(set(self.router._event_router['event1']['all']), {func, func2})

    def test_register_event_event_not_in_router_no_devices_weak(self):
        self.router.register_event('event1', [], func)
        self.assertDictEqual(self.router._event_router, {'event1': {}})

    def test_register_event_some_devices(self):
        self.router.register_event('event1', ['a', 'b', 'c'], func, weak=False)
        self.assertSetEqual(set(self.router._event_router['event1']), {'a', 'b', 'c'})
        for device in {'a', 'b', 'c'}:
            self.assertIsInstance(self.router._event_router['event1'][device], CallbackContainer)

    def test_register_event_single_devices(self):
        self.router.register_event('event1', 'a', func, weak=False)
        self.assertSetEqual(set(self.router._event_router['event1']), {'a'})
        self.assertIsInstance(self.router._event_router['event1']['a'], CallbackContainer)

    def test_get_callbacks_nothing_in_router(self):
        callbacks = self.router._get_callbacks('event2', 'all')
        self.assertListEqual(list(callbacks), [])

    def test_get_callbacks_event_not_in_router(self):
        self.router.register_event('event1', 'all', func)
        callbacks = self.router._get_callbacks('event2', 'all')
        self.assertListEqual(list(callbacks), [])

    def test_get_callbacks_all_devices_only(self):
        self.router.register_event('event1', 'all', func, weak=False)
        self.router.register_event('event1', 'all', func2)
        callbacks = self.router._get_callbacks('event1', 'all')
        self.assertEqual(len(list(callbacks)), 2)

    def test_get_callbacks_specified_devices_only(self):
        self.router.register_event('event1', ['a', 'b', 'c'], func, weak=False)
        self.router.register_event('event1', ['a', 'b'], func2)
        callbacks = self.router._get_callbacks('event1', 'a')
        self.assertEqual(len(list(callbacks)), 2)

    def test_get_callbacks_specified_devices_only_with_all(self):
        def func3(): pass

        self.router.register_event('event1', ['a', 'b', 'c'], func, weak=False)
        self.router.register_event('event1', ['a', 'b'], func2)
        self.router.register_event('event1', 'all', func3, weak=False)
        callbacks = list(self.router._get_callbacks('event1', 'a'))
        self.assertEqual(len(callbacks), 3)

    def test_dispatch_empty_router(self):  # just to check it doesn't error
        self.router.dispatch('event1', {'device_id': 3})

    def test_dispatch_event_not_registered(self):  # just to check it doesn't error
        self.router.register_event('event1', 'all', func)
        self.router.dispatch('event2', {'device_id': 4})

    def test_dispatch_strong_event(self):
        result = {'x': None}

        def func_(data):
            result['x'] = data

        self.router.register_event('event1', 'all', func_, weak=False)
        self.router.dispatch('event1', {'device_id': 3})
        self.assertDictEqual(result, {'x': {'device_id': 3}})

    def test_dispatch_weak_event(self):
        result = {'x': None}

        def func_(data):
            result['x'] = data

        self.router.register_event('event1', 'all', func_)
        self.router.dispatch('event1', {'device_id': 3})
        self.assertDictEqual(result, {'x': {'device_id': 3}})

        result = {'x': None}
        del func_
        self.router.dispatch('event1', {'device_id': 3})
        self.assertDictEqual(result, {'x': None})

    def test_dispatch_multiple_mixed(self):
        result = {'x': None}

        def func_(data):
            result['x'] = data

        def func2_(data):
            result['y'] = data

        self.router.register_event('event1', 3, func_)
        self.router.register_event('event1', 42, func2_, weak=False)
        self.router.dispatch('event1', {'device_id': 3})
        self.router.dispatch('event1', {'device_id': 42})
        self.assertDictEqual(result, {'x': {'device_id': 3}, 'y': {'device_id': 42}})

    def test_is_registered_empty(self):
        self.assertFalse(self.router.is_registered('event1', 1, func))

    def test_is_registered_event_no_devices(self):
        self.router._event_router = {'event1': {}}
        self.assertFalse(self.router.is_registered('event1', 1, func))

    def test_is_registered_event_incorrect_devices(self):
        self.router.register_event('event1', [3, 4, 5], func)
        self.assertFalse(self.router.is_registered('event1', 1, func))

    def test_is_registered_event_all_devices(self):
        self.router.register_event('event1', 'all', func)
        self.assertTrue(self.router.is_registered('event1', 1, func))

    def test_is_registered_event_correct_device(self):
        self.router.register_event('event1', [1, 2, 3], func)
        self.assertTrue(self.router.is_registered('event1', 1, func))

    def test_is_registered_event_correct_device_incorrect_func(self):
        self.router.register_event('event1', [1, 2, 3], func2)
        self.assertFalse(self.router.is_registered('event1', 1, func))
