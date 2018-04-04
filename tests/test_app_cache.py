import os.path
from importlib import import_module
from unittest import TestCase

from walkoff.appgateway.appcache import (AppCache, WalkoffTag,
                                         _get_qualified_class_name, _get_qualified_function_name,
                                         _strip_base_module_from_qualified_name)
from walkoff.appgateway.decorators import action
from walkoff.helpers import UnknownApp, UnknownAppAction

from tests import config


def f1(): pass


class TestAppCache(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.action_tag = {WalkoffTag.action}
        cls.condition_tag = {WalkoffTag.condition}
        cls.transform_tag = {WalkoffTag.transform}
        cls.maxDiff = None

    def setUp(self):
        self.cache = AppCache()

    def assert_cache_has_apps(self, apps):
        self.assertSetEqual(set(self.cache._cache.keys()), set(apps))

    def assert_cached_app_has_actions(self, app='app1', actions=set()):
        self.assertSetEqual(set(self.cache._cache[app].functions.keys()), actions)

    def assert_cache_has_main(self, main, app='A'):
        self.assertEqual(self.cache._cache[app].main, main)

    def test_init(self):
        self.assertDictEqual(self.cache._cache, {})

    def test_get_qualified_function_name(self):
        self.assertEqual(_get_qualified_function_name(f1), 'tests.test_app_cache.f1')

    def test_get_qualified_function_name_with_class(self):
        def f1(): pass

        self.assertEqual(_get_qualified_function_name(f1, cls=TestAppCache),
                         'tests.test_app_cache.TestAppCache.f1')

    def test_get_qualified_class_name(self):
        self.assertEqual(_get_qualified_class_name(TestAppCache),
                         'tests.test_app_cache.TestAppCache')

    def test_strip_base_module_from_qualified_name(self):
        self.assertEqual(_strip_base_module_from_qualified_name('tests.test_app_cache.f1', 'tests'),
                         'test_app_cache.f1')

    def test_strip_base_module_from_qualified_name_invalid_base_module(self):
        self.assertEqual(_strip_base_module_from_qualified_name('tests.test_app_cache.f1', 'invalid'),
                         'tests.test_app_cache.f1')

    def cache_app(self, A):
        self.cache._cache_app(A, 'A', 'tests.test_app_cache')

    def test_cache_module(self):
        module = import_module('tests.testapps.HelloWorldBounded.main')
        from tests.testapps.HelloWorldBounded.main import Main
        self.cache._cache_module(module, 'HelloWorldBounded', 'tests.testapps')
        self.assert_cache_has_main(Main, app='HelloWorldBounded')
        self.assert_cached_app_has_actions(app='HelloWorldBounded', actions={
            'main.Main.helloWorld', 'main.Main.repeatBackToMe', 'main.Main.returnPlusOne', 'main.Main.pause',
            'main.Main.addThree', 'main.Main.buggy_action', 'main.Main.json_sample', 'main.global1',
            'main.Main.wait_for_pause_and_resume'})

    def test_cache_module_nothing_found(self):
        module = import_module('tests.testapps.HelloWorldBounded.display')
        self.cache._cache_module(module, 'HelloWorldBounded', 'tests.testapps')
        self.assertDictEqual(self.cache._cache, {})

    def test_cache_module_no_class(self):
        module = import_module('tests.testapps.HelloWorldBounded.actions')
        self.cache._cache_module(module, 'HelloWorldBounded', 'tests.testapps')
        self.assert_cached_app_has_actions(app='HelloWorldBounded', actions={'actions.global2'})

    def test_import_and_cache_submodules_from_string(self):
        self.cache._import_and_cache_submodules('tests.testapps.HelloWorldBounded', 'HelloWorldBounded',
                                                'tests.testapps')
        from tests.testapps.HelloWorldBounded.main import Main
        self.assert_cache_has_main(Main, app='HelloWorldBounded')
        expected = {
            'main.Main.helloWorld', 'main.Main.repeatBackToMe', 'main.Main.returnPlusOne', 'main.Main.pause',
            'main.Main.addThree', 'main.Main.buggy_action', 'main.Main.json_sample', 'main.global1', 'actions.global2',
            'conditions.top_level_flag', 'conditions.flag1', 'conditions.flag2', 'conditions.flag3',
            'conditions.sub1_top_flag', 'conditions.regMatch', 'conditions.count', 'transforms.top_level_filter',
            'transforms.filter2', 'transforms.sub1_top_filter', 'transforms.filter3', 'transforms.filter1',
            'transforms.complex_filter', 'transforms.length', 'transforms.json_select',
            'main.Main.wait_for_pause_and_resume'}
        self.assert_cached_app_has_actions(app='HelloWorldBounded', actions=expected)

    def test_import_and_cache_submodules_from_module(self):
        module = import_module('tests.testapps.HelloWorldBounded')
        self.cache._import_and_cache_submodules(module, 'HelloWorldBounded', 'tests.testapps')
        from tests.testapps.HelloWorldBounded.main import Main
        self.assert_cache_has_main(Main, app='HelloWorldBounded')
        expected = {
            'main.Main.helloWorld', 'main.Main.repeatBackToMe', 'main.Main.returnPlusOne', 'main.Main.pause',
            'main.Main.addThree', 'main.Main.buggy_action', 'main.Main.json_sample', 'main.global1', 'actions.global2',
            'conditions.top_level_flag', 'conditions.flag1', 'conditions.flag2', 'conditions.flag3',
            'conditions.sub1_top_flag', 'conditions.regMatch', 'conditions.count', 'transforms.top_level_filter',
            'transforms.filter2', 'transforms.sub1_top_filter', 'transforms.filter3', 'transforms.filter1',
            'transforms.complex_filter', 'transforms.length', 'transforms.json_select',
            'main.Main.wait_for_pause_and_resume'}
        self.assert_cached_app_has_actions(app='HelloWorldBounded', actions=expected)

    def test_path_to_module_no_slashes(self):
        self.assertEqual(AppCache._path_to_module('apppath'), 'apppath')

    def test_path_to_module_trailing_slashes(self):
        self.assertEqual(AppCache._path_to_module('apppath' + os.path.sep), 'apppath')

    def test_path_to_module_leading_slashes(self):
        self.assertEqual(AppCache._path_to_module('.' + os.path.sep + 'apppath'), 'apppath')

    def test_path_to_module_strange_path(self):
        self.assertEqual(AppCache._path_to_module('..' + os.path.sep + 'apppath' + os.path.sep), 'apppath')

    def test_cache_apps(self):
        self.cache.cache_apps(config.test_apps_path)
        from testapps.HelloWorldBounded.main import Main
        from testapps.DailyQuote.main import Main as DailyMain
        self.assert_cache_has_main(Main, app='HelloWorldBounded')
        hello_world_expected = {
            'main.Main.helloWorld', 'main.Main.repeatBackToMe', 'main.Main.returnPlusOne', 'main.Main.pause',
            'main.Main.addThree', 'main.Main.buggy_action', 'main.Main.json_sample', 'main.global1', 'actions.global2',
            'conditions.top_level_flag', 'conditions.flag1', 'conditions.flag2', 'conditions.flag3',
            'conditions.sub1_top_flag', 'conditions.regMatch', 'conditions.count', 'transforms.top_level_filter',
            'transforms.filter2', 'transforms.sub1_top_filter', 'transforms.filter3', 'transforms.filter1',
            'transforms.complex_filter', 'transforms.length', 'transforms.json_select',
            'main.Main.wait_for_pause_and_resume'}
        self.assert_cached_app_has_actions(app='HelloWorldBounded', actions=hello_world_expected)
        self.assert_cache_has_main(DailyMain, app='DailyQuote')
        daily_quote_expected = {
            'main.Main.quoteIntro', 'main.Main.repeatBackToMe', 'main.Main.forismaticQuote', 'main.Main.getQuote'}
        self.assert_cache_has_apps({'HelloWorldBounded', 'HelloWorld', 'DailyQuote'})
        self.assert_cached_app_has_actions(app='DailyQuote', actions=daily_quote_expected)

    def test_clear_cache_empty_cache(self):
        self.cache.clear()
        self.assertDictEqual(self.cache._cache, {})

    def test_clear_cache(self):
        self.cache.cache_apps(config.test_apps_path)
        self.cache.clear()
        self.assertDictEqual(self.cache._cache, {})

    def test_get_all_app_names(self):
        class A: pass

        class B: pass

        self.cache_app(A)
        self.cache._cache_app(B, 'B', 'tests.test_app_cache.TestAppCache')
        self.assertSetEqual(set(self.cache.get_app_names()), {'A', 'B'})

    def test_get_all_app_names_empty_cache(self):
        self.assertSetEqual(set(self.cache.get_app_names()), set())

    def test_get_app_empty_cache(self):
        with self.assertRaises(UnknownApp):
            self.cache.get_app('A')

    def test_get_app_missing_app(self):
        class A: pass

        self.cache_app(A)
        with self.assertRaises(UnknownApp):
            self.cache.get_app('B')

    def test_get_app(self):
        class A: pass

        class B: pass

        self.cache_app(A)
        self.cache._cache_app(B, 'B', 'tests.test_app_cache')
        self.assertEqual(self.cache.get_app('A'), A)

    def test_get_app_action_names_empty_cache(self):
        with self.assertRaises(UnknownApp):
            self.cache.get_app('A')

    def test_get_app_action_names_unknown_app(self):
        class A: pass

        self.cache_app(A)
        with self.assertRaises(UnknownApp):
            self.cache.get_app_action_names('B')

    def test_get_app_action_names_no_actions(self):
        class A: pass

        self.cache_app(A)
        self.assertListEqual(self.cache.get_app_action_names('A'), [])

    def test_get_app_action_names(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

        class B:
            @action
            def a(self): pass

            @action
            def b(self): pass

        self.cache_app(A)
        self.cache._cache_app(B, 'B', 'tests.test_app_cache.TestAppCache')
        app_actions = self.cache.get_app_action_names('A')
        self.assertEqual(len(app_actions), 2)
        self.assertSetEqual(set(app_actions), {'A.x', 'A.y'})

    def test_get_app_action_empty_cache(self):
        with self.assertRaises(UnknownApp):
            self.cache.get_app_action('A', 'x')

    def test_get_app_action_unknown_app(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

        self.cache_app(A)
        with self.assertRaises(UnknownApp):
            self.cache.get_app_action('B', 'x')

    def test_get_app_action_no_actions(self):
        class A: pass

        self.cache_app(A)
        with self.assertRaises(UnknownAppAction):
            self.cache.get_app_action('A', 'x')

    def test_get_app_action_unknown_action(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

        self.cache_app(A)
        with self.assertRaises(UnknownAppAction):
            self.cache.get_app_action('A', 'z')

    def test_get_app_action(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

        class B:
            @action
            def a(self): pass

            @action
            def b(self): pass

        self.cache_app(A)
        self.cache._cache_app(B, 'B', 'tests.test_app_cache.TestAppCache')
        self.assertEqual(self.cache.get_app_action('A', 'A.x'), A.x)

    def test_is_app_action_bound_empty_cache(self):
        with self.assertRaises(UnknownApp):
            self.cache.is_app_action_bound('A', 'x')

    def test_is_app_action_bound_unknown_app(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

        self.cache_app(A)
        with self.assertRaises(UnknownApp):
            self.cache.is_app_action_bound('B', 'B.x')

    def test_is_app_action_bound_no_actions(self):
        class A: pass

        self.cache_app(A)
        with self.assertRaises(UnknownAppAction):
            self.cache.is_app_action_bound('A', 'A.x')

    def test_is_app_action_bound_unknown_action(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

        self.cache_app(A)
        with self.assertRaises(UnknownAppAction):
            self.cache.is_app_action_bound('A', 'A.z')

    def test_is_app_action_bound_true(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

        class B:
            @action
            def a(self): pass

            @action
            def b(self): pass

        self.cache_app(A)
        self.cache._cache_app(B, 'B', 'tests.test_app_cache')
        self.assertTrue(self.cache.is_app_action_bound('A', 'A.x'))

    def test_is_app_action_bound_false(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

        class B:
            @action
            def a(self): pass

            @action
            def b(self): pass

        def xx(): pass

        self.cache_app(A)
        self.cache._cache_app(B, 'B', 'tests.test_app_cache')
        self.cache._cache['A'].cache_functions([(xx, self.action_tag)], 'tests.test_app_cache')
        self.assertFalse(self.cache.is_app_action_bound('A', 'xx'))
