from unittest import TestCase

from walkoff.events import WalkoffEvent
from interfaces.exceptions import UnknownEvent
from interfaces.util import convert_events, convert_to_iterable, validate_events, add_docstring


class TestInterfaceEventDispatchHelpers(TestCase):
    def test_convert_events_no_events(self):
        self.assertSetEqual(convert_events([]), set())

    def test_convert_events_one_name(self):
        self.assertSetEqual(convert_events('Common Workflow Signal'),
                            {WalkoffEvent.CommonWorkflowSignal})

    def test_convert_events_one_event(self):
        self.assertSetEqual(convert_events(WalkoffEvent.CommonWorkflowSignal),
                            {WalkoffEvent.CommonWorkflowSignal})

    def test_convert_events_multiple_strings(self):
        self.assertSetEqual(convert_events(('Common Workflow Signal', 'Scheduler Start')),
                            {WalkoffEvent.CommonWorkflowSignal, WalkoffEvent.SchedulerStart})

    def test_convert_events_multiple_events(self):
        self.assertSetEqual(convert_events((WalkoffEvent.CommonWorkflowSignal, WalkoffEvent.SchedulerStart)),
                            {WalkoffEvent.CommonWorkflowSignal, WalkoffEvent.SchedulerStart})

    def test_convert_events_multiple_mixed_events(self):
        self.assertSetEqual(convert_events(('Common Workflow Signal', WalkoffEvent.SchedulerStart)),
                            {WalkoffEvent.CommonWorkflowSignal, WalkoffEvent.SchedulerStart})

    def test_convert_events_one_invalid_name(self):
        with self.assertRaises(UnknownEvent):
            convert_events(['Invalid'])

    def test_convert_events_some_invalid_name(self):
        with self.assertRaises(UnknownEvent):
            convert_events(('Common Workflow Signal', WalkoffEvent.SchedulerStart, 'Invalid'))

    def test_validate_events_all_events_default_available_events(self):
        self.assertEqual(validate_events(), set(WalkoffEvent))

    def test_validate_events_all_events_specified_available_events(self):
        available_events = (WalkoffEvent.CommonWorkflowSignal, WalkoffEvent.SchedulerStart)
        self.assertSetEqual(validate_events(allowed_events=available_events), set(available_events))

    def test_validate_events_no_events(self):
        self.assertSetEqual(set(validate_events(events=[])), set())

    def test_validate_events_no_available_events(self):
        with self.assertRaises(UnknownEvent):
            validate_events(events=[WalkoffEvent.CommonWorkflowSignal], allowed_events=[])

    def test_validate_events_too_few_events(self):
        self.assertSetEqual(validate_events(events=WalkoffEvent.CommonWorkflowSignal),
                            {WalkoffEvent.CommonWorkflowSignal})

    def test_validate_events_too_invalid_events(self):
        with self.assertRaises(UnknownEvent):
            validate_events(events=(WalkoffEvent.CommonWorkflowSignal,),
                            allowed_events=(WalkoffEvent.SchedulerStart,))

    def test_validate_events_single_invalid_event(self):
        with self.assertRaises(UnknownEvent):
            validate_events(events=WalkoffEvent.CommonWorkflowSignal,
                            allowed_events=(WalkoffEvent.SchedulerStart,))

    def test_unknown_event_init_single_event(self):
        exception = UnknownEvent('SingleEvent')
        self.assertIn('SingleEvent', exception.message)

    def test_unknown_event_init_multiple_event(self):
        exception = UnknownEvent(['Event1', 'Event2'])
        self.assertIn('Event1', exception.message)
        self.assertIn('Event2', exception.message)

    def test_add_docstring(self):
        @add_docstring('test_docstring')
        def x(): pass

        self.assertEqual(x.__doc__, 'test_docstring')

    def test_convert_to_iterable_already_iterable(self):
        self.assertListEqual(convert_to_iterable([1, 2, 3, 4]), [1, 2, 3, 4])

    def test_convert_to_iterable(self):
        self.assertListEqual(convert_to_iterable(1), [1])

    def test_convert_to_iterable_with_string(self):
        self.assertListEqual(convert_to_iterable('hello'), ['hello'])
