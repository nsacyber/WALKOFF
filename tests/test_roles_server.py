import json

import walkoff.server.flaskserver
from walkoff.serverdb import Role, Resource, default_resources
from walkoff.extensions import db
from walkoff.server.returncodes import *
from tests.util import servertestcase


class TestRolesServer(servertestcase.ServerTestCase):
    def tearDown(self):
        db.session.rollback()
        for role in [role for role in Role.query.all() if role.name != 'admin' and role.name != 'guest']:
            db.session.delete(role)
        for resource in [resource for resource in Resource.query.all() if
                         resource.name not in default_resources]:
            db.session.delete(resource)
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        walkoff.server.flaskserver.running_context.controller.shutdown_pool()

    def test_read_all_roles_no_added_roles(self):
        response = self.get_with_status_check('/api/roles', headers=self.headers, status_code=SUCCESS)
        self.assertEqual([role['name'] for role in response], ['admin', 'guest'])

    def test_read_all_roles_with_extra_added_roles(self):
        role = Role('role1')
        db.session.add(role)
        response = self.get_with_status_check('/api/roles', headers=self.headers, status_code=SUCCESS)
        self.assertSetEqual({role['name'] for role in response}, {'admin', 'role1', 'guest'})

    def assertRoleJsonIsEqual(self, role, expected):
        self.assertEqual(role['id'], expected['id'])
        self.assertEqual(role['name'], expected['name'])
        self.assertEqual(role['description'], expected['description'])

        expected_resources = {resource['name']: resource['permissions'] for resource in expected['resources']}
        response_resources = {resource['name']: resource['permissions'] for resource in role['resources']}
        self.assertDictEqual(expected_resources, response_resources)

    def test_create_role(self):
        resources = [{'name': 'resource1', 'permissions': ['create']},
                     {'name': 'resource2', 'permissions': ['create']},
                     {'name': 'resource3', 'permissions': ['create']}]
        data = {"name": 'role1', "description": 'desc', "resources": resources}
        response = self.put_with_status_check('/api/roles', headers=self.headers, status_code=OBJECT_CREATED,
                                              content_type='application/json', data=json.dumps(data))
        self.assertIn('id', response)
        data['id'] = response['id']
        self.assertRoleJsonIsEqual(response, data)

    def test_create_role_name_already_exists(self):
        data = {"name": 'role1'}
        self.app.put('/api/roles', headers=self.headers, content_type='application/json', data=json.dumps(data))
        self.put_with_status_check('/api/roles', headers=self.headers, status_code=OBJECT_EXISTS_ERROR,
                                   content_type='application/json', data=json.dumps(data))

    def test_read_role(self):
        data = {"name": 'role1', "description": 'desc', "resources": [{'name': 'resource1', 'permissions': ['create']},
                                                                      {'name': 'resource2', 'permissions': ['create']},
                                                                      {'name': 'resource3', 'permissions': ['create']}]}
        response = json.loads(self.app.put('/api/roles', headers=self.headers, content_type='application/json',
                                           data=json.dumps(data)).get_data(as_text=True))
        role_id = response['id']
        response = self.get_with_status_check('/api/roles/{}'.format(role_id), headers=self.headers)
        data['id'] = role_id
        self.assertRoleJsonIsEqual(response, data)

    def test_read_role_does_not_exist(self):
        self.get_with_status_check('/api/roles/404', headers=self.headers, status_code=OBJECT_DNE_ERROR)

    def test_update_role_name_only(self):
        data_init = {"name": 'role1', "description": 'desc',
                     "resources": [{'name': 'resource1', 'permissions': ['create']},
                                   {'name': 'resource2', 'permissions': ['create']},
                                   {'name': 'resource3', 'permissions': ['create']}]}
        response = json.loads(self.app.put('/api/roles', headers=self.headers, content_type='application/json',
                                           data=json.dumps(data_init)).get_data(as_text=True))
        role_id = response['id']
        data = {'id': role_id, 'name': 'renamed'}
        response = self.post_with_status_check('/api/roles', headers=self.headers, status_code=SUCCESS,
                                               content_type='application/json', data=json.dumps(data))
        expected = dict(data_init)
        expected['name'] = 'renamed'
        expected['id'] = role_id
        self.assertRoleJsonIsEqual(response, expected)

    def test_update_role_name_only_already_exists(self):
        data_init = {"name": 'role1', "description": 'desc',
                     "resources": [{'name': 'resource1', 'permissions': ['create']},
                                   {'name': 'resource2', 'permissions': ['create']},
                                   {'name': 'resource3', 'permissions': ['create']}]}
        response = json.loads(self.app.put('/api/roles', headers=self.headers, content_type='application/json',
                                           data=json.dumps(data_init)).get_data(as_text=True))
        role_id = response['id']
        data2_init = {"name": 'role2', "description": 'desc',
                      "resources": [{'name': 'resource1', 'permissions': ['create']},
                                    {'name': 'resource2', 'permissions': ['create']},
                                    {'name': 'resource3', 'permissions': ['create']}]}
        self.app.put('/api/roles', headers=self.headers, content_type='application/json', data=json.dumps(data2_init))
        data = {'id': role_id, 'name': 'role2'}
        response = self.post_with_status_check('/api/roles', headers=self.headers, status_code=SUCCESS,
                                               content_type='application/json', data=json.dumps(data))
        expected = dict(data_init)
        expected['id'] = role_id
        self.assertRoleJsonIsEqual(response, expected)

    def test_update_role_description_only(self):
        data_init = {"name": 'role1', "description": 'desc',
                     "resources": [{'name': 'resource1', 'permissions': ['create']},
                                   {'name': 'resource2', 'permissions': ['create']},
                                   {'name': 'resource3', 'permissions': ['create']}]}
        response = json.loads(self.app.put('/api/roles', headers=self.headers, content_type='application/json',
                                           data=json.dumps(data_init)).get_data(as_text=True))
        role_id = response['id']
        data = {'id': role_id, 'description': 'new_desc'}
        response = self.post_with_status_check('/api/roles', headers=self.headers, status_code=SUCCESS,
                                               content_type='application/json', data=json.dumps(data))
        expected = dict(data_init)
        expected['description'] = 'new_desc'
        expected['id'] = role_id
        self.assertRoleJsonIsEqual(response, expected)

    def test_update_role_with_resources(self):
        data_init = {"name": 'role1', "description": 'desc',
                     "resources": [{'name': 'resource1', 'permissions': ['create']},
                                   {'name': 'resource2', 'permissions': ['create']},
                                   {'name': 'resource3', 'permissions': ['create']}]}
        response = json.loads(self.app.put('/api/roles', headers=self.headers, content_type='application/json',
                                           data=json.dumps(data_init)).get_data(as_text=True))
        role_id = response['id']
        data = {'id': role_id, 'description': 'new_desc',
                'resources': [{'name': 'resource4', 'permissions': ['create']},
                              {'name': 'resource5', 'permissions': ['create']}]}
        response = self.post_with_status_check('/api/roles', headers=self.headers, status_code=SUCCESS,
                                               content_type='application/json', data=json.dumps(data))
        expected = dict(data_init)
        expected['description'] = 'new_desc'
        expected['id'] = role_id
        expected['resources'] = [{'name': 'resource4', 'permissions': ['create']},
                                 {'name': 'resource5', 'permissions': ['create']}]
        self.assertRoleJsonIsEqual(response, expected)

    def test_update_role_with_resources_permissions(self):
        data_init = {"name": 'role1', "description": 'desc',
                     "resources": [{'name': 'resource1', 'permissions': ['create']},
                                   {'name': 'resource2', 'permissions': ['create']},
                                   {'name': 'resource3', 'permissions': ['create']}]}
        response = json.loads(self.app.put('/api/roles', headers=self.headers, content_type='application/json',
                                           data=json.dumps(data_init)).get_data(as_text=True))
        role_id = response['id']
        data = {'id': role_id, 'description': 'new_desc',
                'resources': [{'name': 'resource4', 'permissions': ['read']},
                              {'name': 'resource5', 'permissions': ['delete']}]}
        response = self.post_with_status_check('/api/roles', headers=self.headers, status_code=SUCCESS,
                                               content_type='application/json', data=json.dumps(data))
        expected = dict(data_init)
        expected['description'] = 'new_desc'
        expected['id'] = role_id
        expected['resources'] = [{'name': 'resource4', 'permissions': ['read']},
                                 {'name': 'resource5', 'permissions': ['delete']}]
        self.assertRoleJsonIsEqual(response, expected)

    def test_update_role_with_invalid_id(self):
        data = {'id': 404, 'description': 'new_desc', 'resources': [{'name': 'resource1', 'permissions': ['create']},
                                                                    {'name': 'resource2', 'permissions': ['create']},
                                                                    {'name': 'resource3', 'permissions': ['create']}]}
        self.post_with_status_check('/api/roles', headers=self.headers, status_code=OBJECT_DNE_ERROR,
                                    content_type='application/json', data=json.dumps(data))

    def test_update_role_with_resources_updates_resource_roles(self):
        resources = [{'name': 'resource1', 'permissions': ['create']},
                     {'name': 'resource2', 'permissions': ['create']},
                     {'name': 'resource3', 'permissions': ['create']}]
        data_init = {"name": 'role1', "description": 'desc', "resources": resources}
        response = json.loads(self.app.put('/api/roles', headers=self.headers, content_type='application/json',
                                           data=json.dumps(data_init)).get_data(as_text=True))
        role_id = response['id']
        data = {'id': role_id, 'description': 'new_desc',
                'resources': [{'name': 'resource4', 'permissions': ['create']},
                              {'name': 'resource5', 'permissions': ['create']},
                              {'name': '/roles', 'permissions': ['create']}]}
        self.app.post('/api/roles', headers=self.headers, content_type='application/json', data=json.dumps(data))
        for resource in resources:
            rsrc = Resource.query.filter_by(name=resource['name']).first()
            self.assertIsNone(rsrc)
        for resource in ['resource4', 'resource5']:
            rsrc = Resource.query.filter_by(name=resource).first()
            self.assertIsNotNone(rsrc)

    def test_delete_role(self):
        data_init = {"name": 'role1', "description": 'desc',
                     "resources": [{'name': 'resource1', 'permissions': ['create']},
                                   {'name': 'resource2', 'permissions': ['create']},
                                   {'name': 'resource3', 'permissions': ['create']}]}
        response = json.loads(self.app.put('/api/roles', headers=self.headers, content_type='application/json',
                                           data=json.dumps(data_init)).get_data(as_text=True))
        role_id = response['id']
        self.delete_with_status_check('/api/roles/{}'.format(role_id), headers=self.headers, status_code=SUCCESS)

    def test_delete_role_does_not_exist(self):
        self.delete_with_status_check('/api/roles/404', headers=self.headers, status_code=OBJECT_DNE_ERROR)

    def test_delete_role_updates_resource_roles(self):
        resources = [{'name': 'resource1', 'permissions': ['create']},
                     {'name': 'resource2', 'permissions': ['create']},
                     {'name': 'resource3', 'permissions': ['create']}]
        data_init = {"name": 'role1', "description": 'desc', "resources": resources}
        response = json.loads(self.app.put('/api/roles', headers=self.headers, content_type='application/json',
                                           data=json.dumps(data_init)).get_data(as_text=True))
        role_id = response['id']
        self.delete_with_status_check('/api/roles/{}'.format(role_id), headers=self.headers, status_code=SUCCESS)
        role = Role.query.filter_by(id=role_id).first()
        self.assertIsNone(role)
