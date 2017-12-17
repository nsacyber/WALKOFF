from tests.util.servertestcase import ServerTestCase
from server.database import User, Role, Message, MessageHistory
from server.extensions import db
from server.returncodes import *
from server import flaskserver
import json


class UserWrapper(object):
    def __init__(self, username, password, roles=[]):
        self.username = username
        self.password = password
        self.user = User(username, password, roles=roles)
        self.messages = None
        self.header = None


class TestMessagingEndpoints(ServerTestCase):

    @classmethod
    def setUpClass(cls):
        cls.context = flaskserver.app.test_request_context()
        cls.context.push()
        cls.app = flaskserver.app.test_client(cls)
        cls.app.testing = True
        db.create_all()
        cls.role_rd = Role('message_guest')
        cls.role_rd.set_resources([{'name': 'messages', 'permissions': ['read', 'delete', 'update']}])

        cls.role_r = Role('read_only')
        cls.role_r.set_resources([{'name': 'messages', 'permissions': ['read', 'update']}])
        db.session.add(cls.role_rd)
        db.session.add(cls.role_r)
        cls.user1 = UserWrapper('username', 'password', roles=[cls.role_rd.name])
        cls.user2 = UserWrapper('username2', 'password2', roles=[cls.role_r.name])
        cls.user3 = UserWrapper('username3', 'password3')
        cls.all_users = (cls.user1, cls.user2, cls.user3)
        db.session.add(cls.user1.user)
        db.session.add(cls.user2.user)
        db.session.add(cls.user3.user)
        db.session.commit()

    @staticmethod
    def make_message(users, requires_reauth=False, requires_action=False):
        message = Message('subject here', json.dumps({'message': 'some message'}), 'workflow_uid1',
                          users, requires_reauth=requires_reauth, requires_response=requires_action)
        db.session.add(message)
        return message

    def setUp(self):
        headers = self.login_all_users()
        self.user1.header = headers[0]
        self.user2.header = headers[1]
        self.user3.header = headers[2]
        self.message1 = TestMessagingEndpoints.make_message([self.user1.user])
        self.message2 = TestMessagingEndpoints.make_message([self.user1.user, self.user2.user])
        self.message3 = TestMessagingEndpoints.make_message([self.user2.user, self.user3.user])
        self.user1.messages = [self.message1, self.message2]
        self.user2.messages = [self.message2, self.message3]
        self.user3.messages = [self.message3]
        db.session.commit()

    def tearDown(self):
        db.session.rollback()
        for message in Message.query.all():
            db.session.delete(message)
        for history_entry in MessageHistory.query.all():
            db.session.delete(history_entry)
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        db.session.rollback()
        for user in [user for user in User.query.all() if user.username != 'admin']:
            db.session.delete(user)
        for role in [role for role in Role.query.all() if role.name != 'admin']:
            db.session.delete(role)
        db.session.commit()

    def login_user(self, user):
        post = self.app.post('/api/auth', content_type="application/json",
                             data=json.dumps(dict(username=user.username, password=user.password)), follow_redirects=True)
        key = json.loads(post.get_data(as_text=True))
        return {'Authorization': 'Bearer {}'.format(key['access_token'])}

    def login_all_users(self):
        return [self.login_user(user) for user in self.all_users]

    def act_on_messages(self, action, user, validate=True, status_code=SUCCESS, messages=None):
        messages = user.messages if messages is None else messages
        data = {'ids': [message.id for message in messages]}
        if validate:
            self.post_with_status_check('/api/messages/{}'.format(action), headers=user.header, status_code=status_code,
                                        data=json.dumps(data), content_type='application/json')
        else:
            self.app.post('/api/messages/{}'.format(action), headers=user.header,
                          data=json.dumps(data), content_type='application/json')

    def get_all_messages_for_user(self, user, status_code=SUCCESS):
        return self.get_with_status_check('/api/messages', headers=user.header, status_code=status_code)

    def assert_message_ids_equal(self, messages, expected_messages=None):
        expected_message_ids = {message.id for message in expected_messages}
        self.assertEqual(len(messages), len(expected_message_ids))
        self.assertSetEqual({message['id'] for message in messages}, expected_message_ids)

    def assert_user_read_status_on_messages(self, user, read=True, messages=None):
        messages = user.messages if messages is None else messages
        if read:
            for message in messages:
                self.assertTrue(message.user_has_read(user.user))
        else:
            for message in messages:
                self.assertFalse(message.user_has_read(user.user))

    def assert_user_num_messages(self, user, num_messages):
        self.assertEqual(len(list(user.user.messages)), num_messages)

    def assert_user_has_message(self, user, message):
        self.assertIn(message, user.user.messages)

    def test_get_all_messages(self):
        response = self.get_all_messages_for_user(self.user1)
        self.assert_message_ids_equal(response, self.user1.messages)
        response = self.get_all_messages_for_user(self.user2)
        self.assert_message_ids_equal(response, self.user2.messages)
        self.get_all_messages_for_user(self.user3, status_code=FORBIDDEN_ERROR)

    def test_read_all_messages(self):
        for user in (self.user1, self.user2):
            self.act_on_messages('read', user)
            self.assert_user_read_status_on_messages(user)
        self.act_on_messages('read', self.user3, status_code=FORBIDDEN_ERROR)

    def test_read_one_message(self):
        for user, message in [(self.user1, self.message1), (self.user2, self.message2)]:
            self.act_on_messages('read', user, messages=[message])
            self.assert_user_read_status_on_messages(user, messages=[message])
        self.act_on_messages('read', self.user3, messages=[self.message3], status_code=FORBIDDEN_ERROR)

    def test_unread_all_messages(self):
        for user in (self.user1, self.user2):
            self.act_on_messages('read', user, validate=False)
            self.act_on_messages('unread', user)
            self.assert_user_read_status_on_messages(user, read=False)
        self.act_on_messages('read', self.user3, status_code=FORBIDDEN_ERROR)

    def test_unread_one_message(self):
        for user, message in [(self.user1, self.message1), (self.user2, self.message2)]:
            self.act_on_messages('read', user, messages=[message])
            self.act_on_messages('unread', user, messages=[message], validate=False)
            self.assert_user_read_status_on_messages(user, messages=[message], read=False)
        self.act_on_messages('unread', self.user3, messages=[self.message3], status_code=FORBIDDEN_ERROR)

    def test_delete_all_messages(self):
        self.act_on_messages('delete', self.user1)
        self.assert_user_num_messages(self.user1, 0)
        for user in (self.user2, self.user3):
            self.act_on_messages('delete', user, status_code=FORBIDDEN_ERROR)
            self.assert_user_num_messages(user, len(user.messages))

    def test_delete_one_message(self):
        self.act_on_messages('delete', self.user1, messages=[self.user1.messages[0]])
        self.assert_user_has_message(self.user1, self.user1.messages[1])
        for user in (self.user2, self.user3):
            self.act_on_messages('delete', user, messages=[user.messages[0]], status_code=FORBIDDEN_ERROR)
            self.assert_user_num_messages(user, len(user.messages))


