import unittest

import server.database
import server.flaskserver
from server.database import (initialize_resource_roles_from_cleared_database, set_resources_for_role,
                             clear_resources_for_role, Role, ResourceType, db,
                             initialize_resource_roles_from_database, default_resources)


class TestRolesPagesCache(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = server.flaskserver.app.test_request_context()
        cls.context.push()
        db.create_all()

    def setUp(self):
        server.database.resource_roles = {}

    def tearDown(self):
        db.session.rollback()
        for role in [role for role in Role.query.all() if role.name != 'admin']:
            db.session.delete(role)
        for resource in [resource for resource in ResourceType.query.all()
                         if resource.resource not in default_resources]:
            db.session.delete(resource)
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        initialize_resource_roles_from_cleared_database()

    def test_initialize_from_clear_db(self):
        initialize_resource_roles_from_cleared_database()
        self.assertDictEqual(server.database.resource_roles, {resource: {'admin'} for resource in default_resources})

    def test_set_resources_for_role_no_resources_in_cache_no_resources_to_add(self):
        set_resources_for_role('role1', [])
        self.assertDictEqual(server.database.resource_roles, {})

    def test_set_resources_for_role_no_resources_in_cache_with_resources_to_add(self):
        set_resources_for_role('role1', ['resource1', 'resource2', 'resource3'])
        self.assertDictEqual(server.database.resource_roles,
                             {'resource1': {'role1'}, 'resource2': {'role1'}, 'resource3': {'role1'}})

    def test_set_resources_for_roles_resources_in_cache_no_resources_to_add(self):
        starting = {'resource1': {'role1'}, 'resource2': {'role1'}, 'resource3': {'role1'}}
        server.database.resource_roles = dict(starting)
        set_resources_for_role('role2', [])
        self.assertDictEqual(server.database.resource_roles, starting)

    def test_set_resources_for_roles_resources_in_cache_new_role_no_overlap(self):
        starting = {'resource1': {'role1'}, 'resource2': {'role1'}, 'resource3': {'role1'}}
        server.database.resource_roles = dict(starting)
        set_resources_for_role('role2', ['resource4', 'resource5'])
        starting.update({'resource4': {'role2'}, 'resource5': {'role2'}})
        self.assertDictEqual(server.database.resource_roles, starting)

    def test_set_resources_for_roles_resources_in_cache_new_role_full_overlap(self):
        starting = {'resource1': {'role1'}, 'resource2': {'role1'}, 'resource3': {'role1'}}
        server.database.resource_roles = dict(starting)
        set_resources_for_role('role2', ['resource1', 'resource2', 'resource3'])
        for resource, roles in starting.items():
            roles.add('role2')
        self.assertDictEqual(server.database.resource_roles, starting)

    def test_set_resources_for_roles_resources_in_cache_new_role_some_overlap(self):
        starting = {'resource1': {'role1'}, 'resource2': {'role1'}, 'resource3': {'role1'}}
        server.database.resource_roles = dict(starting)
        set_resources_for_role('role2', ['resource2', 'resource3', 'resource4', 'resource5'])
        expected = {'resource1': {'role1'}, 'resource2': {'role1', 'role2'}, 'resource3': {'role1', 'role2'},
                    'resource4': {'role2'}, 'resource5': {'role2'}}
        self.assertDictEqual(server.database.resource_roles, expected)

    def test_set_resources_for_roles_resources_in_cache_same_role_no_overlap(self):
        starting = {'resource1': {'role1'}, 'resource2': {'role1'}, 'resource3': {'role1'}}
        server.database.resource_roles = dict(starting)
        set_resources_for_role('role1', {'resource4', 'resource5'})
        starting.update({'resource4': {'role1'}, 'resource5': {'role1'}})
        self.assertDictEqual(server.database.resource_roles, starting)

    def test_set_resources_for_roles_resources_in_cache_same_role_full_overlap(self):
        starting = {'resource1': {'role1'}, 'resource2': {'role1'}, 'resource3': {'role1'}}
        server.database.resource_roles = dict(starting)
        set_resources_for_role('role1', ['resource1', 'resource2', 'resource3'])
        self.assertDictEqual(server.database.resource_roles, starting)

    def test_set_resources_for_roles_resources_in_cache_same_role_some_overlap(self):
        starting = {'resource1': {'role1'}, 'resource2': {'role1'}, 'resource3': {'role1'}}
        server.database.resource_roles = dict(starting)
        set_resources_for_role('role2', ['resource2', 'resource3', 'resource4', 'resource5'])
        starting.update({'resource4': {'role2'}, 'resource5': {'role2'}})
        self.assertDictEqual(server.database.resource_roles, starting)

    def test_clear_resources_for_role_no_cached(self):
        clear_resources_for_role('invalid')
        self.assertDictEqual(server.database.resource_roles, {})

    def test_clear_resources_for_role_with_cached_role_not_in_cache(self):
        starting = {'resource1': {'role1'}, 'resource2': {'role1', 'role2'}, 'resource3': {'role1', 'role2'},
                    'resource4': {'role2'}, 'resource5': {'role2'}}
        server.database.resource_roles = dict(starting)
        clear_resources_for_role('role3')
        self.assertDictEqual(server.database.resource_roles, starting)

    def test_clear_resources_for_role_with_cached_role(self):
        starting = {'resource1': {'role1'}, 'resource2': {'role1', 'role2'}, 'resource3': {'role1', 'role2'},
                    'resource4': {'role2'}, 'resource5': {'role2'}}
        server.database.resource_roles = dict(starting)
        clear_resources_for_role('role2')
        self.assertDictEqual(server.database.resource_roles,
                             {'resource1': {'role1'}, 'resource2': {'role1'}, 'resource3': {'role1'},
                              'resource4': set(), 'resource5': set()})

    def test_init_from_database_none_in_database(self):
        initialize_resource_roles_from_database()
        for resource in default_resources:
            self.assertSetEqual(server.database.resource_roles[resource], {'admin'})

    def test_init_from_database(self):
        role1 = Role('role1', resources=['resource1', 'resource2'])
        db.session.add(role1)
        role2 = Role('role2', resources=['resource2', 'resource3', 'resource4'])
        db.session.add(role2)
        role3 = Role('role3', resources=['resource4', 'resource5'])
        db.session.add(role3)
        db.session.commit()
        initialize_resource_roles_from_database()
        expected = {'resource1': {'role1'},
                    'resource2': {'role1', 'role2'},
                    'resource3': {'role2'},
                    'resource4': {'role2', 'role3'},
                    'resource5': {'role3'}}
        for resource in default_resources:
            expected.update({resource: {'admin'}})
        self.assertDictEqual(server.database.resource_roles, expected)
