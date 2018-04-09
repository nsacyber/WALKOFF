import unittest

from tests.util import execution_db_help
from walkoff.serverdb import db, Role, Resource, default_resources, initialize_default_resources_admin
import walkoff.config
import tests.config


class TestRoles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        walkoff.config.Config.load_config(tests.config)

        from flask import current_app
        cls.context = current_app.test_request_context()
        cls.context.push()

        execution_db_help.setup_dbs()

        initialize_default_resources_admin()
        db.create_all()

    @classmethod
    def tearDownClass(cls):
        execution_db_help.tear_down_execution_db()

    def tearDown(self):
        db.session.rollback()
        for role in [role for role in Role.query.all() if role.name != 'admin' and role.name != 'guest']:
            db.session.delete(role)
        for resource in [resource for resource in Resource.query.all() if
                         resource.name not in default_resources]:
            db.session.delete(resource)
        db.session.commit()

    def assertRoleConstructionIsCorrect(self, role, name, description='', resources=None):
        self.assertEqual(role.name, name)
        self.assertEqual(role.description, description)

        if resources:
            role = role.as_json()
            expected_resources = {resource['name']: resource['permissions'] for resource in resources}
            response_resources = {resource['name']: resource['permissions'] for resource in role['resources']}
            self.assertDictEqual(expected_resources, response_resources)

    def test_resources_init(self):
        resource = Resource(name='/test/resource', permissions=['create'])
        self.assertEqual(resource.name, '/test/resource')

    def test_resources_as_json(self):
        resource = Resource(name='/test/resource', permissions=['create'])
        resource_json = resource.as_json()
        resource_json.pop('id')
        self.assertDictEqual(resource_json, {'name': '/test/resource', 'permissions': ['create']})

    def test_role_init_default(self):
        role = Role(name='test')
        self.assertRoleConstructionIsCorrect(role, 'test')

    def test_role_init_with_description(self):
        role = Role(name='test', description='desc')
        self.assertRoleConstructionIsCorrect(role, 'test', description='desc')

    def test_role_init_with_resources_none_in_db(self):
        resources = [{'name': 'resource1', 'permissions': ['create']},
                     {'name': 'resource2', 'permissions': ['create']},
                     {'name': 'resource3', 'permissions': ['create']}]
        role = Role(name='test', resources=resources)
        db.session.add(role)
        self.assertRoleConstructionIsCorrect(role, 'test', resources=resources)

    def test_set_resources_to_role_no_resources_to_add(self):
        role = Role(name='test')
        role.set_resources({})
        self.assertListEqual(role.resources, [])

    def test_set_resources_to_role_with_no_resources_and_no_resources_in_db(self):
        role = Role(name='test')
        resources = [{'name': 'resource1', 'permissions': ['create']},
                     {'name': 'resource2', 'permissions': ['create']}]
        role.set_resources(resources)
        db.session.add(role)
        self.assertRoleConstructionIsCorrect(role, 'test', resources=resources)

    def test_set_resources_to_role_with_no_resources_and_resources_in_db(self):
        role = Role(name='test')
        db.session.add(Resource('resource1', permissions=['create']))
        resources = [{'name': 'resource1', 'permissions': ['create']},
                     {'name': 'resource2', 'permissions': ['create']}]
        role.set_resources(resources)
        db.session.add(role)
        self.assertRoleConstructionIsCorrect(role, 'test', resources=resources)

    def test_set_resources_to_role_with_existing_resources_with_overlap(self):
        resources = [{'name': 'resource1', 'permissions': ['create']},
                     {'name': 'resource2', 'permissions': ['create']},
                     {'name': 'resource3', 'permissions': ['create']}]
        role = Role(name='test', resources=resources)
        new_resources = [{'name': 'resource3', 'permissions': ['create']},
                         {'name': 'resource4', 'permissions': ['create']},
                         {'name': 'resource5', 'permissions': ['create']}]
        role.set_resources(new_resources)
        db.session.add(role)
        self.assertRoleConstructionIsCorrect(role, 'test', resources=new_resources)

    def test_set_resources_to_role_with_existing_resources_no_overlap(self):
        resources = [{'name': 'resource1', 'permissions': ['create']},
                     {'name': 'resource2', 'permissions': ['create']},
                     {'name': 'resource3', 'permissions': ['create']}]
        role = Role(name='test', resources=resources)
        new_resources = [{'name': 'resource4', 'permissions': ['create']},
                         {'name': 'resource5', 'permissions': ['create']},
                         {'name': 'resource6', 'permissions': ['create']}]
        role.set_resources(new_resources)
        db.session.add(role)
        self.assertRoleConstructionIsCorrect(role, 'test', resources=new_resources)

    def test_set_resources_update_permissions(self):
        resources = [{'name': 'resource1', 'permissions': ['create']},
                     {'name': 'resource2', 'permissions': ['create']},
                     {'name': 'resource3', 'permissions': ['create']}]
        role = Role(name='test', resources=resources)
        db.session.add(role)
        db.session.commit()
        new_resources = [{'name': 'resource1', 'permissions': ['read']},
                         {'name': 'resource2', 'permissions': ['update']},
                         {'name': 'resource3', 'permissions': ['delete']}]
        role.set_resources(new_resources)
        db.session.commit()
        self.assertRoleConstructionIsCorrect(role, 'test', resources=new_resources)

    def test_role_as_json(self):
        resources = [{'name': 'resource1', 'permissions': ['create']},
                     {'name': 'resource2', 'permissions': ['create']},
                     {'name': 'resource3', 'permissions': ['create']}]
        role = Role(name='test', description='desc', resources=resources)
        role_json = role.as_json()
        self.assertSetEqual(set(role_json.keys()), {'name', 'description', 'resources', 'id'})
        self.assertEqual(role_json['name'], 'test')
        self.assertEqual(role_json['description'], 'desc')
        self.assertEqual(len(role_json['resources']), len(resources))
