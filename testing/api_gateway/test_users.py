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


def test_read_user(api_gateway, token, serverdb):
    SUCCESS = 200
    user = User('username', 'asdfghjkl;')
    serverdb.session.add(user)
    serverdb.session.commit()
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}

    response = api_gateway.get('/api/users', headers=header)
    keys = json.loads(response.get_data(as_text=True))
    assert response.status_code == SUCCESS
    assert {user['username'] for user in keys} == {'admin', 'username'}


def test_create_user_name_password_only(api_gateway, token):
    SUCCESS = 200
    data = {'username': 'test_user', 'password': 'NoH4x0rzPls!'}
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    response = api_gateway.post('/api/users', headers=header, content_type='application/json',
                                data=json.dumps(data))
    user = User.query.filter_by(username='test_user').first()
    keys = json.loads(response.get_data(as_text=True))
    assert user is not None
    assert keys == user.as_json()


def test_create_user_username_already_exists(api_gateway, token, serverdb):
    user = User('username', 'asdfghjkl;')
    serverdb.session.add(user)
    serverdb.session.commit()
    data = {'username': 'username', 'password': 'NoH4x0rzPls!'}
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    response = api_gateway.post('/api/users', headers=header, content_type='application/json',
                                data=json.dumps(data))
    assert response.status_code == 400


def test_create_user_with_roles(api_gateway, token, serverdb):
    role = Role('role1')
    serverdb.session.add(role)
    serverdb.session.commit()
    data = {'username': 'username', 'password': 'NoH4x0rzPls!', 'roles': [{'id': role.id}]}
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    response = api_gateway.post('/api/users', headers=header, content_type='application/json',
                                data=json.dumps(data))
    user = User.query.filter_by(username='username').first()
    keys = json.loads(response.get_data(as_text=True))

    assert response.status_code == 201
    assert user is not None
    assert keys == user.as_json()


def test_read_user(api_gateway, token, serverdb):
    user = User('username', 'asdfghjkl;')
    serverdb.session.add(user)
    serverdb.session.commit()
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    response = api_gateway.get("/api/users/{}".format(user.id), headers=header)
    keys = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200
    assert keys == user.as_json()


def test_read_user_user_does_not_exist(api_gateway, token):
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    response = api_gateway.get('/api/users/404', headers=header)
    assert response.status_code == 404


def test_update_user_password_only(api_gateway, token, serverdb):
    user = User('username', 'asdfghjkl;')
    serverdb.session.add(user)
    serverdb.session.commit()
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    data = {'id': user.id, 'old_password': 'asdfghjkl;', 'password': 'changed!'}
    response = api_gateway.put(f'/api/users/{user.id}', headers=header, content_type='application/json',
                               data=json.dumps(data))
    assert response.status_code == 200
    keys = json.loads(response.get_data(as_text=True))
    assert keys == user.as_json()
    assert user.verify_password('changed!') is True


def test_update_user_password_only_invalid_old_password(api_gateway, token, serverdb):
    user = User('username', 'asdfghjkl;')
    serverdb.session.add(user)
    serverdb.session.commit()
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    data = {'id': user.id, 'old_password': 'incorrectpassword', 'password': 'changed!'}
    response = api_gateway.put(f'/api/users/{user.id}', headers=header, content_type='application/json',
                               data=json.dumps(data))
    assert response.status_code == 401
    assert user.verify_password('asdfghjkl;') is True


def test_put_update_user_with_roles(api_gateway, token, serverdb):
    role = Role('role1')
    serverdb.session.add(role)
    serverdb.session.commit()
    user = User('username', 'supersecretshhhhh')
    serverdb.session.add(user)
    serverdb.session.commit()
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    data = {'id': user.id, 'roles': [{'id': role.id}]}
    response = api_gateway.put(f'/api/users/{user.id}', headers=header, content_type='application/json',
                               data=json.dumps(data))
    assert response.status_code == 200
    key = json.loads(response.get_data(as_text=True))
    assert key == user.as_json()
    assert {role.name for role in user.roles} == {'role1'}


def test_update_username(api_gateway, token, serverdb):
    user = User('username', 'whisperDieselEngine')
    serverdb.session.add(user)
    serverdb.session.commit()
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    data = {'id': user.id, 'username': 'new_name'}
    response = api_gateway.put(f'/api/users/{user.id}', headers=header, content_type='application/json',
                               data=json.dumps(data))
    assert response.status_code == 200
    key = json.loads(response.get_data(as_text=True))
    assert user.username == 'new_name'
    assert key == user.as_json()


def test_update_username_name_already_exists(api_gateway, token, serverdb):
    user = User('username', 'whisperDieselEngine')
    serverdb.session.add(user)
    user2 = User('user2', 'shhnow')
    serverdb.session.add(user)
    serverdb.session.add(user2)
    serverdb.session.commit()
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    data = {'id': user.id, 'username': 'user2'}
    response = api_gateway.put(f'/api/users/{user.id}', headers=header, content_type='application/json',
                               data=json.dumps(data))
    assert response.status_code == 400
    assert user.verify_password('whisperDieselEngine') is True  # check password wasn't changed


def test_change_password_and_username(api_gateway, token, serverdb):
    user = User('username', 'asdfghjkl;')
    serverdb.session.add(user)
    serverdb.session.commit()
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    data = {'id': user.id, 'old_password': 'asdfghjkl;', 'password': 'changed!', 'username': 'new_name'}
    response = api_gateway.put(f'/api/users/{user.id}', headers=header, content_type='application/json',
                               data=json.dumps(data))
    assert response.status_code == 200
    assert user.verify_password('changed!') is True
    assert user.username == 'new_name'
    keys = json.loads(response.get_data(as_text=True))
    assert keys == user.as_json()


def test_change_password_and_username_invalid_username(api_gateway, token, serverdb):
    user = User('username', 'whisperDieselEngine')
    user2 = User('user2', 'somethingelse#@!@#')
    serverdb.session.add(user)
    serverdb.session.add(user2)
    serverdb.session.commit()
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    data = {'id': user.id, 'old_password': 'asdfghjkl;', 'password': 'changed!', 'username': 'user2'}
    response = api_gateway.put(f'/api/users/{user.id}', headers=header, content_type='application/json',
                               data=json.dumps(data))
    assert response.status_code == 400
    assert user.verify_password('whisperDieselEngine') is True
    assert user.username == 'username'
    assert user2.verify_password('somethingelse#@!@#')
    assert user2.username == 'user2'


def test_change_password_and_username_invalid_password(api_gateway, token, serverdb):
    user = User('username', 'whisperDieselEngine')
    serverdb.session.add(user)
    serverdb.session.commit()
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    data = {'id': user.id, 'old_password': 'invalid', 'password': 'changed!', 'username': 'new_name'}
    response = api_gateway.put(f'/api/users/{user.id}', headers=header, content_type='application/json',
                               data=json.dumps(data))
    assert response.status_code == 401
    assert user.verify_password('whisperDieselEngine')
    assert user.username == 'username'


def test_update_active_with_guest_user(api_gateway, serverdb):
    user = add_user('guest', 'guest', ['guest'])
    response = api_gateway.post('/api/auth', content_type="application/json",
                                data=json.dumps(dict(username='guest', password='guest')))
    key = json.loads(response.get_data(as_text=True))
    access_token = key['access_token']
    headers = {'Authorization': 'Bearer {}'.format(access_token)}
    data = {'id': user.id, 'active': False}
    response = api_gateway.put(f'/api/users/{user.id}', headers=headers, content_type='application/json',
                               data=json.dumps(data))
    assert response.status_code == 200
    assert user.active is True


def test_update_active_with_admin_user(api_gateway, token, serverdb):
    user = add_user('guest', 'guest', ['guest'])
    data = {'id': user.id, 'active': False}
    headers = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    response = api_gateway.put(f'/api/users/{user.id}', headers=headers, content_type='application/json',
                               data=json.dumps(data))
    assert response.status_code == 200
    assert user.active is False


def test_update_different_user_not_admin(api_gateway):
    user = add_user('guest', 'guest', ['guest'])
    response = api_gateway.post('/api/auth', content_type="application/json",
                                data=json.dumps(dict(username='guest', password='guest')))
    key = json.loads(response.get_data(as_text=True))
    access_token = key['access_token']
    headers = {'Authorization': 'Bearer {}'.format(access_token)}
    admin = User.query.filter_by(username='admin').first()
    data = {'id': admin.id, 'username': 'somethingelse'}
    response = api_gateway.put(f'/api/users/{admin.id}', headers=headers, content_type='application/json',
                               data=json.dumps(data))
    assert response.status_code == 403


def test_update_user_invalid_id(api_gateway, token):
    data = {'id': 404, 'username': 'new_name'}
    headers = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    id = data['id']
    response = api_gateway.put(f'/api/users/{id}', headers=headers, content_type='application/json',
                               data=json.dumps(data))
    assert response.status_code == 404


def test_delete_user(api_gateway, token, serverdb):
    user = User('username', 'asdfghjkl;')
    serverdb.session.add(user)
    serverdb.session.commit()
    headers = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    response = api_gateway.delete(f'/api/users/{user.id}', headers=headers)
    assert response.status_code == 204


def test_delete_user_invalid_id(api_gateway, token):
    headers = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    response = api_gateway.delete('/api/users/404', headers=headers)
    assert response.status_code == 404


def test_delete_current_user(api_gateway):
    user = add_user('test', 'test')
    user.set_roles({1})
    response = api_gateway.post('/api/auth', content_type="application/json",
                                data=json.dumps(dict(username='test', password='test')))
    key = json.loads(response.get_data(as_text=True))
    access_token = key['access_token']
    headers = {'Authorization': 'Bearer {}'.format(access_token)}
    response2 = api_gateway.delete(f'/api/users/{user.id}', headers=headers)
    assert response2.status_code == 403


def test_user_pagination(api_gateway, token):
    headers = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    for i in range(38):
        data = {'username': 'user' + str(i), 'password': 'NoH4x0rzPls!'}
        response = api_gateway.post('/api/users', headers=headers, content_type='application/json',
                                    data=json.dumps(data))
        assert response.status_code == 201

    response = api_gateway.get('/api/users', headers=headers)
    assert response.status_code == 200
    keys = json.loads(response.get_data(as_text=True))
    assert len(keys) == 20

    response = api_gateway.get('/api/users?page=2', headers=headers)
    assert response.status_code == 200
    keys = json.loads(response.get_data(as_text=True))
    assert len(keys) == 20

    response = api_gateway.get('/api/users?page=3', headers=headers)
    assert response.status_code == 200
    keys = json.loads(response.get_data(as_text=True))
    assert len(keys) == 0
