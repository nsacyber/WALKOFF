import json
import unittest

import walkoff.case.database as case_database
from walkoff.case.database import Case
from tests.util import execution_db_help


class TestCaseDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        execution_db_help.setup_dbs()

    @classmethod
    def tearDownClass(cls):
        execution_db_help.tear_down_execution_db()
        case_database.case_db.tear_down()

    def setUp(self):
        case_database.initialize()

    def tearDown(self):
        case_database.case_db.session.query(case_database.Event).delete()
        case_database.case_db.session.query(case_database.Case).delete()
        case_database.case_db.session.commit()

    @staticmethod
    def __construct_basic_db():
        cases = [Case(name='case{}'.format(i)) for i in range(1, 5)]
        for case in cases:
            case_database.case_db.session.add(case)
        case_database.case_db.session.commit()
        return cases

    @staticmethod
    def get_case_ids(names):
        return [case.id for case in case_database.case_db.session.query(Case).filter(Case.name.in_(names)).all()]

    def test_add_event(self):
        TestCaseDatabase.__construct_basic_db()
        event1 = case_database.Event(type='SYSTEM', message='message1')
        case_database.case_db.add_event(event=event1, case_ids=self.get_case_ids(['case1', 'case3']))
        event2 = case_database.Event(type='WORKFLOW', message='message2')
        case_database.case_db.add_event(event=event2, case_ids=self.get_case_ids(['case2', 'case4']))
        event3 = case_database.Event(type='ACTION', message='message3')
        case_database.case_db.add_event(event=event3, case_ids=self.get_case_ids(['case2', 'case3', 'case4']))
        event4 = case_database.Event(type='BRANCH', message='message4')
        case_database.case_db.add_event(event=event4, case_ids=self.get_case_ids(['case1']))

        expected_event_messages = {'case1': [('SYSTEM', 'message1'), ('BRANCH', 'message4')],
                                   'case2': [('WORKFLOW', 'message2'), ('ACTION', 'message3')],
                                   'case3': [('SYSTEM', 'message1'), ('ACTION', 'message3')],
                                   'case4': [('WORKFLOW', 'message2'), ('ACTION', 'message3')]}

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

        event1 = case_database.Event(type='SYSTEM', message='message1')
        case_database.case_db.add_event(event=event1, case_ids=['case1', 'case3'])
        event2 = case_database.Event(type='WORKFLOW', message='message2')
        case_database.case_db.add_event(event=event2, case_ids=['case2', 'case4'])
        event3 = case_database.Event(type='ACTION', message='message3')
        case_database.case_db.add_event(event=event3, case_ids=['case2', 'case3', 'case4'])
        event4 = case_database.Event(type='BRANCH', message='message4')
        case_database.case_db.add_event(event=event4, case_ids=['case1'])

        events = case_database.case_db.session.query(case_database.Event).all()
        smallest_id = min([event.id for event in events])
        expected_json_list = [event.as_json() for event in events]
        for event in expected_json_list:
            if event['id'] == smallest_id:
                event['note'] = 'Note1'

        case_database.case_db.edit_event_note(smallest_id, 'Note1')
        events = case_database.case_db.session.query(case_database.Event).all()
        result_json_list = [event.as_json() for event in events]
        self.assertEqual(len(result_json_list), len(expected_json_list))
        self.assertTrue(all(expected_event in result_json_list for expected_event in expected_json_list))

    def test_edit_note_invalid_id(self):
        TestCaseDatabase.__construct_basic_db()

        event1 = case_database.Event(type='SYSTEM', message='message1')
        case_database.case_db.add_event(event=event1, case_ids=['case1', 'case3'])
        event2 = case_database.Event(type='WORKFLOW', message='message2')
        case_database.case_db.add_event(event=event2, case_ids=['case2', 'case4'])
        event3 = case_database.Event(type='ACTION', message='message3')
        case_database.case_db.add_event(event=event3, case_ids=['case2', 'case3', 'case4'])
        event4 = case_database.Event(type='BRANCH', message='message4')
        case_database.case_db.add_event(event=event4, case_ids=['case1'])

        events = case_database.case_db.session.query(case_database.Event).all()
        expected_json_list = [event.as_json() for event in events]

        case_database.case_db.edit_event_note(None, 'Note1')
        events = case_database.case_db.session.query(case_database.Event).all()
        result_json_list = [event.as_json() for event in events]
        self.assertEqual(len(result_json_list), len(expected_json_list))
        self.assertTrue(all(expected_event in result_json_list for expected_event in expected_json_list))

        invalid_id = max([event.id for event in events]) + 1
        case_database.case_db.edit_event_note(invalid_id, 'Note1')
        events = case_database.case_db.session.query(case_database.Event).all()
        result_json_list = [event.as_json() for event in events]
        self.assertEqual(len(result_json_list), len(expected_json_list))
        self.assertTrue(all(expected_event in result_json_list for expected_event in expected_json_list))

    def test_data_json_field(self):
        TestCaseDatabase.__construct_basic_db()
        event4_data = {"a": 4, "b": [1, 2, 3], "c": "Some_String"}
        event1 = case_database.Event(type='SYSTEM', message='message1')
        case_database.case_db.add_event(event=event1, case_ids=['case1', 'case3'])
        event2 = case_database.Event(type='WORKFLOW', message='message2', data='some_string')
        case_database.case_db.add_event(event=event2, case_ids=['case2', 'case4'])
        event3 = case_database.Event(type='ACTION', message='message3', data=6)
        case_database.case_db.add_event(event=event3, case_ids=['case2', 'case3', 'case4'])
        event4 = case_database.Event(type='BRANCH', message='message4', data=json.dumps(event4_data))
        case_database.case_db.add_event(event=event4, case_ids=['case1'])

        events = case_database.case_db.session.query(case_database.Event).all()
        event_json_list = [event.as_json() for event in events]
        input_output = {'message1': '',
                        'message2': 'some_string',
                        'message3': 6,
                        'message4': event4_data}

        self.assertEqual(len(event_json_list), len(list(input_output.keys())))
        for event in event_json_list:
            self.assertIn(event['message'], input_output)
            self.assertEqual(event['data'], input_output[event['message']])
