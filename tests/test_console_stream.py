import json
from copy import copy
from uuid import uuid4

from flask import Response
from mock import patch

from tests.util.mock_objects import MockRedisCacheAdapter
from tests.util.servertestcase import ServerTestCase
from walkoff.server.blueprints.console import *
from walkoff.server.returncodes import SUCCESS


class TestConsoleStream(ServerTestCase):

    def setUp(self):
        self.cache = MockRedisCacheAdapter()
        console_stream.cache = self.cache

    def tearDown(self):
        self.cache.clear()

    def test_format_console_data(self):
        sender = {'name': 'workflow1', 'execution_id': 'abc-def-ghi'}
        data = {'app_name': 'App1', 'action_name': 'action1', 'level': logging.WARN, 'message': 'some_message'}
        expected = copy(data)
        expected['workflow'] = 'workflow1'
        expected['level'] = logging.getLevelName(logging.WARN)
        self.assertEqual(format_console_data(sender, data=data), expected)

    @patch.object(console_stream, 'publish')
    def test_console_log_callback(self, mock_publish):
        sender = {'name': 'workflow1', 'execution_id': 'abc-def-ghi'}
        data = {'app_name': 'App1', 'action_name': 'action1', 'level': 'WARN', 'message': 'some_message'}
        console_log_callback(sender, data=data)
        expected = format_console_data(sender, data=data)
        mock_publish.assert_called_once_with(expected, event='log', subchannels=sender['execution_id'])

    def call_stream(self, execution_id=None):
        url = '/api/streams/console/log'
        if execution_id:
            url += '?workflow_execution_id={}'.format(execution_id)
        return self.test_client.get(url, headers=self.headers)

    @patch.object(console_stream, 'stream')
    def test_stream_endpoint(self, mock_stream):
        mock_stream.return_value = Response('something', status=SUCCESS)
        execution_id = str(uuid4())
        response = self.call_stream(execution_id=execution_id)
        mock_stream.assert_called_once_with(subchannel=execution_id)
        self.assertEqual(response.status_code, SUCCESS)

    @patch.object(console_stream, 'stream')
    def test_stream_endpoint_invalid_uuid(self, mock_stream):
        mock_stream.return_value = Response('something', status=SUCCESS)
        response = self.call_stream(execution_id='invalid')
        mock_stream.assert_not_called()
        self.assertEqual(response.status_code, BAD_REQUEST)

    @patch.object(console_stream, 'stream')
    def test_stream_endpoint_no_execution_id(self, mock_stream):
        mock_stream.return_value = Response('something', status=SUCCESS)
        response = self.call_stream()
        mock_stream.assert_not_called()
        self.assertEqual(response.status_code, BAD_REQUEST)

    @patch.object(console_stream, 'stream')
    def check_stream_endpoint_no_key(self, mock_stream):
        mock_stream.return_value = Response('something', status=SUCCESS)
        response = self.test_client.get('/api/streams/console/log?access_token=invalid')
        mock_stream.assert_not_called()
        self.assertEqual(response.status_code, 422)
