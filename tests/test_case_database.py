import json
import unittest

from walkoff.case.database import Case, Event
from tests.util import execution_db_help


class TestCaseDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.case_db = execution_db_help.setup_dbs()

    @classmethod
    def tearDownClass(cls):
        execution_db_help.tear_down_execution_db()
        cls.case_db.tear_down()

    def tearDown(self):
        self.case_db.session.query(Event).delete()
        self.case_db.session.query(Case).delete()
        self.case_db.session.commit()

    def __construct_basic_db(self):
        cases = [Case(name='case{}'.format(i)) for i in range(1, 5)]
        for case in cases:
            self.case_db.session.add(case)
        self.case_db.session.commit()
        return cases

    def get_case_ids(self, names):
        return [case.id for case in self.case_db.session.query(Case).filter(Case.name.in_(names)).all()]

    def test_add_event(self):
        self.__construct_basic_db()
        event1 = Event(type='SYSTEM', message='message1')
        self.case_db.add_event(event=event1, case_ids=self.get_case_ids(['case1', 'case3']))
        event2 = Event(type='WORKFLOW', message='message2')
        self.case_db.add_event(event=event2, case_ids=self.get_case_ids(['case2', 'case4']))
        event3 = Event(type='ACTION', message='message3')
        self.case_db.add_event(event=event3, case_ids=self.get_case_ids(['case2', 'case3', 'case4']))
        event4 = Event(type='BRANCH', message='message4')
        self.case_db.add_event(event=event4, case_ids=self.get_case_ids(['case1']))

        expected_event_messages = {'case1': [('SYSTEM', 'message1'), ('BRANCH', 'message4')],
                                   'case2': [('WORKFLOW', 'message2'), ('ACTION', 'message3')],
                                   'case3': [('SYSTEM', 'message1'), ('ACTION', 'message3')],
                                   'case4': [('WORKFLOW', 'message2'), ('ACTION', 'message3')]}

        # check cases to events is as expected
        for case_name, expected_events in expected_event_messages.items():
            case = self.case_db.session.query(Case).filter(Case.name == case_name).all()
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
            event = self.case_db.session.query(Event) \
                .filter(Event.message == event_message).all()

            self.assertEqual(len(event), 1,
                             'There are more than one events sharing a message {0}'.format(event_message))

            event_cases = [case.name for case in event[0].cases.all()]
            self.assertEqual(len(event_cases), len(message_cases),
                             'Unexpected number of cases encountered for messages {0}'.format(event_message))
            self.assertSetEqual(set(event_cases), set(message_cases),
                                'Expected cases does not equal received cases info for event {0}'.format(event_message))

    def test_edit_note(self):
        self.__construct_basic_db()

        event1 = Event(type='SYSTEM', message='message1')
        self.case_db.add_event(event=event1, case_ids=['case1', 'case3'])
        event2 = Event(type='WORKFLOW', message='message2')
        self.case_db.add_event(event=event2, case_ids=['case2', 'case4'])
        event3 = Event(type='ACTION', message='message3')
        self.case_db.add_event(event=event3, case_ids=['case2', 'case3', 'case4'])
        event4 = Event(type='BRANCH', message='message4')
        self.case_db.add_event(event=event4, case_ids=['case1'])

        events = self.case_db.session.query(Event).all()
        smallest_id = min([event.id for event in events])
        expected_json_list = [event.as_json() for event in events]
        for event in expected_json_list:
            if event['id'] == smallest_id:
                event['note'] = 'Note1'

        self.case_db.edit_event_note(smallest_id, 'Note1')
        events = self.case_db.session.query(Event).all()
        result_json_list = [event.as_json() for event in events]
        self.assertEqual(len(result_json_list), len(expected_json_list))
        self.assertTrue(all(expected_event in result_json_list for expected_event in expected_json_list))

    def test_edit_note_invalid_id(self):
        self.__construct_basic_db()

        event1 = Event(type='SYSTEM', message='message1')
        self.case_db.add_event(event=event1, case_ids=['case1', 'case3'])
        event2 = Event(type='WORKFLOW', message='message2')
        self.case_db.add_event(event=event2, case_ids=['case2', 'case4'])
        event3 = Event(type='ACTION', message='message3')
        self.case_db.add_event(event=event3, case_ids=['case2', 'case3', 'case4'])
        event4 = Event(type='BRANCH', message='message4')
        self.case_db.add_event(event=event4, case_ids=['case1'])

        events = self.case_db.session.query(Event).all()
        expected_json_list = [event.as_json() for event in events]

        self.case_db.edit_event_note(None, 'Note1')
        events = self.case_db.session.query(Event).all()
        result_json_list = [event.as_json() for event in events]
        self.assertEqual(len(result_json_list), len(expected_json_list))
        self.assertTrue(all(expected_event in result_json_list for expected_event in expected_json_list))

        invalid_id = max([event.id for event in events]) + 1
        self.case_db.edit_event_note(invalid_id, 'Note1')
        events = self.case_db.session.query(Event).all()
        result_json_list = [event.as_json() for event in events]
        self.assertEqual(len(result_json_list), len(expected_json_list))
        self.assertTrue(all(expected_event in result_json_list for expected_event in expected_json_list))

    def test_data_json_field(self):
        self.__construct_basic_db()
        event4_data = {"a": 4, "b": [1, 2, 3], "c": "Some_String"}
        event1 = Event(type='SYSTEM', message='message1')
        self.case_db.add_event(event=event1, case_ids=['case1', 'case3'])
        event2 = Event(type='WORKFLOW', message='message2', data='some_string')
        self.case_db.add_event(event=event2, case_ids=['case2', 'case4'])
        event3 = Event(type='ACTION', message='message3', data=6)
        self.case_db.add_event(event=event3, case_ids=['case2', 'case3', 'case4'])
        event4 = Event(type='BRANCH', message='message4', data=json.dumps(event4_data))
        self.case_db.add_event(event=event4, case_ids=['case1'])

        events = self.case_db.session.query(Event).all()
        event_json_list = [event.as_json() for event in events]
        input_output = {'message1': '',
                        'message2': 'some_string',
                        'message3': 6,
                        'message4': event4_data}

        self.assertEqual(len(event_json_list), len(list(input_output.keys())))
        for event in event_json_list:
            self.assertIn(event['message'], input_output)
            self.assertEqual(event['data'], input_output[event['message']])
