import json
import unittest
from datetime import timedelta

from flask_jwt_extended import decode_token

from tests.util import execution_db_help
from walkoff.extensions import db
from walkoff.server.returncodes import *
from walkoff.serverdb import add_user
from walkoff.serverdb.tokens import BlacklistedToken
from walkoff.serverdb.user import User


class TestAuthorization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        execution_db_help.setup_dbs()

    @classmethod
    def tearDownClass(cls):
        execution_db_help.tear_down_execution_db()

    def setUp(self):
        import walkoff.server.flaskserver
        self.app = walkoff.server.flaskserver.app.test_client(self)
        self.app.testing = True
        self.context = walkoff.server.flaskserver.app.test_request_context()
        self.context.push()

        from walkoff.serverdb import initialize_default_resources_admin, initialize_default_resources_guest, Role
        db.create_all()

        # Setup admin and guest roles
        initialize_default_resources_admin()
        initialize_default_resources_guest()

        # Setup admin user
        admin_role = Role.query.filter_by(id=1).first()
        admin_user = User.query.filter_by(username="admin").first()
        if not admin_user:
            add_user(username='admin', password='admin', roles=[1])
        elif admin_role not in admin_user.roles:
            admin_user.roles.append(admin_role)

        db.session.commit()

        self.admin_role_id = db.session.query(Role).filter_by(name='admin').first().id
        self.admin_user_id = db.session.query(User).filter_by(username='admin').first().id

    def tearDown(self):
        db.session.rollback()
        User.query.filter_by(username='test').delete()
        for token in BlacklistedToken.query.all():
            db.session.delete(token)
        for user in (user for user in User.query.all() if user.username != 'admin'):
            db.session.delete(user)
        db.session.commit()

    def test_as_json(self):
        token = BlacklistedToken(jti='some_jti', user_identity='user', expires=timedelta(minutes=5))
        self.assertDictEqual(token.as_json(),
                             {'id': None, 'jti': 'some_jti', 'user': 'user', 'expires': str(timedelta(minutes=5))})

    def test_login_authorization_has_correct_return_code(self):
        response = self.app.post('/api/auth', content_type="application/json",
                                 data=json.dumps(dict(username='admin', password='admin')))
        self.assertEqual(response.status_code, OBJECT_CREATED)

    def test_login_authorization_has_correct_structure(self):
        response = self.app.post('/api/auth', content_type="application/json",
                                 data=json.dumps(dict(username='admin', password='admin')))
        key = json.loads(response.get_data(as_text=True))
        self.assertSetEqual(set(key.keys()), {'access_token', 'refresh_token'})

    def test_login_authorization_has_valid_access_token(self):
        response = self.app.post('/api/auth', content_type="application/json",
                                 data=json.dumps(dict(username='admin', password='admin')))
        key = json.loads(response.get_data(as_text=True))
        token = decode_token(key['access_token'])
        self.assertEqual(token['type'], 'access')
        self.assertEqual(token['identity'], self.admin_user_id)
        self.assertTrue(token['fresh'])
        self.assertDictEqual(token['user_claims'], {'username': 'admin', 'roles': [self.admin_role_id]})

    def test_login_authorization_has_valid_refresh_token(self):
        response = self.app.post('/api/auth', content_type="application/json",
                                 data=json.dumps(dict(username='admin', password='admin')))
        key = json.loads(response.get_data(as_text=True))
        token = decode_token(key['refresh_token'])
        self.assertEqual(token['type'], 'refresh')
        self.assertEqual(token['identity'], self.admin_user_id)

    def test_login_updates_user(self):
        user = add_user(username='testlogin', password='test')
        self.app.post('/api/auth', content_type="application/json",
                      data=json.dumps(dict(username='testlogin', password='test')))
        self.assertEqual(user.login_count, 1)
        self.assertTrue(user.active)

    def test_login_authorization_invalid_username(self):
        response = self.app.post('/api/auth', content_type="application/json",
                                 data=json.dumps(dict(username='invalid', password='admin')))
        self.assertEqual(response.status_code, UNAUTHORIZED_ERROR)

    def test_login_authorization_invalid_password(self):
        response = self.app.post('/api/auth', content_type="application/json",
                                 data=json.dumps(dict(username='admin', password='invalid')))
        self.assertEqual(response.status_code, UNAUTHORIZED_ERROR)

    def test_login_inactive_user(self):
        user = add_user(username='testinactive', password='test')
        user.active = False
        response = self.app.post('/api/auth', content_type="application/json",
                                 data=json.dumps(dict(username='testinactive', password='test')))
        self.assertEqual(response.status_code, UNAUTHORIZED_ERROR)

    def test_refresh_valid_token_yields_access_token(self):
        response = self.app.post('/api/auth', content_type="application/json",
                                 data=json.dumps(dict(username='admin', password='admin')))
        key = json.loads(response.get_data(as_text=True))

        headers = {'Authorization': 'Bearer {}'.format(key['refresh_token'])}
        refresh = self.app.post('/api/auth/refresh', content_type="application/json", headers=headers)
        self.assertEqual(refresh.status_code, OBJECT_CREATED)
        key = json.loads(refresh.get_data(as_text=True))
        self.assertSetEqual(set(key.keys()), {'access_token'})
        token = decode_token(key['access_token'])
        self.assertEqual(token['type'], 'access')
        self.assertEqual(token['identity'], self.admin_user_id)
        self.assertFalse(token['fresh'])

    def test_refresh_invalid_user_blacklists_token(self):
        user = add_user(username='test', password='test')

        db.session.commit()
        response = self.app.post('/api/auth', content_type="application/json",
                                 data=json.dumps(dict(username='test', password='test')))
        key = json.loads(response.get_data(as_text=True))
        token = key['refresh_token']
        db.session.delete(user)
        db.session.commit()
        headers = {'Authorization': 'Bearer {}'.format(token)}
        refresh = self.app.post('/api/auth/refresh', content_type="application/json", headers=headers)
        self.assertEqual(refresh.status_code, UNAUTHORIZED_ERROR)
        token = decode_token(token)

        tokens = BlacklistedToken.query.filter_by(jti=token['jti']).all()
        self.assertEqual(len(tokens), 1)

    def test_refresh_deactivated_user(self):
        user = add_user(username='test', password='test')

        db.session.commit()
        response = self.app.post('/api/auth', content_type="application/json",
                                 data=json.dumps(dict(username='test', password='test')))
        key = json.loads(response.get_data(as_text=True))
        token = key['refresh_token']
        headers = {'Authorization': 'Bearer {}'.format(token)}
        user.active = False
        refresh = self.app.post('/api/auth/refresh', content_type="application/json", headers=headers)
        self.assertEqual(refresh.status_code, UNAUTHORIZED_ERROR)

    def test_refresh_with_blacklisted_token(self):
        user = add_user(username='test', password='test')

        db.session.commit()
        response = self.app.post('/api/auth', content_type="application/json",
                                 data=json.dumps(dict(username='test', password='test')))
        key = json.loads(response.get_data(as_text=True))
        token = key['refresh_token']
        db.session.delete(user)
        db.session.commit()
        headers = {'Authorization': 'Bearer {}'.format(token)}
        self.app.post('/api/auth/refresh', content_type="application/json", headers=headers)
        refresh = self.app.post('/api/auth/refresh', content_type="application/json", headers=headers)
        self.assertEqual(refresh.status_code, UNAUTHORIZED_ERROR)
        response = json.loads(refresh.get_data(as_text=True))
        self.assertDictEqual(response, {'error': 'Token is revoked'})

    def test_logout_no_refresh_token(self):
        response = self.app.post('/api/auth', content_type="application/json",
                                 data=json.dumps(dict(username='admin', password='admin')))
        key = json.loads(response.get_data(as_text=True))
        headers = {'Authorization': 'Bearer {}'.format(key['access_token'])}
        response = self.app.post('/api/auth/logout', headers=headers)
        self.assertEqual(response.status_code, BAD_REQUEST)
        self.assertEqual(len(BlacklistedToken.query.all()), 0)

    def test_logout_mismatched_tokens(self):
        response = self.app.post('/api/auth', content_type="application/json",
                                 data=json.dumps(dict(username='admin', password='admin')))
        key = json.loads(response.get_data(as_text=True))
        headers = {'Authorization': 'Bearer {}'.format(key['access_token'])}

        add_user(username='test', password='test')

        db.session.commit()
        response = self.app.post('/api/auth', content_type="application/json",
                                 data=json.dumps(dict(username='test', password='test')))
        key = json.loads(response.get_data(as_text=True))
        token = key['refresh_token']

        response = self.app.post('/api/auth/logout', headers=headers, content_type="application/json",
                                 data=json.dumps(dict(refresh_token=token)))
        self.assertEqual(response.status_code, BAD_REQUEST)
        self.assertEqual(len(BlacklistedToken.query.all()), 0)

    def test_logout(self):
        response = self.app.post('/api/auth', content_type="application/json",
                                 data=json.dumps(dict(username='admin', password='admin')))
        key = json.loads(response.get_data(as_text=True))
        access_token = key['access_token']
        refresh_token = key['refresh_token']
        headers = {'Authorization': 'Bearer {}'.format(access_token)}
        response = self.app.post('/api/auth/logout', headers=headers, content_type="application/json",
                                 data=json.dumps(dict(refresh_token=refresh_token)))
        refresh_token = decode_token(refresh_token)
        refresh_token_jti = refresh_token['jti']
        self.assertEqual(response.status_code, NO_CONTENT)
        tokens = BlacklistedToken.query.filter_by(jti=refresh_token_jti).all()
        self.assertEqual(len(tokens), 1)

    def test_logout_updates_user(self):
        user = add_user('testlogout', 'test')
        response = self.app.post('/api/auth', content_type="application/json",
                                 data=json.dumps(dict(username='testlogout', password='test')))
        key = json.loads(response.get_data(as_text=True))
        access_token = key['access_token']
        refresh_token = key['refresh_token']
        headers = {'Authorization': 'Bearer {}'.format(access_token)}
        self.app.post('/api/auth/logout', headers=headers, content_type="application/json",
                      data=json.dumps(dict(refresh_token=refresh_token)))
        self.assertEqual(user.login_count, 0)
