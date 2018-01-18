from unittest import TestCase
from tests.util.mock_objects import MockRedisCacheAdapter
from walkoff.server.blueprints.workflowresult import *
from walkoff.helpers import convert_action_argument
from copy import deepcopy
import json


class TestWorkflowResultStream(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cache = MockRedisCacheAdapter()
        sse_stream.cache = cls.cache
        cls.sender_no_args = {'name': 'action1', 'uid': 'uid2'}
        cls.sender_with_args = {'name': 'action1', 'uid': 'uid2',
                                'arguments': [{'name': 42, 'value': json.dumps(44)}]}
        cls.kwargs_success =  {'data': {'result': 33, 'status': 'Success'}}
        cls.kwargs_failure = {'data': {'result': 33, 'status': 'Failure'}}

    def tearDown(self):
        self.cache.clear()

    def test_convert_action_argument(self):
        arg1 = {'name': 'a', 'reference': '32'}
        expected1 = deepcopy(arg1)
        self.assertDictEqual(convert_action_argument(arg1), expected1)

        selection = [1, 'a', 3]
        arg2 = deepcopy(arg1)
        arg2['selection'] = json.dumps(selection)
        expected2 = deepcopy(arg2)
        expected2['selection'] = selection
        self.assertDictEqual(convert_action_argument(arg2), expected2)

        data = {'result': 1, 'status': 'Success'}
        arg3 = {'name': 'a', 'value': json.dumps(data)}
        expected3 = deepcopy(arg3)
        expected3['value'] = data
        self.assertDictEqual(convert_action_argument(arg3), expected3)

        data = 'abc'
        arg4 = {'name': 'a', 'value': data}
        expected4 = deepcopy(arg4)
        expected4['value'] = data
        self.assertDictEqual(convert_action_argument(arg4), expected4)

    def test_format_workflow_result_no_args(self):
        expected = {'action_name': 'action1',
                    'action_uid': 'uid2',
                    'arguments': [],
                    'result': 33,
                    'status': 'Success'}
        formatted = format_workflow_result(deepcopy(self.sender_no_args), **deepcopy(self.kwargs_success))
        timestamp = formatted.pop('timestamp', None)
        self.assertIsNotNone(timestamp)
        self.assertDictEqual(formatted, expected)

    def test_format_workflow_result_with_args(self):
        expected = {'action_name': 'action1',
                    'action_uid': 'uid2',
                    'arguments': [{'name': 42, 'value': 44}],
                    'result': 33,
                    'status': 'Success'}
        formatted = format_workflow_result(deepcopy(self.sender_with_args), **deepcopy(self.kwargs_success))
        timestamp = formatted.pop('timestamp', None)
        self.assertIsNotNone(timestamp)
        self.assertDictEqual(formatted, expected)

    def test_action_ended_callback(self):
        expected = {'action_name': 'action1',
                    'action_uid': 'uid2',
                    'arguments': [{'name': 42, 'value': 44}],
                    'result': 33,
                    'status': 'Success'}
        response = action_ended_callback(deepcopy(self.sender_with_args), **deepcopy(self.kwargs_success))
        timestamp = response['data'].pop('timestamp', None)
        self.assertIsNotNone(timestamp)
        self.assertDictEqual(response, {'data': expected, 'event': 'action_success'})

    def test_action_error_callback(self):
        expected = {'action_name': 'action1',
                    'action_uid': 'uid2',
                    'arguments': [{'name': 42, 'value': 44}],
                    'result': 33,
                    'status': 'Failure'}
        response = action_error_callback(deepcopy(self.sender_with_args), **deepcopy(self.kwargs_failure))
        timestamp = response['data'].pop('timestamp', None)
        self.assertIsNotNone(timestamp)
        self.assertDictEqual(response, {'data': expected, 'event': 'action_error'})
