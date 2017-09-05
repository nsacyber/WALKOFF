import unittest
from server.database import db, Role, Page, default_urls


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
        for page in [page for page in Page.query.all() if page.url not in default_urls]:
            db.session.delete(page)
        db.session.commit()

    def assertRoleConstructionIsCorrect(self, role, name, description='', pages=None):
        self.assertEqual(role.name, name)
        self.assertEqual(role.description, description)
        expected_pages = set(pages) if pages is not None else set()
        self.assertSetEqual({page.url for page in role.pages}, expected_pages)

    def test_pages_init(self):
        page = Page(url='/test/page')
        self.assertEqual(page.url, '/test/page')

    def test_pages_as_json(self):
        page = Page(url='/test/page')
        self.assertDictEqual(page.as_json(), {'url': '/test/page'})

    def test_role_init_default(self):
        role = Role(name='test')
        self.assertRoleConstructionIsCorrect(role, 'test')

    def test_role_init_with_description(self):
        role = Role(name='test', description='desc')
        self.assertRoleConstructionIsCorrect(role, 'test', description='desc')

    def test_role_init_with_pages_none_in_db(self):
        pages = ['page1', 'page2', 'page3']
        role = Role(name='test', pages=pages)
        db.session.add(role)
        self.assertRoleConstructionIsCorrect(role, 'test', pages=pages)
        self.assertSetEqual({page.url for page in Page.query.all()}, set(default_urls) | set(pages))

    def test_role_init_with_some_in_db(self):
        pages = ['page1', 'page2', 'page3']
        db.session.add(Page('page1'))
        role = Role(name='test', pages=pages)
        db.session.add(role)
        self.assertRoleConstructionIsCorrect(role, 'test', pages=pages)
        self.assertSetEqual({page.url for page in Page.query.all()}, set(pages) | set(default_urls))
        for page in (page for page in Page.query.all() if page.url in pages):
            self.assertListEqual([role.name for role in page.roles], ['test'])

    def test_set_pages_to_role_no_pages_to_add(self):
        role = Role(name='test')
        role.set_pages([])
        self.assertListEqual(role.pages, [])

    def test_set_pages_to_role_with_no_pages_and_no_pages_in_db(self):
        role = Role(name='test')
        pages = ['page1', 'page2']
        role.set_pages(pages)
        db.session.add(role)
        self.assertSetEqual({page.url for page in role.pages}, set(pages))
        self.assertEqual({page.url for page in Page.query.all()}, set(pages) | set(default_urls))

    def test_set_pages_to_role_with_no_pages_and_pages_in_db(self):
        role = Role(name='test')
        db.session.add(Page('page1'))
        pages = ['page1', 'page2']
        role.set_pages(pages)
        db.session.add(role)
        self.assertSetEqual({page.url for page in role.pages}, set(pages))
        self.assertEqual({page.url for page in Page.query.all()}, set(pages) | set(default_urls))

    def test_set_pages_to_role_with_existing_pages_with_overlap(self):
        pages = ['page1', 'page2', 'page3']
        role = Role(name='test', pages=pages)
        new_pages = ['page3', 'page4', 'page5']
        role.set_pages(new_pages)
        db.session.add(role)
        self.assertSetEqual({page.url for page in role.pages}, set(new_pages))
        self.assertEqual({page.url for page in Page.query.all()}, set(new_pages) | set(default_urls))

    def test_set_pages_to_role_shared_pages(self):
        pages1 = ['page1', 'page2', 'page3', 'page4']
        overlap_pages = ['page3', 'page4']
        pages2 = ['page3', 'page4', 'page5', 'page6']
        role1 = Role(name='test1', pages=pages1)
        db.session.add(role1)
        role2 = Role(name='test2', pages=pages2)
        db.session.add(role2)
        db.session.commit()
        self.assertSetEqual({page.url for page in role1.pages}, set(pages1))
        self.assertSetEqual({page.url for page in role2.pages}, set(pages2))

        def assert_pages_have_correct_roles(pages, roles):
            for page in pages:
                page = Page.query.filter_by(url=page).first()
                self.assertSetEqual({role.name for role in page.roles}, roles)

        assert_pages_have_correct_roles(['page1', 'page2'], {'test1'})
        assert_pages_have_correct_roles(overlap_pages, {'test1', 'test2'})
        assert_pages_have_correct_roles(['page5', 'page6'], {'test2'})

    def test_page_as_json_with_multiple_roles(self):
        pages1 = ['page1', 'page2', 'page3', 'page4']
        overlap_pages = ['page3', 'page4']
        pages2 = ['page3', 'page4', 'page5', 'page6']
        role1 = Role(name='test1', pages=pages1)
        db.session.add(role1)
        role2 = Role(name='test2', pages=pages2)
        db.session.add(role2)
        db.session.commit()

        def assert_page_json_is_correct(pages, roles):
            for page in pages:
                page_json = Page.query.filter_by(url=page).first().as_json(with_roles=True)
                self.assertEqual(page_json['url'], page)
                self.assertSetEqual(set(page_json['roles']), roles)

        assert_page_json_is_correct(['page1', 'page2'], {'test1'})
        assert_page_json_is_correct(overlap_pages, {'test1', 'test2'})
        assert_page_json_is_correct(['page5', 'page6'], {'test2'})

    def test_role_as_json(self):
        pages = ['page1', 'page2', 'page3']
        role = Role(name='test', description='desc', pages=pages)
        role_json = role.as_json()
        self.assertSetEqual(set(role_json.keys()), {'name', 'description', 'pages', 'id'})
        self.assertEqual(role_json['name'], 'test')
        self.assertEqual(role_json['description'], 'desc')
        self.assertSetEqual(set(role_json['pages']), set(pages))
