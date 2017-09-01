import unittest
from server.tokens import *
from datetime import timedelta
import json
from flask_jwt_extended import decode_token
from server.returncodes import *
from server.security import encrypt_password
from server.flaskserver import running_context


class TestAuthorization(unittest.TestCase):

    def setUp(self):
        import server.flaskserver
        self.app = server.flaskserver.app.test_client(self)
        self.app.testing = True
        self.context = server.flaskserver.app.test_request_context()
        self.context.push()

    def tearDown(self):
        running_context.User.query.filter_by(email='test').delete()
        from server.tokens import BlacklistedToken
        BlacklistedToken.query.delete()

    def test_as_json(self):
        token = BlacklistedToken(jti='some_jti', user_identity='user', expires=timedelta(minutes=5))
        self.assertDictEqual(token.as_json(),
                             {'id': None, 'jti': 'some_jti', 'user': 'user', 'expires': timedelta(minutes=5)})

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
        self.assertEqual(token['identity'], 'admin')
        self.assertListEqual(token['user_claims']['roles'], ['admin'])
        self.assertTrue(token['fresh'])

    def test_login_authorization_has_valid_refresh_token(self):
        response = self.app.post('/api/auth', content_type="application/json",
                                 data=json.dumps(dict(username='admin', password='admin')))
        key = json.loads(response.get_data(as_text=True))
        token = decode_token(key['refresh_token'])
        self.assertEqual(token['type'], 'refresh')
        self.assertEqual(token['identity'], 'admin')

    def test_login_authorization_invalid_username(self):
        response = self.app.post('/api/auth', content_type="application/json",
                             data=json.dumps(dict(username='invalid', password='admin')))
        self.assertEqual(response.status_code, UNAUTHORIZED_ERROR)

    def test_login_authorization_invalid_password(self):
        response = self.app.post('/api/auth', content_type="application/json",
                                 data=json.dumps(dict(username='admin', password='invalid')))
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
        self.assertEqual(token['identity'], 'admin')
        self.assertListEqual(token['user_claims']['roles'], ['admin'])
        self.assertFalse(token['fresh'])

    def test_refresh_invalid_user_blacklists_token(self):
        user = running_context.user_datastore.create_user(email='test', password=encrypt_password('test'))

        from server.database import db
        db.session.commit()
        response = self.app.post('/api/auth', content_type="application/json",
                                 data=json.dumps(dict(username='test', password='test')))
        key = json.loads(response.get_data(as_text=True))
        token = key['refresh_token']
        running_context.user_datastore.delete_user(user)
        db.session.commit()
        headers = {'Authorization': 'Bearer {}'.format(token)}
        refresh = self.app.post('/api/auth/refresh', content_type="application/json", headers=headers)
        self.assertEqual(refresh.status_code, UNAUTHORIZED_ERROR)
        token = decode_token(token)
        from server.tokens import BlacklistedToken

        tokens = BlacklistedToken.query.filter_by(jti=token['jti']).all()
        self.assertEqual(len(tokens), 1)

    def test_refresh_with_blacklisted_token(self):
        user = running_context.user_datastore.create_user(email='test', password=encrypt_password('test'))

        from server.database import db
        db.session.commit()
        response = self.app.post('/api/auth', content_type="application/json",
                                 data=json.dumps(dict(username='test', password='test')))
        key = json.loads(response.get_data(as_text=True))
        token = key['refresh_token']
        running_context.user_datastore.delete_user(user)
        db.session.commit()
        headers = {'Authorization': 'Bearer {}'.format(token)}
        self.app.post('/api/auth/refresh', content_type="application/json", headers=headers)
        refresh = self.app.post('/api/auth/refresh', content_type="application/json", headers=headers)
        self.assertEqual(refresh.status_code, UNAUTHORIZED_ERROR)
        response = json.loads(refresh.get_data(as_text=True))
        self.assertDictEqual(response, {'error': 'Token is revoked'})



