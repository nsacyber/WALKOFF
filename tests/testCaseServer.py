import unittest
import json
from tests.util.case import construct_case1, construct_case2
import core.case.database as case_database
from core.case.subscription import set_subscriptions
from core.executionelement import ExecutionElement
from core.case.callbacks import EventEntry
from server import flaskServer as flask_server
from os.path import join


class TestCaseServer(unittest.TestCase):
    def setUp(self):
        case_database.initialize()
        self.app = flask_server.app.test_client(self)
        self.app.testing = True
        self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)
        response = self.app.post('/key', data=dict(email='admin', password='admin'),
                                 follow_redirects=True).get_data(as_text=True)

        self.key = json.loads(response)["auth_token"]
        self.headers = {"Authentication-Token": self.key}

    def tearDown(self):
        case_database.case_db.tearDown()

    @staticmethod
    def __basic_case_setup():
        case1, _ = construct_case1()
        case2, _ = construct_case2()
        case3, _ = construct_case1()
        case4, _ = construct_case2()
        cases = {'case1': case1, 'case2': case2, 'case3': case3, 'case4': case4}
        set_subscriptions(cases)
        return cases

    def test_display_cases_typical(self):
        cases = TestCaseServer.__basic_case_setup()
        response = self.app.post('/cases', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        expected_cases = set(cases.keys())
        received_cases = [case['name'] for case in response['cases']]
        self.assertEqual(len(expected_cases), len(received_cases), 'Received unexpected number of cases')
        self.assertSetEqual(expected_cases, set(received_cases), 'Received incorrect cases')

    def test_display_cases_none(self):
        response = self.app.post('/cases', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        expected_cases = []
        received_cases = [case['name'] for case in response['cases']]
        self.assertEqual(len(expected_cases), len(received_cases), 'Received unexpected number of cases')
        self.assertSetEqual(set(expected_cases), set(received_cases), 'Received incorrect cases')

    def test_display_case_not_found(self):
        response = self.app.post('/cases/hiThere', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        with self.assertRaises(KeyError):
            _ = response['cases']
        self.assertEqual(response['status'], 'Case with given name does not exist',
                         'Received unexpected number of cases')

    def test_display_case(self):
        TestCaseServer.__basic_case_setup()

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

        def create_event_logs(events):
            return [case_database.EventLog(type=event.type,
                                           ancestry=','.join(map(str, event.ancestry)),
                                           message=event.message)
                    for event in events]

        def event_logs_as_json(events):
            return [event.as_json() for event in create_event_logs(events)]

        case_events = [('case1', [event1, event4]), ('case2', [event2, event3]),
                       ('case3', [event1, event3]), ('case4', [event2, event3])]

        expected_events_collection = {case_name: event_logs_as_json(events) for case_name, events in case_events}

        for case_name, expected_events in expected_events_collection.items():
            response = self.app.post('/cases/{0}'.format(case_name), headers=self.headers)
            self.assertEqual(response.status_code, 200)
            response = json.loads(response.get_data(as_text=True))
            self.assertEqual(case_name, response['case']['name'], 'Received case name differs from expected')
            received_events = [{key: event[key] for key in ['type', 'message', 'ancestry']}
                               for event in response['case']['events']]
            expected_events = [{key: event[key] for key in ['type', 'message', 'ancestry']}
                               for event in expected_events]
            self.assertEqual(len(received_events), len(expected_events), 'Unexpected number of events receieved')
            for event in expected_events:
                self.assertTrue(event in received_events, 'Expected event is not in receieved events')

    def test_display_possible_subscriptions(self):
        with open(join('.', 'data', 'events.json')) as f:
            expected_response = json.loads(f.read())

        response = self.app.post('/cases/subscriptions/available', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, expected_response)

    def test_display_subscriptions(self):
        case1, accept1 = construct_case1()
        case2, accept2 = construct_case2()
        case3, accept3 = construct_case1()
        case4, accept4 = construct_case2()
        cases = {'case1': case1, 'case2': case2, 'case3': case3, 'case4': case4}
        set_subscriptions(cases)

        expected_response = {key: case.as_json() for key, case in cases.items()}

        response = self.app.post('/cases/subscriptions/', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(expected_response, response)

    def test_edit_global_subscription(self):

        global_subs = {"controller": ['a', 'b', 'c', 'd'],
                       "workflow": ['e'],
                       "step": [],
                       "next_step": ['f'],
                       "flag": [],
                       "filter": ['g', 'h', 'i']}

        response = self.app.post('/cases/subscriptions/case1/global/edit', data=global_subs, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        #self.assertEquals(response.get_data(as_text=True), "case1")



        # test adding, removing, editing subscription

