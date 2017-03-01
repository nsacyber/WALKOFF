import unittest

import core.case.database as case_database
from core.case.subscription import _SubscriptionEventList
from tests.util.case import *
import copy


class TestCaseSubscriptionList(unittest.TestCase):
    def test_subscription_list_star_init(self):
        subscription_list1 = _SubscriptionEventList.construct('*')
        self.assertIsNotNone(subscription_list1, '_SubscriptionList constructed with "*" is None')
        self.assertTrue(subscription_list1.all,
                        '_SubscriptionList initialized with "*" operator should have self.all = True')
        self.assertTrue(subscription_list1.is_subscribed('a'),
                        '_SubscriptionList constructed with "*" should be subscribed to all events')

    def test_subscription_list_list_init(self):
        subscription_list2_events = ['a', 'b', 'c', 'd']
        subscription_list2 = _SubscriptionEventList.construct(subscription_list2_events)
        self.assertIsNotNone(subscription_list2, '_SubscriptionList constructed with a list of events is None')
        self.assertFalse(subscription_list2.all,
                         '_SubscriptionList not initialized with "*" should have self.all = False')
        self.assertTrue(all(subscription_list2.is_subscribed(event_name) for event_name in subscription_list2_events),
                        'Some events subscribed to in _SubscriptionList are improperly subscribed to')
        self.assertFalse(subscription_list2.is_subscribed('ff'), 'event not subscribed to is claiming to be subscribed')

    def test_subscription_list_single_init(self):
        subscription_list3 = _SubscriptionEventList.construct('a')
        self.assertIsNotNone(subscription_list3, '_SubscriptionList constructed with a single events is None')
        self.assertFalse(subscription_list3.all,
                         '_SubscriptionList not initialized with "*" should have self.all = False')
        self.assertTrue(subscription_list3.is_subscribed('a'),
                        'Some events subscribed to in _SubscriptionList are improperly subscribed to')
        self.assertFalse(subscription_list3.is_subscribed('ff'), 'event not subscribed to is claiming to be subscribed')

    def test_json(self):
        subscription_list1 = _SubscriptionEventList.construct('*')
        subscription_list2 = _SubscriptionEventList.construct(['a', 'b', 'c', 'd'])
        subscription_list3 = _SubscriptionEventList.construct('a')
        self.assertDictEqual({"events": [], "all": True}, subscription_list1.as_json())
        self.assertDictEqual({"events": ['a', 'b', 'c', 'd'], "all": False}, subscription_list2.as_json())
        self.assertDictEqual({"events": ['a'], "all": False}, subscription_list3.as_json())


class TestGlobalSubscriptions(unittest.TestCase):
    def setUp(self):
        self.step_subs_events = ['b', 'c']
        self.filter_subs_events = ['d', 'e']
        self.global_subs = GlobalSubscriptions(controller='a', step=self.step_subs_events, flag='*',
                                               filter=self.filter_subs_events)
        self.none_error_message = 'A subscription level which should not be None is None: {0}'
        self.should_be_subscribed_message = 'A subscription level which should be subscribed ' \
                                            'to events {0} is not subscribed: {1}'
        self.should_not_be_subscribed_message = 'A subscription level which should be not subscribed ' \
                                                'to events {0} is subscribed: {1}'
        self.uninitialized_subscribed_message = 'An uninitialized subscription level should be subscribed to no events'
        self.level_iter = iter(self.global_subs)

    def test_iteration(self):
        for _ in range(6):
            next(self.level_iter)
        with self.assertRaises(StopIteration):
            next(self.level_iter)

    def test_controller_subscriptions(self):
        controller_subs = next(self.level_iter)
        self.assertIsNotNone(controller_subs, self.none_error_message.format('controller'))
        self.assertTrue(controller_subs.is_subscribed('a'), self.should_be_subscribed_message.format('a', 'controller'))
        self.assertFalse(controller_subs.is_subscribed('b'),
                         self.should_not_be_subscribed_message.format('b', 'controller'))

    def test_workflow_subscriptions(self):
        next(self.level_iter)
        workflow_subs = next(self.level_iter)
        self.assertIsNotNone(workflow_subs, self.none_error_message.format('workflow'))
        self.assertFalse(workflow_subs.is_subscribed('b'), self.uninitialized_subscribed_message)

    def test_step_subscriptions(self):
        next(self.level_iter)
        next(self.level_iter)
        step_subs = next(self.level_iter)
        self.assertIsNotNone(step_subs, self.none_error_message.format('step'))
        self.assertTrue(all(step_subs.is_subscribed(event_name) for event_name in self.step_subs_events),
                        self.should_be_subscribed_message.format(self.step_subs_events, 'step'))
        self.assertFalse(step_subs.is_subscribed('a'), self.should_not_be_subscribed_message.format('a', 'step'))

    def test_nextstep_subscriptions(self):
        for _ in range(3):
            next(self.level_iter)
        nextstep_subs = next(self.level_iter)
        self.assertIsNotNone(nextstep_subs, self.none_error_message.format('next step'))
        self.assertFalse(nextstep_subs.is_subscribed('b'), self.uninitialized_subscribed_message)

    def test_flag_subscriptions(self):
        for _ in range(4):
            next(self.level_iter)
        flag_subs = next(self.level_iter)
        self.assertIsNotNone(flag_subs, self.none_error_message.format('flag'))
        self.assertTrue(all(flag_subs.is_subscribed(event_name) for event_name in ['a', 'b', 'ff']),
                        'subscription level initialized with "*" should be subscribed to all events')

    def test_filter_subscriptions(self):
        for _ in range(5):
            next(self.level_iter)
        filter_subs = next(self.level_iter)
        self.assertIsNotNone(filter_subs, self.none_error_message.format('filter'))
        self.assertTrue(all(filter_subs.is_subscribed(event_name) for event_name in self.filter_subs_events),
                        self.should_be_subscribed_message.format(self.filter_subs_events, 'filter'))
        self.assertFalse(filter_subs.is_subscribed('a'), self.should_not_be_subscribed_message.format('a', 'filter'))

    def test_json(self):
        expected_json = {"controller": {"events": ['a'], "all": False},
                         "workflow": {"events": [], "all": False},
                         "step": {"events": ['b', 'c'], "all": False},
                         "next_step": {"events": [], "all": False},
                         "flag": {"events": [], "all": True},
                         "filter": {"events": ['d', 'e'], "all": False}}
        self.assertDictEqual(expected_json, self.global_subs.as_json())


class TestSubscription(unittest.TestCase):
    def setUp(self):
        self.sub1_events = ['a', 'b', 'c']
        self.global_sub1_events = ['a', 'd', 'f', 'g']
        self.global_sub1 = _SubscriptionEventList(self.global_sub1_events)
        self.sub1_all_events = set(self.sub1_events) | set(self.global_sub1_events)
        self.sub2_disabled = ['a', 'd', 'f']
        self.valid_with_global = set(self.sub1_all_events) - set(self.sub2_disabled)

    def test_subscription_base(self):
        sub1 = Subscription(events=self.sub1_events)
        self.assertIsNotNone(sub1, 'Subscription initialized with event=list should not be None')
        self.assertTrue(all(sub1.is_subscribed(event_name) for event_name in self.sub1_events),
                        'Subscription which should be subscribed to events {0} is not'.format(self.sub1_events))
        self.assertTrue(
            all(sub1.is_subscribed(event_name, global_subs=self.global_sub1) for event_name in self.sub1_all_events),
            'Subscription of {0} given global subscriptions {1} and is not subscribed '
            'some of events in {2}'.format(self.sub1_events, self.global_sub1_events, self.sub1_all_events))
        not_subscribed = ['x', 'y', 'z']
        self.assertTrue(not any(sub1.is_subscribed(event_name, global_subs=self.global_sub1)
                                for event_name in not_subscribed),
                        'Subscription of {0}, given global subscriptions {1}, is subscribed to'
                        'some of events in {2}'.format(self.sub1_events, self.global_sub1_events, not_subscribed))
        self.assertDictEqual(sub1.subscriptions, {})

    def test_subscription_with_disabled(self):
        sub2 = Subscription(events=self.sub1_events, disabled=self.sub2_disabled)
        self.assertIsNotNone(sub2, 'Subscription initialized with event=list and disabled=list should not be None')
        self.assertTrue(not any(sub2.is_subscribed(event_name) for event_name in self.sub2_disabled),
                        'Subscription should not be subscribed to events which are disabled')
        valid_subs = set(self.sub1_events) - set(self.sub2_disabled)
        self.assertTrue(all(sub2.is_subscribed(event_name) for event_name in valid_subs),
                        'Subscription should be subscribed to all events which are not disabled')
        self.assertTrue(all(sub2.is_subscribed(event_name, global_subs=self.global_sub1)
                            for event_name in self.valid_with_global),
                        'Subscription should be subscribed to all events in either self or global which '
                        'are not disabled')
        self.assertTrue(not any(sub2.is_subscribed(event_name, global_subs=self.global_sub1)
                                for event_name in self.sub2_disabled),
                        'Subscription should not be subscribed to any events which are disabled')

    def test_subscription_with_all_disabled(self):
        sub3 = Subscription(events=self.sub1_events, disabled='*')
        self.assertIsNotNone(sub3, 'Subscription initialized with event=list and disabled="*" should not be None')
        self.assertTrue(not any(sub3.is_subscribed(event_name) for event_name in self.sub1_events),
                        'Subscription should not be subscribed to any events when all are disabled')
        self.assertTrue(not any(sub3.is_subscribed(event_name, global_subs=self.global_sub1)
                                for event_name in self.valid_with_global),
                        'Subscription should not be subscribed to any events in either self or global when all are '
                        'not disabled')
        self.assertTrue(not any(sub3.is_subscribed(event_name, global_subs=self.global_sub1)
                                for event_name in self.sub2_disabled),
                        'Subscription should not be subscribed to any events which are disabled')
        self.assertDictEqual(sub3.subscriptions, {})

    def test_subscribed_with_all_enabled_all_disabled(self):
        sub4 = Subscription(events='*', disabled='*')
        self.assertIsNotNone(sub4, 'Subscription initialized with event="*" and disabled="*" should not be None')
        self.assertTrue(not any(sub4.is_subscribed(event_name) for event_name in self.sub1_events),
                        'Subscription should not be subscribed to any events when all are disabled')
        self.assertTrue(not any(sub4.is_subscribed(event_name, global_subs=self.global_sub1)
                                for event_name in self.valid_with_global),
                        'Subscription should not be subscribed to any events in either self or global when all are '
                        'not disabled')
        self.assertTrue(not any(sub4.is_subscribed(event_name, global_subs=self.global_sub1)
                                for event_name in self.sub2_disabled),
                        'Subscription should not be subscribed to any events which are disabled')
        self.assertDictEqual(sub4.subscriptions, {})

    def test_subscription_subscriptions(self):
        subsub = Subscription(events='f')
        sub5 = Subscription(events=self.sub1_events, disabled=self.sub2_disabled, subscriptions={'sub_element': subsub})
        self.assertIsNotNone(sub5, 'Subscription initialized with event=list and disabled=list with subscriptions '
                                   'should not be None')
        valid_subs = set(self.sub1_events) - set(self.sub2_disabled)
        self.assertTrue(all(sub5.is_subscribed(event_name) for event_name in valid_subs),
                        'Subscription should be subscribed to all events which are not disabled')
        self.assertTrue(all(sub5.is_subscribed(event_name, global_subs=self.global_sub1)
                            for event_name in self.valid_with_global),
                        'Subscription should be subscribed to all events in either self or global which '
                        'are not disabled')
        self.assertTrue(not any(sub5.is_subscribed(event_name, global_subs=self.global_sub1)
                                for event_name in self.sub2_disabled),
                        'Subscription should not be subscribed to any events which are disabled')
        self.assertDictEqual({'sub_element': subsub}, sub5.subscriptions)

    def as_json(self):
        sub1 = Subscription(events=self.sub1_events)
        sub2 = Subscription(events=self.sub1_events, disabled=self.sub2_disabled)
        sub3 = Subscription(events=self.sub1_events, disabled='*')
        sub4 = Subscription(events='*', disabled='*')
        subsub = Subscription(events='f')
        sub5 = Subscription(events=self.sub1_events, disabled=self.sub2_disabled, subscriptions={'sub_element': subsub})
        sub1_expected_json = {"events": {"events": ['a', 'b', 'c'], "all": False},
                              "disabled": {"events": [], "all": False},
                              "subscriptions": {}}
        sub2_expected_json = {"events": {"events": ['a', 'b', 'c'], "all": False},
                              "disabled": {"events": ['a', 'd', 'f'], "all": False},
                              "subscriptions": {}}
        sub3_expected_json = {"events": {"events": ['a', 'b', 'c'], "all": False},
                              "disabled": {"events": [], "all": True},
                              "subscriptions": {}}
        sub4_expected_json = {"events": {"events": [], "all": True},
                              "disabled": {"events": [], "all": True},
                              "subscriptions": {}}
        sub5_expected_json = {"events": {"events": ['a', 'b', 'c'], "all": False},
                              "disabled": {"events": ['a', 'd', 'f'], "all": False},
                              "subscriptions": {"sub_element": {"events": ['f'], "all": False}}}
        self.assertDictEqual(sub1_expected_json, sub1.as_json())
        self.assertDictEqual(sub2_expected_json, sub2.as_json())
        self.assertDictEqual(sub3_expected_json, sub3.as_json())
        self.assertDictEqual(sub4_expected_json, sub4.as_json())
        self.assertDictEqual(sub5_expected_json, sub5.as_json())


class TestCaseSubscriptions(unittest.TestCase):
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

    def test_case_subscriptions_json(self):
        case1, _ = construct_case2()
        global_subs = GlobalSubscriptions(controller='a', next_step=[4, 5], flag='*', filter='x')
        expected_json = {"subscriptions": {"controller1": case1.subscriptions["controller1"].as_json()},
                         "global_subscriptions": global_subs.as_json()}
        self.assertDictEqual(expected_json, case1.as_json())


class TestSubscriptionFunctions(unittest.TestCase):
    def setUp(self):
        case_database.initialize()

    def tearDown(self):
        case_database.case_db.tearDown()

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

    def test_all_as_json(self):
        case1, acceptance1 = construct_case1()
        case2, acceptance2 = construct_case2()
        cases = {'case1': case1, 'case2': case2}
        set_subscriptions(cases)
        self.assertDictEqual({"case1": case1.as_json(), "case2": case2.as_json()}, subscriptions_as_json())

    def test_edit_global_subscription(self):
        global_subs = GlobalSubscriptions(controller='new_controller_event')
        case1, acceptance1 = construct_case1()
        case2, acceptance2 = construct_case2()
        cases = {'case1': case1, 'case2': case2}
        set_subscriptions(cases)
        edit_global_subscription('case1', global_subs)
        self.assertDictEqual(global_subs.as_json(), get_subscriptions()['case1'].global_subscriptions.as_json())

    def test_edit_global_subscription_invalid_case(self):
        global_subs = GlobalSubscriptions()
        with self.assertRaises(KeyError):
            edit_global_subscription('nonesense_case_name', global_subs)

    def test_edit_subscriptions(self):
        case1, acceptance1 = construct_case1()
        case2, acceptance2 = construct_case2()
        cases = {'case1': case1, 'case2': case2}
        set_subscriptions(cases)
        self.assertTrue(edit_subscription('case1', ['controller1', 'workflow2', 'step1'], [3, 2]))
        self.assertTrue(edit_subscription('case2',
                                          ['controller1', 'workflow1', 'step2', 'next2', 'flag1', 'filter1'],
                                          ['y', 'z']))
        self.assertTrue(get_subscriptions()['case1'].is_subscribed(['controller1', 'workflow2', 'step1'], 3))
        self.assertTrue(get_subscriptions()['case1'].is_subscribed(['controller1', 'workflow2', 'step1'], 2))
        self.assertTrue(get_subscriptions()['case2'].is_subscribed(
            ['controller1', 'workflow1', 'step2', 'next2', 'flag1', 'filter1'], 'y'))
        self.assertTrue(get_subscriptions()['case2'].is_subscribed(
            ['controller1', 'workflow1', 'step2', 'next2', 'flag1', 'filter1'], 'z'))

    def test_edit_subscriptions_unsubscribed(self):
        case1, acceptance1 = construct_case1()
        case2, acceptance2 = construct_case2()
        cases = {'case1': case1, 'case2': case2}
        set_subscriptions(cases)
        self.assertFalse(edit_subscription('case1', ['controller3', 'workflow3', 'step4'], [3, 2]))
        self.assertFalse(edit_subscription('case2', ['controller1', 'workflow1', 'step1', 'next2'], ['y', 'z']))

    def test_edit_subscriptions_invalid_case(self):
        global_subs = GlobalSubscriptions(controller='a')
        subs = Subscription(events=['b'], subscriptions=Subscription(events=['d', 'e']))
        case_sub = CaseSubscriptions(global_subscriptions=global_subs, subscriptions=subs)
        cases = {'case2': case_sub}
        set_subscriptions(cases)
        original_subscriptions = copy.deepcopy(get_subscriptions())
        self.assertFalse(edit_subscription('nonesense_case', ['a', 'b', 'c'], ['d', 'e']))
        # Apparently assertDictEquals says this is false. Infuriating.
        self.assertEqual(str(original_subscriptions), str(get_subscriptions()))

    def test_add_subscriptions(self):
        case1, acceptance1 = construct_case1()
        case2, acceptance2 = construct_case2()
        cases = {'case1': case1, 'case2': case2}
        set_subscriptions(cases)

        ancestry1 = ['controller3', 'workflow3', 'step4', 'aaa']
        events1 = [3, 2]
        add_subscription('case1', ancestry1, events1)
        self.assertTrue(all(get_subscriptions()['case1'].is_subscribed(ancestry1, event) for event in events1))

        ancestry2 = ['controller1', 'workflow1', 'step1', 'next2', 'madeup1', 'madeup2']
        events2 = ['y', 'z']
        add_subscription('case2', ancestry2, events2)
        self.assertTrue(all(get_subscriptions()['case2'].is_subscribed(ancestry2, event) for event in events2))

        case1, acceptance1 = construct_case1()
        cases = {'case1': case1, 'case2': case2}
        set_subscriptions(cases)
        ancestry3 = ['controller3', 'workflow3', 'step4']
        events3 = [3, 2]
        add_subscription('case1', ancestry3, events3)
        self.assertTrue(all(get_subscriptions()['case1'].is_subscribed(ancestry3, event) for event in events3))

    def test_add_subscriptions_invalid_case(self):
        global_subs = GlobalSubscriptions(controller='a')
        subs = Subscription(events=['b'], subscriptions=Subscription(events=['d', 'e']))
        case_sub = CaseSubscriptions(global_subscriptions=global_subs, subscriptions=subs)
        cases = {'case2': case_sub}
        set_subscriptions(cases)
        original_subscriptions = copy.deepcopy(get_subscriptions())
        add_subscription('nonesense_case', ['a', 'b', 'c'], ['d', 'e'])
        # Apparently assertDictEquals says this is false. Infuriating.
        self.assertEqual(str(original_subscriptions), str(get_subscriptions()))

    def test_remove_subscriptions_node(self):
        sub1 = Subscription()
        sub2 = Subscription()
        sub3 = Subscription()

        sub4 = Subscription(subscriptions={'sub1': sub1, 'sub2': sub2})
        sub5 = Subscription(subscriptions={'sub3': sub3})
        sub6 = Subscription()

        sub7 = Subscription(subscriptions={'sub4': sub4})
        sub8 = Subscription(subscriptions={'sub5': sub5})
        sub9 = Subscription(subscriptions={'sub6': sub6})
        sub10 = Subscription()

        sub11 = Subscription(subscriptions={'sub7': sub7, 'sub8': sub8})
        sub12 = Subscription(subscriptions={'sub9': sub9})
        sub13 = Subscription(subscriptions={'sub10': sub10})

        sub14 = Subscription(subscriptions={'sub11': sub11, 'sub12': sub12, 'sub13': sub13})

        case1 = CaseSubscriptions(subscriptions={'sub14': sub14})

        sub15 = Subscription()
        sub16 = Subscription()
        sub17 = Subscription()

        sub18 = Subscription(subscriptions={'sub15': sub15, 'sub16': sub16})
        sub19 = Subscription(subscriptions={'sub17': sub17})
        sub20 = Subscription()

        sub21 = Subscription(subscriptions={'sub18': sub18})
        sub22 = Subscription(subscriptions={'sub19': sub19, 'sub20': sub20})

        case2 = CaseSubscriptions(subscriptions={'sub21': sub21, 'sub22': sub22})

        set_subscriptions({'case1': case1, 'case2': case2})

        empty_global = GlobalSubscriptions().as_json()
        empty_sub_list = _SubscriptionEventList().as_json()

        def construct_expected_json(tree):
            return {key: {'disabled': empty_sub_list,
                          'events': empty_sub_list,
                          'subscriptions': construct_expected_json(subs) if subs else {}}
                    for key, subs in tree.items()}

        def construct_case_json(tree):
            return {'global_subscriptions': empty_global,
                    'subscriptions': construct_expected_json(tree)}

        tree1 = {'sub14': {'sub11': {'sub7': {'sub4': {'sub1': {},
                                                       'sub2': {}}},
                                     'sub8': {'sub5': {'sub3': {}}}},
                           'sub12': {'sub9': {'sub6': {}}},
                           'sub13': {'sub10': {}}}}

        tree2 = {'sub21': {'sub18': {'sub15': {},
                                     'sub16': {}}},
                 'sub22': {'sub19': {'sub17': {}},
                           'sub20': {}}}

        # test that construct expected json is working
        self.assertDictEqual({'case1': construct_case_json(tree1), 'case2': construct_case_json(tree2)},
                             subscriptions_as_json())

        # testing removing nodes from case 1. Effects are cumulative
        tree1_after_rem10 = {'sub14': {'sub11': {'sub7': {'sub4': {'sub1': {},
                                                                   'sub2': {}}},
                                                 'sub8': {'sub5': {'sub3': {}}}},
                                       'sub12': {'sub9': {'sub6': {}}},
                                       'sub13': {}}}
        remove_subscription_node('case1', ['sub14', 'sub13', 'sub10'])
        self.assertDictEqual({'case1': construct_case_json(tree1_after_rem10), 'case2': construct_case_json(tree2)},
                             subscriptions_as_json())

        tree2_after_rem20 = {'sub21': {'sub18': {'sub15': {},
                                                 'sub16': {}}},
                             'sub22': {'sub19': {'sub17': {}}}}
        remove_subscription_node('case2', ['sub22', 'sub20'])
        self.assertDictEqual(
            {'case1': construct_case_json(tree1_after_rem10), 'case2': construct_case_json(tree2_after_rem20)},
            subscriptions_as_json())

        tree1_after_rem9 = {'sub14': {'sub11': {'sub7': {'sub4': {'sub1': {},
                                                                  'sub2': {}}},
                                                'sub8': {'sub5': {'sub3': {}}}},
                                      'sub12': {},
                                      'sub13': {}}}

        remove_subscription_node('case1', ['sub14', 'sub12', 'sub9'])
        self.assertDictEqual(
            {'case1': construct_case_json(tree1_after_rem9), 'case2': construct_case_json(tree2_after_rem20)},
            subscriptions_as_json())

        tree1_after_rem4 = {'sub14': {'sub11': {'sub7': {},
                                                'sub8': {'sub5': {'sub3': {}}}},
                                      'sub12': {},
                                      'sub13': {}}}

        remove_subscription_node('case1', ['sub14', 'sub11', 'sub7', 'sub4'])
        self.assertDictEqual(
            {'case1': construct_case_json(tree1_after_rem4), 'case2': construct_case_json(tree2_after_rem20)},
            subscriptions_as_json())

        tree2_after_rem18 = {'sub21': {},
                             'sub22': {'sub19': {'sub17': {}}}}

        remove_subscription_node('case2', ['sub21', 'sub18'])
        self.assertDictEqual(
            {'case1': construct_case_json(tree1_after_rem4), 'case2': construct_case_json(tree2_after_rem18)},
            subscriptions_as_json())

        tree1_after_rem11 = {'sub14': {'sub12': {},
                                       'sub13': {}}}

        remove_subscription_node('case1', ['sub14', 'sub11'])
        self.assertDictEqual(
            {'case1': construct_case_json(tree1_after_rem11), 'case2': construct_case_json(tree2_after_rem18)},
            subscriptions_as_json())

        tree1_after_rem14 = {}
        remove_subscription_node('case1', ['sub14'])
        self.assertDictEqual(
            {'case1': construct_case_json(tree1_after_rem14), 'case2': construct_case_json(tree2_after_rem18)},
            subscriptions_as_json())

        tree2_after_rem22 = {'sub21': {}}

        remove_subscription_node('case2', ['sub22'])
        self.assertDictEqual(
            {'case1': construct_case_json(tree1_after_rem14), 'case2': construct_case_json(tree2_after_rem22)},
            subscriptions_as_json())

        tree2_after_rem21 = {}
        remove_subscription_node('case2', ['sub21'])
        self.assertDictEqual(
            {'case1': construct_case_json(tree1_after_rem14), 'case2': construct_case_json(tree2_after_rem21)},
            subscriptions_as_json())

    def test_remove_subscriptions_node_invalid_case(self):
        global_subs = GlobalSubscriptions(controller='a')

        subs = Subscription(events=['b'], subscriptions=Subscription(events=['d', 'e']))
        case_sub = CaseSubscriptions(global_subscriptions=global_subs, subscriptions=subs)
        cases = {'case2': case_sub}
        set_subscriptions(cases)
        original_subscriptions = copy.deepcopy(get_subscriptions())
        remove_subscription_node('nonesense_case', ['a', 'b', 'c'])
        # Apparently assertDictEquals says this is false. Infuriating.
        self.assertEqual(str(original_subscriptions), str(get_subscriptions()))
