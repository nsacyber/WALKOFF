from unittest import TestCase
from server.database import Message, MessageHistory
from server.messaging import MessageAction
from server.messaging.utils import strip_requires_auth_from_message_body, save_message, \
    get_all_matching_users_for_message
from server.database import db, User, Role
from server import flaskserver
from datetime import datetime
from core.events import WalkoffEvent
import json


class TestMessageDatabase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.context = flaskserver.app.test_request_context()
        cls.context.push()
        db.create_all()
        for user in [user for user in User.query.all() if user.username != 'admin']:
            db.session.delete(user)
        for role in [role for role in Role.query.all() if role.name != 'admin']:
            db.session.delete(role)
        for message in Message.query.all():
            db.session.delete(message)
        db.session.commit()

    def setUp(self):
        self.user = User('username', 'password')
        self.user2 = User('username2', 'password2')

        self.role = Role('visitor')
        db.session.add(self.role)
        self.user3 = User('username3', 'password3', roles=[self.role.name])
        db.session.add(self.user)
        db.session.add(self.user2)
        db.session.add(self.user3)
        db.session.commit()

    def tearDown(self):
        db.session.rollback()
        for message in Message.query.all():
            db.session.delete(message)
        for history_entry in MessageHistory.query.all():
            db.session.delete(history_entry)
        for user in [user for user in User.query.all() if user.username != 'admin']:
            db.session.delete(user)
        for role in [role for role in Role.query.all() if role.name != 'admin']:
            db.session.delete(role)
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        db.session.rollback()
        for user in [user for user in User.query.all() if user.username != 'admin']:
            db.session.delete(user)
        for role in [role for role in Role.query.all() if role.name != 'admin']:
            db.session.delete(role)
        db.session.commit()

    def get_default_message(self, commit=False, requires_reauth=False, requires_action=False):
        message = Message('subject here', json.dumps({'message': 'some message'}), 'workflow_uid1',
                          [self.user, self.user2], requires_reauth=requires_reauth, requires_action=requires_action)
        db.session.add(message)
        if commit:
            db.session.commit()
        return message

    def test_init_message(self):
        message = Message('subject here', 'body goes here', 'workflow_uid1', [self.user, self.user2])
        self.assertEqual(message.subject, 'subject here')
        self.assertEqual(message.body, 'body goes here')
        self.assertEqual(message.workflow_execution_uid, 'workflow_uid1')
        self.assertListEqual(list(message.users), [self.user, self.user2])
        self.assertFalse(message.requires_reauth)
        self.assertFalse(message.requires_action)
        db.session.add(message)
        db.session.commit()
        self.assertIsNotNone(message.id)
        self.assertLess((datetime.utcnow() - message.created_at).total_seconds(), 5)
        self.assertEqual(len(list(self.user.messages)), 1)

    def test_init_message_requires_reauth(self):
        message = Message('subject here', 'body goes here', 'workflow_uid1', [self.user], requires_reauth=True)
        self.assertTrue(message.requires_reauth)

    def test_init_message_requires_action(self):
        message = Message('subject here', 'body goes here', 'workflow_uid1', [self.user], requires_action=True)
        self.assertTrue(message.requires_action)

    def test_user_reads_message(self):
        message = self.get_default_message()
        message.record_user_action(self.user, MessageAction.read)
        self.assertEqual(len(list(message.history)), 1)
        history = list(message.history)[0]
        self.assertEqual(history.action, MessageAction.read)
        self.assertEqual(history.user_id, self.user.id)
        self.assertEqual(history.username, self.user.username)
        self.assertTrue(message.user_has_read(self.user))
        self.assertFalse(message.user_has_read(self.user2))

    def test_invalid_user_reads_message(self):
        message = self.get_default_message()
        message.record_user_action(self.user3, MessageAction.read)
        self.assertEqual(len(list(message.history)), 0)
        for user in (self.user, self.user2, self.user3):
            self.assertFalse(message.user_has_read(user))

    def test_user_unreads_message_which_is_not_read(self):
        message = self.get_default_message()
        message.record_user_action(self.user, MessageAction.unread)
        self.assertEqual(len(list(message.history)), 0)
        self.assertFalse(message.user_has_read(self.user))

    def test_invalid_user_unreads_message(self):
        message = self.get_default_message()
        message.record_user_action(self.user3, MessageAction.unread)
        self.assertEqual(len(list(message.history)), 0)
        for user in (self.user, self.user2, self.user3):
            self.assertFalse(message.user_has_read(user))

    def test_user_unreads_message(self):
        message = self.get_default_message()
        message.record_user_action(self.user, MessageAction.read)
        message.record_user_action(self.user, MessageAction.unread)
        self.assertEqual(len(list(message.history)), 2)
        self.assertFalse(message.user_has_read(self.user))
        self.assertEqual(list(message.history)[1].action, MessageAction.unread)

    def test_user_has_read_message(self):
        message = self.get_default_message()
        message.record_user_action(self.user, MessageAction.read)
        message.record_user_action(self.user, MessageAction.unread)
        message.record_user_action(self.user, MessageAction.read)
        self.assertTrue(message.user_has_read(self.user))
        message.record_user_action(self.user, MessageAction.unread)
        self.assertFalse(message.user_has_read(self.user))

    def test_user_last_read_at(self):
        message = self.get_default_message()
        message.record_user_action(self.user, MessageAction.read)
        message.record_user_action(self.user2, MessageAction.read)
        message.record_user_action(self.user, MessageAction.read)
        self.assertIsNone(message.user_last_read_at(self.user3))
        self.assertEqual(message.user_last_read_at(self.user), message.history[2].timestamp)
        self.assertEqual(message.user_last_read_at(self.user2), message.history[1].timestamp)

    def test_get_read_by(self):
        message = self.get_default_message()
        message.record_user_action(self.user, MessageAction.read)
        message.record_user_action(self.user2, MessageAction.read)
        message.record_user_action(self.user, MessageAction.unread)
        self.assertSetEqual(message.get_read_by(), {self.user.username, self.user2.username})

    def test_user_deletes_message(self):
        message = self.get_default_message()
        message.record_user_action(self.user, MessageAction.delete)
        self.assertEqual(len(list(message.history)), 1)
        history = list(message.history)[0]
        self.assertEqual(history.action, MessageAction.delete)
        self.assertEqual(history.user_id, self.user.id)
        self.assertEqual(history.username, self.user.username)
        self.assertEqual(len(list(self.user.messages)), 0)
        self.assertEqual(len(list(self.user2.messages)), 1)

    def test_invalid_user_deletes_message(self):
        message = self.get_default_message()
        message.record_user_action(self.user3, MessageAction.delete)
        self.assertEqual(len(list(message.history)), 0)
        for user in (self.user, self.user2):
            self.assertEqual(len(list(user.messages)), 1)

    def test_user_acts_on_message(self):
        message = self.get_default_message(requires_action=True)
        message.record_user_action(self.user, MessageAction.act)
        self.assertEqual(len(list(message.history)), 1)
        history = list(message.history)[0]
        self.assertEqual(history.action, MessageAction.act)
        self.assertEqual(history.user_id, self.user.id)
        self.assertEqual(history.username, self.user.username)

    def test_acts_on_message_which_does_not_require_action(self):
        message = self.get_default_message()
        message.record_user_action(self.user, MessageAction.act)
        self.assertEqual(len(list(message.history)), 0)

    def test_invalid_user_acts_on_message(self):
        message = self.get_default_message(requires_action=True)
        message.record_user_action(self.user3, MessageAction.act)
        self.assertEqual(len(list(message.history)), 0)

    def test_is_acted_on(self):
        message = self.get_default_message(requires_action=True)
        self.assertFalse(message.is_acted_on()[0])
        self.assertIsNone(message.is_acted_on()[1])
        self.assertIsNone(message.is_acted_on()[2])
        message.record_user_action(self.user, MessageAction.read)
        self.assertFalse(message.is_acted_on()[0])
        self.assertIsNone(message.is_acted_on()[1])
        self.assertIsNone(message.is_acted_on()[2])
        message.record_user_action(self.user2, MessageAction.act)
        self.assertTrue(message.is_acted_on()[0])
        act_history = message.history[1]
        self.assertEqual(message.is_acted_on()[1], act_history.timestamp)
        self.assertEqual(message.is_acted_on()[2], self.user2.username)

    def test_is_acted_on_already_acted_on(self):
        message = self.get_default_message(requires_action=True)
        message.record_user_action(self.user, MessageAction.act)
        message.record_user_action(self.user2, MessageAction.act)
        self.assertEqual(len(list(message.history)), 1)
        self.assertEqual(message.history[0].user_id, self.user.id)

    def test_as_json(self):
        message = self.get_default_message(commit=True)
        message_json = message.as_json(with_read_by=False)
        self.assertGreater(message_json['id'], 0)
        self.assertEqual(message_json['subject'], 'subject here')
        self.assertDictEqual(message_json['body'], {'message': 'some message'})
        self.assertEqual(message_json['workflow_execution_uid'], 'workflow_uid1')
        self.assertFalse(message_json['requires_reauthorization'])
        self.assertFalse(message_json['requires_action'])
        self.assertFalse(message_json['awaiting_action'])
        for field in ('read_by', 'acted_on_at', 'acted_on_by'):
            self.assertNotIn(field, message_json)

    def test_as_json_requires_reauth(self):
        message = self.get_default_message(requires_reauth=True)
        message_json = message.as_json(with_read_by=False)
        self.assertTrue(message_json['requires_reauthorization'])

    def test_as_json_requires_action(self):
        message = self.get_default_message(requires_action=True)
        message_json = message.as_json(with_read_by=False)
        self.assertTrue(message_json['requires_action'])
        self.assertTrue(message_json['awaiting_action'])

    def test_as_json_with_read_by(self):
        message = self.get_default_message()
        message.record_user_action(self.user, MessageAction.read)
        message_json = message.as_json(with_read_by=True)
        self.assertListEqual(message_json['read_by'], [self.user.username])
        message.record_user_action(self.user2, MessageAction.read)
        message_json = message.as_json(with_read_by=True)
        self.assertSetEqual(set(message_json['read_by']), {self.user.username, self.user2.username})

    def test_as_json_with_read_by_user_has_unread(self):
        message = self.get_default_message()
        message.record_user_action(self.user, MessageAction.read)
        message_json = message.as_json(with_read_by=True)
        self.assertListEqual(message_json['read_by'], [self.user.username])
        message.record_user_action(self.user2, MessageAction.read)
        message.record_user_action(self.user2, MessageAction.unread)
        message_json = message.as_json(with_read_by=True)
        self.assertSetEqual(set(message_json['read_by']), {self.user.username, self.user2.username})

    def test_as_json_with_acted_on(self):
        message = self.get_default_message(commit=True, requires_action=True)
        message.record_user_action(self.user, MessageAction.act)
        db.session.commit()
        message_json = message.as_json()
        message_history = message.history[0]
        self.assertFalse(message_json['awaiting_action'])
        self.assertEqual(message_json['acted_on_at'], str(message_history.timestamp))
        self.assertEqual(message_json['acted_on_by'], message_history.username)

    def test_as_json_for_user(self):
        message = self.get_default_message(commit=True)
        message_json = message.as_json(user=self.user)
        self.assertFalse(message_json['is_read'])
        message_json = message.as_json(user=self.user2)
        self.assertFalse(message_json['is_read'])
        message.record_user_action(self.user, MessageAction.read)
        message.record_user_action(self.user2, MessageAction.read)
        db.session.commit()
        user1_history = message.history[0]
        user2_history = message.history[1]
        message_json = message.as_json(user=self.user)
        self.assertTrue(message_json['is_read'])
        self.assertEqual(message_json['last_read_at'], str(user1_history.timestamp))
        message_json = message.as_json(user=self.user2)
        self.assertTrue(message_json['is_read'])
        self.assertEqual(message_json['last_read_at'], str(user2_history.timestamp))

    def test_strip_requires_auth_from_message_body(self):
        body = {'body': [{'message': 'look here', 'requires_auth': True},
                {'message': 'also here', 'requires_auth': False},
                {'message': 'here thing'}]}
        self.assertTrue(strip_requires_auth_from_message_body(body))
        self.assertListEqual(body['body'], [{'message': 'look here'}, {'message': 'also here'}, {'message': 'here thing'}])

    def test_strip_requires_auth_from_message_body_none_require_auth(self):
        body = {'body': [{'message': 'look here', 'requires_auth': False},
                {'message': 'also here', 'requires_auth': False},
                {'message': 'here thing'}]}
        self.assertFalse(strip_requires_auth_from_message_body(body))

    def test_get_all_matching_members_for_message_no_users_or_roles_in_db(self):
        self.assertListEqual(get_all_matching_users_for_message([10, 20, 30], [20, 42]), [])

    def test_get_all_matching_members_for_message(self):
        users = get_all_matching_users_for_message([self.user.id, self.user2.id], [])
        self.assertEqual(len(users), 2)
        for user in users:
            self.assertIn(user, [self.user, self.user2])

        users = get_all_matching_users_for_message([], [self.role.id])
        self.assertListEqual(users, [self.user3])

        users = get_all_matching_users_for_message([self.user.id, self.user2.id], [self.role.id])
        self.assertEqual(len(users), 3)
        for user in users:
            self.assertIn(user, [self.user, self.user2, self.user3])

    def test_save_message(self):
        user1 = User('aaaaa', 'passssss')
        user2 = User('bbbbb', 'passs')
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        message_data = {'users': [user1.id, user2.id],
                        'roles': [],
                        'subject': 'Re: This thing',
                        'requires_reauth': False}
        workflow_execution_uid = 'workflow_uid1'
        body = {'body': [{'text': 'Here is something to look at'}, {'url': 'look.here.com'}]}
        save_message(body, message_data, workflow_execution_uid, False)
        messages = Message.query.all()
        self.assertEqual(len(messages), 1)
        message = messages[0]
        self.assertEqual(message.subject, message_data['subject'])
        self.assertEqual(len(message.users), 2)
        for user in message.users:
            self.assertIn(user, [user1, user2])
        self.assertEqual(message.body, json.dumps(body['body']))

    def test_save_message_with_roles(self):
        role = Role('some role')
        db.session.add(role)
        user1 = User('aaaaa', 'passssss', roles=[role.name])
        user2 = User('bbbbb', 'passs', roles=[role.name])
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        message_data = {'users': [user1.id],
                        'roles': [role.id],
                        'subject': 'Re: This thing',
                        'requires_reauth': False}
        workflow_execution_uid = 'workflow_uid1'
        body = {'body': [{'text': 'Here is something to look at'}, {'url': 'look.here.com'}]}
        save_message(body, message_data, workflow_execution_uid, False)
        messages = Message.query.all()
        self.assertEqual(len(messages), 1)
        message = messages[0]
        self.assertEqual(len(message.users), 2)
        for user in message.users:
            self.assertIn(user, [user1, user2])

    def test_save_message_no_valid_users(self):
        message_data = {'users': [10, 20],
                        'roles': [],
                        'subject': 'Re: This a thing',
                        'requires_reauth': False}
        workflow_execution_uid = 'workflow_uid4'
        body = {'body': [{'text': 'Here is something to look at'}, {'url': 'look.here.com'}]}
        save_message(body, message_data, workflow_execution_uid, False)
        messages = Message.query.all()
        self.assertEqual(len(messages), 0)

    def test_save_message_callback(self):
        body = {'body': [{'message': 'look here', 'requires_auth': False},
                         {'message': 'also here', 'requires_auth': False},
                         {'message': 'here thing'}]}
        message_data = {'body': body,
                        'users': [self.user.id],
                        'roles': [self.role.id],
                        'subject': 'Warning about thing',
                        'requires_reauth': False}
        sender = {'workflow_execution_uid': 'workflow_uid10'}

        WalkoffEvent.SendMessage.send(sender, data=message_data)
        messages = Message.query.all()
        self.assertEqual(len(messages), 1)
        message = messages[0]
        self.assertEqual(message.subject, 'Warning about thing')
        self.assertFalse(message.requires_action)

    def test_save_message_callback_requires_auth(self):
        body = {'body': [{'message': 'look here', 'requires_auth': False},
                         {'message': 'also here', 'requires_auth': True},
                         {'message': 'here thing'}]}
        message_data = {'body': body,
                        'users': [self.user.id],
                        'roles': [self.role.id],
                        'subject': 'Re: Best chicken recipe',
                        'requires_reauth': False}
        sender = {'workflow_execution_uid': 'workflow_uid14'}

        WalkoffEvent.SendMessage.send(sender, data=message_data)
        messages = Message.query.all()
        self.assertEqual(len(messages), 1)
        message = messages[0]
        self.assertEqual(message.subject, 'Re: Best chicken recipe')
        from server import messaging
        self.assertTrue(messaging.workflow_authorization_cache.workflow_requires_authorization('workflow_uid14'))
        self.assertTrue(message.requires_action)

    def test_message_actions_convert_string(self):
        self.assertEqual(MessageAction.convert_string('read'), MessageAction.read)
        self.assertEqual(MessageAction.convert_string('unread'), MessageAction.unread)
        self.assertIsNone(MessageAction.convert_string('__some_invalid_name'))





