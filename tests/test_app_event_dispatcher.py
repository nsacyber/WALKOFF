from unittest import TestCase

import core.config.config
from core.events import WalkoffEvent, EventType
from core.helpers import UnknownApp, UnknownAppAction
from interfaces import AppEventDispatcher


def func(): pass


class TestAppEventDispatcher(TestCase):
    @classmethod
    def setUpClass(cls):
        core.config.config.app_apis = {'App1': {'actions': {'action1': None,
                                                            'action2': None,
                                                            'action3': None}},
                                       'App2': {}}
        cls.possible_events = {event for event in WalkoffEvent if event.event_type == EventType.action}

    @classmethod
    def tearDownClass(cls):
        core.config.config.app_apis = {}

    def setUp(self):
        self.router = AppEventDispatcher()

    def assert_router_structure(self, app, actions, events, devices):
        self.assertSetEqual(set(self.router._router.keys()), {app})
        self.assertSetEqual(set(self.router._router[app].keys()), actions)
        for action in actions:
            self.assertSetEqual(set(self.router._router[app][action]._event_router.keys()), events)
            for event in self.router._router[app][action]._event_router.values():
                self.assertSetEqual(set(event.keys()), devices)

    def test_init(self):
        self.assertDictEqual(self.router._router, {})

    def test_validate_app_actions_unknown_app(self):
        with self.assertRaises(UnknownApp):
            AppEventDispatcher.validate_app_actions('Invalid', 'action1')

    def test_validate_app_actions_app_with_no_actions(self):
        with self.assertRaises(UnknownApp):
            AppEventDispatcher.validate_app_actions('App2', 'action1')

    def test_validate_app_actions_all_actions(self):
        self.assertSetEqual(AppEventDispatcher.validate_app_actions('App1', 'all'), {'action1', 'action2', 'action3'})

    def test_validate_app_actions_single_valid_actions(self):
        self.assertSetEqual(AppEventDispatcher.validate_app_actions('App1', 'action1'), {'action1'})

    def test_validate_app_actions_single_invalid_actions(self):
        with self.assertRaises(UnknownAppAction):
            AppEventDispatcher.validate_app_actions('App1', 'invalid')

    def test_validate_app_actions_multiple_valid_actions(self):
        self.assertSetEqual(AppEventDispatcher.validate_app_actions('App1', ['action1', 'action2']),
                            {'action1', 'action2'})

    def test_validate_app_actions_multiple_invalid_actions(self):
        with self.assertRaises(UnknownAppAction):
            AppEventDispatcher.validate_app_actions('App1', ['invalid1', 'invalid2'])

    def test_validate_app_actions_mixed_valid_invalid_actions(self):
        with self.assertRaises(UnknownAppAction):
            AppEventDispatcher.validate_app_actions('App1', ['invalid1', 'invalid2', 'action1', 'action2'])

    def test_register_app_actions_invalid_app(self):
        with self.assertRaises(UnknownApp):
            self.router.register_app_actions(func, 'Invalid', self.possible_events)

    def test_register_app_actions_invalid_action(self):
        with self.assertRaises(UnknownAppAction):
            self.router.register_app_actions(func, 'App1', self.possible_events, actions='invalid')

    def test_register_app_actions_all_actions_all_events_all_devices_app_not_registered(self):
        self.router.register_app_actions(func, 'App1', self.possible_events)
        self.assert_router_structure('App1', {'action1', 'action2', 'action3'}, self.possible_events, {'all'})

    def test_register_app_actions_all_actions_all_events_all_devices_app_registered(self):
        self.router._router = {'App1': {}}
        self.router.register_app_actions(func, 'App1', self.possible_events)
        self.assert_router_structure('App1', {'action1', 'action2', 'action3'}, self.possible_events, {'all'})

    def test_register_app_actions_all_actions_all_events_single_device(self):
        self.router.register_app_actions(func, 'App1', self.possible_events, device_ids=1)
        self.assert_router_structure('App1', {'action1', 'action2', 'action3'}, self.possible_events, {1})

    def test_register_app_actions_all_actions_all_events_multiple_devices(self):
        self.router.register_app_actions(func, 'App1', self.possible_events, device_ids=[1, 2, 3])
        self.assert_router_structure('App1', {'action1', 'action2', 'action3'}, self.possible_events, {1, 2, 3})

    def test_register_app_actions_app_actions_single_event_all_devices(self):
        self.router.register_app_actions(func, 'App1', events={WalkoffEvent.ActionStarted})
        self.assert_router_structure('App1', {'action1', 'action2', 'action3'}, {WalkoffEvent.ActionStarted}, {'all'})

    def test_register_app_actions_app_actions_multiple_events_all_devices(self):
        self.router.register_app_actions(func, 'App1',
                                         events=(WalkoffEvent.ActionStarted, WalkoffEvent.ActionExecutionError))
        self.assert_router_structure('App1', {'action1', 'action2', 'action3'},
                                     {WalkoffEvent.ActionStarted, WalkoffEvent.ActionExecutionError}, {'all'})

    def test_register_app_actions_app_actions_single_action(self):
        self.router.register_app_actions(func, 'App1', self.possible_events, actions='action1')
        self.assert_router_structure('App1', {'action1'}, self.possible_events, {'all'})

    def test_register_app_actions_app_actions_multiple_actions(self):
        self.router.register_app_actions(func, 'App1', self.possible_events, actions=['action1', 'action2'])
        self.assert_router_structure('App1', {'action1', 'action2'}, self.possible_events, {'all'})

    def test_dispatch_nothing_in_router(self):  # check it doesn't error
        self.router.dispatch(WalkoffEvent.ActionStarted, {'app_name': 'App1', 'action_name': 'action1'})

    def test_dispatch_app_not_in_router(self):
        result = {'x': False}

        def x(data):
            result['x'] = True

        self.router.register_app_actions(x, 'App1', {WalkoffEvent.ActionStarted}, actions=['action1', 'action2'])
        self.router.dispatch(WalkoffEvent.ActionStarted, {'app_name': 'App2', 'action_name': 'action1'})
        self.assertDictEqual(result, {'x': False})

    def test_dispatch_action_not_in_router(self):
        result = {'x': False}

        def x(data):
            result['x'] = True

        self.router.register_app_actions(x, 'App1', {WalkoffEvent.ActionStarted}, actions=['action1', 'action2'])
        self.router.dispatch(WalkoffEvent.ActionStarted, {'app_name': 'App1', 'action_name': 'action3'})
        self.assertDictEqual(result, {'x': False})

    def test_dispatch_action_weak(self):
        result = {'x': False, 'count': 0}

        def x(data):
            result['x'] = data
            result['count'] += 1

        self.router.register_app_actions(x, 'App1', {WalkoffEvent.ActionStarted},
                                         actions=['action1', 'action2'], weak=True)
        data = {'app_name': 'App1', 'action_name': 'action2', 'device_id': 42}
        self.router.dispatch(WalkoffEvent.ActionStarted, data)
        self.assertDictEqual(result, {'x': data, 'count': 1})
        del x
        self.router.dispatch(WalkoffEvent.ActionStarted, data)
        self.assertDictEqual(result, {'x': data, 'count': 1})

    def test_dispatch_action_strong(self):
        result = {'x': False, 'count': 0}

        def x(data):
            result['x'] = data
            result['count'] += 1

        self.router.register_app_actions(x, 'App1', {WalkoffEvent.ActionStarted},
                                         actions=['action1', 'action2'], weak=False)
        data = {'app_name': 'App1', 'action_name': 'action2', 'device_id': 42}
        self.router.dispatch(WalkoffEvent.ActionStarted, data)
        self.assertDictEqual(result, {'x': data, 'count': 1})
        del x
        self.router.dispatch(WalkoffEvent.ActionStarted, data)
        self.assertDictEqual(result, {'x': data, 'count': 2})

    def test_is_registered_nothing_in_router(self):
        self.assertFalse(self.router.is_registered('App1', 'action1', WalkoffEvent.ActionStarted, 1, func))

    def test_is_registered_app_not_in_router(self):
        self.router._router = {'App2': {}}
        self.assertFalse(self.router.is_registered('App1', 'action1', WalkoffEvent.ActionStarted, 1, func))

    def test_is_registered_action_not_in_router(self):
        self.router.register_app_actions(func, 'App1', {WalkoffEvent.ActionStarted}, actions=['action1', 'action2'])
        self.assertFalse(self.router.is_registered('App1', 'action3', WalkoffEvent.ActionStarted, 1, func))

    def test_is_registered_action_device_not_in_router(self):
        self.router.register_app_actions(func, 'App1', {WalkoffEvent.ActionStarted},
                                         actions=['action1', 'action2'], device_ids=1)
        self.assertFalse(self.router.is_registered('App1', 'action1', WalkoffEvent.ActionStarted, 2, func))

    def test_is_registered_action_func_not_in_router(self):
        def func2(): pass

        self.router.register_app_actions(func2, 'App1', {WalkoffEvent.ActionStarted},
                                         actions=['action1', 'action2'], device_ids=1)
        self.assertFalse(self.router.is_registered('App1', 'action1', WalkoffEvent.ActionStarted, 1, func))

    def test_is_registered_valid(self):
        self.router.register_app_actions(func, 'App1', {WalkoffEvent.ActionStarted},
                                         actions=['action1', 'action2'], device_ids=1)
        self.assertTrue(self.router.is_registered('App1', 'action1', WalkoffEvent.ActionStarted, 1, func))
