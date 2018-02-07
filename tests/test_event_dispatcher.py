from unittest import TestCase

from walkoff.events import WalkoffEvent, EventType
from interfaces.dispatchers import EventDispatcher


def func(): pass


def func2(): pass


class TestEventDispatcher(TestCase):
    def setUp(self):
        self.router = EventDispatcher()

    def assert_router_structure(self, events, ids=None, names=None, num_funcs=None):
        names = names if names is not None else {}
        ids = ids if ids is not None else {}
        entry_ids = set(ids) | set(names)
        num_funcs = num_funcs if num_funcs is not None else 1
        self.assertSetEqual(set(self.router._router.keys()), entry_ids)
        for entry_id in entry_ids:
            self.assertSetEqual(set(self.router._router[entry_id].keys()), events)
            for event in events:
                self.assertEqual(len(list(self.router._router[entry_id][event])), num_funcs)

    def test_init(self):
        self.assertDictEqual(self.router._router, {})

    def test_register_events_no_ids_or_names(self):
        self.router.register_events(func, {WalkoffEvent.ActionStarted})
        self.assert_router_structure({WalkoffEvent.ActionStarted}, ids={'all'})

    def test_register_events_single_event_enum_single_id(self):
        self.router.register_events(func, {WalkoffEvent.ActionStarted}, sender_ids='a')
        self.assert_router_structure({WalkoffEvent.ActionStarted}, ids='a')

    def test_register_events_multiple_events_single_id(self):
        self.router.register_events(func, [WalkoffEvent.ActionStarted, WalkoffEvent.ActionExecutionError],
                                    sender_ids='a')
        self.assert_router_structure({WalkoffEvent.ActionStarted, WalkoffEvent.ActionExecutionError}, ids='a')

    def test_register_events_multiple_ids(self):
        self.router.register_events(func, {WalkoffEvent.ActionStarted}, sender_ids=['a', 'b'])
        self.assert_router_structure({WalkoffEvent.ActionStarted}, ids=['a', 'b'])

    def test_register_events_single_name(self):
        self.router.register_events(func, {WalkoffEvent.ActionStarted}, names='a')
        self.assert_router_structure({WalkoffEvent.ActionStarted}, names='a')

    def test_register_events_multiple_names(self):
        self.router.register_events(func, {WalkoffEvent.ActionStarted}, names=['a', 'b'])
        self.assert_router_structure({WalkoffEvent.ActionStarted}, names=['a', 'b'])

    def test_register_events_names_and_ids(self):
        self.router.register_events(func, {WalkoffEvent.ActionStarted}, sender_ids=['c', 'd'], names=['a', 'b'])
        self.assert_router_structure({WalkoffEvent.ActionStarted}, names=['a', 'b'], ids=['c', 'd'])

    def test_register_events_duplicate_names_different_events(self):
        self.router.register_events(func, {WalkoffEvent.ActionStarted}, names='a')
        self.router.register_events(func, {WalkoffEvent.ActionExecutionError}, names='a')
        self.assert_router_structure({WalkoffEvent.ActionStarted, WalkoffEvent.ActionExecutionError}, names='a')

    def test_register_events_duplicate_names_same_event_different_funcs(self):
        self.router.register_events(func, {WalkoffEvent.ActionStarted}, names='a')
        self.router.register_events(func2, {WalkoffEvent.ActionStarted}, names='a')
        self.assert_router_structure({WalkoffEvent.ActionStarted}, names='a', num_funcs=2)

    def test_register_events_duplicate_names_same_event_same_funcs(self):
        self.router.register_events(func, {WalkoffEvent.ActionStarted}, names='a')
        self.router.register_events(func, {WalkoffEvent.ActionStarted}, names='a')
        self.assert_router_structure({WalkoffEvent.ActionStarted}, names='a')

    def test_get_callbacks_empty_router(self):
        self.assertListEqual(list(self.router._get_callbacks('a', None, WalkoffEvent.ActionArgumentsInvalid)), [])

    def test_get_callbacks_id_nor_name_found(self):
        self.router.register_events(func, {WalkoffEvent.ActionStarted}, names='a')
        self.router.register_events(func, {WalkoffEvent.ActionStarted}, sender_ids='b')
        self.assertListEqual(list(self.router._get_callbacks('c', None, WalkoffEvent.ActionArgumentsInvalid)), [])

    def test_get_callbacks_sender_id_found(self):
        self.router.register_events(func, {WalkoffEvent.ActionStarted}, names='a')
        self.router.register_events(func2, {WalkoffEvent.ActionStarted}, names='a')
        self.router.register_events(func, {WalkoffEvent.ActionStarted}, names='b')
        self.assertEqual(len(list(self.router._get_callbacks('a', 'c', WalkoffEvent.ActionStarted))), 2)

    def test_get_callbacks_sender_name_found(self):
        self.router.register_events(func, {WalkoffEvent.ActionStarted}, names='a')
        self.router.register_events(func2, {WalkoffEvent.ActionStarted}, names='a')
        self.router.register_events(func, {WalkoffEvent.ActionStarted}, names='b')
        self.assertEqual(len(list(self.router._get_callbacks('c', 'a', WalkoffEvent.ActionStarted))), 2)

    def test_get_callbacks_sender_and_name_found(self):
        def func3(): pass

        self.router.register_events(func, {WalkoffEvent.ActionStarted}, names='a')
        self.router.register_events(func2, {WalkoffEvent.ActionStarted}, names='a')
        self.router.register_events(func3, {WalkoffEvent.ActionStarted}, names='b')
        self.assertEqual(len(list(self.router._get_callbacks('a', 'b', WalkoffEvent.ActionStarted))), 3)

    def test_get_callbacks_sender_and_name_found_duplicate_funcs(self):
        self.router.register_events(func, {WalkoffEvent.ActionStarted}, names='a')
        self.router.register_events(func2, {WalkoffEvent.ActionStarted}, names='a')
        self.router.register_events(func, {WalkoffEvent.ActionStarted}, names='b')
        self.assertEqual(len(list(self.router._get_callbacks('a', 'b', WalkoffEvent.ActionStarted))), 2)

    def test_dispatch_nothing_in_router(self):
        self.router.dispatch(WalkoffEvent.ActionStarted, {'sender_id': 42})

    def test_dispatch_sender_id_only_weak(self):
        result = {'x': True, 'count': 0}

        def x(data):
            result['x'] = data
            result['count'] += 1

        self.router.register_events(x, {WalkoffEvent.ActionStarted}, names='a')

        self.router.dispatch(WalkoffEvent.ActionStarted, {'sender_id': 'a'})
        self.assertDictEqual(result, {'x': {'sender_id': 'a'}, 'count': 1})
        del x
        self.router.dispatch(WalkoffEvent.ActionStarted, {'sender_id': 'a'})
        self.assertDictEqual(result, {'x': {'sender_id': 'a'}, 'count': 1})

    def test_dispatch_sender_id_only_strong(self):
        result = {'x': True, 'count': 0}

        def x(data):
            result['x'] = data
            result['count'] += 1

        self.router.register_events(x, {WalkoffEvent.ActionStarted}, names='a', weak=False)

        self.router.dispatch(WalkoffEvent.ActionStarted, {'sender_id': 'a'})
        self.assertDictEqual(result, {'x': {'sender_id': 'a'}, 'count': 1})
        del x
        self.router.dispatch(WalkoffEvent.ActionStarted, {'sender_id': 'a'})
        self.assertDictEqual(result, {'x': {'sender_id': 'a'}, 'count': 2})

    def test_dispatch_sender_name(self):
        result = {'x': True, 'count': 0}

        def x(data):
            result['x'] = data
            result['count'] += 1

        self.router.register_events(x, {WalkoffEvent.ActionStarted}, names='b')

        self.router.dispatch(WalkoffEvent.ActionStarted, {'sender_id': 'a', 'sender_name': 'b'})
        self.assertDictEqual(result, {'x': {'sender_id': 'a', 'sender_name': 'b'}, 'count': 1})

    def test_dispatch_sender_name_and_id(self):
        result = {'x': True, 'count': 0}
        result2 = {'x': False}

        def x(data):
            result['x'] = data
            result['count'] += 1

        def y(data):
            result2['x'] = True

        self.router.register_events(x, {WalkoffEvent.ActionStarted}, names='b')
        self.router.register_events(y, {WalkoffEvent.ActionStarted}, names='a')

        self.router.dispatch(WalkoffEvent.ActionStarted, {'sender_id': 'a', 'sender_name': 'b'})
        self.assertDictEqual(result, {'x': {'sender_id': 'a', 'sender_name': 'b'}, 'count': 1})
        self.assertTrue(result2['x'])

    def test_dispatch_registed_no_sender_name_or_uid(self):
        result = {'x': True, 'count': 0}
        result2 = {'x': False}

        def x(data):
            result['x'] = data
            result['count'] += 1

        def y(data):
            result2['x'] = True

        self.router.register_events(x, {WalkoffEvent.ActionStarted})
        self.router.register_events(y, {WalkoffEvent.ActionStarted})

        self.router.dispatch(WalkoffEvent.ActionStarted, {'sender_id': 'a', 'sender_name': 'b'})
        self.assertDictEqual(result, {'x': {'sender_id': 'a', 'sender_name': 'b'}, 'count': 1})
        self.assertTrue(result2['x'])

    def test_dispatch_controller_event(self):
        result = {'x': False}

        def x():
            result['x'] = True

        self.router.register_events(x, {WalkoffEvent.SchedulerStart}, names=EventType.controller.name)

        self.router.dispatch(WalkoffEvent.SchedulerStart, None)
        self.assertTrue(result['x'])

    def test_is_registered_empty_router(self):
        self.assertFalse(self.router.is_registered('a', WalkoffEvent.ActionArgumentsInvalid, func))

    def test_is_registered_id_not_registered(self):
        self.router.register_events(func, {WalkoffEvent.SchedulerStart}, names='b')
        self.assertFalse(self.router.is_registered('a', WalkoffEvent.ActionArgumentsInvalid, func))

    def test_is_registered_event_not_registered(self):
        self.router.register_events(func, {WalkoffEvent.SchedulerStart}, names='a')
        self.assertFalse(self.router.is_registered('a', WalkoffEvent.ActionArgumentsInvalid, func))

    def test_is_registered_func_not_registered(self):
        self.router.register_events(func2, {WalkoffEvent.ActionArgumentsInvalid}, names='a')
        self.assertFalse(self.router.is_registered('a', WalkoffEvent.ActionArgumentsInvalid, func))

    def test_is_registered_valid(self):
        self.router.register_events(func, {WalkoffEvent.ActionArgumentsInvalid}, names='a')
        self.assertTrue(self.router.is_registered('a', WalkoffEvent.ActionArgumentsInvalid, func))
