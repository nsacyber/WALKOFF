from walkoff.case.logger import CaseLogger
from walkoff.case.subscription import SubscriptionCache, Subscription
from unittest import TestCase
from mock import patch, create_autospec
from walkoff.case.database import CaseDatabase
import json
import uuid
from walkoff.events import WalkoffEvent, EventType


class TestCaseLogger(TestCase):

    def setUp(self):
        self.logger = self.get_basic_case_logger()

    @staticmethod
    def get_case_logger(subscriptions):
        repo = create_autospec(CaseDatabase)
        return CaseLogger(repo, subscriptions=subscriptions)

    @staticmethod
    def get_basic_case_logger():
        subscription_cache = SubscriptionCache()
        return TestCaseLogger.get_case_logger(subscription_cache)

    @staticmethod
    def assert_mock_called_once_with(mock, *args):
        mock.assert_called_once()
        mock.assert_called_with(*args)

    @patch.object(SubscriptionCache, 'add_subscriptions')
    def test_add_subscriptions(self, mock_add_subs):
        subs = [Subscription('id', ['e1'])]
        self.logger.add_subscriptions('case1', subs)
        self.assert_mock_called_once_with(mock_add_subs, 'case1', subs)

    @patch.object(SubscriptionCache, 'update_subscriptions')
    def test_update_subscriptions(self, mock_update_subs):
        subs = [Subscription('id', ['e1'])]
        self.logger.update_subscriptions('case1', subs)
        self.assert_mock_called_once_with(mock_update_subs, 'case1', subs)

    @patch.object(SubscriptionCache, 'delete_case')
    def test_delete_case(self, mock_delete_case):
        self.logger.delete_case('case1')
        self.assert_mock_called_once_with(mock_delete_case, 'case1')

    @patch.object(SubscriptionCache, 'clear')
    def test_clear_subscriptions(self, mock_clear):
        self.logger.clear_subscriptions()
        self.assert_mock_called_once_with(mock_clear)

    def test_format_data_with_none(self):
        self.assertEqual(CaseLogger._format_data(None), '')

    def test_format_data_with_string(self):
        string = 'something'
        self.assertEqual(CaseLogger._format_data(string), string)

    def test_format_data_with_jsonable_dict(self):
        data = {'a': 'something', 'b': 5}
        expected = json.dumps(data)
        self.assertEqual(CaseLogger._format_data(data), expected)

    def test_format_data_with_unjsonable_dict(self):
        class A: pass
        data = {'a': 'something', 'b': A()}
        expected = str(data)
        self.assertEqual(CaseLogger._format_data(data), expected)

    def test_create_event_entry(self):
        event = WalkoffEvent.WorkflowExecutionStart
        uid = uuid.uuid4()
        data = {'a': 'something', 'b': 5}
        expected_data = json.dumps(data)
        event_entry = CaseLogger._create_event_entry(event, uid, data)
        self.assertEqual(event_entry.type, EventType.workflow.name)
        self.assertEqual(event_entry.originator, uid)
        self.assertEqual(event_entry.message, event.value.message)
        self.assertEqual(event_entry.data, expected_data)

    @patch.object(SubscriptionCache, 'get_cases_subscribed')
    @patch.object(CaseDatabase, 'add_event')
    def test_log_unloggable_event(self, mock_repo_add_event, mock_get_cases_subscribed):
        event = WalkoffEvent.SendMessage
        self.logger.log(event, uuid.uuid4())
        mock_repo_add_event.assert_not_called()
        mock_get_cases_subscribed.assert_not_called()

    @patch.object(SubscriptionCache, 'get_cases_subscribed', return_value=set())
    @patch.object(CaseDatabase, 'add_event')
    def test_log_no_cases(self, mock_repo_add_event, mock_get_cases_subscribed):
        event = WalkoffEvent.WorkflowExecutionStart
        uid = uuid.uuid4()
        self.logger.log(event, uid)
        mock_repo_add_event.assert_not_called()
        self.assert_mock_called_once_with(mock_get_cases_subscribed, str(uid), event.signal_name)

    @patch.object(SubscriptionCache, 'get_cases_subscribed', return_value={1, 2})
    @patch.object(CaseDatabase, 'add_event')
    def test_log(self, mock_repo_add_event, mock_get_cases_subscribed):
        event = WalkoffEvent.WorkflowExecutionStart
        uid = uuid.uuid4()
        self.logger.log(event, uid)
        self.assert_mock_called_once_with(mock_get_cases_subscribed, str(uid), event.signal_name)
