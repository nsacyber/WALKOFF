import json
from datetime import datetime
from unittest import TestCase
from uuid import uuid4

import walkoff.config.paths
import walkoff.messaging
from tests.util import execution_db_help
from walkoff.events import WalkoffEvent
from walkoff.helpers import utc_as_rfc_datetime
from walkoff.messaging import MessageAction
from walkoff.messaging.utils import strip_requires_response_from_message_body, save_message, \
    get_all_matching_users_for_message, log_action_taken_on_message
from walkoff.server import flaskserver
from walkoff.serverdb import db, User, Role
from walkoff.serverdb.message import Message, MessageHistory


class TestMessageDatabase(TestCase):

    @classmethod
    def setUpClass(cls):
        execution_db_help.setup_dbs()
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
        db.session.commit()
        self.user3 = User('username3', 'password3', roles=[self.role.id])
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
        walkoff.messaging.workflow_authorization_cache._cache = {}
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        db.session.rollback()
        for user in [user for user in User.query.all() if user.username != 'admin']:
            db.session.delete(user)
        for role in [role for role in Role.query.all() if role.name != 'admin']:
            db.session.delete(role)
        db.session.commit()

        execution_db_help.tear_down_device_db()

    def get_default_message(self, commit=False, requires_reauth=False, requires_response=False):
        uid = uuid4()
        message = Message('subject here', json.dumps({'message': 'some message'}), uid,
                          [self.user, self.user2], requires_reauth=requires_reauth, requires_response=requires_response)
        db.session.add(message)
        if commit:
            db.session.commit()
        return message, uid

    def test_init(self):
        uid = uuid4()
        message = Message('subject here', 'body goes here', uid, [self.user, self.user2])
        self.assertEqual(message.subject, 'subject here')
        self.assertEqual(message.body, 'body goes here')
        self.assertEqual(message.workflow_execution_id, uid)
        self.assertListEqual(list(message.users), [self.user, self.user2])
        self.assertFalse(message.requires_reauth)
        self.assertFalse(message.requires_response)
        db.session.add(message)
        db.session.commit()
        self.assertIsNotNone(message.id)
        self.assertLess((datetime.utcnow() - message.created_at).total_seconds(), 5)
        self.assertEqual(len(list(self.user.messages)), 1)

    def test_init_message_requires_reauth(self):
        message = Message('subject here', 'body goes here', uuid4(), [self.user], requires_reauth=True)
        self.assertTrue(message.requires_reauth)

    def test_init_message_requires_action(self):
        message = Message('subject here', 'body goes here', uuid4(), [self.user], requires_response=True)
        self.assertTrue(message.requires_response)

    def test_user_reads_message(self):
        message, uid = self.get_default_message()
        message.record_user_action(self.user, MessageAction.read)
        self.assertEqual(len(list(message.history)), 1)
        history = list(message.history)[0]
        self.assertEqual(history.action, MessageAction.read)
        self.assertEqual(history.user_id, self.user.id)
        self.assertEqual(history.username, self.user.username)
        self.assertTrue(message.user_has_read(self.user))
        self.assertFalse(message.user_has_read(self.user2))

    def test_invalid_user_reads_message(self):
        message, uid = self.get_default_message()
        message.record_user_action(self.user3, MessageAction.read)
        self.assertEqual(len(list(message.history)), 0)
        for user in (self.user, self.user2, self.user3):
            self.assertFalse(message.user_has_read(user))

    def test_user_unreads_message_which_is_not_read(self):
        message, uid = self.get_default_message()
        message.record_user_action(self.user, MessageAction.unread)
        self.assertEqual(len(list(message.history)), 0)
        self.assertFalse(message.user_has_read(self.user))

    def test_invalid_user_unreads_message(self):
        message, uid = self.get_default_message()
        message.record_user_action(self.user3, MessageAction.unread)
        self.assertEqual(len(list(message.history)), 0)
        for user in (self.user, self.user2, self.user3):
            self.assertFalse(message.user_has_read(user))

    def test_user_unreads_message(self):
        message, uid = self.get_default_message()
        message.record_user_action(self.user, MessageAction.read)
        message.record_user_action(self.user, MessageAction.unread)
        self.assertEqual(len(list(message.history)), 2)
        self.assertFalse(message.user_has_read(self.user))
        self.assertEqual(list(message.history)[1].action, MessageAction.unread)

    def test_user_has_read_message(self):
        message, uid = self.get_default_message()
        message.record_user_action(self.user, MessageAction.read)
        message.record_user_action(self.user, MessageAction.unread)
        message.record_user_action(self.user, MessageAction.read)
        self.assertTrue(message.user_has_read(self.user))
        message.record_user_action(self.user, MessageAction.unread)
        self.assertFalse(message.user_has_read(self.user))

    def test_user_last_read_at(self):
        message, uid = self.get_default_message()
        message.record_user_action(self.user, MessageAction.read)
        message.record_user_action(self.user2, MessageAction.read)
        message.record_user_action(self.user, MessageAction.read)
        self.assertIsNone(message.user_last_read_at(self.user3))
        self.assertEqual(message.user_last_read_at(self.user), message.history[2].timestamp)
        self.assertEqual(message.user_last_read_at(self.user2), message.history[1].timestamp)

    def test_get_read_by(self):
        message, uid = self.get_default_message()
        message.record_user_action(self.user, MessageAction.read)
        message.record_user_action(self.user2, MessageAction.read)
        message.record_user_action(self.user, MessageAction.unread)
        self.assertSetEqual(message.get_read_by(), {self.user.username, self.user2.username})

    def test_user_deletes_message(self):
        message, uid = self.get_default_message()
        message.record_user_action(self.user, MessageAction.delete)
        self.assertEqual(len(list(message.history)), 1)
        history = list(message.history)[0]
        self.assertEqual(history.action, MessageAction.delete)
        self.assertEqual(history.user_id, self.user.id)
        self.assertEqual(history.username, self.user.username)
        self.assertEqual(len(list(self.user.messages)), 0)
        self.assertEqual(len(list(self.user2.messages)), 1)

    def test_invalid_user_deletes_message(self):
        message, uid = self.get_default_message()
        message.record_user_action(self.user3, MessageAction.delete)
        self.assertEqual(len(list(message.history)), 0)
        for user in (self.user, self.user2):
            self.assertEqual(len(list(user.messages)), 1)

    def test_user_acts_on_message(self):
        message, uid = self.get_default_message(requires_response=True)
        message.record_user_action(self.user, MessageAction.respond)
        self.assertEqual(len(list(message.history)), 1)
        history = list(message.history)[0]
        self.assertEqual(history.action, MessageAction.respond)
        self.assertEqual(history.user_id, self.user.id)
        self.assertEqual(history.username, self.user.username)

    def test_acts_on_message_which_does_not_require_action(self):
        message, uid = self.get_default_message()
        message.record_user_action(self.user, MessageAction.respond)
        self.assertEqual(len(list(message.history)), 0)

    def test_invalid_user_acts_on_message(self):
        message, uid = self.get_default_message(requires_response=True)
        message.record_user_action(self.user3, MessageAction.respond)
        self.assertEqual(len(list(message.history)), 0)

    def test_is_responded(self):
        message, uid = self.get_default_message(requires_response=True)
        self.assertFalse(message.is_responded()[0])
        self.assertIsNone(message.is_responded()[1])
        self.assertIsNone(message.is_responded()[2])
        message.record_user_action(self.user, MessageAction.read)
        self.assertFalse(message.is_responded()[0])
        self.assertIsNone(message.is_responded()[1])
        self.assertIsNone(message.is_responded()[2])
        message.record_user_action(self.user2, MessageAction.respond)
        self.assertTrue(message.is_responded()[0])
        act_history = message.history[1]
        self.assertEqual(message.is_responded()[1], act_history.timestamp)
        self.assertEqual(message.is_responded()[2], self.user2.username)

    def test_is_responded_already_responded(self):
        message, uid = self.get_default_message(requires_response=True)
        message.record_user_action(self.user, MessageAction.respond)
        message.record_user_action(self.user2, MessageAction.respond)
        self.assertEqual(len(list(message.history)), 1)
        self.assertEqual(message.history[0].user_id, self.user.id)

    def test_as_json(self):
        message, uid = self.get_default_message(commit=True)
        message_json = message.as_json(with_read_by=False)
        self.assertEqual(message_json['id'], message.id)
        self.assertEqual(message_json['subject'], 'subject here')
        self.assertDictEqual(message_json['body'], {'message': 'some message'})
        self.assertEqual(message_json['workflow_execution_id'], str(uid))
        self.assertFalse(message_json['requires_reauthorization'])
        self.assertFalse(message_json['requires_response'])
        self.assertFalse(message_json['awaiting_response'])
        for field in ('read_by', 'responded_at', 'responded_by'):
            self.assertNotIn(field, message_json)

    def test_as_json_summary(self):
        message, uid = self.get_default_message(commit=True)
        message_json = message.as_json(summary=True)
        self.assertEqual(message_json['id'], message.id)
        self.assertEqual(message_json['subject'], 'subject here')
        self.assertFalse(message_json['awaiting_response'])
        self.assertEqual(message_json['created_at'], utc_as_rfc_datetime(message.created_at))
        for field in ('read_by', 'responded_at', 'responded_by', 'body', 'workflow_execution_uid',
                      'requires_reauthorization', 'requires_response', 'is_read', 'last_read_at'):
            self.assertNotIn(field, message_json)

    def test_as_json_requires_reauth(self):
        message, uid = self.get_default_message(requires_reauth=True, commit=True)
        message_json = message.as_json(with_read_by=False)
        self.assertTrue(message_json['requires_reauthorization'])

    def test_as_json_requires_action(self):
        message, uid = self.get_default_message(requires_response=True, commit=True)
        message_json = message.as_json(with_read_by=False)
        self.assertTrue(message_json['requires_response'])
        self.assertTrue(message_json['awaiting_response'])

    def test_as_json_with_read_by(self):
        message, uid = self.get_default_message(commit=True)
        message.record_user_action(self.user, MessageAction.read)
        message_json = message.as_json(with_read_by=True)
        self.assertListEqual(message_json['read_by'], [self.user.username])
        message.record_user_action(self.user2, MessageAction.read)
        message_json = message.as_json(with_read_by=True)
        self.assertSetEqual(set(message_json['read_by']), {self.user.username, self.user2.username})

    def test_as_json_with_read_by_user_has_unread(self):
        message, uid = self.get_default_message(commit=True)
        message.record_user_action(self.user, MessageAction.read)
        message_json = message.as_json(with_read_by=True)
        self.assertListEqual(message_json['read_by'], [self.user.username])
        message.record_user_action(self.user2, MessageAction.read)
        message.record_user_action(self.user2, MessageAction.unread)
        message_json = message.as_json(with_read_by=True)
        self.assertSetEqual(set(message_json['read_by']), {self.user.username, self.user2.username})

    def test_as_json_with_responded(self):
        message, uid = self.get_default_message(commit=True, requires_response=True)
        message.record_user_action(self.user, MessageAction.respond)
        db.session.commit()
        message_json = message.as_json()
        message_history = message.history[0]
        self.assertFalse(message_json['awaiting_response'])
        self.assertEqual(message_json['responded_at'], utc_as_rfc_datetime(message_history.timestamp))
        self.assertEqual(message_json['responded_by'], message_history.username)

    def test_as_json_for_user(self):
        message, uid = self.get_default_message(commit=True)
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
        self.assertEqual(message_json['last_read_at'], utc_as_rfc_datetime(user1_history.timestamp))
        message_json = message.as_json(user=self.user2)
        self.assertTrue(message_json['is_read'])
        self.assertEqual(message_json['last_read_at'], utc_as_rfc_datetime(user2_history.timestamp))

    def test_as_json_for_user_summary(self):
        message, uid = self.get_default_message(commit=True)
        message_json = message.as_json(user=self.user, summary=True)
        self.assertFalse(message_json['is_read'])
        message.record_user_action(self.user, MessageAction.read)
        db.session.commit()
        user1_history = message.history[0]
        message_json = message.as_json(user=self.user, summary=True)
        self.assertTrue(message_json['is_read'])
        self.assertEqual(message_json['last_read_at'], utc_as_rfc_datetime(user1_history.timestamp))

    def test_strip_requires_auth_from_message_body(self):
        body = [{'message': 'look here', 'requires_response': True},
                {'message': 'also here', 'requires_response': False},
                {'message': 'here thing'}]
        self.assertTrue(strip_requires_response_from_message_body(body))
        self.assertListEqual(body,
                             [{'message': 'look here'}, {'message': 'also here'}, {'message': 'here thing'}])

    def test_strip_requires_auth_from_message_body_none_require_response(self):
        body = [{'message': 'look here', 'requires_response': False},
                {'message': 'also here', 'requires_response': False},
                {'message': 'here thing'}]
        self.assertFalse(strip_requires_response_from_message_body(body))

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
        workflow_execution_id = uuid4()
        body = [{'text': 'Here is something to look at'}, {'url': 'look.here.com'}]
        save_message(body, message_data, workflow_execution_id, False)
        messages = Message.query.all()
        self.assertEqual(len(messages), 1)
        message = messages[0]
        self.assertEqual(message.subject, message_data['subject'])
        self.assertEqual(len(message.users), 2)
        for user in message.users:
            self.assertIn(user, [user1, user2])
        self.assertEqual(message.body, json.dumps(body))

    def test_save_message_with_roles(self):
        role = Role('some role')
        db.session.add(role)
        user1 = User('aaaaa', 'passssss', roles=[role.id])
        user2 = User('bbbbb', 'passs', roles=[role.id])
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        message_data = {'users': [user1.id],
                        'roles': [role.id],
                        'subject': 'Re: This thing',
                        'requires_reauth': False}
        workflow_execution_id = uuid4()
        body = [{'text': 'Here is something to look at'}, {'url': 'look.here.com'}]
        save_message(body, message_data, workflow_execution_id, False)
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
        workflow_execution_id = 'workflow_uid4'
        body = {'body': [{'text': 'Here is something to look at'}, {'url': 'look.here.com'}]}
        save_message(body, message_data, workflow_execution_id, False)
        messages = Message.query.all()
        self.assertEqual(len(messages), 0)

    def test_save_message_callback(self):
        body = [{'message': 'look here', 'requires_auth': False},
                {'message': 'also here', 'requires_auth': False},
                {'message': 'here thing'}]
        message_data = {'message': {'body': body,
                                    'users': [self.user.id],
                                    'roles': [self.role.id],
                                    'subject': 'Warning about thing',
                                    'requires_reauth': False},
                        'workflow': {'execution_id': uuid4()}}
        sender = {}
        WalkoffEvent.SendMessage.send(sender, data=message_data)
        messages = Message.query.all()
        self.assertEqual(len(messages), 1)
        message = messages[0]
        self.assertEqual(message.subject, 'Warning about thing')
        self.assertFalse(message.requires_response)

    def test_save_message_callback_requires_auth(self):
        uid = uuid4()
        body = [{'message': 'look here', 'requires_response': False},
                {'message': 'also here', 'requires_response': True},
                {'message': 'here thing'}]
        message_data = {'message': {'body': body,
                                    'users': [self.user.id],
                                    'roles': [self.role.id],
                                    'subject': 'Re: Best chicken recipe',
                                    'requires_reauth': False},
                        'workflow': {'execution_id': uid}}
        sender = {}
        WalkoffEvent.SendMessage.send(sender, data=message_data)
        messages = Message.query.all()
        self.assertEqual(len(messages), 1)
        message = messages[0]
        self.assertEqual(message.subject, 'Re: Best chicken recipe')
        from walkoff import messaging
        self.assertTrue(messaging.workflow_authorization_cache.workflow_requires_authorization(uid))
        self.assertTrue(message.requires_response)

    def test_save_message_callback_sends_message_created(self):
        body = [{'message': 'look here', 'requires_response': False},
                {'message': 'also here', 'requires_response': True},
                {'message': 'here thing'}]
        message_data = {'message': {'body': body,
                                    'users': [self.user.id],
                                    'roles': [self.role.id],
                                    'subject': 'Re: Best chicken recipe',
                                    'requires_reauth': False},
                        'workflow': {'execution_id': uuid4()}}
        sender = {}
        res = {'called': False}

        @walkoff.messaging.MessageActionEvent.created.connect
        def caller(message, **data):
            res['called'] = True
            self.assertEqual(len(list(message.users)), 2)
            self.assertSetEqual({user.id for user in message.users}, {self.user.id, self.user3.id})

        WalkoffEvent.SendMessage.send(sender, data=message_data)
        self.assertTrue(res['called'])

    def test_message_actions_convert_string(self):
        self.assertEqual(MessageAction.convert_string('read'), MessageAction.read)
        self.assertEqual(MessageAction.convert_string('unread'), MessageAction.unread)
        self.assertIsNone(MessageAction.convert_string('__some_invalid_name'))

    @staticmethod
    def construct_mock_trigger_sender(workflow_execution_uid):
        return {'id': 'mock',
                'app_name': 'mock',
                'action_name': 'mock'}

    def test_invalid_trigger_pops_user_from_cache(self):
        uid1 = uuid4()
        uid2 = uuid4()
        walkoff.messaging.workflow_authorization_cache.add_authorized_users(uid1, users=[1, 2])
        walkoff.messaging.workflow_authorization_cache.add_user_in_progress(uid1, 1)
        walkoff.messaging.workflow_authorization_cache.add_user_in_progress(uid1, 2)

        WalkoffEvent.TriggerActionNotTaken.send(self.construct_mock_trigger_sender(uid2),
                                                data={'workflow_execution_id': uid2})
        self.assertEqual(walkoff.messaging.workflow_authorization_cache.peek_user_in_progress(uid1), 2)
        self.assertIsNone(walkoff.messaging.workflow_authorization_cache.peek_user_in_progress(uid2))
        WalkoffEvent.TriggerActionNotTaken.send(self.construct_mock_trigger_sender(uid1),
                                                data={'workflow_execution_id': uid1})
        self.assertEqual(walkoff.messaging.workflow_authorization_cache.peek_user_in_progress(uid1), 1)

    def test_log_action_taken_on_message(self):
        uid = uuid4()
        message = Message('subject', 'body', uid, users=[self.user, self.user2], requires_response=True)
        db.session.add(message)
        log_action_taken_on_message(self.user.id, uid)
        self.assertEqual(len(list(message.history)), 1)
        self.assertEqual(message.history[0].action, MessageAction.respond)

    def test_log_action_taken_on_message_invalid_user(self):
        uid = uuid4()
        message = Message('subject', 'body', uid, users=[self.user, self.user2], requires_response=True)
        db.session.add(message)
        log_action_taken_on_message(1000, uid)
        self.assertEqual(len(list(message.history)), 0)

    def test_trigger_action_taken_workflow(self):
        uid = str(uuid4())
        message = Message('subject', 'body', uid, users=[self.user, self.user2], requires_response=True)
        db.session.add(message)
        db.session.commit()
        walkoff.messaging.workflow_authorization_cache.add_authorized_users(uid, users=[1, 2])
        walkoff.messaging.workflow_authorization_cache.add_user_in_progress(uid, self.user.id)
        WalkoffEvent.TriggerActionTaken.send(self.construct_mock_trigger_sender(uid),
                                             data={'workflow_execution_id': uid})
        message = Message.query.filter(Message.workflow_execution_id == uid).first()
        self.assertEqual(len(list(message.history)), 1)
        self.assertEqual(message.history[0].action, MessageAction.respond)
        self.assertFalse(walkoff.messaging.workflow_authorization_cache.workflow_requires_authorization(uid))

    def test_trigger_action_taken_workflow_sends_responded_message(self):
        uid = str(uuid4())
        message = Message('subject', 'body', uid, users=[self.user, self.user2], requires_response=True)
        db.session.add(message)
        db.session.commit()
        walkoff.messaging.workflow_authorization_cache.add_authorized_users(uid, users=[1, 2])
        walkoff.messaging.workflow_authorization_cache.add_user_in_progress(uid, self.user.id)

        res = {'called': False}

        @walkoff.messaging.MessageActionEvent.responded.connect
        def connected(message_in, **data):
            res['called'] = True
            self.assertEqual(message_in.id, message.id)
            self.assertEqual(data['data']['user'], self.user)

        WalkoffEvent.TriggerActionTaken.send(self.construct_mock_trigger_sender(uid),
                                             data={'workflow_execution_id': uid})
        self.assertTrue(res['called'])

    def test_message_action_get_all_names(self):
        self.assertListEqual(MessageAction.get_all_action_names(), [action.name for action in MessageAction])
