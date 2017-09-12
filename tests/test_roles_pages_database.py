import unittest
from server.database import db, Role, ResourcePermission, default_resources


class TestRoles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import server.flaskserver
        cls.context = server.flaskserver.app.test_request_context()
        cls.context.push()
        db.create_all()

    def tearDown(self):
        db.session.rollback()
        for role in [role for role in Role.query.all() if role.name != 'admin']:
            db.session.delete(role)
        for resource in [resource for resource in ResourcePermission.query.all() if resource.resource not in default_resources]:
            db.session.delete(resource)
        db.session.commit()

    def assertRoleConstructionIsCorrect(self, role, name, description='', resources=None):
        self.assertEqual(role.name, name)
        self.assertEqual(role.description, description)
        expected_resources = set(resources) if resources is not None else set()
        self.assertSetEqual({resource.resource for resource in role.resources}, expected_resources)

    def test_resources_init(self):
        resource = ResourcePermission(resource='/test/resource')
        self.assertEqual(resource.resource, '/test/resource')

    def test_resources_as_json(self):
        resource = ResourcePermission(resource='/test/resource')
        self.assertDictEqual(resource.as_json(), {'resource': '/test/resource'})

    def test_role_init_default(self):
        role = Role(name='test')
        self.assertRoleConstructionIsCorrect(role, 'test')

    def test_role_init_with_description(self):
        role = Role(name='test', description='desc')
        self.assertRoleConstructionIsCorrect(role, 'test', description='desc')

    def test_role_init_with_resources_none_in_db(self):
        resources = ['resource1', 'resource2', 'resource3']
        role = Role(name='test', resources=resources)
        db.session.add(role)
        self.assertRoleConstructionIsCorrect(role, 'test', resources=resources)
        self.assertSetEqual({resource.resource for resource in ResourcePermission.query.all()}, set(default_resources) | set(resources))

    def test_role_init_with_some_in_db(self):
        resources = ['resource1', 'resource2', 'resource3']
        db.session.add(ResourcePermission('resource1'))
        role = Role(name='test', resources=resources)
        db.session.add(role)
        self.assertRoleConstructionIsCorrect(role, 'test', resources=resources)
        self.assertSetEqual({resource.resource for resource in ResourcePermission.query.all()}, set(resources) | set(default_resources))
        for resource in (resource for resource in ResourcePermission.query.all() if resource.resource in resources):
            self.assertListEqual([role.name for role in resource.roles], ['test'])

    def test_set_resources_to_role_no_resources_to_add(self):
        role = Role(name='test')
        role.set_resources([])
        self.assertListEqual(role.resources, [])

    def test_set_resources_to_role_with_no_resources_and_no_resources_in_db(self):
        role = Role(name='test')
        resources = ['resource1', 'resource2']
        role.set_resources(resources)
        db.session.add(role)
        self.assertSetEqual({resource.resource for resource in role.resources}, set(resources))
        self.assertEqual({resource.resource for resource in ResourcePermission.query.all()}, set(resources) | set(default_resources))

    def test_set_resources_to_role_with_no_resources_and_resources_in_db(self):
        role = Role(name='test')
        db.session.add(ResourcePermission('resource1'))
        resources = ['resource1', 'resource2']
        role.set_resources(resources)
        db.session.add(role)
        self.assertSetEqual({resource.resource for resource in role.resources}, set(resources))
        self.assertEqual({resource.resource for resource in ResourcePermission.query.all()}, set(resources) | set(default_resources))

    def test_set_resources_to_role_with_existing_resources_with_overlap(self):
        resources = ['resource1', 'resource2', 'resource3']
        role = Role(name='test', resources=resources)
        new_resources = ['resource3', 'resource4', 'resource5']
        role.set_resources(new_resources)
        db.session.add(role)
        self.assertSetEqual({resource.resource for resource in role.resources}, set(new_resources))
        self.assertEqual({resource.resource for resource in ResourcePermission.query.all()}, set(new_resources) | set(default_resources))

    def test_set_resources_to_role_shared_resources(self):
        resources1 = ['resource1', 'resource2', 'resource3', 'resource4']
        overlap_resources = ['resource3', 'resource4']
        resources2 = ['resource3', 'resource4', 'resource5', 'resource6']
        role1 = Role(name='test1', resources=resources1)
        db.session.add(role1)
        role2 = Role(name='test2', resources=resources2)
        db.session.add(role2)
        db.session.commit()
        self.assertSetEqual({resource.resource for resource in role1.resources}, set(resources1))
        self.assertSetEqual({resource.resource for resource in role2.resources}, set(resources2))

        def assert_resources_have_correct_roles(resources, roles):
            for resource in resources:
                resource = ResourcePermission.query.filter_by(resource=resource).first()
                self.assertSetEqual({role.name for role in resource.roles}, roles)

        assert_resources_have_correct_roles(['resource1', 'resource2'], {'test1'})
        assert_resources_have_correct_roles(overlap_resources, {'test1', 'test2'})
        assert_resources_have_correct_roles(['resource5', 'resource6'], {'test2'})

    def test_resource_as_json_with_multiple_roles(self):
        resources1 = ['resource1', 'resource2', 'resource3', 'resource4']
        overlap_resources = ['resource3', 'resource4']
        resources2 = ['resource3', 'resource4', 'resource5', 'resource6']
        role1 = Role(name='test1', resources=resources1)
        db.session.add(role1)
        role2 = Role(name='test2', resources=resources2)
        db.session.add(role2)
        db.session.commit()

        def assert_resource_json_is_correct(resources, roles):
            for resource in resources:
                resource_json = ResourcePermission.query.filter_by(resource=resource).first().as_json(with_roles=True)
                self.assertEqual(resource_json['resource'], resource)
                self.assertSetEqual(set(resource_json['roles']), roles)

        assert_resource_json_is_correct(['resource1', 'resource2'], {'test1'})
        assert_resource_json_is_correct(overlap_resources, {'test1', 'test2'})
        assert_resource_json_is_correct(['resource5', 'resource6'], {'test2'})

    def test_role_as_json(self):
        resources = ['resource1', 'resource2', 'resource3']
        role = Role(name='test', description='desc', resources=resources)
        role_json = role.as_json()
        self.assertSetEqual(set(role_json.keys()), {'name', 'description', 'resources', 'id'})
        self.assertEqual(role_json['name'], 'test')
        self.assertEqual(role_json['description'], 'desc')
        self.assertSetEqual(set(role_json['resources']), set(resources))
