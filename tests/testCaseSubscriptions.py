import unittest
from core.case.subscription import _SubscriptionEventList
from core.case.subscription import *
import core.case.database as case_database
from tests.util.case import *


class TestCaseSubscriptions(unittest.TestCase):
    def setUp(self):
        case_database.initialize()

    def tearDown(self):
        case_database.case_db.tearDown()

    def test_subscription_list(self):

        subscription_list1 = _SubscriptionEventList.construct('*')
        self.assertIsNotNone(subscription_list1, '_SubscriptionList constructed with "*" is None')
        self.assertTrue(subscription_list1.all,
                        '_SubscriptionList initialized with "*" operator should have self.all = True')
        self.assertTrue(subscription_list1.is_subscribed('a'),
                        '_SubscriptionList constructed with "*" should be subscribed to all events')

        subscription_list2_events = ['a', 'b', 'c', 'd']
        subscription_list2 = _SubscriptionEventList.construct(subscription_list2_events)
        self.assertIsNotNone(subscription_list2, '_SubscriptionList constructed with a list of events is None')
        self.assertFalse(subscription_list2.all,
                         '_SubscriptionList not initialized with "*" should have self.all = False')
        self.assertTrue(all(subscription_list2.is_subscribed(event_name) for event_name in subscription_list2_events),
                        'Some events subscribed to in _SubscriptionList are improperly subscribed to')
        self.assertFalse(subscription_list2.is_subscribed('ff'), 'event not subscribed to is claiming to be subscribed')

        subscription_list3 = _SubscriptionEventList.construct('a')
        self.assertIsNotNone(subscription_list3, '_SubscriptionList constructed with a single events is None')
        self.assertFalse(subscription_list3.all,
                         '_SubscriptionList not initialized with "*" should have self.all = False')
        self.assertTrue(subscription_list3.is_subscribed('a'),
                        'Some events subscribed to in _SubscriptionList are improperly subscribed to')
        self.assertFalse(subscription_list3.is_subscribed('ff'), 'event not subscribed to is claiming to be subscribed')

    def test_global_subscriptions(self):
        step_subs_events = ['b', 'c']
        filter_subs_events = ['d', 'e']
        global_subs = GlobalSubscriptions(controller='a', step=step_subs_events, flag='*', filter=filter_subs_events)

        none_error_message = 'A subscription level which should not be None is None: {0}'
        should_be_subscribed_message = 'A subscription level which should be subscribed ' \
                                       'to events {0} is not subscribed: {1}'
        should_not_be_subscribed_message = 'A subscription level which should be not subscribed ' \
                                           'to events {0} is subscribed: {1}'
        unitialized_subscribed_message = 'An uninitialized subscription level should be subscriped to no events'

        level_iter = iter(global_subs)

        controller_subs = next(level_iter)
        self.assertIsNotNone(controller_subs, none_error_message.format('controller'))
        self.assertTrue(controller_subs.is_subscribed('a'), should_be_subscribed_message.format('a', 'controller'))
        self.assertFalse(controller_subs.is_subscribed('b'), should_not_be_subscribed_message.format('b', 'controller'))

        workflow_subs = next(level_iter)
        self.assertIsNotNone(workflow_subs, none_error_message.format('workflow'))
        self.assertFalse(workflow_subs.is_subscribed('b'), unitialized_subscribed_message)

        step_subs = next(level_iter)
        self.assertIsNotNone(step_subs, none_error_message.format('step'))
        self.assertTrue(all(step_subs.is_subscribed(event_name) for event_name in step_subs_events),
                        should_be_subscribed_message.format(step_subs_events, 'step'))
        self.assertFalse(step_subs.is_subscribed('a'), should_not_be_subscribed_message.format('a', 'step'))

        nextstep_subs = next(level_iter)
        self.assertIsNotNone(nextstep_subs, none_error_message.format('next step'))
        self.assertFalse(nextstep_subs.is_subscribed('b'), unitialized_subscribed_message)

        flag_subs = next(level_iter)
        self.assertIsNotNone(flag_subs, none_error_message.format('flag'))
        self.assertTrue(all(flag_subs.is_subscribed(event_name) for event_name in ['a', 'b', 'ff']),
                        'subscription level initialized with "*" should be subscribed to all events')

        filter_subs = next(level_iter)
        self.assertIsNotNone(filter_subs, none_error_message.format('filter'))
        self.assertTrue(all(filter_subs.is_subscribed(event_name) for event_name in filter_subs_events),
                        should_be_subscribed_message.format(filter_subs_events, 'filter'))
        self.assertFalse(filter_subs.is_subscribed('a'), should_not_be_subscribed_message.format('a', 'filter'))

        with self.assertRaises(StopIteration):
            next(level_iter)

    def test_subscription(self):
        sub1_events = ['a', 'b', 'c']
        sub1 = Subscription(events=sub1_events)
        global_sub1_events = ['a', 'd', 'f', 'g']
        sub1_all_events = set(sub1_events) | set(global_sub1_events)
        global_sub1 = _SubscriptionEventList(global_sub1_events)
        self.assertIsNotNone(sub1, 'Subscription initialized with event=list should not be None')
        self.assertTrue(all(sub1.is_subscribed(event_name) for event_name in sub1_events),
                        'Subscription which should be subscribed to events {0} is not'.format(sub1_events))
        self.assertTrue(all(sub1.is_subscribed(event_name, global_subs=global_sub1) for event_name in sub1_all_events),
                        'Subscription of {0} given global subscriptions {1} and is not subscribed '
                        'some of events in {2}'.format(sub1_events, global_sub1_events, sub1_all_events))
        not_subscribed = ['x', 'y', 'z']
        self.assertTrue(not any(sub1.is_subscribed(event_name, global_subs=global_sub1)
                                for event_name in not_subscribed),
                        'Subscription of {0}, given global subscriptions {1}, is subscribed to'
                        'some of events in {2}'.format(sub1_events, global_sub1_events, not_subscribed))

        sub2_disabled = ['a', 'd', 'f']
        sub2 = Subscription(events=sub1_events, disabled=sub2_disabled)
        self.assertIsNotNone(sub2, 'Subscription initialized with event=list and disabled=list should not be None')
        self.assertTrue(not any(sub2.is_subscribed(event_name) for event_name in sub2_disabled),
                        'Subscription should not be subscribed to events which are disabled')
        valid_subs = set(sub1_events) - set(sub2_disabled)
        self.assertTrue(all(sub2.is_subscribed(event_name) for event_name in valid_subs),
                        'Subscription should be subscribed to all events which are not disabled')
        valid_with_global = set(sub1_all_events) - set(sub2_disabled)
        self.assertTrue(all(sub2.is_subscribed(event_name, global_subs=global_sub1)
                            for event_name in valid_with_global),
                        'Subscription should be subscribed to all events in either self or global which '
                        'are not disabled')
        self.assertTrue(not any(sub2.is_subscribed(event_name, global_subs=global_sub1)
                                for event_name in sub2_disabled),
                        'Subscription should not be subscribed to any events which are disabled')

        sub3 = Subscription(events=sub1_events, disabled='*')
        self.assertIsNotNone(sub3, 'Subscription initialized with event=list and disabled="*" should not be None')
        self.assertTrue(not any(sub3.is_subscribed(event_name) for event_name in sub1_events),
                        'Subscription should not be subscribed to any events when all are disabled')
        valid_with_global = set(sub1_all_events) - set(sub2_disabled)
        self.assertTrue(not any(sub3.is_subscribed(event_name, global_subs=global_sub1)
                                for event_name in valid_with_global),
                        'Subscription should not be subscribed to any events in either self or global when all are '
                        'not disabled')
        self.assertTrue(not any(sub3.is_subscribed(event_name, global_subs=global_sub1)
                                for event_name in sub2_disabled),
                        'Subscription should not be subscribed to any events which are disabled')

        sub4 = Subscription(events='*', disabled='*')
        self.assertIsNotNone(sub4, 'Subscription initialized with event="*" and disabled="*" should not be None')
        self.assertTrue(not any(sub4.is_subscribed(event_name) for event_name in sub1_events),
                        'Subscription should not be subscribed to any events when all are disabled')
        valid_with_global = set(sub1_all_events) - set(sub2_disabled)
        self.assertTrue(not any(sub4.is_subscribed(event_name, global_subs=global_sub1)
                                for event_name in valid_with_global),
                        'Subscription should not be subscribed to any events in either self or global when all are '
                        'not disabled')
        self.assertTrue(not any(sub4.is_subscribed(event_name, global_subs=global_sub1)
                                for event_name in sub2_disabled),
                        'Subscription should not be subscribed to any events which are disabled')

    def test_case_subscriptions(self):
        case, acceptance = construct_case1()
        all_valid = all_valid_events(acceptance)
        acceptance_error_message = 'Subscription of execution level {0}, failed to accept an event from its list of ' \
                                   'subscribed events: {1} '
        rejection_error_message = 'Subscription of execution level {0}, failed to reject an event from its list ' \
                                  'of rejected events: {1} '
        for ancestry_combo in all_valid:
            self.assertTrue(all(case.is_subscribed(ancestry_combo['ancestry'], event_name)
                                for event_name in ancestry_combo['events']),
                            acceptance_error_message.format(ancestry_combo['ancestry'][-1], ancestry_combo['events']))
            self.assertTrue(not any(case.is_subscribed(ancestry_combo['ancestry'], event_name)
                                    for event_name in ancestry_combo['rejected']),
                            rejection_error_message.format(ancestry_combo['ancestry'][-1], ancestry_combo['rejected']))

    def test_set_subscriptions(self):
        case1, acceptance1 = construct_case1()
        case2, acceptance2 = construct_case2()
        cases = {'case1': case1, 'case2': case2}
        set_subscriptions(cases)
        cases_in_db = [case.name for case in case_database.case_db.session.query(case_database.Cases).all()]
        self.assertSetEqual(set(cases.keys()), set(cases_in_db), 'Not all cases were added to subscribed cases')

    def test_is_case_subscribed(self):
        case1, acceptance1 = construct_case1()
        case2, acceptance2 = construct_case2()
        all_valid1 = all_valid_events(acceptance1)
        all_valid2 = all_valid_events(acceptance2)
        acceptance_error_message = 'Case {0} Subscription of execution level {1}, failed to accept an event from its ' \
                                   'list of subscribed events: {2} '
        rejection_error_message = 'Case {0} Subscription of execution level {1}, failed to reject an event from its ' \
                                  'list of rejected events: {2} '
        cases = {'case1': case1, 'case2': case2}
        set_subscriptions(cases)
        for case, valid in (('case1', all_valid1), ('case2', all_valid2)):
            for ancestry_combo in valid:
                self.assertTrue(all(is_case_subscribed(case, ancestry_combo['ancestry'], event_name)
                                    for event_name in ancestry_combo['events']),
                                acceptance_error_message.format(case, ancestry_combo['ancestry'][-1],
                                                                ancestry_combo['events']))
                self.assertTrue(not any(is_case_subscribed(case, ancestry_combo['ancestry'], event_name)
                                        for event_name in ancestry_combo['rejected']),
                                rejection_error_message.format(case, ancestry_combo['ancestry'][-1],
                                                               ancestry_combo['rejected']))
