from unittest import TestCase
from server.messaging import (Message, get_all_matching_users_for_message, save_message,
                              strip_requires_auth_from_message_body)
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

    def tearDown(self):
        db.session.rollback()
        for user in [user for user in User.query.all() if user.username != 'admin']:
            db.session.delete(user)
        for message in Message.query.all():
            db.session.delete(message)
        for role in [role for role in Role.query.all() if role.name != 'admin']:
            db.session.delete(role)
        db.session.commit()

    def test_init_message(self):
        user = User('username', 'password')
        user2 = User('username2', 'password2')
        db.session.add(user)
        message = Message('subject here', 'body goes here', 'workflow_uid1', [user, user2])
        self.assertEqual(message.subject, 'subject here')
        self.assertEqual(message.body, 'body goes here')
        self.assertEqual(message.workflow_execution_uid, 'workflow_uid1')
        self.assertListEqual(list(message.users), [user, user2])
        self.assertFalse(message.requires_reauth)
        db.session.add(message)
        db.session.commit()
        self.assertIsNotNone(message.id)
        self.assertLess((datetime.utcnow() - message.created_at).total_seconds(), 5)
        self.assertFalse(message.is_read)
        self.assertIsNone(message.read_at)
        self.assertEqual(len(list(user.messages)), 1)

    def test_init_message_requires_reauth(self):
        user = User('username', 'password')
        db.session.add(user)
        message = Message('subject here', 'body goes here', 'workflow_uid1', [user], requires_reauth=True)
        self.assertTrue(message.requires_reauth)

    def test_read(self):
        user = User('username', 'password')
        db.session.add(user)
        message = Message('subject here', 'body goes here', 'workflow_uid1', [user], requires_reauth=True)
        message.read()
        self.assertTrue(message.is_read)
        self.assertIsNotNone(message.read_at)
        self.assertLess((datetime.utcnow()-message.read_at).total_seconds(), 5)

    def test_unread(self):
        user = User('username', 'password')
        db.session.add(user)
        message = Message('subject here', 'body goes here', 'workflow_uid1', [user], requires_reauth=True)
        message.read()
        self.assertTrue(message.is_read)
        self.assertIsNotNone(message.read_at)
        message.unread()
        self.assertFalse(message.is_read)
        self.assertIsNone(message.read_at)
        db.session.commit()

    def test_as_json(self):
        user = User('username', 'password')
        user2 = User('username2', 'password2')
        db.session.add(user)
        message = Message('subject here', json.dumps({'message': 'some message'}), 'workflow_uid1', [user, user2])
        db.session.add(message)
        db.session.commit()
        message_json = message.as_json()
        self.assertGreater(message_json['id'], 0)
        self.assertEqual(message_json['subject'], 'subject here')
        self.assertDictEqual(message_json['body'], {'message': 'some message'})
        self.assertEqual(message_json['workflow_execution_uid'], 'workflow_uid1')
        self.assertFalse(message_json['requires_reauthorization'])
        self.assertFalse(message_json['is_read'])
        self.assertIsNotNone(message_json['created_at'])
        self.assertNotIn('read_at', message_json)

    def test_as_json_requires_reauth(self):
        user = User('username', 'password')
        user2 = User('username2', 'password2')
        db.session.add(user)
        message = Message(
            'subject here', json.dumps({'message': 'some message'}), 'workflow_uid1',
            [user, user2], requires_reauth=True)
        db.session.add(message)
        db.session.commit()
        message_json = message.as_json()
        self.assertTrue(message_json['requires_reauthorization'])

    def test_as_json_read_message(self):
        user = User('username', 'password')
        user2 = User('username2', 'password2')
        db.session.add(user)
        message = Message(
            'subject here', json.dumps({'message': 'some message'}), 'workflow_uid1',
            [user, user2], requires_reauth=True)
        message.read()
        message_json = message.as_json()
        self.assertTrue(message_json['is_read'])
        self.assertIsNotNone(message_json['read_at'])

    def test_strip_requires_auth_from_message_body(self):
        body = [{'message': 'look here', 'requires_auth': True},
                {'message': 'also here', 'requires_auth': False},
                {'message': 'here thing'}]
        self.assertTrue(strip_requires_auth_from_message_body(body))
        self.assertListEqual(body, [{'message': 'look here'}, {'message': 'also here'}, {'message': 'here thing'}])

    def test_strip_requires_auth_from_message_body_none_require_auth(self):
        body = [{'message': 'look here', 'requires_auth': False},
                {'message': 'also here', 'requires_auth': False},
                {'message': 'here thing'}]
        self.assertFalse(strip_requires_auth_from_message_body(body))

    def test_get_all_matching_members_for_message_no_users_or_roles_in_db(self):
        self.assertListEqual(get_all_matching_users_for_message([10, 20, 30], [20, 42]), [])

    def test_get_all_matching_members_for_message(self):
        user1 = User('user1', 'pass1')
        user2 = User('user2', 'pass1')
        role = Role('role1')
        db.session.add(role)
        user3 = User('user3', 'pass1', roles=['role1'])
        db.session.add(user1)
        db.session.add(user2)
        db.session.add(user3)
        db.session.commit()
        users = get_all_matching_users_for_message([user1.id, user2.id], [])
        self.assertEqual(len(users), 2)
        for user in users:
            self.assertIn(user, [user1, user2])

        users = get_all_matching_users_for_message([], [role.id])
        self.assertListEqual(users, [user3])

        users = get_all_matching_users_for_message([user1.id, user2.id], [role.id])
        self.assertEqual(len(users), 3)
        for user in users:
            self.assertIn(user, [user1, user2, user3])

    def test_save_message(self):
        user1 = User('user1', 'pass1')
        user2 = User('user2', 'pass1')
        role = Role('role1')
        db.session.add(role)
        user3 = User('user3', 'pass1', roles=['role1'])
        db.session.add(user1)
        db.session.add(user2)
        db.session.add(user3)
        db.session.commit()
        message_data = {'users': [user1.id, user2.id],
                        'roles': [],
                        'subject': 'Re: This thing',
                        'requires_reauth': False}
        workflow_execution_uid = 'workflow_uid1'
        body = [{'text': 'Here is something to look at'}, {'url': 'look.here.com'}]
        save_message(body, message_data, workflow_execution_uid)
        messages = Message.query.all()
        self.assertEqual(len(messages), 1)
        message = messages[0]
        self.assertEqual(message.subject, message_data['subject'])
        self.assertEqual(len(message.users), 2)
        for user in message.users:
            self.assertIn(user, [user1, user2])
        self.assertEqual(message.body, json.dumps(body))

    def test_save_message_with_roles(self):
        user1 = User('user1', 'pass1')
        user2 = User('user2', 'pass1')
        role = Role('role1')
        db.session.add(role)
        user3 = User('user3', 'pass1', roles=['role1'])
        db.session.add(user1)
        db.session.add(user2)
        db.session.add(user3)
        db.session.commit()
        message_data = {'users': [user2.id],
                        'roles': [role.id],
                        'subject': 'Re: This thing',
                        'requires_reauth': False}
        workflow_execution_uid = 'workflow_uid1'
        body = [{'text': 'Here is something to look at'}, {'url': 'look.here.com'}]
        save_message(body, message_data, workflow_execution_uid)
        messages = Message.query.all()
        self.assertEqual(len(messages), 1)
        message = messages[0]
        self.assertEqual(len(message.users), 2)
        for user in message.users:
            self.assertIn(user, [user2, user3])

    def test_save_message_no_valid_users(self):
        message_data = {'users': [10, 20],
                        'roles': [],
                        'subject': 'Re: This a thing',
                        'requires_reauth': False}
        workflow_execution_uid = 'workflow_uid4'
        body = [{'text': 'Here is something to look at'}, {'url': 'look.here.com'}]
        save_message(body, message_data, workflow_execution_uid)
        messages = Message.query.all()
        self.assertEqual(len(messages), 0)

    def test_save_message_callback(self):
        body = [{'message': 'look here', 'requires_auth': False},
                {'message': 'also here', 'requires_auth': False},
                {'message': 'here thing'}]
        user1 = User('user1', 'pass1')
        user2 = User('user2', 'pass1')
        role = Role('role1')
        db.session.add(role)
        user3 = User('user3', 'pass1', roles=['role1'])
        db.session.add(user1)
        db.session.add(user2)
        db.session.add(user3)
        db.session.commit()
        message_data = {'body': body,
                        'users': [user2.id],
                        'roles': [role.id],
                        'subject': 'Warning about thing',
                        'requires_reauth': False}
        sender = {'workflow_execution_uid': 'workflow_uid10'}

        WalkoffEvent.SendMessage.send(sender, data=message_data)
        messages = Message.query.all()
        self.assertEqual(len(messages), 1)
        message = messages[0]
        self.assertEqual(message.subject, 'Warning about thing')

    def test_save_message_callback_requires_auth(self):
        body = [{'message': 'look here', 'requires_auth': False},
                {'message': 'also here', 'requires_auth': True},
                {'message': 'here thing'}]
        user1 = User('user1', 'pass1')
        user2 = User('user2', 'pass1')
        role = Role('role1')
        db.session.add(role)
        user3 = User('user3', 'pass1', roles=['role1'])
        db.session.add(user1)
        db.session.add(user2)
        db.session.add(user3)
        db.session.commit()
        message_data = {'body': body,
                        'users': [user2.id],
                        'roles': [role.id],
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






