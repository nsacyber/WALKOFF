from unittest import TestCase
from tests.util.mock_objects import MockRedisCacheAdapter
from walkoff.server.blueprints.notifications import *


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


class TestNotificationStream(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cache = MockRedisCacheAdapter()
        sse_stream.cache = cls.cache

    def tearDown(self):
        self.cache.clear()

    @staticmethod
    def get_standard_message_and_user():
        message = MockMessage(1, 'sub', [MockUser(1, 'uname'), MockUser(2, 'admin2')], 'now', False)
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
        formatted = format_read_responded_data(message, self._format_user_dict(user))
        self.assert_timestamp_is_not_none(formatted)
        self.assertDictEqual(formatted, {'id': 1, 'username': 'uname2'})

    def test_message_created_callback(self):
        message, user = self.get_standard_message_and_user()
        result, ids = message_created_callback(message, **self._format_user_dict(user))
        self.assertSetEqual(ids, {1, 2})
        expected = {'id': message.id, 'subject': message.subject, 'created_at': message.created_at, 'is_read': False,
                    'awaiting_response': message.requires_response}
        self.assertDictEqual(result, expected)

    def test_message_read_callback(self):
        message, user = self.get_standard_message_and_user()
        result, ids = message_read_callback(message, **self._format_user_dict(user))
        self.assertSetEqual(ids, {1, 2})
        self.assert_timestamp_is_not_none(result)
        self.assertDictEqual(result, {'id': message.id, 'username': user.username})

    def test_message_responded_callback(self):
        message, user = self.get_standard_message_and_user()
        result, ids = message_responded_callback(message, **self._format_user_dict(user))
        self.assertSetEqual(ids, {1, 2})
        self.assert_timestamp_is_not_none(result)
        self.assertDictEqual(result, {'id': message.id, 'username': user.username})