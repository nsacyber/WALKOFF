from unittest import TestCase

from walkoff.appgateway.appcache import AppCacheEntry, FunctionEntry
from walkoff.appgateway.decorators import *


class TestAppCacheEntry(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.action_tag = {WalkoffTag.action}
        cls.condition_tag = {WalkoffTag.condition}
        cls.transform_tag = {WalkoffTag.transform}
        cls.clspath = 'tests.test_app_cache_entry'
        cls.maxDiff = None

    def setUp(self):
        self.entry = AppCacheEntry('app1')

    def assert_entry_has_functions(self, expected_functions, entry=None):
        entry = self.entry if entry is None else entry
        self.assertDictEqual(entry.functions, expected_functions)

    def test_init(self):
        app_name = 'App1'
        cache = AppCacheEntry(app_name)
        self.assertEqual(cache.app_name, app_name)
        self.assertIsNone(cache.main)
        self.assertDictEqual(cache.functions, {})

    def test_cache_action(self):
        def x(): pass

        self.entry.cache_functions([(x, self.action_tag)], self.clspath)
        self.assert_entry_has_functions({'x': FunctionEntry(run=x, is_bound=False, tags=self.action_tag)})

    def test_cache_action_multiple_actions(self):
        def x(): pass

        def y(): pass

        self.entry.cache_functions([(x, self.action_tag), (y, self.action_tag)], self.clspath)
        self.assert_entry_has_functions({'x': FunctionEntry(run=x, is_bound=False, tags=self.action_tag),
                                         'y': FunctionEntry(run=y, is_bound=False, tags=self.action_tag)})

    def test_cache_action_overwrite(self):
        def x(): pass

        original_id = id(x)
        self.entry.cache_functions([(x, self.action_tag)], self.clspath)

        def x(): pass

        self.entry.cache_functions([(x, self.action_tag)], self.clspath)
        self.assert_entry_has_functions({'x': FunctionEntry(run=x, is_bound=False, tags=self.action_tag)})
        self.assertNotEqual(id(self.entry.functions['x'].run), original_id)

    def test_cache_app_no_actions_empty_cache(self):
        class A: pass

        self.entry.cache_app_class(A, self.clspath)
        self.assertEqual(self.entry.main, A)
        self.assertDictEqual(self.entry.functions, {})

    def test_cache_app_with_actions_empty_cache(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

            def z(self): pass

        self.entry.cache_app_class(A, self.clspath)
        self.assertEqual(self.entry.main, A)
        self.assert_entry_has_functions(
            {'A.x': FunctionEntry(run=A.x, is_bound=True, tags=self.action_tag),
             'A.y': FunctionEntry(run=A.y, is_bound=True, tags=self.action_tag)})

    def test_cache_app_with_actions_and_global_actions(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

            def z(self): pass

        def z(): pass

        self.entry.cache_app_class(A, self.clspath)
        self.entry.cache_functions([(z, self.action_tag)], self.clspath)
        self.assertEqual(self.entry.main, A)

        self.assert_entry_has_functions(
            {'A.x': FunctionEntry(run=A.x, is_bound=True, tags=self.action_tag),
             'A.y': FunctionEntry(run=A.y, is_bound=True, tags=self.action_tag),
             'z': FunctionEntry(run=z, is_bound=False, tags=self.action_tag)})

    def test_clear_existing_bound_functions_no_actions(self):
        class A: pass

        self.entry.cache_app_class(A, self.clspath)
        self.entry.clear_bound_functions()
        self.assertDictEqual(self.entry.functions, {})

    def test_clear_existing_bound_functions_no_bound_actions(self):
        def x(): pass

        def y(): pass

        self.entry.cache_functions([(x, self.action_tag), (y, self.action_tag)], self.clspath)
        self.entry.clear_bound_functions()
        self.assert_entry_has_functions({'x': FunctionEntry(run=x, is_bound=False, tags=self.action_tag),
                                         'y': FunctionEntry(run=y, is_bound=False, tags=self.action_tag)})

    def test_clear_existing_bound_functions(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

            def z(self): pass

        def z(): pass

        self.entry.cache_app_class(A, self.clspath)
        self.entry.cache_functions([(z, self.action_tag)], self.clspath)
        self.entry.clear_bound_functions()
        self.assert_entry_has_functions({'z': FunctionEntry(run=z, is_bound=False, tags=self.action_tag)})
