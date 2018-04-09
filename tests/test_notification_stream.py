from tests.util.mock_objects import MockRedisCacheAdapter
from walkoff.server.blueprints.notifications import *
from datetime import datetime
from mock import patch
from tests.util.servertestcase import ServerTestCase
from walkoff.server.returncodes import SUCCESS
from flask import Response
import json


class MockUser:
    def __init__(self, id_, username):
        self.id = id_
        self.username = username


class MockMessage:
    def __init__(self, id_, subject, users, created_at, requires_response):
        self.id = id_
        self.subject = subject
        self.users = users
        self.created_at = created_at
        self.requires_response = requires_response


class TestNotificationStream(ServerTestCase):

    def setUp(self):
        self.cache = MockRedisCacheAdapter()
        sse_stream.cache = self.cache

    def tearDown(self):
        self.cache.clear()

    @staticmethod
    def get_standard_message_and_user():
        message = MockMessage(1, 'sub', [MockUser(1, 'uname'), MockUser(2, 'admin2')], datetime.utcnow(), False)
        user = MockUser(3, 'uname2')
        return message, user

    @staticmethod
    def _format_user_dict(user):
        return {'data': {'user': user}}

    def assert_timestamp_is_not_none(self, formatted):
        timestamp = formatted.pop('timestamp', None)
        self.assertIsNotNone(timestamp)

    def test_format_read_responded_data(self):
        message, user = self.get_standard_message_and_user()
        formatted = format_read_responded_data(message, user)
        self.assert_timestamp_is_not_none(formatted)
        self.assertDictEqual(formatted, {'id': 1, 'username': 'uname2'})

    @patch.object(sse_stream, 'publish')
    def test_message_created_callback(self, mock_publish):
        message, user = self.get_standard_message_and_user()
        result, ids = message_created_callback(message, **self._format_user_dict(user))
        self.assertSetEqual(ids, {1, 2})
        expected = {
            'id': message.id,
            'subject': message.subject,
            'created_at': message.created_at.isoformat(),
            'is_read': False,
            'awaiting_response': message.requires_response}
        self.assertDictEqual(result, expected)
        mock_publish.assert_called_once_with(result, subchannels=ids, event=NotificationSseEvent.created.name)

    @patch.object(sse_stream, 'publish')
    def test_message_read_callback(self, mock_publish):
        message, user = self.get_standard_message_and_user()
        result, ids = message_read_callback(message, **self._format_user_dict(user))
        self.assertSetEqual(ids, {1, 2})
        mock_publish.assert_called_once_with(result, subchannels=ids, event=NotificationSseEvent.read.name)
        self.assert_timestamp_is_not_none(result)
        self.assertDictEqual(result, {'id': message.id, 'username': user.username})

    @patch.object(sse_stream, 'publish')
    def test_message_responded_callback(self, mock_publish):
        message, user = self.get_standard_message_and_user()
        result, ids = message_responded_callback(message, **self._format_user_dict(user))
        self.assertSetEqual(ids, {1, 2})
        mock_publish.assert_called_once_with(result, subchannels=ids, event=NotificationSseEvent.responded.name)
        self.assert_timestamp_is_not_none(result)
        self.assertDictEqual(result, {'id': message.id, 'username': user.username})

    @patch.object(sse_stream, 'stream')
    def test_notifications_stream_endpoint(self,  mock_stream):
        mock_stream.return_value = Response('something', status=SUCCESS)
        post = self.test_client.post('/api/auth', content_type="application/json",
                             data=json.dumps(dict(username='admin', password='admin')), follow_redirects=True)
        key = json.loads(post.get_data(as_text=True))['access_token']
        response = self.test_client.get('/api/streams/messages/notifications?access_token={}'.format(key))
        mock_stream.assert_called_once_with(subchannel=1)
        self.assertEqual(response.status_code, SUCCESS)

    @patch.object(sse_stream, 'stream')
    def test_notifications_stream_endpoint_no_key(self, mock_stream):
        mock_stream.return_value = Response('something', status=SUCCESS)
        response = self.test_client.get('/api/streams/messages/notifications?access_token=invalid')
        mock_stream.assert_not_called()
        self.assertEqual(response.status_code, 422)