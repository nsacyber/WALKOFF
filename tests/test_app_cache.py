import os.path
from importlib import import_module
from unittest import TestCase

from walkoff.appgateway import AppCache
from walkoff.core.decorators import action
from walkoff.core.helpers import UnknownApp, UnknownAppAction


def f1(): pass


class TestAppCache(TestCase):
    def setUp(self):
        self.cache = AppCache()

    def test_init(self):
        self.assertDictEqual(self.cache._cache, {})

    def test_get_qualified_function_name(self):
        self.assertEqual(AppCache._get_qualified_function_name(f1), 'tests.test_app_cache.f1')

    def test_get_qualified_function_name_with_class(self):
        def f1(): pass

        self.assertEqual(AppCache._get_qualified_function_name(f1, cls=TestAppCache),
                         'tests.test_app_cache.TestAppCache.f1')

    def test_get_qualified_class_name(self):
        self.assertEqual(AppCache._get_qualified_class_name(TestAppCache),
                         'tests.test_app_cache.TestAppCache')

    def test_strip_base_module_from_qualified_name(self):
        self.assertEqual(AppCache._strip_base_module_from_qualified_name('tests.test_app_cache.f1', 'tests'),
                         'test_app_cache.f1')

    def test_strip_base_module_from_qualified_name_invalid_base_module(self):
        self.assertEqual(AppCache._strip_base_module_from_qualified_name('tests.test_app_cache.f1', 'invalid'),
                         'tests.test_app_cache.f1')

    def test_cache_action_empty_cache(self):
        def x(): pass

        self.cache._cache_action(x, 'app1', 'tests.test_app_cache.TestAppCache', 'action', cls=TestAppCache)
        self.assertDictEqual(self.cache._cache, {'app1': {'actions': {'x': {'run': x, 'bound': False}}}})

    def test_cache_action_existing_app_name_entry(self):
        def x(): pass

        self.cache._cache['app1'] = {}
        self.cache._cache_action(x, 'app1', 'tests.test_app_cache.TestAppCache', 'action', cls=TestAppCache)
        self.assertDictEqual(self.cache._cache, {'app1': {'actions': {'x': {'run': x, 'bound': False}}}})

    def test_cache_action_existing_app_name_and_actions_tag(self):
        def x(): pass

        self.cache._cache['app1'] = {'actions': {}}
        self.cache._cache_action(x, 'app1', 'tests.test_app_cache.TestAppCache', 'action', cls=TestAppCache)
        self.assertDictEqual(self.cache._cache, {'app1': {'actions': {'x': {'run': x, 'bound': False}}}})

    def test_cache_action_multiple_actions_same_app(self):
        def x(): pass

        def y(): pass

        self.cache._cache_action(x, 'app1', 'tests.test_app_cache.TestAppCache', 'action', cls=TestAppCache)
        self.cache._cache_action(y, 'app1', 'tests.test_app_cache.TestAppCache', 'action', cls=TestAppCache)
        self.assertDictEqual(self.cache._cache, {'app1': {'actions': {'x': {'run': x, 'bound': False},
                                                                      'y': {'run': y, 'bound': False}}}})

    def test_cache_action_multiple_actions_different_app(self):
        def x(): pass

        def y(): pass

        self.cache._cache_action(x, 'app1', 'tests.test_app_cache.TestAppCache', 'action', cls=TestAppCache)
        self.cache._cache_action(y, 'app2', 'tests.test_app_cache.TestAppCache', 'action', cls=TestAppCache)
        self.assertDictEqual(self.cache._cache, {'app1': {'actions': {'x': {'run': x, 'bound': False}}},
                                                 'app2': {'actions': {'y': {'run': y, 'bound': False}}}})

    def test_cache_action_overwrite(self):
        def x(): pass

        original_id = id(x)

        self.cache._cache_action(x, 'app1', 'tests.test_app_cache.TestAppCache', 'action', cls=TestAppCache)

        def x(): pass

        self.cache._cache_action(x, 'app1', 'tests.test_app_cache.TestAppCache', 'action', cls=TestAppCache)
        self.assertDictEqual(self.cache._cache, {'app1': {'actions': {'x': {'run': x, 'bound': False}}}})
        self.assertNotEqual(id(self.cache._cache['app1']['actions']['x']['run']), original_id)

    def test_cache_app_no_actions_empty_cache(self):
        class A: pass

        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
        self.assertDictEqual(self.cache._cache, {'A': {'main': A, 'actions': {}}})

    def test_cache_app_no_actions_app_name_exists(self):
        class A: pass

        self.cache._cache['A'] = {}
        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
        self.assertDictEqual(self.cache._cache, {'A': {'main': A, 'actions': {}}})

    def test_cache_app_no_actions_app_name_exists_main_is_empty(self):
        class A: pass

        self.cache._cache['A'] = {'main': None}
        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
        self.assertDictEqual(self.cache._cache, {'A': {'main': A, 'actions': {}}})

    def test_cache_app_with_actions_empty_cache(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

            def z(self): pass

        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
        self.maxDiff = None
        self.assertDictEqual(self.cache._cache, {'A': {'main': A,
                                                       'actions': {
                                                           'tests.test_app_cache.A.x': {'run': A.x, 'bound': True},
                                                           'tests.test_app_cache.A.y': {'run': A.y, 'bound': True}}}})

    def test_cache_app_with_actions_app_name_exists(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

            def z(self): pass

        self.cache._cache['A'] = {}
        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
        self.assertDictEqual(self.cache._cache, {'A': {'main': A,
                                                       'actions': {
                                                           'tests.test_app_cache.A.x': {'run': A.x, 'bound': True},
                                                           'tests.test_app_cache.A.y': {'run': A.y, 'bound': True}}}})

    def test_cache_app_with_actions_app_name_exists_main_is_empty(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

            def z(self): pass

        self.cache._cache['A'] = {'main': None}
        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
        self.assertDictEqual(self.cache._cache,
                             {'A': {'main': A, 'actions': {'tests.test_app_cache.A.x': {'run': A.x, 'bound': True},
                                                           'tests.test_app_cache.A.y': {'run': A.y, 'bound': True}}}})

    def test_cache_app_with_actions_and_global_actions(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

            def z(self): pass

        def z(): pass

        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
        self.cache._cache_action(z, 'A', 'tests.test_app_cache.TestAppCache', 'action', cls=TestAppCache)
        self.assertDictEqual(self.cache._cache,
                             {'A': {'main': A, 'actions': {'tests.test_app_cache.A.x': {'run': A.x, 'bound': True},
                                                           'tests.test_app_cache.A.y': {'run': A.y, 'bound': True},
                                                           'z': {'run': z, 'bound': False}}}})

    def test_cache_app_with_actions_and_global_actions_name_conflict_resolved(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

            @action
            def z(self): pass

        def z(): pass

        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
        self.cache._cache_action(z, 'A', 'tests.test_app_cache.TestAppCache', 'action', cls=TestAppCache)
        self.assertDictEqual(self.cache._cache,
                             {'A': {'main': A, 'actions': {'tests.test_app_cache.A.x': {'run': A.x, 'bound': True},
                                                           'tests.test_app_cache.A.y': {'run': A.y, 'bound': True},
                                                           'tests.test_app_cache.A.z': {'run': A.z, 'bound': True},
                                                           'z': {'run': z, 'bound': False}}}})

    def test_clear_existing_bound_functions_no_actions(self):
        class A: pass

        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
        self.cache._cache['A'].pop('actions')
        self.cache._clear_existing_bound_functions('A')
        self.assertDictEqual(self.cache._cache, {'A': {'main': A}})

    def test_clear_existing_bound_functions_no_bound_actions(self):
        def x(): pass

        def y(): pass

        self.cache._cache_action(x, 'app1', 'tests.test_app_cache.TestAppCache', 'action', cls=TestAppCache)
        self.cache._cache_action(y, 'app1', 'tests.test_app_cache.TestAppCache', 'action', cls=TestAppCache)
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

        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
        self.cache._cache_action(z, 'A', 'tests.test_app_cache.TestAppCache', 'action', cls=TestAppCache)
        self.cache._clear_existing_bound_functions('A')
        self.assertDictEqual(self.cache._cache, {'A': {'main': A, 'actions': {'z': {'run': z, 'bound': False}}}})

    def test_cache_module(self):
        module = import_module('tests.testapps.HelloWorldBounded.main')
        from tests.testapps.HelloWorldBounded.main import Main, global1
        self.cache._cache_module(module, 'HelloWorldBounded', 'tests.testapps')
        self.maxDiff = None
        expected = {'HelloWorldBounded': {'main': Main,
                                          'actions': {'main.Main.helloWorld': {'run': Main.helloWorld, 'bound': True},
                                                      'main.Main.repeatBackToMe': {'run': Main.repeatBackToMe,
                                                                                   'bound': True},
                                                      'main.Main.returnPlusOne': {'run': Main.returnPlusOne,
                                                                                  'bound': True},
                                                      'main.Main.pause': {'run': Main.pause, 'bound': True},
                                                      'main.Main.addThree': {'run': Main.addThree, 'bound': True},
                                                      'main.Main.buggy_action': {'run': Main.buggy_action,
                                                                                 'bound': True},
                                                      'main.Main.json_sample': {'run': Main.json_sample, 'bound': True},
                                                      'main.global1': {'run': global1, 'bound': False}}}}
        self.assertDictEqual(self.cache._cache, expected)

    def test_cache_module_nothing_found(self):
        module = import_module('tests.testapps.HelloWorldBounded.display')
        self.cache._cache_module(module, 'HelloWorldBounded', 'tests.testapps')
        self.assertDictEqual(self.cache._cache, {})

    def test_cache_module_no_class(self):
        module = import_module('tests.testapps.HelloWorldBounded.actions')
        self.cache._cache_module(module, 'HelloWorldBounded', 'tests.testapps')
        from tests.testapps.HelloWorldBounded.actions import global2
        self.assertDictEqual(self.cache._cache,
                             {'HelloWorldBounded': {'actions': {'actions.global2': {'run': global2, 'bound': False}}}})

    def test_import_and_cache_submodules_from_string(self):
        self.cache._import_and_cache_submodules('tests.testapps.HelloWorldBounded', 'HelloWorldBounded',
                                                'tests.testapps')
        from tests.testapps.HelloWorldBounded.main import Main, global1
        from tests.testapps.HelloWorldBounded.actions import global2
        from tests.testapps.HelloWorldBounded.conditions import (top_level_flag, flag1, flag2, flag3, sub1_top_flag,
                                                                 regMatch, count)
        from tests.testapps.HelloWorldBounded.transforms import (top_level_filter, filter1, filter2, filter3,
                                                                 complex_filter,
                                                                 length, json_select, sub1_top_filter)
        expected = {'HelloWorldBounded': {'main': Main,
                                          'actions': {'main.Main.helloWorld': {'run': Main.helloWorld, 'bound': True},
                                                      'main.Main.repeatBackToMe': {'run': Main.repeatBackToMe,
                                                                                   'bound': True},
                                                      'main.Main.returnPlusOne': {'run': Main.returnPlusOne,
                                                                                  'bound': True},
                                                      'main.Main.pause': {'run': Main.pause, 'bound': True},
                                                      'main.Main.addThree': {'run': Main.addThree, 'bound': True},
                                                      'main.Main.buggy_action': {'run': Main.buggy_action,
                                                                                 'bound': True},
                                                      'main.Main.json_sample': {'run': Main.json_sample, 'bound': True},
                                                      'main.global1': {'run': global1, 'bound': False},
                                                      'actions.global2': {'run': global2, 'bound': False}},
                                          'conditions': {'conditions.top_level_flag': {'run': top_level_flag},
                                                         'conditions.flag1': {'run': flag1},
                                                         'conditions.flag2': {'run': flag2},
                                                         'conditions.flag3': {'run': flag3},
                                                         'conditions.sub1_top_flag': {'run': sub1_top_flag},
                                                         'conditions.regMatch': {'run': regMatch},
                                                         'conditions.count': {'run': count}},
                                          'transforms': {'transforms.top_level_filter': {'run': top_level_filter},
                                                         'transforms.filter2': {'run': filter2},
                                                         'transforms.sub1_top_filter': {'run': sub1_top_filter},
                                                         'transforms.filter3': {'run': filter3},
                                                         'transforms.filter1': {'run': filter1},
                                                         'transforms.complex_filter': {'run': complex_filter},
                                                         'transforms.length': {'run': length},
                                                         'transforms.json_select': {'run': json_select}}}}
        self.assertDictEqual(self.cache._cache, expected)

    def test_import_and_cache_submodules_from_module(self):
        module = import_module('tests.testapps.HelloWorldBounded')
        self.cache._import_and_cache_submodules(module, 'HelloWorldBounded', 'tests.testapps')
        from tests.testapps.HelloWorldBounded.main import Main, global1
        from tests.testapps.HelloWorldBounded.actions import global2
        from tests.testapps.HelloWorldBounded.conditions import (top_level_flag, flag1, flag2, flag3, sub1_top_flag,
                                                                 regMatch, count)
        from tests.testapps.HelloWorldBounded.transforms import (top_level_filter, filter1, filter2, filter3,
                                                                 complex_filter,
                                                                 length, json_select, sub1_top_filter)
        expected = {'HelloWorldBounded': {'main': Main,
                                          'actions': {'main.Main.helloWorld': {'run': Main.helloWorld, 'bound': True},
                                                      'main.Main.repeatBackToMe': {'run': Main.repeatBackToMe,
                                                                                   'bound': True},
                                                      'main.Main.returnPlusOne': {'run': Main.returnPlusOne,
                                                                                  'bound': True},
                                                      'main.Main.pause': {'run': Main.pause, 'bound': True},
                                                      'main.Main.addThree': {'run': Main.addThree, 'bound': True},
                                                      'main.Main.buggy_action': {'run': Main.buggy_action,
                                                                                 'bound': True},
                                                      'main.Main.json_sample': {'run': Main.json_sample, 'bound': True},
                                                      'main.global1': {'run': global1, 'bound': False},
                                                      'actions.global2': {'run': global2, 'bound': False}},
                                          'conditions': {'conditions.top_level_flag': {'run': top_level_flag},
                                                         'conditions.flag1': {'run': flag1},
                                                         'conditions.flag2': {'run': flag2},
                                                         'conditions.flag3': {'run': flag3},
                                                         'conditions.sub1_top_flag': {'run': sub1_top_flag},
                                                         'conditions.regMatch': {'run': regMatch},
                                                         'conditions.count': {'run': count}},
                                          'transforms': {'transforms.top_level_filter': {'run': top_level_filter},
                                                         'transforms.filter2': {'run': filter2},
                                                         'transforms.sub1_top_filter': {'run': sub1_top_filter},
                                                         'transforms.filter3': {'run': filter3},
                                                         'transforms.filter1': {'run': filter1},
                                                         'transforms.complex_filter': {'run': complex_filter},
                                                         'transforms.length': {'run': length},
                                                         'transforms.json_select': {'run': json_select}}}}
        self.assertDictEqual(self.cache._cache, expected)

    def test_path_to_module_no_slashes(self):
        self.assertEqual(AppCache._path_to_module('apppath'), 'apppath')

    def test_path_to_module_trailing_slashes(self):
        self.assertEqual(AppCache._path_to_module('apppath' + os.path.sep), 'apppath')

    def test_path_to_module_leading_slashes(self):
        self.assertEqual(AppCache._path_to_module('.' + os.path.sep + 'apppath'), 'apppath')

    def test_path_to_module_strange_path(self):
        self.assertEqual(AppCache._path_to_module('..' + os.path.sep + 'apppath' + os.path.sep), 'apppath')

    def test_cache_apps(self):
        self.cache.cache_apps(os.path.join('.', 'tests', 'testapps'))
        from tests.testapps.HelloWorldBounded.main import Main, global1
        from tests.testapps.HelloWorldBounded.conditions import (top_level_flag, flag1, flag2, flag3, sub1_top_flag,
                                                                 regMatch, count)
        from tests.testapps.HelloWorldBounded.transforms import (top_level_filter, filter1, filter2, filter3,
                                                                 complex_filter,
                                                                 length, json_select, sub1_top_filter)
        from tests.testapps.HelloWorldBounded.actions import global2
        from tests.testapps.DailyQuote.main import Main as DailyMain
        self.maxDiff = None
        expected = {'HelloWorldBounded': {'main': Main,
                                          'actions': {'main.Main.helloWorld': {'run': Main.helloWorld, 'bound': True},
                                                      'main.Main.repeatBackToMe': {'run': Main.repeatBackToMe,
                                                                                   'bound': True},
                                                      'main.Main.returnPlusOne': {'run': Main.returnPlusOne,
                                                                                  'bound': True},
                                                      'main.Main.pause': {'run': Main.pause, 'bound': True},
                                                      'main.Main.addThree': {'run': Main.addThree, 'bound': True},
                                                      'main.Main.buggy_action': {'run': Main.buggy_action,
                                                                                 'bound': True},
                                                      'main.Main.json_sample': {'run': Main.json_sample, 'bound': True},
                                                      'main.global1': {'run': global1, 'bound': False},
                                                      'actions.global2': {'run': global2, 'bound': False}},
                                          'conditions': {'conditions.top_level_flag': {'run': top_level_flag},
                                                         'conditions.flag1': {'run': flag1},
                                                         'conditions.flag2': {'run': flag2},
                                                         'conditions.flag3': {'run': flag3},
                                                         'conditions.sub1_top_flag': {'run': sub1_top_flag},
                                                         'conditions.regMatch': {'run': regMatch},
                                                         'conditions.count': {'run': count}},
                                          'transforms': {'transforms.top_level_filter': {'run': top_level_filter},
                                                         'transforms.filter2': {'run': filter2},
                                                         'transforms.sub1_top_filter': {'run': sub1_top_filter},
                                                         'transforms.filter3': {'run': filter3},
                                                         'transforms.filter1': {'run': filter1},
                                                         'transforms.complex_filter': {'run': complex_filter},
                                                         'transforms.length': {'run': length},
                                                         'transforms.json_select': {'run': json_select}}},
                    'DailyQuote': {'main': DailyMain,
                                   'actions': {'main.Main.quoteIntro': {'run': DailyMain.quoteIntro, 'bound': True},
                                               'main.Main.repeatBackToMe': {'run': DailyMain.repeatBackToMe,
                                                                            'bound': True},
                                               'main.Main.forismaticQuote': {'run': DailyMain.forismaticQuote,
                                                                             'bound': True},
                                               'main.Main.getQuote': {'run': DailyMain.getQuote, 'bound': True}}}}
        self.cache._cache.pop("HelloWorld")
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

        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
        self.cache._cache_app(B, 'B', 'tests.test_app_cache.TestAppCache')
        self.assertSetEqual(set(self.cache.get_app_names()), {'A', 'B'})

    def test_get_all_app_names_empty_cache(self):
        self.assertSetEqual(set(self.cache.get_app_names()), set())

    def test_get_app_empty_cache(self):
        with self.assertRaises(UnknownApp):
            self.cache.get_app('A')

    def test_get_app_missing_app(self):
        class A: pass

        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
        with self.assertRaises(UnknownApp):
            self.cache.get_app('B')

    def test_get_app_missing_main(self):
        def x(): pass

        self.cache._cache_action(x, 'A', 'tests.test_app_cache.TestAppCache', 'action', cls=TestAppCache)
        with self.assertRaises(UnknownApp):
            self.cache.get_app('A')

    def test_get_app(self):
        class A: pass

        class B: pass

        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
        self.cache._cache_app(B, 'B', 'tests.test_app_cache.TestAppCache')
        self.assertEqual(self.cache.get_app('A'), A)

    def test_get_app_action_names_empty_cache(self):
        with self.assertRaises(UnknownApp):
            self.cache.get_app('A')

    def test_get_app_action_names_unknown_app(self):
        class A: pass

        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
        with self.assertRaises(UnknownApp):
            self.cache.get_app_action_names('B')

    def test_get_app_action_names_no_actions(self):
        class A: pass

        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
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

        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
        self.cache._cache_app(B, 'B', 'tests.test_app_cache.TestAppCache')
        app_actions = self.cache.get_app_action_names('A')
        self.assertEqual(len(app_actions), 2)
        self.assertSetEqual(set(app_actions), {'tests.test_app_cache.A.x', 'tests.test_app_cache.A.y'})

    def test_get_app_action_empty_cache(self):
        with self.assertRaises(UnknownApp):
            self.cache.get_app_action('A', 'x')

    def test_get_app_action_unknown_app(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
        with self.assertRaises(UnknownApp):
            self.cache.get_app_action('B', 'x')

    def test_get_app_action_no_actions(self):
        class A: pass

        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
        with self.assertRaises(UnknownAppAction):
            self.cache.get_app_action('A', 'x')

    def test_get_app_action_unknown_action(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
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

        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
        self.cache._cache_app(B, 'B', 'tests.test_app_cache.TestAppCache')
        self.assertEqual(self.cache.get_app_action('A', 'tests.test_app_cache.A.x'), A.x)

    def test_is_app_action_bound_empty_cache(self):
        with self.assertRaises(UnknownApp):
            self.cache.is_app_action_bound('A', 'x')

    def test_is_app_action_bound_unknown_app(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
        with self.assertRaises(UnknownApp):
            self.cache.is_app_action_bound('B', 'tests.test_app_cache.B.x')

    def test_is_app_action_bound_no_actions(self):
        class A: pass

        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
        with self.assertRaises(UnknownAppAction):
            self.cache.is_app_action_bound('A', 'tests.test_app_cache.A.x')

    def test_is_app_action_bound_unknown_action(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
        with self.assertRaises(UnknownAppAction):
            self.cache.is_app_action_bound('A', 'tests.test_app_cache.A.z')

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

        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
        self.cache._cache_app(B, 'B', 'tests.test_app_cache.TestAppCache')
        self.assertTrue(self.cache.is_app_action_bound('A', 'tests.test_app_cache.A.x'))

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

        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')
        self.cache._cache_app(B, 'B', 'tests.test_app_cache.TestAppCache')
        self.cache._cache_action(xx, 'A', 'tests.test_app_cache.TestAppCache', 'action', cls=TestAppCache)
        self.assertFalse(self.cache.is_app_action_bound('A', 'xx'))
