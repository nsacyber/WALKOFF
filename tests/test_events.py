from copy import deepcopy
from unittest import TestCase

from walkoff.events import *


class TestEvents(TestCase):
    original_signals = deepcopy(WalkoffSignal._signals)

    def setUp(self):
        WalkoffSignal._signals = {}

    @classmethod
    def tearDownClass(cls):
        WalkoffSignal._signals = cls.original_signals
        for x, value in WalkoffSignal._signals.items():
            if hasattr(value, '__test'):
                WalkoffSignal._signals.pop(x)

    def test_walkoff_signal_init_default(self):
        signal = WalkoffSignal('name', EventType.action)
        self.assertEqual(signal.name, 'name')
        self.assertEqual(signal.event_type, EventType.action)
        self.assertIsInstance(signal.signal, Signal)
        self.assertEqual(len(WalkoffSignal._signals), 0)
        self.assertTrue(signal.is_loggable)

    def test_walkoff_signal_init_loggable_false(self):
        signal = WalkoffSignal('name', EventType.action, loggable=False)
        self.assertEqual(signal.name, 'name')
        self.assertEqual(signal.event_type, EventType.action)
        self.assertIsInstance(signal.signal, Signal)
        self.assertEqual(len(WalkoffSignal._signals), 0)
        self.assertFalse(signal.is_loggable)

    def test_walkoff_signal_connect_strong_ref(self):
        def xx(): pass

        setattr(xx, '__test', True)
        signal = WalkoffSignal('name', EventType.action, loggable=False)
        signal.connect(xx, weak=False)
        xx_id = id(xx)
        self.assertIn(xx_id, WalkoffSignal._signals)
        self.assertEqual(len(signal.signal.receivers), 1)
        del xx
        self.assertIn(xx_id, WalkoffSignal._signals)
        self.assertEqual(len(signal.signal.receivers), 1)

    def test_walkoff_signal_connect_weak_ref(self):
        def xx(): pass

        setattr(xx, '__test', True)
        signal = WalkoffSignal('name', EventType.action, loggable=False)
        signal.connect(xx)
        xx_id = id(xx)
        self.assertNotIn(xx_id, WalkoffSignal._signals)
        self.assertEqual(len(signal.signal.receivers), 1)
        del xx
        self.assertNotIn(xx_id, WalkoffSignal._signals)
        self.assertEqual(len(signal.signal.receivers), 0)

    def test_walkoff_signal_send(self):
        signal = WalkoffSignal('name', EventType.action, loggable=False)
        result = {'triggered': False}

        def xx(sender, **kwargs):
            result['triggered'] = True
            result['sender'] = sender
            result['kwargs'] = kwargs

        setattr(xx, '__test', True)
        signal.connect(xx)
        signal.send(5, x=42)
        self.assertTrue(result['triggered'])
        self.assertEqual(result['sender'], 5)
        self.assertDictEqual(result['kwargs'], {'x': 42})

    def test_walkoff_signal_store_callback(self):
        def xx(): pass

        setattr(xx, '__test', True)
        WalkoffSignal._store_callback(xx)
        self.assertEqual(WalkoffSignal._signals[id(xx)], xx)

    def test_controller_signal_init(self):
        signal = ControllerSignal('name', 'message', 16)
        self.assertEqual(signal.name, 'name')
        self.assertEqual(signal.scheduler_event, 16)
        self.assertEqual(signal.event_type, EventType.controller)
        self.assertTrue(signal.is_loggable)

    def test_workflow_signal_init(self):
        signal = WorkflowSignal('name', 'message')
        self.assertEqual(signal.name, 'name')
        self.assertEqual(signal.event_type, EventType.workflow)
        self.assertTrue(signal.is_loggable)

    def test_action_signal_init(self):
        signal = ActionSignal('name', 'message')
        self.assertEqual(signal.name, 'name')
        self.assertEqual(signal.event_type, EventType.action)
        self.assertTrue(signal.is_loggable)

    def test_action_signal_init_unloggable(self):
        signal = ActionSignal('name', 'message', loggable=False)
        self.assertEqual(signal.name, 'name')
        self.assertEqual(signal.event_type, EventType.action)
        self.assertFalse(signal.is_loggable)

    def test_branch_signal_init(self):
        signal = BranchSignal('name', 'message')
        self.assertEqual(signal.name, 'name')
        self.assertEqual(signal.event_type, EventType.branch)
        self.assertTrue(signal.is_loggable)

    def test_condition_signal_init(self):
        signal = ConditionSignal('name', 'message')
        self.assertEqual(signal.name, 'name')
        self.assertEqual(signal.event_type, EventType.condition)
        self.assertTrue(signal.is_loggable)

    def test_transform_signal_init(self):
        signal = TransformSignal('name', 'message')
        self.assertEqual(signal.name, 'name')
        self.assertEqual(signal.event_type, EventType.transform)
        self.assertTrue(signal.is_loggable)

    def test_walkoff_event_signal_name(self):
        self.assertEqual(WalkoffEvent.CommonWorkflowSignal.signal_name, 'Common Workflow Signal')

    def test_walkoff_event_signal(self):
        self.assertEqual(WalkoffEvent.CommonWorkflowSignal.signal, WalkoffEvent.CommonWorkflowSignal.value.signal)

    def test_walkoff_event_event_type(self):
        self.assertEqual(WalkoffEvent.CommonWorkflowSignal.event_type, EventType.other)

    def test_walkoff_event_get_event_from_name(self):
        self.assertEqual(WalkoffEvent.get_event_from_name('CommonWorkflowSignal'), WalkoffEvent.CommonWorkflowSignal)

    def test_walkoff_event_get_event_from_name_invalid(self):
        self.assertIsNone(WalkoffEvent.get_event_from_name('Invalid'))

    def test_walkoff_event_get_event_from_signal_name(self):
        self.assertEqual(WalkoffEvent.get_event_from_signal_name('Common Workflow Signal'),
                         WalkoffEvent.CommonWorkflowSignal)

    def test_walkoff_event_get_event_from_signal_name_invalid(self):
        self.assertIsNone(WalkoffEvent.get_event_from_signal_name('Invalid'))

    def test_walkoff_event_requires_data(self):
        for event in (
                WalkoffEvent.WorkflowShutdown, WalkoffEvent.ActionExecutionSuccess,
                WalkoffEvent.ActionExecutionError, WalkoffEvent.SendMessage):
            self.assertTrue(event.requires_data())

    def test_walkoff_event_does_not_require_data(self):
        for event in (WalkoffEvent.TransformError, WalkoffEvent.SchedulerStart, WalkoffEvent.SchedulerShutdown):
            self.assertFalse(event.requires_data())

    def test_walkoff_event_is_loggable(self):
        for event in (WalkoffEvent.CommonWorkflowSignal, WalkoffEvent.SendMessage):
            self.assertFalse(event.is_loggable())
        for event in (WalkoffEvent.SchedulerStart, WalkoffEvent.ActionStarted):
            self.assertTrue(event.is_loggable())

    def test_walkoff_event_connect_strong_reference(self):
        def xx(): pass

        setattr(xx, '__test', True)
        WalkoffEvent.CommonWorkflowSignal.connect(xx, weak=False)
        xx_id = id(xx)
        self.assertIn(xx_id, WalkoffSignal._signals)
        self.assertEqual(len(WalkoffEvent.CommonWorkflowSignal.signal.receivers), 1)
        del xx
        self.assertIn(xx_id, WalkoffSignal._signals)
        self.assertEqual(len(WalkoffEvent.CommonWorkflowSignal.signal.receivers), 1)

    def test_walkoff_event_connect_weak_reference(self):
        def xx(): pass

        setattr(xx, '__test', True)
        WalkoffEvent.CommonWorkflowSignal.connect(xx)
        xx_id = id(xx)
        self.assertNotIn(xx_id, WalkoffSignal._signals)
        self.assertEqual(len(WalkoffEvent.CommonWorkflowSignal.signal.receivers), 1)
        del xx
        self.assertNotIn(xx_id, WalkoffSignal._signals)
        self.assertEqual(len(WalkoffEvent.CommonWorkflowSignal.signal.receivers), 0)

    def test_walkoff_event_send(self):
        result = {'triggered': False}

        def xx(sender, **kwargs):
            result['triggered'] = True
            result['sender'] = sender
            result['kwargs'] = kwargs

        WalkoffEvent.CommonWorkflowSignal.connect(xx)
        WalkoffEvent.CommonWorkflowSignal.send(5, x=42)
        self.assertTrue(result['triggered'])
        self.assertEqual(result['sender'], 5)
        self.assertDictEqual(result['kwargs'], {'x': 42})
