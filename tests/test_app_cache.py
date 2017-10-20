from unittest import TestCase
from apps import AppCache
from core.decorators import action
from importlib import import_module
from core.helpers import UnknownApp, UnknownAppAction

def f1(): pass


class TestAppCacheCreation(TestCase):

    def setUp(self):
        self.cache = AppCache()

    def test_init(self):
        self.assertDictEqual(self.cache._cache, {})

    def test_get_qualified_function_name(self):
        self.assertEqual(AppCache._get_qualified_function_name(f1), 'tests.test_app_cache.f1')

    def test_get_qualified_class_name(self):
        self.assertEqual(AppCache._get_qualified_class_name(TestAppCacheCreation),
                         'tests.test_app_cache.TestAppCacheCreation')

    def test_cache_action_empty_cache(self):
        def x(): pass
        self.cache._cache_action('x', x, 'app1')
        self.assertDictEqual(self.cache._cache, {'app1': {'actions': {'x': {'run': x, 'bound': False}}}})

    def test_cache_action_existing_app_name_entry(self):
        def x(): pass
        self.cache._cache['app1'] = {}
        self.cache._cache_action('x', x, 'app1')
        self.assertDictEqual(self.cache._cache, {'app1': {'actions': {'x': {'run': x, 'bound': False}}}})

    def test_cache_action_existing_app_name_and_actions_tag(self):
        def x(): pass
        self.cache._cache['app1'] = {'actions':  {}}
        self.cache._cache_action('x', x, 'app1')
        self.assertDictEqual(self.cache._cache, {'app1': {'actions': {'x': {'run': x, 'bound': False}}}})

    def test_cache_action_multiple_actions_same_app(self):
        def x(): pass
        def y(): pass
        self.cache._cache_action('x', x, 'app1')
        self.cache._cache_action('y', y, 'app1')
        self.assertDictEqual(self.cache._cache, {'app1': {'actions': {'x': {'run': x, 'bound': False},
                                                                      'y': {'run': y, 'bound': False}}}})

    def test_cache_action_multiple_actions_different_app(self):
        def x(): pass
        def y(): pass
        self.cache._cache_action('x', x, 'app1')
        self.cache._cache_action('y', y, 'app2')
        self.assertDictEqual(self.cache._cache, {'app1': {'actions': {'x': {'run': x, 'bound': False}}},
                                                 'app2': {'actions': {'y': {'run': y, 'bound': False}}}})

    def test_cache_action_overwrite(self):
        def x(): pass
        original_id = id(x)

        self.cache._cache_action('x', x, 'app1')

        def x(): pass

        self.cache._cache_action('x', x, 'app1')
        self.assertDictEqual(self.cache._cache, {'app1': {'actions': {'x': {'run': x, 'bound': False}}}})
        self.assertNotEqual(id(self.cache._cache['app1']['actions']['x']['run']), original_id)

    def test_cache_app_no_actions_empty_cache(self):
        class A: pass
        self.cache._cache_app(A, 'A')
        self.assertDictEqual(self.cache._cache, {'A': {'main': A, 'actions': {}}})

    def test_cache_app_no_actions_app_name_exists(self):
        class A: pass
        self.cache._cache['A'] = {}
        self.cache._cache_app(A, 'A')
        self.assertDictEqual(self.cache._cache, {'A': {'main': A, 'actions': {}}})

    def test_cache_app_no_actions_app_name_exists_main_is_empty(self):
        class A: pass
        self.cache._cache['A'] = {'main': None}
        self.cache._cache_app(A, 'A')
        self.assertDictEqual(self.cache._cache, {'A': {'main': A, 'actions': {}}})

    def test_cache_app_with_actions_empty_cache(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

            def z(self): pass

        self.cache._cache_app(A, 'A')
        self.assertDictEqual(self.cache._cache, {'A': {'main': A, 'actions': {'x': {'run': A.x, 'bound': True},
                                                                              'y': {'run': A.y, 'bound': True}}}})

    def test_cache_app_with_actions_app_name_exists(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

            def z(self): pass

        self.cache._cache['A'] = {}
        self.cache._cache_app(A, 'A')
        self.assertDictEqual(self.cache._cache, {'A': {'main': A, 'actions': {'x': {'run': A.x, 'bound': True},
                                                                              'y': {'run': A.y, 'bound': True}}}})

    def test_cache_app_with_actions_app_name_exists_main_is_empty(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

            def z(self): pass

        self.cache._cache['A'] = {'main': None}
        self.cache._cache_app(A, 'A')
        self.assertDictEqual(self.cache._cache, {'A': {'main': A, 'actions': {'x': {'run': A.x, 'bound': True},
                                                                              'y': {'run': A.y, 'bound': True}}}})

    def test_cache_app_with_actions_and_global_action(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

            def z(self): pass

        def z(): pass

        self.cache._cache_app(A, 'A')
        self.cache._cache_action('z', z, 'A')
        self.assertDictEqual(self.cache._cache, {'A': {'main': A, 'actions': {'x': {'run': A.x, 'bound': True},
                                                                              'y': {'run': A.y, 'bound': True},
                                                                              'z': {'run': z, 'bound': False}}}})

    def test_clear_existing_bound_functions_no_actions(self):
        class A: pass
        self.cache._cache_app(A, 'A')
        self.cache._cache['A'].pop('actions')
        self.cache._clear_existing_bound_functions('A')
        self.assertDictEqual(self.cache._cache, {'A': {'main': A}})

    def test_clear_existing_bound_functions_no_bound_actions(self):
        def x(): pass
        def y(): pass
        self.cache._cache_action('x', x, 'app1')
        self.cache._cache_action('y', y, 'app1')
        self.cache._clear_existing_bound_functions('app1')
        self.assertDictEqual(self.cache._cache, {'app1': {'actions': {'x': {'run': x, 'bound': False},
                                                                      'y': {'run': y, 'bound': False}}}})

    def test_clear_existing_bound_functions(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

            def z(self): pass

        def z(): pass

        self.cache._cache_app(A, 'A')
        self.cache._cache_action('z', z, 'A')
        self.cache._clear_existing_bound_functions('A')
        self.assertDictEqual(self.cache._cache, {'A': {'main': A, 'actions': {'z': {'run': z, 'bound': False}}}})

    def test_cache_module(self):
        module = import_module('tests.apps.HelloWorld.main')
        from tests.apps.HelloWorld.main import Main, global1
        self.cache._cache_module(module, 'HelloWorld')
        expected = {'HelloWorld': {'main': Main,
                                   'actions': {'helloWorld': {'run': Main.helloWorld, 'bound': True},
                                               'repeatBackToMe': {'run': Main.repeatBackToMe, 'bound': True},
                                               'returnPlusOne': {'run': Main.returnPlusOne, 'bound': True},
                                               'pause': {'run': Main.pause, 'bound': True},
                                               'addThree': {'run': Main.addThree, 'bound': True},
                                               'buggy_action': {'run': Main.buggy_action, 'bound': True},
                                               'json_sample': {'run': Main.json_sample, 'bound': True},
                                               'sample_event': {'run': Main.sample_event, 'bound': True},
                                               'global1': {'run': global1, 'bound': False}}}}
        self.assertDictEqual(self.cache._cache, expected)

    def test_cache_module_nothing_found(self):
        module = import_module('tests.apps.HelloWorld.events')
        self.cache._cache_module(module, 'HelloWorld')
        self.assertDictEqual(self.cache._cache, {})

    def test_cache_module_no_class(self):
        module = import_module('tests.apps.HelloWorld.actions')
        self.cache._cache_module(module, 'HelloWorld')
        from tests.apps.HelloWorld.actions import global2
        self.assertDictEqual(self.cache._cache,
                             {'HelloWorld': {'actions': {'global2': {'run': global2, 'bound': False}}}})

    def test_import_and_cache_submodules_from_string(self):
        self.cache._import_and_cache_submodules('tests.apps.HelloWorld', 'HelloWorld')
        from tests.apps.HelloWorld.main import Main, global1
        from tests.apps.HelloWorld.actions import global2
        expected = {'HelloWorld': {'main': Main,
                                   'actions': {'helloWorld': {'run': Main.helloWorld, 'bound': True},
                                               'repeatBackToMe': {'run': Main.repeatBackToMe, 'bound': True},
                                               'returnPlusOne': {'run': Main.returnPlusOne, 'bound': True},
                                               'pause': {'run': Main.pause, 'bound': True},
                                               'addThree': {'run': Main.addThree, 'bound': True},
                                               'buggy_action': {'run': Main.buggy_action, 'bound': True},
                                               'json_sample': {'run': Main.json_sample, 'bound': True},
                                               'sample_event': {'run': Main.sample_event, 'bound': True},
                                               'global1': {'run': global1, 'bound': False},
                                               'global2': {'run': global2, 'bound': False}}}}
        self.assertDictEqual(self.cache._cache, expected)

    def test_import_and_cache_submodules_from_module(self):
        module = import_module('tests.apps.HelloWorld')
        self.cache._import_and_cache_submodules(module, 'HelloWorld')
        from tests.apps.HelloWorld.main import Main, global1
        from tests.apps.HelloWorld.actions import global2
        expected = {'HelloWorld': {'main': Main,
                                   'actions': {'helloWorld': {'run': Main.helloWorld, 'bound': True},
                                               'repeatBackToMe': {'run': Main.repeatBackToMe, 'bound': True},
                                               'returnPlusOne': {'run': Main.returnPlusOne, 'bound': True},
                                               'pause': {'run': Main.pause, 'bound': True},
                                               'addThree': {'run': Main.addThree, 'bound': True},
                                               'buggy_action': {'run': Main.buggy_action, 'bound': True},
                                               'json_sample': {'run': Main.json_sample, 'bound': True},
                                               'sample_event': {'run': Main.sample_event, 'bound': True},
                                               'global1': {'run': global1, 'bound': False},
                                               'global2': {'run': global2, 'bound': False}}}}
        self.assertDictEqual(self.cache._cache, expected)

    def test_list_apps(self):
        listed_apps = AppCache.list_apps('./tests/apps')
        self.assertEqual(len(listed_apps), 2)
        self.assertSetEqual(set(listed_apps), {'HelloWorld', 'DailyQuote'})

    def test_path_to_module_no_slashes(self):
        self.assertEqual(AppCache._path_to_module('apppath'), 'apppath')

    def test_path_to_module_trailing_slashes(self):
        self.assertEqual(AppCache._path_to_module('apppath/'), 'apppath')

    def test_path_to_module_leading_slashes(self):
        self.assertEqual(AppCache._path_to_module('./apppath'), 'apppath')

    def test_path_to_module_strange_path(self):
        self.assertEqual(AppCache._path_to_module('../apppath/'), 'apppath')

    def test_cache_apps(self):
        self.cache.cache_apps('./tests/apps')
        from tests.apps.HelloWorld.main import Main, global1
        from tests.apps.HelloWorld.actions import global2
        from tests.apps.DailyQuote.main import Main as DailyMain
        self.maxDiff = None
        expected = {'HelloWorld': {'main': Main,
                                   'actions': {'helloWorld': {'run': Main.helloWorld, 'bound': True},
                                               'repeatBackToMe': {'run': Main.repeatBackToMe, 'bound': True},
                                               'returnPlusOne': {'run': Main.returnPlusOne, 'bound': True},
                                               'pause': {'run': Main.pause, 'bound': True},
                                               'addThree': {'run': Main.addThree, 'bound': True},
                                               'buggy_action': {'run': Main.buggy_action, 'bound': True},
                                               'json_sample': {'run': Main.json_sample, 'bound': True},
                                               'sample_event': {'run': Main.sample_event, 'bound': True},
                                               'global1': {'run': global1, 'bound': False},
                                               'global2': {'run': global2, 'bound': False}}},
                    'DailyQuote': {'main': DailyMain,
                                   'actions': {'quoteIntro': {'run': DailyMain.quoteIntro, 'bound': True},
                                              'repeatBackToMe': {'run': DailyMain.repeatBackToMe, 'bound': True},
                                              'forismaticQuote': {'run': DailyMain.forismaticQuote, 'bound': True},
                                              'getQuote': {'run': DailyMain.getQuote, 'bound': True}}}}
        self.assertDictEqual(self.cache._cache, expected)

    def test_clear_cache_empty_cache(self):
        self.cache.clear()
        self.assertDictEqual(self.cache._cache, {})

    def test_clear_cache(self):
        self.cache.cache_apps('./tests/apps')
        self.cache.clear()
        self.assertDictEqual(self.cache._cache, {})

    def test_get_all_app_names(self):
        class A: pass
        class B: pass
        self.cache._cache_app(A, 'A')
        self.cache._cache_app(B, 'B')
        self.assertSetEqual(set(self.cache.get_app_names()), {'A', 'B'})

    def test_get_all_app_names_empty_cache(self):
        self.assertSetEqual(set(self.cache.get_app_names()), set())

    def test_get_app_empty_cache(self):
        with self.assertRaises(UnknownApp):
            self.cache.get_app('A')

    def test_get_app_missing_app(self):
        class A: pass
        self.cache._cache_app(A, 'A')
        with self.assertRaises(UnknownApp):
            self.cache.get_app('B')

    def test_get_app_missing_main(self):
        def x(): pass
        self.cache._cache_action('x', x, 'A')
        with self.assertRaises(UnknownApp):
            self.cache.get_app('A')

    def test_get_app(self):
        class A: pass
        class B: pass
        self.cache._cache_app(A, 'A')
        self.cache._cache_app(B, 'B')
        self.assertEqual(self.cache.get_app('A'), A)

    def test_get_app_action_names_empty_cache(self):
        with self.assertRaises(UnknownApp):
            self.cache.get_app('A')

    def test_get_app_action_names_unknown_app(self):
        class A: pass
        self.cache._cache_app(A, 'A')
        with self.assertRaises(UnknownApp):
            self.cache.get_app_action_names('B')

    def test_get_app_action_names_no_actions(self):
        class A: pass
        self.cache._cache_app(A, 'A')
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

        self.cache._cache_app(A, 'A')
        self.cache._cache_app(B, 'B')
        app_actions = self.cache.get_app_action_names('A')
        self.assertEqual(len(app_actions), 2)
        self.assertSetEqual(set(app_actions), {'x', 'y'})

    def test_get_app_action_empty_cache(self):
        with self.assertRaises(UnknownApp):
            self.cache.get_app_action('A', 'x')

    def test_get_app_action_unknown_app(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass
        self.cache._cache_app(A, 'A')
        with self.assertRaises(UnknownApp):
            self.cache.get_app_action('B', 'x')

    def test_get_app_action_no_actions(self):
        class A: pass
        self.cache._cache_app(A, 'A')
        with self.assertRaises(UnknownAppAction):
            self.cache.get_app_action('A', 'x')

    def test_get_app_action_unknown_action(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass
        self.cache._cache_app(A, 'A')
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

        self.cache._cache_app(A, 'A')
        self.cache._cache_app(B, 'B')
        self.assertEqual(self.cache.get_app_action('A', 'x'), A.x)

    def test_is_app_action_bound_empty_cache(self):
        with self.assertRaises(UnknownApp):
            self.cache.is_app_action_bound('A', 'x')

    def test_is_app_action_bound_unknown_app(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

        self.cache._cache_app(A, 'A')
        with self.assertRaises(UnknownApp):
            self.cache.is_app_action_bound('B', 'x')

    def test_is_app_action_bound_no_actions(self):
        class A: pass

        self.cache._cache_app(A, 'A')
        with self.assertRaises(UnknownAppAction):
            self.cache.is_app_action_bound('A', 'x')

    def test_is_app_action_bound_unknown_action(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

        self.cache._cache_app(A, 'A')
        with self.assertRaises(UnknownAppAction):
            self.cache.is_app_action_bound('A', 'z')

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

        self.cache._cache_app(A, 'A')
        self.cache._cache_app(B, 'B')
        self.assertTrue(self.cache.is_app_action_bound('A', 'x'))

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

        self.cache._cache_app(A, 'A')
        self.cache._cache_app(B, 'B')
        self.cache._cache_action('xx', xx, 'A')
        self.assertFalse(self.cache.is_app_action_bound('A', 'xx'))