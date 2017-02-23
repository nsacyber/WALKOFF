import unittest

import core.case.database as case_database
from core.case.callbacks import EventEntry
from core.executionelement import ExecutionElement
from tests.util.case import *


class TestCaseDatabase(unittest.TestCase):
    def setUp(self):
        case_database.initialize()

    def tearDown(self):
        case_database.case_db.tearDown()

    @staticmethod
    def __construct_basic_db():
        case1, _ = construct_case1()
        case2, _ = construct_case2()
        case3, _ = construct_case1()
        case4, _ = construct_case2()
        cases = {'case1': case1, 'case2': case2, 'case3': case3, 'case4': case4}
        set_subscriptions(cases)
        return cases

    def test_register_cases(self):
        cases = TestCaseDatabase.__construct_basic_db()
        cases_in_db = [case.name for case in case_database.case_db.session.query(case_database.Cases).all()]
        self.assertSetEqual(set(cases.keys()), set(cases_in_db), 'Not all cases were added to subscribed cases')
        self.assertEqual(len(set(cases_in_db)), len(cases_in_db), 'Duplicate case was added to database')

    def test_add_event(self):
        TestCaseDatabase.__construct_basic_db()

        elem1 = ExecutionElement(name='b', parent_name='a')
        elem2 = ExecutionElement(name='c', parent_name='b', ancestry=['a', 'b', 'c'])
        elem3 = ExecutionElement(name='d', parent_name='c')
        elem4 = ExecutionElement()

        event1 = EventEntry(elem1, 'message1', 'SYSTEM')
        event2 = EventEntry(elem2, 'message2', 'WORKFLOW')
        event3 = EventEntry(elem3, 'message3', 'STEP')
        event4 = EventEntry(elem4, 'message4', 'NEXT')

        case_database.case_db.add_event(event=event1, cases=['case1', 'case3'])
        case_database.case_db.add_event(event=event2, cases=['case2', 'case4'])
        case_database.case_db.add_event(event=event3, cases=['case2', 'case3', 'case4'])
        case_database.case_db.add_event(event=event4, cases=['case1'])

        expected_event_messages = {'case1': [('SYSTEM', 'message1'), ('NEXT', 'message4')],
                                   'case2': [('WORKFLOW', 'message2'), ('STEP', 'message3')],
                                   'case3': [('SYSTEM', 'message1'), ('STEP', 'message3')],
                                   'case4': [('WORKFLOW', 'message2'), ('STEP', 'message3')]}

        # check cases to events is as expected
        for case_name, expected_events in expected_event_messages.items():
            case = case_database.case_db.session.query(case_database.Cases) \
                .filter(case_database.Cases.name == case_name).all()
            self.assertEqual(len(case), 1, 'There are more than one cases sharing a name {0}'.format(case_name))

            case_event_info = [(event.type, event.message) for event in case[0].events.all()]

            self.assertEqual(len(case_event_info), len(expected_events),
                             'Unexpected number of messages encountered for case {0}'.format(case_name))
            self.assertSetEqual(set(case_event_info), set(expected_events),
                                'Expected event info does not equal received event info for case {0}'.format(case_name))

        # check events to cases is as expected
        expected_cases = {'message1': ['case1', 'case3'],
                          'message2': ['case2', 'case4'],
                          'message3': ['case2', 'case3', 'case4'],
                          'message4': ['case1']}
        for event_message, message_cases in expected_cases.items():
            event = case_database.case_db.session.query(case_database.EventLog) \
                .filter(case_database.EventLog.message == event_message).all()

            self.assertEqual(len(event), 1,
                             'There are more than one events sharing a message {0}'.format(event_message))

            event_cases = [case.name for case in event[0].cases.all()]
            self.assertEqual(len(event_cases), len(message_cases),
                             'Unexpected number of cases encountered for messages {0}'.format(event_message))
            self.assertSetEqual(set(event_cases), set(message_cases),
                                'Expected cases does not equal received cases info for event {0}'.format(event_message))
