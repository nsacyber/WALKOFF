import pytest
import json
import requests
import logging
from api_gateway.server.app import app
from flask_jwt_extended import decode_token, JWTManager
from api_gateway.flask_config import Config
from api_gateway.serverdb.user import User
from api_gateway.serverdb.role import Role
from api_gateway.serverdb.tokens import BlacklistedToken
from api_gateway.serverdb import add_user

logger = logging.getLogger(__name__)


def test_login_has_correct_return_code(api_gateway, serverdb):
    SUCCESS = 201
    header = {'content-type': 'application/json'}
    response = api_gateway.post('/api/auth',
                                data=json.dumps(dict(username='admin', password='admin')), headers=header)
    assert response.status_code == SUCCESS


def test_login_has_correct_structure(api_gateway, serverdb):
    SUCCESS = {'access_token', 'refresh_token'}
    header = {'content-type': 'application/json'}
    response = api_gateway.post('/api/auth',
                                data=json.dumps(dict(username='admin', password='admin')), headers=header)
    key = json.loads(response.get_data(as_text=True))
    assert set(key.keys()) == SUCCESS


def test_login_has_valid_access_token(api_gateway, serverdb):
    header = {'content-type': 'application/json'}
    response = api_gateway.post('/api/auth',
                                data=json.dumps(dict(username='admin', password='admin')), headers=header)
    keys = json.loads(response.get_data(as_text=True))
    with app.app_context():
        token = decode_token(keys['access_token'])
        uid = serverdb.session.query(User).filter_by(username='admin').first().id
        rid = serverdb.session.query(Role).filter_by(name="admin").first().id

    SUCCESS = {'username': 'admin', 'roles': [rid]}

    assert token['type'] == 'access'
    # assert token['fresh'] == True
    assert token['identity'] == uid
    assert token['user_claims'] == SUCCESS


def test_login_has_valid_refresh_token(api_gateway, serverdb):
    header = {'content-type': 'application/json'}
    response = api_gateway.post('/api/auth',
                                data=json.dumps(dict(username='admin', password='admin')), headers=header)
    keys = json.loads(response.get_data(as_text=True))
    with app.app_context():
        token = decode_token(keys['refresh_token'])
        uid = serverdb.session.query(User).filter_by(username='admin').first().id

    assert token['type'] == 'refresh'
    assert token['identity'] == uid


def test_login_updates_user(api_gateway, serverdb):
    uname = "newestuser2"
    user = add_user(username=uname, password='test')
    header = {'content-type': 'application/json'}
    api_gateway.post('/api/auth',
                     data=json.dumps(dict(username=uname, password='test')), headers=header)
    check = serverdb.session.query(User).filter_by(username=uname).first().login_count
    assert check == 1


def test_login_auth_invalid_username(api_gateway, serverdb):
    FAILURE = 401
    header = {'content-type': 'application/json'}
    response = api_gateway.post('/api/auth',
                                data=json.dumps(dict(username="invalid", password='admin')), headers=header)
    assert response.status_code == FAILURE


def test_login_auth_invalid_password(api_gateway, serverdb):
    FAILURE = 401
    header = {'content-type': 'application/json'}
    response = api_gateway.post('/api/auth',
                                data=json.dumps(dict(username="admin", password='invalid')), headers=header)
    assert response.status_code == FAILURE


def test_login_inactive_user(api_gateway, serverdb):
    user = add_user(username="testinactive", password="test")
    user.active = False
    serverdb.session.commit()
    FAILURE = 401
    header = {'content-type': 'application/json'}
    response = api_gateway.post('/api/auth',
                                data=json.dumps(dict(username="testinactive", password='test')), headers=header)
    assert response.status_code == FAILURE


def test_refresh_valid_token_yields_access_token(api_gateway, serverdb):
    SUCCESS = 201
    header = {'content-type': "application/json"}
    response = api_gateway.post('/api/auth',
                                data=json.dumps(dict(username='admin', password='admin')), headers=header)
    key = json.loads(response.get_data(as_text=True))

    headers = {'Authorization': 'Bearer {}'.format(key['refresh_token'])}
    refresh = api_gateway.post('/api/auth/refresh', content_type="application/json", headers=headers)

    key = json.loads(refresh.get_data(as_text=True))
    keys = set(key.keys())
    uid = serverdb.session.query(User).filter_by(username='admin').first().id
    token = decode_token(key['access_token'])

    assert refresh.status_code == SUCCESS
    assert keys == {'access_token'}
    assert token['type'] == 'access'
    assert token['identity'] == uid
    assert token['fresh'] == False


def test_refresh_invalid_user_blacklists_token(api_gateway, serverdb):
    user = add_user(username='test', password='test')
    header = {'content-type': "application/json"}
    response = api_gateway.post('/api/auth',
                                data=json.dumps(dict(username='test', password='test')), headers=header)
    key = json.loads(response.get_data(as_text=True))
    token = key['refresh_token']
    serverdb.session.delete(user)
    serverdb.session.commit()
    headers = {'Authorization': 'Bearer {}'.format(token)}
    refresh = api_gateway.post('/api/auth/refresh', content_type="application/json", headers=headers)
    assert refresh.status_code == 401

    token = decode_token(token)

    tokens = BlacklistedToken.query.filter_by(jti=token['jti']).all()
    assert len(tokens) == 1


def test_refresh_deactivated_user(api_gateway, serverdb):
    FAILURE = 401
    user = add_user(username='test', password='test')
    header = {'content-type': "application/json"}
    response = api_gateway.post('/api/auth',
                                data=json.dumps(dict(username='test', password='test')), headers=header)
    key = json.loads(response.get_data(as_text=True))
    token = key['refresh_token']
    headers = {'Authorization': 'Bearer {}'.format(token)}
    user.active = False
    serverdb.session.commit()
    refresh = api_gateway.post('/api/auth/refresh', content_type="application/json", headers=headers)
    assert refresh.status_code == FAILURE


def test_refresh_with_blacklisted_token(api_gateway, serverdb):
    user = add_user(username='test', password='test')
    header = {'content-type': "application/json"}
    response = api_gateway.post('/api/auth',
                                data=json.dumps(dict(username='test', password='test')), headers=header)

    key = json.loads(response.get_data(as_text=True))
    token = key['refresh_token']
    serverdb.session.delete(user)
    serverdb.session.commit()

    headers = {'Authorization': 'Bearer {}'.format(token)}
    api_gateway.post('/api/auth/refresh', content_type="application/json", headers=headers)
    # first api post places user on Blacklist, second one used for failure verification
    refresh = api_gateway.post('/api/auth/refresh', content_type="application/json", headers=headers)
    response = json.loads(refresh.get_data(as_text=True))

    assert refresh.status_code == 401
    assert response == {'error': 'Token is revoked'}


def test_logout_no_refresh_token(api_gateway, serverdb):
    header = {'content-type': "application/json"}
    response = api_gateway.post('/api/auth',
                                data=json.dumps(dict(username='admin', password='admin')), headers=header)
    key = json.loads(response.get_data(as_text=True))
    headers = {'Authorization': 'Bearer {}'.format(key['access_token'])}
    response = api_gateway.post('/api/auth/logout', headers=headers)
    assert response.status_code == 400
    assert len(BlacklistedToken.query.all()) == 0


def test_logout_mismatched_tokens(api_gateway, serverdb):
    header = {'content-type': "application/json"}
    response = api_gateway.post('/api/auth',
                                data=json.dumps(dict(username='admin', password='admin')), headers=header)
    key = json.loads(response.get_data(as_text=True))
    headers = {'Authorization': 'Bearer {}'.format(key['access_token'])}

    add_user(username='test', password='test')

    response = api_gateway.post('/api/auth',
                                data=json.dumps(dict(username='test', password='test')), headers=header)
    key = json.loads(response.get_data(as_text=True))
    token = key['refresh_token']

    response = api_gateway.post('/api/auth/logout', headers=headers, content_type="application/json",
                                data=json.dumps(dict(refresh_token=token)))
    assert response.status_code == 400
    assert len(BlacklistedToken.query.all()) == 0


def test_logout(api_gateway, serverdb):
    header = {'content-type': "application/json"}
    response = api_gateway.post('/api/auth',
                                data=json.dumps(dict(username='admin', password='admin')), headers=header)
    key = json.loads(response.get_data(as_text=True))
    access_token = key['access_token']
    refresh_token = key['refresh_token']
    headers = {'Authorization': 'Bearer {}'.format(access_token)}
    response = api_gateway.post('/api/auth/logout', headers=headers, content_type="application/json",
                                data=json.dumps(dict(refresh_token=refresh_token)))
    refresh_token = decode_token(refresh_token)
    refresh_token_jti = refresh_token['jti']
    assert response.status_code == 204

    tokens = BlacklistedToken.query.filter_by(jti=refresh_token_jti).all()
    assert len(tokens) == 1


def test_logout_updates_user(api_gateway, serverdb):
    user = add_user('testlogout', 'test')
    header = {'content-type': "application/json"}
    response = api_gateway.post('/api/auth',
                                data=json.dumps(dict(username='testlogout', password='test')), headers=header)
    key = json.loads(response.get_data(as_text=True))
    access_token = key['access_token']
    refresh_token = key['refresh_token']
    headers = {'Authorization': 'Bearer {}'.format(access_token)}
    api_gateway.post('/api/auth/logout', headers=headers, content_type="application/json",
                     data=json.dumps(dict(refresh_token=refresh_token)))
    assert user.login_count == 0
