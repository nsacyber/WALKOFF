import json

import server.database
from server.database import Role, db, initialize_resource_roles_from_cleared_database
from server.returncodes import *
from tests.util import servertestcase
import server.flaskserver


class TestRolesServer(servertestcase.ServerTestCase):

    def setUp(self):
        server.database.resource_roles = {}

    def tearDown(self):
        db.session.rollback()
        for role in [role for role in Role.query.all() if role.name != 'admin']:
            db.session.delete(role)
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        initialize_resource_roles_from_cleared_database()
        server.flaskserver.running_context.controller.shutdown_pool()

    def test_read_all_roles_no_added_roles(self):
        response = self.get_with_status_check('/api/roles', headers=self.headers, status_code=SUCCESS)
        self.assertEqual([role['name'] for role in response], ['admin'])

    def test_read_all_roles_with_extra_added_roles(self):
        role = Role('role1')
        db.session.add(role)
        response = self.get_with_status_check('/api/roles', headers=self.headers, status_code=SUCCESS)
        self.assertSetEqual({role['name'] for role in response}, {'admin', 'role1'})

    def assertRoleJsonIsEqual(self, role, expected):
        self.assertEqual(role['id'], expected['id'])
        self.assertEqual(role['name'], expected['name'])
        self.assertEqual(role['description'], expected['description'])
        self.assertSetEqual(set(role['resources']), set(expected['resources']))

    def test_create_role(self):
        resources = ['resource1', 'resource2', 'resource3']
        data = {"name": 'role1', "description": 'desc', "resources": resources}
        response = self.put_with_status_check('/api/roles', headers=self.headers, status_code=OBJECT_CREATED,
                                              content_type='application/json', data=json.dumps(data))
        self.assertIn('id', response)
        for resource in resources:
            self.assertSetEqual(set(server.database.resource_roles[resource]), {'role1'})
        data['id'] = response['id']
        self.assertRoleJsonIsEqual(response, data)

    def test_create_role_with_roles_in_urls(self):
        resources = ['resource1', 'resource2', 'resource3', '/roles']
        data = {"name": 'role1', "description": 'desc', "resources": resources}
        response = self.put_with_status_check('/api/roles', headers=self.headers, status_code=OBJECT_CREATED,
                                              content_type='application/json', data=json.dumps(data))
        self.assertIn('id', response)
        reduced_resources = ['resource1', 'resource2', 'resource3']
        for resource in reduced_resources:
            self.assertSetEqual(set(server.database.resource_roles[resource]), {'role1'})
        data['id'] = response['id']
        data['resources'] = reduced_resources
        self.assertRoleJsonIsEqual(response, data)

    def test_create_role_name_already_exists(self):
        data = {"name": 'role1'}
        self.app.put('/api/roles', headers=self.headers, content_type='application/json', data=json.dumps(data))
        self.put_with_status_check('/api/roles', headers=self.headers, status_code=OBJECT_EXISTS_ERROR,
                                   content_type='application/json', data=json.dumps(data))

    def test_read_role(self):
        data = {"name": 'role1', "description": 'desc', "resources": ['resource1', 'resource2', 'resource3']}
        response = json.loads(self.app.put('/api/roles', headers=self.headers, content_type='application/json',
                                           data=json.dumps(data)).get_data(as_text=True))
        role_id = response['id']
        response = self.get_with_status_check('/api/roles/{}'.format(role_id), headers=self.headers)
        data['id'] = role_id
        self.assertRoleJsonIsEqual(response, data)

    def test_read_role_does_not_exist(self):
        self.get_with_status_check('/api/roles/404', headers=self.headers, status_code=OBJECT_DNE_ERROR)

    def test_update_role_name_only(self):
        data_init = {"name": 'role1', "description": 'desc', "resources": ['resource1', 'resource2', 'resource3']}
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
        data_init = {"name": 'role1', "description": 'desc', "resources": ['resource1', 'resource2', 'resource3']}
        response = json.loads(self.app.put('/api/roles', headers=self.headers, content_type='application/json',
                                           data=json.dumps(data_init)).get_data(as_text=True))
        role_id = response['id']
        data2_init = {"name": 'role2', "description": 'desc', "resources": ['resource1', 'resource2', 'resource3']}
        self.app.put('/api/roles', headers=self.headers, content_type='application/json', data=json.dumps(data2_init))
        data = {'id': role_id, 'name': 'role2'}
        response = self.post_with_status_check('/api/roles', headers=self.headers, status_code=SUCCESS,
                                               content_type='application/json', data=json.dumps(data))
        expected = dict(data_init)
        expected['id'] = role_id
        self.assertRoleJsonIsEqual(response, expected)

    def test_update_role_description_only(self):
        data_init = {"name": 'role1', "description": 'desc', "resources": ['resource1', 'resource2', 'resource3']}
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
        data_init = {"name": 'role1', "description": 'desc', "resources": ['resource1', 'resource2', 'resource3']}
        response = json.loads(self.app.put('/api/roles', headers=self.headers, content_type='application/json',
                                           data=json.dumps(data_init)).get_data(as_text=True))
        role_id = response['id']
        data = {'id': role_id, 'description': 'new_desc', 'resources': ['resource4', 'resource5']}
        response = self.post_with_status_check('/api/roles', headers=self.headers, status_code=SUCCESS,
                                               content_type='application/json', data=json.dumps(data))
        expected = dict(data_init)
        expected['description'] = 'new_desc'
        expected['id'] = role_id
        expected['resources'] = ['resource4', 'resource5']
        self.assertRoleJsonIsEqual(response, expected)

    def test_update_role_with_roles_endpoint_in_resources(self):
        data_init = {"name": 'role1', "description": 'desc', "resources": ['resource1', 'resource2', 'resource3']}
        response = json.loads(self.app.put('/api/roles', headers=self.headers, content_type='application/json',
                                           data=json.dumps(data_init)).get_data(as_text=True))
        role_id = response['id']
        data = {'id': role_id, 'description': 'new_desc', 'resources': ['resource4', 'resource5', '/roles']}
        response = self.post_with_status_check('/api/roles', headers=self.headers, status_code=SUCCESS,
                                               content_type='application/json', data=json.dumps(data))
        expected = dict(data_init)
        expected['description'] = 'new_desc'
        expected['id'] = role_id
        expected['resources'] = ['resource4', 'resource5']
        self.assertRoleJsonIsEqual(response, expected)

    def test_update_role_with_invalid_id(self):
        data = {'id': 404, 'description': 'new_desc', 'resources': ['resource4', 'resource5', '/roles']}
        self.post_with_status_check('/api/roles', headers=self.headers, status_code=OBJECT_DNE_ERROR,
                                               content_type='application/json', data=json.dumps(data))

    def test_update_role_with_resources_updates_resource_roles(self):
        resources = ['resource1', 'resource2', 'resource3']
        data_init = {"name": 'role1', "description": 'desc', "resources": resources}
        response = json.loads(self.app.put('/api/roles', headers=self.headers, content_type='application/json',
                                           data=json.dumps(data_init)).get_data(as_text=True))
        role_id = response['id']
        data = {'id': role_id, 'description': 'new_desc', 'resources': ['resource4', 'resource5', '/roles']}
        self.app.post('/api/roles', headers=self.headers, content_type='application/json', data=json.dumps(data))
        for resource in resources:
            self.assertNotIn('role1', server.database.resource_roles[resource])
        for resource in ['resource4', 'resource5']:
            self.assertIn('role1', server.database.resource_roles[resource])

    def test_delete_role(self):
        data_init = {"name": 'role1', "description": 'desc', "resources": ['resource1', 'resource2', 'resource3']}
        response = json.loads(self.app.put('/api/roles', headers=self.headers, content_type='application/json',
                                           data=json.dumps(data_init)).get_data(as_text=True))
        role_id = response['id']
        self.delete_with_status_check('/api/roles/{}'.format(role_id), headers=self.headers, status_code=SUCCESS)

    def test_delete_role_does_not_exist(self):
        self.delete_with_status_check('/api/roles/404', headers=self.headers, status_code=OBJECT_DNE_ERROR)

    def test_delete_role_updates_resource_roles(self):
        resources = ['resource1', 'resource2', 'resource3']
        data_init = {"name": 'role1', "description": 'desc', "resources": resources}
        response = json.loads(self.app.put('/api/roles', headers=self.headers, content_type='application/json',
                                           data=json.dumps(data_init)).get_data(as_text=True))
        role_id = response['id']
        self.delete_with_status_check('/api/roles/{}'.format(role_id), headers=self.headers, status_code=SUCCESS)
        for resource in resources:
            self.assertNotIn('role1', server.database.resource_roles[resource])
