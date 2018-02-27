from unittest import TestCase

import walkoff.config.config
from walkoff.events import WalkoffEvent, EventType
from interfaces import InterfaceEventDispatcher, dispatcher
from interfaces.exceptions import UnknownEvent, InvalidEventHandler
from walkoff.helpers import UnknownAppAction, UnknownApp
from tests.util import execution_db_help
import uuid
from walkoff.executiondb.representable import Representable


class MockWorkflow(Representable):
    def __init__(self):
        self.id = uuid.uuid4()
        self.name = "name"
        self._execution_id = uuid.uuid4()

    def get_execution_id(self):
        return self._execution_id

    def as_json(self):
        return {'id': self.id,
                'execution_id': self._execution_id,
                'name': self.name}


class TestInterfaceEventDispatcher(TestCase):
    @classmethod
    def setUpClass(cls):
        execution_db_help.setup_dbs()
        walkoff.config.config.app_apis = {'App1': {'actions': {'action1': None,
                                                            'action2': None,
                                                            'action3': None}},
                                       'App2': {}}
        cls.action_events = {event for event in WalkoffEvent if event.event_type == EventType.action and event != WalkoffEvent.SendMessage}

    def setUp(self):
        dispatcher._clear()

    def tearDown(self):
        execution_db_help.cleanup_device_db()

    @classmethod
    def tearDownClass(cls):
        dispatcher._clear()
        walkoff.config.config.app_apis = {}
        execution_db_help.tear_down_device_db()

    def test_singleton(self):
        self.assertEqual(id(dispatcher), id(InterfaceEventDispatcher()))

    def test_registration_correct_number_methods_generated(self):
        methods = [method for method in dir(dispatcher) if method.startswith('on_')]
        expected_number = len([event for event in WalkoffEvent if event.event_type != EventType.other and event != WalkoffEvent.SendMessage]) + 2
        # 2: one for on_app_action and one for on_walkoff_event
        self.assertEqual(len(methods), expected_number)

    def test_all_events_are_controller_single_non_controller(self):
        self.assertFalse(InterfaceEventDispatcher._all_events_are_controller({WalkoffEvent.ActionStarted}))

    def test_all_events_are_controller_multiple_non_controller(self):
        self.assertFalse(InterfaceEventDispatcher._all_events_are_controller({WalkoffEvent.ActionStarted,
                                                                              WalkoffEvent.ActionExecutionError}))

    def test_all_events_are_controller_single_controller(self):
        self.assertTrue(InterfaceEventDispatcher._all_events_are_controller({WalkoffEvent.SchedulerStart}))

    def test_all_events_are_controller_multiple_controller(self):
        self.assertTrue(InterfaceEventDispatcher._all_events_are_controller({WalkoffEvent.SchedulerStart,
                                                                             WalkoffEvent.SchedulerJobExecuted}))

    def test_all_events_are_controller_mixed_events(self):
        with self.assertRaises(ValueError):
            InterfaceEventDispatcher._all_events_are_controller({WalkoffEvent.WorkflowShutdown,
                                                                 WalkoffEvent.SchedulerStart})

    def test_validate_handler_function_args_not_controller_too_few(self):
        def x(): pass

        with self.assertRaises(InvalidEventHandler):
            InterfaceEventDispatcher._validate_handler_function_args(x, False)

    def test_validate_handler_function_args_not_controller_too_many(self):
        def x(a, b): pass

        with self.assertRaises(InvalidEventHandler):
            InterfaceEventDispatcher._validate_handler_function_args(x, False)

    def test_validate_handler_function_args_not_controller_valid(self):
        def x(a): pass

        InterfaceEventDispatcher._validate_handler_function_args(x, False)

    def test_validate_handler_function_args_controller_valid(self):
        def x(): pass

        InterfaceEventDispatcher._validate_handler_function_args(x, True)

    def test_validate_handler_function_args_controller_too_many(self):
        def x(a): pass

        with self.assertRaises(InvalidEventHandler):
            InterfaceEventDispatcher._validate_handler_function_args(x, True)

    def test_make_on_event_docstring_not_controller(self):
        doc = InterfaceEventDispatcher._make_on_walkoff_event_docstring(WalkoffEvent.ActionStarted)
        self.assertIn('sender_uids', doc)
        self.assertIn('sender_ids', doc)
        self.assertIn('names', doc)
        self.assertIn('weak', doc)
        self.assertIn('def handler(data)', doc)

    def test_make_on_event_docstring_controller(self):
        doc = InterfaceEventDispatcher._make_on_walkoff_event_docstring(WalkoffEvent.SchedulerStart)
        self.assertIn('weak', doc)
        self.assertNotIn('sender_uids', doc)
        self.assertNotIn('sender_ids', doc)
        self.assertNotIn('names', doc)
        self.assertIn('def handler()', doc)

    def test_on_walkoff_events_single_invalid_event(self):
        with self.assertRaises(UnknownEvent):
            @dispatcher.on_walkoff_events('Invalid', sender_ids='a')
            def x(data): pass

    def test_on_walkoff_events_invalid_event_in_valid_events(self):
        with self.assertRaises(UnknownEvent):
            @dispatcher.on_walkoff_events({'Invalid', WalkoffEvent.ActionStarted}, sender_ids='a')
            def x(data): pass

    def test_on_walkoff_events_single_event_single_id(self):
        @dispatcher.on_walkoff_events({WalkoffEvent.ActionStarted}, sender_ids='a')
        def x(data): pass

        self.assertTrue(dispatcher.event_dispatcher.is_registered('a', WalkoffEvent.ActionStarted, x))

    def test_on_walkoff_events_single_event_single_id_strong(self):
        @dispatcher.on_walkoff_events({WalkoffEvent.ActionStarted}, sender_ids='a', weak=False)
        def x(data): pass

        self.assertTrue(dispatcher.event_dispatcher.is_registered('a', WalkoffEvent.ActionStarted, x))

    def test_on_walkoff_events_single_event_multiple_ids(self):
        @dispatcher.on_walkoff_events({WalkoffEvent.ActionStarted}, sender_ids=('a', 'b'))
        def x(data): pass

        self.assertTrue(dispatcher.event_dispatcher.is_registered('a', WalkoffEvent.ActionStarted, x))
        self.assertTrue(dispatcher.event_dispatcher.is_registered('b', WalkoffEvent.ActionStarted, x))

    def test_on_walkoff_events_single_event_single_name(self):
        @dispatcher.on_walkoff_events({WalkoffEvent.ActionStarted}, names='a')
        def x(data): pass

        self.assertTrue(dispatcher.event_dispatcher.is_registered('a', WalkoffEvent.ActionStarted, x))

    def test_on_walkoff_events_single_event_multiple_names(self):
        @dispatcher.on_walkoff_events({WalkoffEvent.ActionStarted}, names=('a', 'b'))
        def x(data): pass

        self.assertTrue(dispatcher.event_dispatcher.is_registered('a', WalkoffEvent.ActionStarted, x))
        self.assertTrue(dispatcher.event_dispatcher.is_registered('b', WalkoffEvent.ActionStarted, x))

    def test_on_walkoff_events_single_event_mixed_name_ids(self):
        @dispatcher.on_walkoff_events({WalkoffEvent.ActionStarted}, sender_ids='c', names=('a', 'b'))
        def x(data): pass

        self.assertTrue(dispatcher.event_dispatcher.is_registered('a', WalkoffEvent.ActionStarted, x))
        self.assertTrue(dispatcher.event_dispatcher.is_registered('b', WalkoffEvent.ActionStarted, x))
        self.assertTrue(dispatcher.event_dispatcher.is_registered('c', WalkoffEvent.ActionStarted, x))

    def test_on_walkoff_events_multiple_events_single_name(self):
        @dispatcher.on_walkoff_events({WalkoffEvent.AppInstanceCreated, WalkoffEvent.ActionStarted}, names='a')
        def x(data): pass

        self.assertTrue(dispatcher.event_dispatcher.is_registered('a', WalkoffEvent.ActionStarted, x))
        self.assertTrue(dispatcher.event_dispatcher.is_registered('a', WalkoffEvent.AppInstanceCreated, x))

    def test_on_walkoff_events_controller_event_no_ids_or_names(self):
        @dispatcher.on_walkoff_events({WalkoffEvent.SchedulerStart})
        def x(): pass

        self.assertTrue(
            dispatcher.event_dispatcher.is_registered(EventType.controller.name, WalkoffEvent.SchedulerStart, x))

    def test_on_walkoff_events_multiple_controller_events_no_ids_or_names(self):
        @dispatcher.on_walkoff_events({WalkoffEvent.SchedulerStart, WalkoffEvent.SchedulerShutdown})
        def x(): pass

        self.assertTrue(
            dispatcher.event_dispatcher.is_registered(EventType.controller.name, WalkoffEvent.SchedulerStart, x))
        self.assertTrue(
            dispatcher.event_dispatcher.is_registered(EventType.controller.name, WalkoffEvent.SchedulerShutdown, x))

    def test_on_walkoff_events_controller_event_with_ids(self):
        @dispatcher.on_walkoff_events({WalkoffEvent.SchedulerStart}, sender_ids='a')
        def x(): pass

        self.assertTrue(
            dispatcher.event_dispatcher.is_registered(EventType.controller.name, WalkoffEvent.SchedulerStart, x))
        self.assertFalse(dispatcher.event_dispatcher.is_registered('a', WalkoffEvent.SchedulerStart, x))

    def test_on_walkoff_events_multiple_controller_events_with_names(self):
        @dispatcher.on_walkoff_events({WalkoffEvent.SchedulerStart, WalkoffEvent.SchedulerShutdown}, names=('a', 'b'))
        def x(): pass

        self.assertTrue(
            dispatcher.event_dispatcher.is_registered(EventType.controller.name, WalkoffEvent.SchedulerStart, x))
        self.assertTrue(
            dispatcher.event_dispatcher.is_registered(EventType.controller.name, WalkoffEvent.SchedulerShutdown, x))

    def test_on_walkoff_events_invalid_function(self):
        with self.assertRaises(InvalidEventHandler):
            @dispatcher.on_walkoff_events({WalkoffEvent.ActionStarted}, sender_ids='c')
            def x(): pass

    def test_on_walkoff_events_invalid_function_control_event(self):
        with self.assertRaises(InvalidEventHandler):
            @dispatcher.on_walkoff_events({WalkoffEvent.SchedulerStart})
            def x(data): pass

    def test_on_app_action_invalid_event(self):
        with self.assertRaises(UnknownEvent):
            @dispatcher.on_app_actions('App1', events='Invalid')
            def x(data): pass

    def test_on_app_action_non_action_event(self):
        with self.assertRaises(UnknownEvent):
            @dispatcher.on_app_actions('App1', events=WalkoffEvent.SchedulerStart)
            def x(data): pass

    def test_on_app_action_invalid_handler_function_arg_count(self):
        with self.assertRaises(InvalidEventHandler):
            @dispatcher.on_app_actions('App1')
            def x(): pass

    def test_on_app_action_with_invalid_app(self):
        with self.assertRaises(UnknownApp):
            @dispatcher.on_app_actions('Invalid')
            def x(data): pass

    def test_on_app_action_with_invalid_action(self):
        with self.assertRaises(UnknownAppAction):
            @dispatcher.on_app_actions('App1', actions='invalid')
            def x(data): pass

    def test_on_app_action_single_action_all_events_all_devices(self):
        @dispatcher.on_app_actions('App1', actions='action1')
        def x(data): pass

        for event in self.action_events:
            self.assertTrue(dispatcher.app_action_dispatcher.is_registered('App1', 'action1', event, 'all', x))

    def test_on_app_action_multiple_actions_all_events_all_devices(self):
        @dispatcher.on_app_actions('App1', actions=('action1', 'action2'))
        def x(data): pass

        for event in self.action_events:
            self.assertTrue(dispatcher.app_action_dispatcher.is_registered('App1', 'action1', event, 'all', x))
            self.assertTrue(dispatcher.app_action_dispatcher.is_registered('App1', 'action2', event, 'all', x))

    def test_on_app_action_single_action_single_event_all_devices(self):
        @dispatcher.on_app_actions('App1', actions='action1', events=WalkoffEvent.ActionStarted)
        def x(data): pass

        self.assertTrue(dispatcher.app_action_dispatcher.is_registered('App1', 'action1', WalkoffEvent.ActionStarted,
                                                                       'all', x))

    def test_on_app_action_single_action_multiple_events_all_devices(self):
        @dispatcher.on_app_actions('App1', actions='action1',
                                   events=[WalkoffEvent.ActionStarted, WalkoffEvent.ActionExecutionError])
        def x(data): pass

        self.assertTrue(dispatcher.app_action_dispatcher.is_registered('App1', 'action1', WalkoffEvent.ActionStarted,
                                                                       'all', x))
        self.assertTrue(
            dispatcher.app_action_dispatcher.is_registered('App1', 'action1', WalkoffEvent.ActionExecutionError,
                                                           'all', x))

    def test_on_app_action_single_action_single_events_single_device(self):
        @dispatcher.on_app_actions('App1', actions='action1', events=WalkoffEvent.ActionStarted, device_ids=1)
        def x(data): pass

        self.assertTrue(dispatcher.app_action_dispatcher.is_registered('App1', 'action1', WalkoffEvent.ActionStarted,
                                                                       1, x))

    def test_on_app_action_single_action_single_events_multiple_devices(self):
        @dispatcher.on_app_actions('App1', actions='action1', events=WalkoffEvent.ActionStarted, device_ids=[1, 2])
        def x(data): pass

        self.assertTrue(dispatcher.app_action_dispatcher.is_registered('App1', 'action1', WalkoffEvent.ActionStarted,
                                                                       1, x))
        self.assertTrue(dispatcher.app_action_dispatcher.is_registered('App1', 'action1', WalkoffEvent.ActionStarted,
                                                                       2, x))

    def test_example_on_walkoff_event_controller_event(self):

        result = {'x': False}

        @dispatcher.on_walkoff_events(WalkoffEvent.SchedulerStart, sender_ids='a')
        def x():
            result['x'] = True

        self.id = 'test'
        WalkoffEvent.SchedulerStart.send(self)
        self.assertTrue(result['x'])

    def test_example_on_walkoff_event_controller_event_one_errors(self):

        result = {'x': False}

        @dispatcher.on_walkoff_events(WalkoffEvent.SchedulerStart, sender_ids='a')
        def x():
            result['x'] = True

        @dispatcher.on_walkoff_events(WalkoffEvent.SchedulerStart, sender_ids='a')
        def y():
            raise ValueError()

        self.id = 'test'
        WalkoffEvent.SchedulerStart.send(self)
        self.assertTrue(result['x'])

    @staticmethod
    def get_kwargs(workflow):
        return {'workflow': {'execution_id': str(workflow.get_execution_id())}}

    def test_example_on_walkoff_event_noncontroller_event(self):

        result = {'x': False}
        self.id = uuid.uuid4()

        @dispatcher.on_walkoff_events(WalkoffEvent.ActionStarted, sender_ids=self.id)
        def x(data):
            result['x'] = True
            result['data'] = data

        workflow = MockWorkflow()
        WalkoffEvent.WorkflowExecutionPending.send(workflow.as_json())

        data = {'id': self.id, 'name': 'b', 'device_id': 2, 'app_name': 'App1', 'action_name': 'action1',
                'execution_id': uuid.uuid4()}
        kwargs = self.get_kwargs(workflow)
        WalkoffEvent.ActionStarted.send(data, data=kwargs)
        expected = data
        expected.update(kwargs)
        expected['sender_id'] = expected.pop('id')
        expected['sender_name'] = expected.pop('name')
        self.assertTrue(result['x'])
        self.assertDictEqual(result['data'], expected)

    def test_example_on_walkoff_event_noncontroller_event_with_uids(self):

        result = {'x': False}
        self.id = uuid.uuid4()

        @dispatcher.on_walkoff_events(WalkoffEvent.ActionStarted, sender_uids=self.id)
        def x(data):
            result['x'] = True
            result['data'] = data

        workflow = MockWorkflow()
        WalkoffEvent.WorkflowExecutionPending.send(workflow.as_json())

        data = {'id': self.id, 'name': 'b', 'device_id': 2, 'app_name': 'App1', 'action_name': 'action1',
                'execution_id': uuid.uuid4()}
        kwargs = self.get_kwargs(workflow)
        WalkoffEvent.ActionStarted.send(data, data=kwargs)
        expected = data
        expected.update(kwargs)
        expected['sender_id'] = expected.pop('id')
        expected['sender_name'] = expected.pop('name')
        self.assertTrue(result['x'])
        self.assertDictEqual(result['data'], expected)

    def test_example_on_app_action_event(self):

        result = {}

        @dispatcher.on_app_actions('App1', actions='action1', events=WalkoffEvent.ActionStarted)
        def x(data):
            result['data'] = data

        workflow = MockWorkflow()
        WalkoffEvent.WorkflowExecutionPending.send(workflow.as_json())

        self.id = 'test'
        data = {'id': uuid.uuid4(), 'name': 'b', 'device_id': 2, 'app_name': 'App1', 'action_name': 'action1',
                'execution_id': uuid.uuid4()}
        kwargs = self.get_kwargs(workflow)
        WalkoffEvent.ActionStarted.send(data, data=kwargs)
        expected = data
        expected.update(kwargs)
        expected['sender_id'] = expected.pop('id')
        expected['sender_name'] = expected.pop('name')
        self.assertDictEqual(result['data'], expected)

    def test_example_on_app_action_event_one_event_errors(self):

        result = {}

        @dispatcher.on_app_actions('App1', actions='action1', events=WalkoffEvent.ActionStarted)
        def x(data):
            result['data'] = data

        @dispatcher.on_app_actions('App1', actions='action1', events=WalkoffEvent.ActionStarted)
        def y(data):
            result['y'] = True
            raise ValueError()

        workflow = MockWorkflow()
        WalkoffEvent.WorkflowExecutionPending.send(workflow.as_json())

        self.id = 'test'
        data = {'id': uuid.uuid4(), 'name': 'b', 'device_id': 2, 'app_name': 'App1', 'action_name': 'action1',
                'execution_id': uuid.uuid4()}
        kwargs = self.get_kwargs(workflow)
        WalkoffEvent.ActionStarted.send(data, data=kwargs)
        expected = data
        expected.update(kwargs)
        expected['sender_id'] = expected.pop('id')
        expected['sender_name'] = expected.pop('name')
        self.assertDictEqual(result['data'], expected)
        self.assertTrue(result['y'])

    def test_example_autogenerated_registration(self):
        result = {}
        self.id = uuid.uuid4()

        @dispatcher.on_action_started(sender_ids=self.id)
        def x(data):
            result['data'] = data

        workflow = MockWorkflow()
        WalkoffEvent.WorkflowExecutionPending.send(workflow.as_json())

        data = {'id': self.id, 'name': 'b', 'device_id': 2, 'app_name': 'App1', 'action_name': 'action1',
                'execution_id': uuid.uuid4()}
        kwargs = self.get_kwargs(workflow)
        WalkoffEvent.ActionStarted.send(data, data=kwargs)
        expected = data
        expected.update(kwargs)
        expected['sender_id'] = expected.pop('id')
        expected['sender_name'] = expected.pop('name')
        self.assertDictEqual(result['data'], expected)
