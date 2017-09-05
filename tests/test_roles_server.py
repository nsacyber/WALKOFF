from server.database import Role, db, initialize_page_roles_from_cleared_database, default_urls
import server.database
from tests.util import servertestcase
from server.returncodes import *

import json


class TestRolesServer(servertestcase.ServerTestCase):

    def setUp(self):
        server.database.page_roles = {}

    def tearDown(self):
        db.session.rollback()
        for role in [role for role in Role.query.all() if role.name != 'admin']:
            db.session.delete(role)
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        initialize_page_roles_from_cleared_database()

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
        self.assertSetEqual(set(role['pages']), set(expected['pages']))

    def test_create_role(self):
        pages = ['page1', 'page2', 'page3']
        data = {"name": 'role1', "description": 'desc', "pages": pages}
        response = self.put_with_status_check('/api/roles', headers=self.headers, status_code=OBJECT_CREATED,
                                              content_type='application/json', data=json.dumps(data))
        self.assertIn('id', response)
        for page in pages:
            self.assertSetEqual(set(server.database.page_roles[page]), {'role1'})
        data['id'] = response['id']
        self.assertRoleJsonIsEqual(response, data)

    def test_create_role_with_roles_in_urls(self):
        pages = ['page1', 'page2', 'page3', '/roles']
        data = {"name": 'role1', "description": 'desc', "pages": pages}
        response = self.put_with_status_check('/api/roles', headers=self.headers, status_code=OBJECT_CREATED,
                                              content_type='application/json', data=json.dumps(data))
        self.assertIn('id', response)
        reduced_pages = ['page1', 'page2', 'page3']
        for page in reduced_pages:
            self.assertSetEqual(set(server.database.page_roles[page]), {'role1'})
        data['id'] = response['id']
        data['pages'] = reduced_pages
        self.assertRoleJsonIsEqual(response, data)

    def test_create_role_name_already_exists(self):
        data = {"name": 'role1'}
        self.app.put('/api/roles', headers=self.headers, content_type='application/json', data=json.dumps(data))
        self.put_with_status_check('/api/roles', headers=self.headers, status_code=OBJECT_EXISTS_ERROR,
                                   content_type='application/json', data=json.dumps(data))

    def test_read_role(self):
        data = {"name": 'role1', "description": 'desc', "pages": ['page1', 'page2', 'page3']}
        response = json.loads(self.app.put('/api/roles', headers=self.headers, content_type='application/json',
                                           data=json.dumps(data)).get_data(as_text=True))
        role_id = response['id']
        response = self.get_with_status_check('/api/roles/{}'.format(role_id), headers=self.headers)
        data['id'] = role_id
        self.assertRoleJsonIsEqual(response, data)

    def test_read_role_does_not_exist(self):
        self.get_with_status_check('/api/roles/404', headers=self.headers, status_code=OBJECT_DNE_ERROR)

    def test_update_role_name_only(self):
        data_init = {"name": 'role1', "description": 'desc', "pages": ['page1', 'page2', 'page3']}
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
        data_init = {"name": 'role1', "description": 'desc', "pages": ['page1', 'page2', 'page3']}
        response = json.loads(self.app.put('/api/roles', headers=self.headers, content_type='application/json',
                                           data=json.dumps(data_init)).get_data(as_text=True))
        role_id = response['id']
        data2_init = {"name": 'role2', "description": 'desc', "pages": ['page1', 'page2', 'page3']}
        self.app.put('/api/roles', headers=self.headers, content_type='application/json', data=json.dumps(data2_init))
        data = {'id': role_id, 'name': 'role2'}
        response = self.post_with_status_check('/api/roles', headers=self.headers, status_code=SUCCESS,
                                               content_type='application/json', data=json.dumps(data))
        expected = dict(data_init)
        expected['id'] = role_id
        self.assertRoleJsonIsEqual(response, expected)

    def test_update_role_description_only(self):
        data_init = {"name": 'role1', "description": 'desc', "pages": ['page1', 'page2', 'page3']}
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

    def test_update_role_with_pages(self):
        data_init = {"name": 'role1', "description": 'desc', "pages": ['page1', 'page2', 'page3']}
        response = json.loads(self.app.put('/api/roles', headers=self.headers, content_type='application/json',
                                           data=json.dumps(data_init)).get_data(as_text=True))
        role_id = response['id']
        data = {'id': role_id, 'description': 'new_desc', 'pages': ['page4', 'page5']}
        response = self.post_with_status_check('/api/roles', headers=self.headers, status_code=SUCCESS,
                                               content_type='application/json', data=json.dumps(data))
        expected = dict(data_init)
        expected['description'] = 'new_desc'
        expected['id'] = role_id
        expected['pages'] = ['page4', 'page5']
        self.assertRoleJsonIsEqual(response, expected)

    def test_update_role_with_roles_endpoint_in_pages(self):
        data_init = {"name": 'role1', "description": 'desc', "pages": ['page1', 'page2', 'page3']}
        response = json.loads(self.app.put('/api/roles', headers=self.headers, content_type='application/json',
                                           data=json.dumps(data_init)).get_data(as_text=True))
        role_id = response['id']
        data = {'id': role_id, 'description': 'new_desc', 'pages': ['page4', 'page5', '/roles']}
        response = self.post_with_status_check('/api/roles', headers=self.headers, status_code=SUCCESS,
                                               content_type='application/json', data=json.dumps(data))
        expected = dict(data_init)
        expected['description'] = 'new_desc'
        expected['id'] = role_id
        expected['pages'] = ['page4', 'page5']
        self.assertRoleJsonIsEqual(response, expected)

    def test_update_role_with_invalid_id(self):
        data = {'id': 404, 'description': 'new_desc', 'pages': ['page4', 'page5', '/roles']}
        self.post_with_status_check('/api/roles', headers=self.headers, status_code=OBJECT_DNE_ERROR,
                                               content_type='application/json', data=json.dumps(data))

    def test_update_role_with_pages_updates_page_roles(self):
        pages = ['page1', 'page2', 'page3']
        data_init = {"name": 'role1', "description": 'desc', "pages": pages}
        response = json.loads(self.app.put('/api/roles', headers=self.headers, content_type='application/json',
                                           data=json.dumps(data_init)).get_data(as_text=True))
        role_id = response['id']
        data = {'id': role_id, 'description': 'new_desc', 'pages': ['page4', 'page5', '/roles']}
        self.app.post('/api/roles', headers=self.headers, content_type='application/json', data=json.dumps(data))
        for page in pages:
            self.assertNotIn('role1', server.database.page_roles[page])
        for page in ['page4', 'page5']:
            self.assertIn('role1', server.database.page_roles[page])

    def test_delete_role(self):
        data_init = {"name": 'role1', "description": 'desc', "pages": ['page1', 'page2', 'page3']}
        response = json.loads(self.app.put('/api/roles', headers=self.headers, content_type='application/json',
                                           data=json.dumps(data_init)).get_data(as_text=True))
        role_id = response['id']
        self.delete_with_status_check('/api/roles/{}'.format(role_id), headers=self.headers, status_code=SUCCESS)

    def test_delete_role_does_not_exist(self):
        self.delete_with_status_check('/api/roles/404', headers=self.headers, status_code=OBJECT_DNE_ERROR)

    def test_delete_role_updates_page_roles(self):
        pages = ['page1', 'page2', 'page3']
        data_init = {"name": 'role1', "description": 'desc', "pages": pages}
        response = json.loads(self.app.put('/api/roles', headers=self.headers, content_type='application/json',
                                           data=json.dumps(data_init)).get_data(as_text=True))
        role_id = response['id']
        self.delete_with_status_check('/api/roles/{}'.format(role_id), headers=self.headers, status_code=SUCCESS)
        for page in pages:
            self.assertNotIn('role1', server.database.page_roles[page])
