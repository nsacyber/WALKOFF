import unittest
from server.database import (initialize_page_roles_from_cleared_database, set_urls_for_role, clear_urls_for_role, Role,
                             Page, db, initialize_page_roles_from_database, default_urls)
import server.database
import server.flaskserver


class TestRolesPagesCache(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.context = server.flaskserver.app.test_request_context()
        cls.context.push()
        db.create_all()

    def setUp(self):
        server.database.page_roles = {}

    def tearDown(self):
        db.session.rollback()
        for role in [role for role in Role.query.all() if role.name != 'admin']:
            db.session.delete(role)
        for page in [page for page in Page.query.all() if page.url not in default_urls]:
            db.session.delete(page)
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        initialize_page_roles_from_cleared_database()

    def test_initialize_from_clear_db(self):
        initialize_page_roles_from_cleared_database()
        self.assertDictEqual(server.database.page_roles, {page: {'admin'} for page in default_urls})

    def test_set_urls_for_role_no_urls_in_cache_no_urls_to_add(self):
        set_urls_for_role('role1', [])
        self.assertDictEqual(server.database.page_roles, {})

    def test_set_urls_for_role_no_urls_in_cache_with_urls_to_add(self):
        set_urls_for_role('role1', ['page1', 'page2', 'page3'])
        self.assertDictEqual(server.database.page_roles, {'page1': {'role1'}, 'page2': {'role1'}, 'page3': {'role1'}})

    def test_set_urls_for_roles_urls_in_cache_no_urls_to_add(self):
        starting = {'page1': {'role1'}, 'page2': {'role1'}, 'page3': {'role1'}}
        server.database.page_roles = dict(starting)
        set_urls_for_role('role2', [])
        self.assertDictEqual(server.database.page_roles, starting)

    def test_set_urls_for_roles_urls_in_cache_new_role_no_overlap(self):
        starting = {'page1': {'role1'}, 'page2': {'role1'}, 'page3': {'role1'}}
        server.database.page_roles = dict(starting)
        set_urls_for_role('role2', ['page4', 'page5'])
        starting.update({'page4': {'role2'}, 'page5': {'role2'}})
        self.assertDictEqual(server.database.page_roles, starting)

    def test_set_urls_for_roles_urls_in_cache_new_role_full_overlap(self):
        starting = {'page1': {'role1'}, 'page2': {'role1'}, 'page3': {'role1'}}
        server.database.page_roles = dict(starting)
        set_urls_for_role('role2', ['page1', 'page2', 'page3'])
        for url, roles in starting.items():
            roles.add('role2')
        self.assertDictEqual(server.database.page_roles, starting)

    def test_set_urls_for_roles_urls_in_cache_new_role_some_overlap(self):
        starting = {'page1': {'role1'}, 'page2': {'role1'}, 'page3': {'role1'}}
        server.database.page_roles = dict(starting)
        set_urls_for_role('role2', ['page2', 'page3', 'page4', 'page5'])
        expected = {'page1': {'role1'}, 'page2': {'role1', 'role2'}, 'page3': {'role1', 'role2'},
                    'page4': {'role2'}, 'page5': {'role2'}}
        self.assertDictEqual(server.database.page_roles, expected)

    def test_set_urls_for_roles_urls_in_cache_same_role_no_overlap(self):
        starting = {'page1': {'role1'}, 'page2': {'role1'}, 'page3': {'role1'}}
        server.database.page_roles = dict(starting)
        set_urls_for_role('role1', {'page4', 'page5'})
        starting.update({'page4': {'role1'}, 'page5': {'role1'}})
        self.assertDictEqual(server.database.page_roles, starting)

    def test_set_urls_for_roles_urls_in_cache_same_role_full_overlap(self):
        starting = {'page1': {'role1'}, 'page2': {'role1'}, 'page3': {'role1'}}
        server.database.page_roles = dict(starting)
        set_urls_for_role('role1', ['page1', 'page2', 'page3'])
        self.assertDictEqual(server.database.page_roles, starting)

    def test_set_urls_for_roles_urls_in_cache_same_role_some_overlap(self):
        starting = {'page1': {'role1'}, 'page2': {'role1'}, 'page3': {'role1'}}
        server.database.page_roles = dict(starting)
        set_urls_for_role('role2', ['page2', 'page3', 'page4', 'page5'])
        starting.update({'page4': {'role2'}, 'page5': {'role2'}})
        self.assertDictEqual(server.database.page_roles, starting)

    def test_clear_urls_for_role_no_cached(self):
        clear_urls_for_role('invalid')
        self.assertDictEqual(server.database.page_roles, {})

    def test_clear_urls_for_role_with_cached_role_not_in_cache(self):
        starting = {'page1': {'role1'}, 'page2': {'role1', 'role2'}, 'page3': {'role1', 'role2'},
                    'page4': {'role2'}, 'page5': {'role2'}}
        server.database.page_roles = dict(starting)
        clear_urls_for_role('role3')
        self.assertDictEqual(server.database.page_roles, starting)

    def test_clear_urls_for_role_with_cached_role(self):
        starting = {'page1': {'role1'}, 'page2': {'role1', 'role2'}, 'page3': {'role1', 'role2'},
                    'page4': {'role2'}, 'page5': {'role2'}}
        server.database.page_roles = dict(starting)
        clear_urls_for_role('role2')
        self.assertDictEqual(server.database.page_roles, {'page1': {'role1'}, 'page2': {'role1'}, 'page3': {'role1'},
                                                          'page4': set(), 'page5': set()})

    def test_init_from_database_none_in_database(self):
        initialize_page_roles_from_database()
        for page in default_urls:
            self.assertSetEqual(server.database.page_roles[page], {'admin'})

    def test_init_from_database(self):
        role1 = Role('role1', pages=['page1', 'page2'])
        db.session.add(role1)
        role2 = Role('role2', pages=['page2', 'page3', 'page4'])
        db.session.add(role2)
        role3 = Role('role3', pages=['page4', 'page5'])
        db.session.add(role3)
        db.session.commit()
        initialize_page_roles_from_database()
        expected = {'page1': {'role1'},
                    'page2': {'role1', 'role2'},
                    'page3': {'role2'},
                    'page4': {'role2', 'role3'},
                    'page5': {'role3'}}
        for page in default_urls:
            expected.update({page: {'admin'}})
        self.assertDictEqual(server.database.page_roles, expected)