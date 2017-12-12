from tests.util.servertestcase import ServerTestCase
from server.messaging import *
from server.database import User, Role, Resource, Permission
from server.returncodes import *
from server import flaskserver

class UserWrapper(object):
    def __init__(self, username, password, roles=[]):
        self.username = username
        self.password = password
        self.user = User(username, password, roles=roles)


class TestMessagingEndpoints(ServerTestCase):

    @classmethod
    def setUpClass(cls):
        cls.context = flaskserver.app.test_request_context()
        cls.context.push()
        cls.role = Role('visitor')
        db.session.add(cls.role)
        cls.user1 = UserWrapper('username', 'password')
        cls.user2 = UserWrapper('username2', 'password2')
        cls.user3 = UserWrapper('username3', 'password3', roles=[cls.role.name])
        cls.all_users = (cls.user1, cls.user2, cls.user3)
        db.session.add(cls.user1.user)
        db.session.add(cls.user2.user)
        db.session.add(cls.user3.user)

        cls.message1 = TestMessagingEndpoints.make_message([cls.user1.user])
        cls.message2 = TestMessagingEndpoints.make_message([cls.user1.user, cls.user2.user])
        cls.message3 = TestMessagingEndpoints.make_message([cls.user2.user, cls.user3.user])
        db.session.commit()

    @staticmethod
    def make_message(users, requires_reauth=False, requires_action=False):
        message = Message('subject here', json.dumps({'message': 'some message'}), 'workflow_uid1',
                          users, requires_reauth=requires_reauth, requires_action=requires_action)
        db.session.add(message)
        return message

    def tearDown(self):
        db.session.rollback()
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

    def test_get_all_messages(self):
        headers = self.login_all_users()
        response = self.get_with_status_check('/api/messages', headers=headers[0], status_code=SUCCESS)
        print(response)
