from datetime import datetime
from unittest import TestCase

from tests.util import execution_db_help
from walkoff.messaging import MessageAction
from walkoff.server import flaskserver
from walkoff.serverdb import db
from walkoff.serverdb.message import MessageHistory
from walkoff.serverdb.user import User


class TestMessageHistoryDatabase(TestCase):

    @classmethod
    def setUpClass(cls):
        execution_db_help.setup_dbs()

        cls.context = flaskserver.app.test_request_context()
        cls.context.push()
        db.create_all()
        for user in [user for user in User.query.all() if user.username != 'admin']:
            db.session.delete(user)
        for message in MessageHistory.query.all():
            db.session.delete(message)
        db.session.commit()
        cls.user1 = User('username', 'password')
        cls.user2 = User('username2', 'pwwww3')
        db.session.add(cls.user1)
        db.session.add(cls.user2)
        db.session.commit()

    def tearDown(self):
        db.session.rollback()
        for message in MessageHistory.query.all():
            db.session.delete(message)

    @classmethod
    def tearDownClass(cls):
        db.session.rollback()
        for user in [user for user in User.query.all() if user.username != 'admin']:
            db.session.delete(user)
        for message in MessageHistory.query.all():
            db.session.delete(message)

        execution_db_help.tear_down_execution_db()

    def assert_message_history_init_correct(self, message_history, action, user):
        self.assertEqual(message_history.action, action)
        self.assertEqual(message_history.user_id, user.id)
        self.assertEqual(message_history.username, user.username)
        self.assertLess((datetime.utcnow() - message_history.timestamp).total_seconds(), 5)

    def check_action_construction(self, action):
        message_history = MessageHistory(self.user1, action)
        db.session.add(message_history)
        db.session.commit()
        self.assert_message_history_init_correct(message_history, action, self.user1)
        message_history = MessageHistory(self.user2, action)
        db.session.add(message_history)
        db.session.commit()
        self.assert_message_history_init_correct(message_history, action, self.user2)

    def test_read_message(self):
        self.check_action_construction(MessageAction.read)

    def test_unread_message(self):
        self.check_action_construction(MessageAction.unread)

    def test_deleted_message(self):
        self.check_action_construction(MessageAction.delete)

    def test_acted_on_message(self):
        self.check_action_construction(MessageAction.respond)

    def test_as_json(self):
        message_history = MessageHistory(self.user1, MessageAction.read)
        db.session.add(message_history)
        db.session.commit()
        message_json = message_history.as_json()
        self.assertIsNotNone(message_json['timestamp'])
        self.assertEqual(message_json['action'], 'read')
        self.assertEqual(message_json['user_id'], self.user1.id)
        self.assertEqual(message_json['username'], self.user1.username)
        message_history = MessageHistory(self.user1, MessageAction.unread)
        db.session.add(message_history)
        db.session.commit()
        message_json = message_history.as_json()
        self.assertEqual(message_json['action'], 'unread')
