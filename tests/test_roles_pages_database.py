import unittest

from server.database import db, Role, Resource, default_resources, initialize_default_resources_for_admin


class TestRoles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import server.flaskserver
        cls.context = server.flaskserver.app.test_request_context()
        cls.context.push()
        initialize_default_resources_for_admin()
        db.create_all()

    def tearDown(self):
        db.session.rollback()
        for role in [role for role in Role.query.all() if role.name != 'admin']:
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

    # def test_set_resources_to_role_shared_resources(self):
    #     resources1 = ['resource1', 'resource2', 'resource3', 'resource4']
    #     overlap_resources = ['resource3', 'resource4']
    #     resources2 = ['resource3', 'resource4', 'resource5', 'resource6']
    #     role1 = Role(name='test1', resources=resources1)
    #     db.session.add(role1)
    #     role2 = Role(name='test2', resources=resources2)
    #     db.session.add(role2)
    #     db.session.commit()
    #     self.assertSetEqual({resource.resource for resource in role1.resources}, set(resources1))
    #     self.assertSetEqual({resource.resource for resource in role2.resources}, set(resources2))
    #
    #     def assert_resources_have_correct_roles(resources, roles):
    #         for resource in resources:
    #             resource = Resource.query.filter_by(resource=resource).first()
    #             self.assertSetEqual({role.name for role in resource.roles}, roles)
    #
    #     assert_resources_have_correct_roles(['resource1', 'resource2'], {'test1'})
    #     assert_resources_have_correct_roles(overlap_resources, {'test1', 'test2'})
    #     assert_resources_have_correct_roles(['resource5', 'resource6'], {'test2'})

    # def test_resource_as_json_with_multiple_roles(self):
    #     resources1 = {'resource1': ['create'],
    #                   'resource2': ['create'],
    #                   'resource3': ['create'],
    #                   'resource4': ['create']}
    #     overlap_resources = ['resource3', 'resource4']
    #     resources2 = {'resource3': ['create'],
    #                   'resource4': ['create'],
    #                   'resource5': ['create'],
    #                   'resource6': ['create']}
    #     role1 = Role(name='test1', resources=resources1)
    #     db.session.add(role1)
    #     role2 = Role(name='test2', resources=resources2)
    #     db.session.add(role2)
    #     db.session.commit()
    #
    #     def assert_resource_json_is_correct(resources, roles):
    #         for resource in resources:
    #             resource_json = Resource.query.filter_by(name=resource).first().as_json(with_roles=True)
    #             self.assertEqual(resource_json['resource'], resource)
    #             self.assertSetEqual(set(resource_json['roles']), roles)
    #
    #     assert_resource_json_is_correct(['resource1', 'resource2'], {'test1'})
    #     assert_resource_json_is_correct(overlap_resources, {'test1', 'test2'})
    #     assert_resource_json_is_correct(['resource5', 'resource6'], {'test2'})

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
