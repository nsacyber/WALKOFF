import pytest
import json
import requests
import logging
from api_gateway.serverdb.user import User
from api_gateway.serverdb.role import Role
from api_gateway.serverdb.resource import Resource
from api_gateway.serverdb.tokens import BlacklistedToken
from api_gateway.serverdb import add_user

logger = logging.getLogger(__name__)


def test_read_all_roles_no_added_roles(api_gateway, token, serverdb):
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    response = api_gateway.get('/api/roles', headers=header)
    assert response.status_code == 200
    keys = json.loads(response.get_data(as_text=True))
    assert [role['name'] for role in keys] == ['admin', 'guest']


def test_read_all_roles_with_extra_added_roles(api_gateway, token, serverdb):
    role = Role('role1')
    serverdb.session.add(role)
    serverdb.session.commit()
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    response = api_gateway.get('/api/roles', headers=header)
    keys = json.loads(response.get_data(as_text=True))
    assert {role['name'] for role in keys} == {'admin', 'role1', 'guest'}


def assert_role_json_is_equal(role, expected):
    assert role['id'] == expected['id']
    assert role['name'] == expected['name']
    assert role['description'] == expected['description']

    expected_resources = {resource['name']: resource['permissions'] for resource in expected['resources']}
    response_resources = {resource['name']: resource['permissions'] for resource in role['resources']}
    assert expected_resources == response_resources


def test_create_role(api_gateway, token, serverdb):
    resources = [{'name': 'resource1', 'permissions': ['create']},
                 {'name': 'resource2', 'permissions': ['create']},
                 {'name': 'resource3', 'permissions': ['create']}]
    data = {"name": 'role1', "description": 'desc', "resources": resources}
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    response = api_gateway.post('/api/roles', headers=header,
                                content_type='application/json', data=json.dumps(data))
    assert response.status_code == 201
    keys = json.loads(response.get_data(as_text=True))
    assert 'id' in keys
    data['id'] = keys['id']
    assert_role_json_is_equal(keys, data)


def test_create_role_name_already_exists(api_gateway, token, serverdb):
    data = {"name": 'role1'}
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    response = api_gateway.post('/api/roles', headers=header, content_type='application/json',
                                data=json.dumps(data))
    keys = json.loads(response.get_data(as_text=True))
    response = api_gateway.put(f'/api/roles/{keys["id"]}', headers=header,
                               content_type='application/json', data=json.dumps(data))
    assert response.status_code == 400


def test_read_role(api_gateway, token, serverdb):
    data = {"name": 'role1', "description": 'desc', "resources": [{'name': 'resource1', 'permissions': ['create']},
                                                                  {'name': 'resource2', 'permissions': ['create']},
                                                                  {'name': 'resource3', 'permissions': ['create']}]}
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    response = api_gateway.post('/api/roles', headers=header, content_type='application/json',
                                data=json.dumps(data))
    keys = json.loads(response.get_data(as_text=True))
    role_id = keys['id']
    response = api_gateway.get(f'/api/roles/{role_id}', headers=header)
    keys = json.loads(response.get_data(as_text=True))
    data['id'] = role_id
    assert_role_json_is_equal(keys, data)


def test_read_role_does_not_exist(api_gateway, token):
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    response = api_gateway.get('/api/roles/404', headers=header)
    assert response.status_code == 404


def test_update_role_name_only(api_gateway, token, serverdb):
    data_init = {"name": 'role1', "description": 'desc',
                 "resources": [{'name': 'resource1', 'permissions': ['create']},
                               {'name': 'resource2', 'permissions': ['create']},
                               {'name': 'resource3', 'permissions': ['create']}]}
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    response = api_gateway.post('/api/roles', headers=header, content_type='application/json',
                                data=json.dumps(data_init))
    keys = json.loads(response.get_data(as_text=True))
    role_id = keys['id']
    data = {'id': role_id, 'name': 'renamed'}
    response = api_gateway.put(f'/api/roles/{role_id}', headers=header,
                               content_type='application/json', data=json.dumps(data))
    assert response.status_code == 200
    keys = json.loads(response.get_data(as_text=True))
    expected = dict(data_init)
    expected['name'] = 'renamed'
    expected['id'] = role_id
    assert_role_json_is_equal(keys, expected)


def test_update_role_name_only_already_exists(api_gateway, token, serverdb):
    data_init = {"name": 'role1', "description": 'desc',
                 "resources": [{'name': 'resource1', 'permissions': ['create']},
                               {'name': 'resource2', 'permissions': ['create']},
                               {'name': 'resource3', 'permissions': ['create']}]}
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    response = api_gateway.post('/api/roles', headers=header, content_type='application/json',
                                data=json.dumps(data_init))
    key = json.loads(response.get_data(as_text=True))
    role_id = key['id']
    data2_init = {"name": 'role2', "description": 'desc',
                  "resources": [{'name': 'resource1', 'permissions': ['create']},
                                {'name': 'resource2', 'permissions': ['create']},
                                {'name': 'resource3', 'permissions': ['create']}]}
    api_gateway.post('/api/roles', headers=header, content_type='application/json',
                     data=json.dumps(data2_init))
    data = {'id': role_id, 'name': 'role2'}
    response = api_gateway.put(f'/api/roles/{role_id}', headers=header,
                               content_type='application/json', data=json.dumps(data))
    key2 = json.loads(response.get_data(as_text=True))
    expected = dict(data_init)
    expected['id'] = role_id
    assert_role_json_is_equal(key2, expected)


def test_update_role_description_only(api_gateway, token, serverdb):
    data_init = {"name": 'role1', "description": 'desc',
                 "resources": [{'name': 'resource1', 'permissions': ['create']},
                               {'name': 'resource2', 'permissions': ['create']},
                               {'name': 'resource3', 'permissions': ['create']}]}
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    response = api_gateway.post('/api/roles', headers=header, content_type='application/json',
                                data=json.dumps(data_init))
    key = json.loads(response.get_data(as_text=True))
    role_id = key['id']
    data = {'id': role_id, 'description': 'new_desc'}
    response = api_gateway.put(f'/api/roles/{role_id}', headers=header,
                               content_type='application/json', data=json.dumps(data))
    key = json.loads(response.get_data(as_text=True))
    expected = dict(data_init)
    expected['description'] = 'new_desc'
    expected['id'] = role_id
    assert_role_json_is_equal(key, expected)


def test_update_role_with_resources_put(api_gateway, token, serverdb):
    data_init = {"name": 'role1', "description": 'desc',
                 "resources": [{'name': 'resource1', 'permissions': ['create']},
                               {'name': 'resource2', 'permissions': ['create']},
                               {'name': 'resource3', 'permissions': ['create']}]}
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    response = api_gateway.post('/api/roles', headers=header, content_type='application/json',
                                data=json.dumps(data_init))
    key = json.loads(response.get_data(as_text=True))
    role_id = key['id']
    data = {'id': role_id, 'description': 'new_desc',
            'resources': [{'name': 'resource4', 'permissions': ['create']},
                          {'name': 'resource5', 'permissions': ['create']}]}
    response = api_gateway.put(f'/api/roles/{role_id}', headers=header,
                               content_type='application/json', data=json.dumps(data))
    assert response.status_code == 200
    expected = dict(data_init)
    expected['description'] = 'new_desc'
    expected['id'] = role_id
    expected['resources'] = [{'name': 'resource4', 'permissions': ['create']},
                             {'name': 'resource5', 'permissions': ['create']}]


def test_update_role_with_resources_permissions(api_gateway, token, serverdb):
    data_init = {"name": 'role1', "description": 'desc',
                 "resources": [{'name': 'resource1', 'permissions': ['create']},
                               {'name': 'resource2', 'permissions': ['create']},
                               {'name': 'resource3', 'permissions': ['create']}]}
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    response = api_gateway.post('/api/roles', headers=header, content_type='application/json',
                                data=json.dumps(data_init))
    key = json.loads(response.get_data(as_text=True))
    role_id = key['id']
    data = {'id': role_id, 'description': 'new_desc',
            'resources': [{'name': 'resource4', 'permissions': ['read']},
                          {'name': 'resource5', 'permissions': ['delete']}]}
    response = api_gateway.put(f'/api/roles/{role_id}', headers=header,
                               content_type='application/json', data=json.dumps(data))
    key = json.loads(response.get_data(as_text=True))
    expected = dict(data_init)
    expected['description'] = 'new_desc'
    expected['id'] = role_id
    expected['resources'] = [{'name': 'resource4', 'permissions': ['read']},
                             {'name': 'resource5', 'permissions': ['delete']}]
    assert_role_json_is_equal(key, expected)


def test_update_role_with_invalid_id(api_gateway, token, serverdb):
    data = {'id': 404, 'description': 'new_desc', 'resources': [{'name': 'resource1', 'permissions': ['create']},
                                                                {'name': 'resource2', 'permissions': ['create']},
                                                                {'name': 'resource3', 'permissions': ['create']}]}
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    response = api_gateway.put(f'/api/roles/{data["id"]}', headers=header,
                               content_type='application/json', data=json.dumps(data))
    assert response.status_code == 404


def test_update_role_with_resources_updates_resource_roles(api_gateway, token, serverdb):
    resources = [{'name': 'resource1', 'permissions': ['create']},
                 {'name': 'resource2', 'permissions': ['create']},
                 {'name': 'resource3', 'permissions': ['create']}]
    data_init = {"name": 'role1', "description": 'desc', "resources": resources}
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    response = api_gateway.post('/api/roles', headers=header, content_type='application/json',
                                data=json.dumps(data_init))
    key = json.loads(response.get_data(as_text=True))
    role_id = key['id']
    data = {'id': role_id, 'description': 'new_desc',
            'resources': [{'name': 'resource4', 'permissions': ['create']},
                          {'name': 'resource5', 'permissions': ['create']},
                          {'name': '/roles', 'permissions': ['create']}]}
    api_gateway.put(f'/api/roles/{role_id}', headers=header, content_type='application/json', data=json.dumps(data))
    for resource in resources:
        rsrc = Resource.query.filter_by(name=resource['name']).first()
        assert rsrc is None
    for resource in ['resource4', 'resource5']:
        rsrc = Resource.query.filter_by(name=resource).first()
        assert rsrc is not None


def test_delete_role(api_gateway, token, serverdb):
    data_init = {"name": 'role1', "description": 'desc',
                 "resources": [{'name': 'resource1', 'permissions': ['create']},
                               {'name': 'resource2', 'permissions': ['create']},
                               {'name': 'resource3', 'permissions': ['create']}]}
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    response = api_gateway.post('/api/roles', headers=header, content_type='application/json',
                                data=json.dumps(data_init))
    key = json.loads(response.get_data(as_text=True))
    role_id = key['id']
    response = api_gateway.delete(f'/api/roles/{role_id}', headers=header)
    assert response.status_code == 204


def test_delete_role_does_not_exist(api_gateway, token, serverdb):
    header = {'Authorization': 'Bearer {}'. format(token['access_token'])}
    response = api_gateway.delete('/api/roles/404', headers=header)
    assert response.status_code == 404


def test_delete_role_updates_resource_roles(api_gateway, token, serverdb):
    resources = [{'name': 'resource1', 'permissions': ['create']},
                 {'name': 'resource2', 'permissions': ['create']},
                 {'name': 'resource3', 'permissions': ['create']}]
    data_init = {"name": 'role1', "description": 'desc', "resources": resources}
    header = {'Authorization': 'Bearer {}'. format(token['access_token'])}
    response = api_gateway.post('/api/roles', headers=header, content_type='application/json',
                                                data=json.dumps(data_init))
    key = json.loads(response.get_data(as_text=True))
    role_id = key['id']
    response = api_gateway.delete(f'/api/roles/{role_id}', headers=header)
    assert response.status_code == 204
    role = Role.query.filter_by(id=role_id).first()
    assert role is None
