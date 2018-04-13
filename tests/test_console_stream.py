import json
from copy import copy

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
        mock_publish.assert_called_once_with(expected, event='log')

    @patch.object(console_stream, 'stream')
    def test_stream_endpoint(self, mock_stream):
        mock_stream.return_value = Response('something', status=SUCCESS)
        post = self.test_client.post('/api/auth', content_type="application/json",
                                     data=json.dumps(dict(username='admin', password='admin')), follow_redirects=True)
        key = json.loads(post.get_data(as_text=True))['access_token']
        response = self.test_client.get('/api/streams/console/log?access_token={}'.format(key))
        mock_stream.assert_called_once_with()
        self.assertEqual(response.status_code, SUCCESS)

    @patch.object(console_stream, 'stream')
    def check_stream_endpoint_no_key(self, mock_stream):
        mock_stream.return_value = Response('something', status=SUCCESS)
        response = self.test_client.get('/api/streams/console/log?access_token=invalid')
        mock_stream.assert_not_called()
        self.assertEqual(response.status_code, 422)
