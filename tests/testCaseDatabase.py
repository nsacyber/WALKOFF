import unittest
import json

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
        cases_in_db = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        self.assertSetEqual(set(cases.keys()), set(cases_in_db), 'Not all cases were added to subscribed cases')
        self.assertEqual(len(set(cases_in_db)), len(cases_in_db), 'Duplicate case was added to database')

    def test_delete_cases(self):
        TestCaseDatabase.__construct_basic_db()
        case_database.case_db.delete_cases(['case1', 'case2'])
        cases_in_db = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = ['case3', 'case4']
        self.assertSetEqual(set(expected_cases), set(cases_in_db))
        self.assertEqual(len(set(cases_in_db)), len(expected_cases))

    def test_rename_case(self):
        TestCaseDatabase.__construct_basic_db()
        case_database.case_db.rename_case('case1', 'renamed')
        cases_in_db = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = ['renamed', 'case2', 'case3', 'case4']
        self.assertSetEqual(set(expected_cases), set(cases_in_db))
        self.assertEqual(len(set(cases_in_db)), len(expected_cases))

    def test_rename_case_empty_name(self):
        TestCaseDatabase.__construct_basic_db()
        case_database.case_db.rename_case('case1', '')
        cases_in_db = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = ['case1', 'case2', 'case3', 'case4']
        self.assertSetEqual(set(expected_cases), set(cases_in_db))
        self.assertEqual(len(set(cases_in_db)), len(expected_cases))

    def test_rename_case_invalid_case(self):
        TestCaseDatabase.__construct_basic_db()
        case_database.case_db.rename_case('case5', 'renamed')
        cases_in_db = [case.name for case in case_database.case_db.session.query(case_database.Case).all()]
        expected_cases = ['case1', 'case2', 'case3', 'case4']
        self.assertSetEqual(set(expected_cases), set(cases_in_db))
        self.assertEqual(len(set(cases_in_db)), len(expected_cases))

    def test_add_case_note(self):
        TestCaseDatabase.__construct_basic_db()
        case_database.case_db.edit_case_note('case1', 'Note1')
        case = case_database.case_db.session.query(case_database.Case).\
                filter(case_database.Case.name == 'case1').first()
        self.assertEqual(case.note, 'Note1')

    def test_add_case_note_empty_case_name(self):
        TestCaseDatabase.__construct_basic_db()
        case_database.case_db.edit_case_note('', 'Note1')
        case = case_database.case_db.session.query(case_database.Case).\
                filter(case_database.Case.name == 'case1').first()
        self.assertIsNone(case.note)

    def test_add_case_note_invalid_case(self):
        TestCaseDatabase.__construct_basic_db()
        original_cases_in_db = case_database.case_db.session.query(case_database.Case).all()
        original_notes = [case.note for case in original_cases_in_db]
        case_database.case_db.edit_case_note('case5', 'Note1')
        result_cases_in_db = case_database.case_db.session.query(case_database.Case).all()
        result_notes = [case.note for case in original_cases_in_db]
        self.assertEqual(len(original_cases_in_db), len(result_cases_in_db))
        self.assertSetEqual(set(original_cases_in_db), set(result_cases_in_db))
        self.assertEqual(len(original_notes), len(result_notes))
        self.assertSetEqual(set(original_notes), set(result_notes))

    def test_add_event(self):
        TestCaseDatabase.__construct_basic_db()

        elem1 = ExecutionElement(name='b', parent_name='a')
        elem2 = ExecutionElement(name='c', parent_name='b', ancestry=['a', 'b', 'c'])
        elem3 = ExecutionElement(name='d', parent_name='c')
        elem4 = ExecutionElement()

        event1 = EventEntry(elem1, 'SYSTEM', 'message1')
        event2 = EventEntry(elem2, 'WORKFLOW', 'message2')
        event3 = EventEntry(elem3, 'STEP', 'message3')
        event4 = EventEntry(elem4, 'NEXT', 'message4')

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
            case = case_database.case_db.session.query(case_database.Case) \
                .filter(case_database.Case.name == case_name).all()
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
            event = case_database.case_db.session.query(case_database.Event) \
                .filter(case_database.Event.message == event_message).all()

            self.assertEqual(len(event), 1,
                             'There are more than one events sharing a message {0}'.format(event_message))

            event_cases = [case.name for case in event[0].cases.all()]
            self.assertEqual(len(event_cases), len(message_cases),
                             'Unexpected number of cases encountered for messages {0}'.format(event_message))
            self.assertSetEqual(set(event_cases), set(message_cases),
                                'Expected cases does not equal received cases info for event {0}'.format(event_message))

    def test_edit_note(self):
        TestCaseDatabase.__construct_basic_db()

        elem1 = ExecutionElement(name='b', parent_name='a')
        elem2 = ExecutionElement(name='c', parent_name='b', ancestry=['a', 'b', 'c'])
        elem3 = ExecutionElement(name='d', parent_name='c')
        elem4 = ExecutionElement()

        event1 = EventEntry(elem1, 'SYSTEM', 'message1')
        event2 = EventEntry(elem2, 'WORKFLOW', 'message2')
        event3 = EventEntry(elem3, 'STEP', 'message3')
        event4 = EventEntry(elem4, 'NEXT', 'message4')

        case_database.case_db.add_event(event=event1, cases=['case1', 'case3'])
        case_database.case_db.add_event(event=event2, cases=['case2', 'case4'])
        case_database.case_db.add_event(event=event3, cases=['case2', 'case3', 'case4'])
        case_database.case_db.add_event(event=event4, cases=['case1'])

        events = case_db.session.query(case_database.Event).all()
        smallest_id = min([event.id for event in events])
        expected_json_list = [event.as_json() for event in events]
        for event in expected_json_list:
            if event['id'] == str(smallest_id):
                event['note'] = 'Note1'

        case_db.edit_event_note(smallest_id, 'Note1')
        events = case_db.session.query(case_database.Event).all()
        result_json_list = [event.as_json() for event in events]
        self.assertEqual(len(result_json_list), len(expected_json_list))
        self.assertTrue(all(expected_event in result_json_list for expected_event in expected_json_list))

    def test_edit_note_invalid_id(self):
        TestCaseDatabase.__construct_basic_db()

        elem1 = ExecutionElement(name='b', parent_name='a')
        elem2 = ExecutionElement(name='c', parent_name='b', ancestry=['a', 'b', 'c'])
        elem3 = ExecutionElement(name='d', parent_name='c')
        elem4 = ExecutionElement()

        event1 = EventEntry(elem1, 'SYSTEM', 'message1')
        event2 = EventEntry(elem2, 'WORKFLOW', 'message2')
        event3 = EventEntry(elem3, 'STEP', 'message3')
        event4 = EventEntry(elem4, 'NEXT', 'message4')

        case_database.case_db.add_event(event=event1, cases=['case1', 'case3'])
        case_database.case_db.add_event(event=event2, cases=['case2', 'case4'])
        case_database.case_db.add_event(event=event3, cases=['case2', 'case3', 'case4'])
        case_database.case_db.add_event(event=event4, cases=['case1'])

        events = case_db.session.query(case_database.Event).all()
        expected_json_list = [event.as_json() for event in events]

        case_db.edit_event_note(None, 'Note1')
        events = case_db.session.query(case_database.Event).all()
        result_json_list = [event.as_json() for event in events]
        self.assertEqual(len(result_json_list), len(expected_json_list))
        self.assertTrue(all(expected_event in result_json_list for expected_event in expected_json_list))

        invalid_id = max([event.id for event in events]) + 1
        case_db.edit_event_note(invalid_id, 'Note1')
        events = case_db.session.query(case_database.Event).all()
        result_json_list = [event.as_json() for event in events]
        self.assertEqual(len(result_json_list), len(expected_json_list))
        self.assertTrue(all(expected_event in result_json_list for expected_event in expected_json_list))

    def test_data_json_field(self):
        TestCaseDatabase.__construct_basic_db()

        elem1 = ExecutionElement(name='b', parent_name='a')
        elem2 = ExecutionElement(name='c', parent_name='b', ancestry=['a', 'b', 'c'])
        elem3 = ExecutionElement(name='d', parent_name='c')
        elem4 = ExecutionElement()

        event4_data = {"a": 4, "b": [1, 2, 3], "c": "Some_String"}
        event1 = EventEntry(elem1, 'SYSTEM', 'message1')
        event2 = EventEntry(elem2, 'WORKFLOW', 'message2', data='some_string')
        event3 = EventEntry(elem3, 'STEP', 'message3', data=6)
        event4 = EventEntry(elem4, 'NEXT', 'message4', data=json.dumps(event4_data))

        case_database.case_db.add_event(event=event1, cases=['case1', 'case3'])
        case_database.case_db.add_event(event=event2, cases=['case2', 'case4'])
        case_database.case_db.add_event(event=event3, cases=['case2', 'case3', 'case4'])
        case_database.case_db.add_event(event=event4, cases=['case1'])

        events = case_db.session.query(case_database.Event).all()
        event_json_list = [event.as_json() for event in events]

        input_output ={'message1': '',
                       'message2': 'some_string',
                       'message3': 6,
                       'message4': event4_data}

        self.assertEqual(len(event_json_list), len(list(input_output.keys())))
        for event in event_json_list:
            self.assertIn(event['message'], input_output)
            self.assertEqual(event['data'], input_output[event['message']])



