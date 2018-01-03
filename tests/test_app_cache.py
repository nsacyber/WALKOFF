import os.path
from importlib import import_module
from unittest import TestCase

from walkoff.appgateway.appcache import AppCache, FunctionEntry, WalkoffTag
from walkoff.appgateway.decorators import action
from walkoff.helpers import UnknownApp, UnknownAppAction


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

    def assert_cached_app_has_actions(self, app='app1', actions={}):
        self.assertDictEqual(self.cache._cache[app]['actions'], actions)

    def assert_cache_has_main(self, main, app='A'):
        self.assertEqual(self.cache._cache[app]['main'], main)

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

    def cache_action(self, func, app='app1', tags=None):
        tags = self.action_tag if tags is None else tags
        self.cache._cache_action(
            func, app, 'tests.test_app_cache.TestAppCache', tags, cls=TestAppCache)

    def test_cache_action_empty_cache(self):
        def x(): pass
        self.cache_action(x)
        self.assert_cache_has_apps({'app1'})
        self.assert_cached_app_has_actions(actions={'x': FunctionEntry(run=x, is_bound=False, tags=self.action_tag)})

    def test_cache_action_existing_app_name_entry(self):
        def x(): pass

        self.cache._cache['app1'] = {}
        self.cache_action(x)
        self.assert_cache_has_apps({'app1'})
        self.assert_cached_app_has_actions(actions={'x': FunctionEntry(run=x, is_bound=False, tags=self.action_tag)})

    def test_cache_action_existing_app_name_and_actions_tag(self):
        def x(): pass

        self.cache._cache['app1'] = {'actions': {}}
        self.cache_action(x)
        self.assert_cache_has_apps({'app1'})
        self.assert_cached_app_has_actions(actions={'x': FunctionEntry(run=x, is_bound=False, tags=self.action_tag)})

    def test_cache_action_multiple_actions_same_app(self):
        def x(): pass

        def y(): pass
        self.cache_action(x)
        self.cache_action(y)
        self.assert_cache_has_apps({'app1'})
        self.assert_cached_app_has_actions(actions={'x': FunctionEntry(run=x, is_bound=False, tags=self.action_tag),
                                                    'y': FunctionEntry(run=y, is_bound=False, tags=self.action_tag)})

    def test_cache_action_multiple_actions_different_app(self):
        def x(): pass

        def y(): pass
        self.cache_action(x)
        self.cache_action(y, app='app2')
        self.assert_cache_has_apps({'app1', 'app2'})
        self.assert_cached_app_has_actions(
            actions={'x': FunctionEntry(run=x, is_bound=False, tags=self.action_tag)})
        self.assert_cached_app_has_actions(app='app2',
                                           actions={'y': FunctionEntry(run=y, is_bound=False, tags=self.action_tag)})

    def test_cache_action_overwrite(self):
        def x(): pass

        original_id = id(x)

        self.cache_action(x)
        def x(): pass
        self.cache_action(x)
        self.assert_cache_has_apps({'app1'})
        self.assert_cached_app_has_actions(actions={'x': FunctionEntry(run=x, is_bound=False, tags=self.action_tag)})
        self.assertNotEqual(id(self.cache._cache['app1']['actions']['x'].run), original_id)

    def test_cache_app_no_actions_empty_cache(self):
        class A: pass

        self.cache_app(A)
        self.assert_cache_has_main(A)
        self.assert_cached_app_has_actions(app='A')

    def test_cache_app_no_actions_app_name_exists(self):
        class A: pass

        self.cache._cache['A'] = {}
        self.cache_app(A)
        self.assert_cache_has_main(A)
        self.assert_cached_app_has_actions(app='A')

    def cache_app(self, A):
        self.cache._cache_app(A, 'A', 'tests.test_app_cache.TestAppCache')

    def test_cache_app_no_actions_app_name_exists_main_is_empty(self):
        class A: pass

        self.cache._cache['A'] = {'main': None}
        self.cache_app(A)
        self.assert_cache_has_main(A)
        self.assert_cached_app_has_actions(app='A')

    def test_cache_app_with_actions_empty_cache(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

            def z(self): pass

        self.cache_app(A)
        self.assert_cache_has_main(A)
        self.assert_cached_app_has_actions(
            app='A',
            actions={'tests.test_app_cache.A.x': FunctionEntry(run=A.x, is_bound=True, tags=self.action_tag),
                     'tests.test_app_cache.A.y': FunctionEntry(run=A.y, is_bound=True, tags=self.action_tag)})

    def test_cache_app_with_actions_app_name_exists(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

            def z(self): pass

        self.cache._cache['A'] = {}
        self.cache_app(A)
        self.assert_cache_has_main(A)
        self.assert_cached_app_has_actions(
            app='A',
            actions={'tests.test_app_cache.A.x': FunctionEntry(run=A.x, is_bound=True, tags=self.action_tag),
                     'tests.test_app_cache.A.y': FunctionEntry(run=A.y, is_bound=True, tags=self.action_tag)})

    def test_cache_app_with_actions_app_name_exists_main_is_empty(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

            def z(self): pass

        self.cache._cache['A'] = {'main': None}
        self.cache_app(A)
        self.assert_cache_has_main(A)
        self.assert_cached_app_has_actions(
            app='A',
            actions={'tests.test_app_cache.A.x': FunctionEntry(run=A.x, is_bound=True, tags=self.action_tag),
                     'tests.test_app_cache.A.y': FunctionEntry(run=A.y, is_bound=True, tags=self.action_tag)})

    def test_cache_app_with_actions_and_global_actions(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

            def z(self): pass

        def z(): pass

        self.cache_app(A)
        self.cache_action(z, app='A')
        self.assert_cache_has_main(A)
        self.assert_cached_app_has_actions(
            app='A',
            actions={'tests.test_app_cache.A.x': FunctionEntry(run=A.x, is_bound=True, tags=self.action_tag),
                     'tests.test_app_cache.A.y': FunctionEntry(run=A.y, is_bound=True, tags=self.action_tag),
                     'z': FunctionEntry(run=z, is_bound=False, tags=self.action_tag)})

    def test_cache_app_with_actions_and_global_actions_name_conflict_resolved(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

            @action
            def z(self): pass

        def z(): pass

        self.cache_app(A)
        self.cache_action(z, app='A')
        self.assert_cache_has_main(A)
        self.assert_cached_app_has_actions(
            app='A',
            actions={'tests.test_app_cache.A.x': FunctionEntry(run=A.x, is_bound=True, tags=self.action_tag),
                     'tests.test_app_cache.A.y': FunctionEntry(run=A.y, is_bound=True, tags=self.action_tag),
                     'tests.test_app_cache.A.z': FunctionEntry(run=A.z, is_bound=True, tags=self.action_tag),
                     'z': FunctionEntry(run=z, is_bound=False, tags=self.action_tag)})

    def test_clear_existing_bound_functions_no_actions(self):
        class A: pass

        self.cache_app(A)
        self.cache._cache['A'].pop('actions')
        self.cache._clear_existing_bound_functions('A')
        self.assertDictEqual(self.cache._cache, {'A': {'main': A}})

    def test_clear_existing_bound_functions_no_bound_actions(self):
        def x(): pass

        def y(): pass

        self.cache_action(x)
        self.cache_action(y)
        self.cache._clear_existing_bound_functions('app1')
        self.assertDictEqual(self.cache._cache,
                             {'app1': {'actions': {'x': FunctionEntry(run=x, is_bound=False, tags=self.action_tag),
                                               'y': FunctionEntry(run=y, is_bound=False, tags=self.action_tag)}}})

    def test_clear_existing_bound_functions(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

            def z(self): pass

        def z(): pass

        self.cache_app(A)
        self.cache_action(z, app='A')
        self.cache._clear_existing_bound_functions('A')
        self.assertDictEqual(
            self.cache._cache,
            {'A': {'main': A, 'actions': {'z': FunctionEntry(run=z, is_bound=False, tags=self.action_tag)}}})

    def test_cache_module(self):
        module = import_module('tests.testapps.HelloWorldBounded.main')
        from tests.testapps.HelloWorldBounded.main import Main, global1
        self.cache._cache_module(module, 'HelloWorldBounded', 'tests.testapps')
        self.assert_cache_has_main(Main, app='HelloWorldBounded')
        self.assert_cached_app_has_actions(
            app='HelloWorldBounded',
            actions={
                'main.Main.helloWorld': FunctionEntry(run=Main.helloWorld, is_bound=True, tags=self.action_tag),
                'main.Main.repeatBackToMe': FunctionEntry(run=Main.repeatBackToMe, is_bound=True, tags=self.action_tag),
                'main.Main.returnPlusOne': FunctionEntry(run=Main.returnPlusOne, is_bound=True, tags=self.action_tag),
                'main.Main.pause': FunctionEntry(run=Main.pause, is_bound=True, tags=self.action_tag),
                'main.Main.addThree': FunctionEntry(run=Main.addThree, is_bound=True, tags=self.action_tag),
                'main.Main.buggy_action': FunctionEntry(run=Main.buggy_action, is_bound=True, tags=self.action_tag),
                'main.Main.json_sample': FunctionEntry(run=Main.json_sample, is_bound=True, tags=self.action_tag),
                'main.global1': FunctionEntry(run=global1, is_bound=False, tags=self.action_tag)})

    def test_cache_module_nothing_found(self):
        module = import_module('tests.testapps.HelloWorldBounded.display')
        self.cache._cache_module(module, 'HelloWorldBounded', 'tests.testapps')
        self.assertDictEqual(self.cache._cache, {})

    def test_cache_module_no_class(self):
        module = import_module('tests.testapps.HelloWorldBounded.actions')
        self.cache._cache_module(module, 'HelloWorldBounded', 'tests.testapps')
        from tests.testapps.HelloWorldBounded.actions import global2
        self.assert_cached_app_has_actions(
            app='HelloWorldBounded',
            actions={'actions.global2': FunctionEntry(run=global2, is_bound=False, tags=self.action_tag)})

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
        self.assert_cache_has_main(Main, app='HelloWorldBounded')
        expected = {
            'main.Main.helloWorld': FunctionEntry(run=Main.helloWorld, is_bound=True, tags=self.action_tag),
            'main.Main.repeatBackToMe': FunctionEntry(run=Main.repeatBackToMe, is_bound=True, tags=self.action_tag),
            'main.Main.returnPlusOne': FunctionEntry(run=Main.returnPlusOne, is_bound=True, tags=self.action_tag),
            'main.Main.pause': FunctionEntry(run=Main.pause, is_bound=True, tags=self.action_tag),
            'main.Main.addThree': FunctionEntry(run=Main.addThree, is_bound=True, tags=self.action_tag),
            'main.Main.buggy_action': FunctionEntry(run=Main.buggy_action, is_bound=True, tags=self.action_tag),
            'main.Main.json_sample': FunctionEntry(run=Main.json_sample, is_bound=True, tags=self.action_tag),
            'main.global1': FunctionEntry(run=global1, is_bound=False, tags=self.action_tag),
            'actions.global2': FunctionEntry(run=global2, is_bound=False, tags=self.action_tag),
            'conditions.top_level_flag': FunctionEntry(run=top_level_flag, is_bound=False, tags=self.condition_tag),
            'conditions.flag1': FunctionEntry(run=flag1, is_bound=False, tags=self.condition_tag),
            'conditions.flag2': FunctionEntry(run=flag2, is_bound=False, tags=self.condition_tag),
            'conditions.flag3': FunctionEntry(run=flag3, is_bound=False, tags=self.condition_tag),
            'conditions.sub1_top_flag': FunctionEntry(run=sub1_top_flag, is_bound=False, tags=self.condition_tag),
            'conditions.regMatch': FunctionEntry(run=regMatch, is_bound=False, tags=self.condition_tag),
            'conditions.count': FunctionEntry(run=count, is_bound=False, tags=self.condition_tag),
            'transforms.top_level_filter': FunctionEntry(run=top_level_filter, is_bound=False, tags=self.transform_tag),
            'transforms.filter2': FunctionEntry(run=filter2, is_bound=False, tags=self.transform_tag),
            'transforms.sub1_top_filter': FunctionEntry(run=sub1_top_filter, is_bound=False, tags=self.transform_tag),
            'transforms.filter3': FunctionEntry(run=filter3, is_bound=False, tags=self.transform_tag),
            'transforms.filter1':FunctionEntry(run=filter1, is_bound=False, tags=self.transform_tag),
            'transforms.complex_filter': FunctionEntry(run=complex_filter, is_bound=False, tags=self.transform_tag),
            'transforms.length': FunctionEntry(run=length, is_bound=False, tags=self.transform_tag),
            'transforms.json_select': FunctionEntry(run=json_select, is_bound=False, tags=self.transform_tag)}
        self.assert_cached_app_has_actions(app='HelloWorldBounded', actions=expected)

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
        self.assert_cache_has_main(Main, app='HelloWorldBounded')
        expected = {
            'main.Main.helloWorld': FunctionEntry(run=Main.helloWorld, is_bound=True, tags=self.action_tag),
            'main.Main.repeatBackToMe': FunctionEntry(run=Main.repeatBackToMe, is_bound=True, tags=self.action_tag),
            'main.Main.returnPlusOne': FunctionEntry(run=Main.returnPlusOne, is_bound=True, tags=self.action_tag),
            'main.Main.pause': FunctionEntry(run=Main.pause, is_bound=True, tags=self.action_tag),
            'main.Main.addThree': FunctionEntry(run=Main.addThree, is_bound=True, tags=self.action_tag),
            'main.Main.buggy_action': FunctionEntry(run=Main.buggy_action, is_bound=True, tags=self.action_tag),
            'main.Main.json_sample': FunctionEntry(run=Main.json_sample, is_bound=True, tags=self.action_tag),
            'main.global1': FunctionEntry(run=global1, is_bound=False, tags=self.action_tag),
            'actions.global2': FunctionEntry(run=global2, is_bound=False, tags=self.action_tag),
            'conditions.top_level_flag': FunctionEntry(run=top_level_flag, is_bound=False, tags=self.condition_tag),
            'conditions.flag1': FunctionEntry(run=flag1, is_bound=False, tags=self.condition_tag),
            'conditions.flag2': FunctionEntry(run=flag2, is_bound=False, tags=self.condition_tag),
            'conditions.flag3': FunctionEntry(run=flag3, is_bound=False, tags=self.condition_tag),
            'conditions.sub1_top_flag': FunctionEntry(run=sub1_top_flag, is_bound=False, tags=self.condition_tag),
            'conditions.regMatch': FunctionEntry(run=regMatch, is_bound=False, tags=self.condition_tag),
            'conditions.count': FunctionEntry(run=count, is_bound=False, tags=self.condition_tag),
            'transforms.top_level_filter': FunctionEntry(run=top_level_filter, is_bound=False, tags=self.transform_tag),
            'transforms.filter2': FunctionEntry(run=filter2, is_bound=False, tags=self.transform_tag),
            'transforms.sub1_top_filter': FunctionEntry(run=sub1_top_filter, is_bound=False, tags=self.transform_tag),
            'transforms.filter3': FunctionEntry(run=filter3, is_bound=False, tags=self.transform_tag),
            'transforms.filter1': FunctionEntry(run=filter1, is_bound=False, tags=self.transform_tag),
            'transforms.complex_filter': FunctionEntry(run=complex_filter, is_bound=False, tags=self.transform_tag),
            'transforms.length': FunctionEntry(run=length, is_bound=False, tags=self.transform_tag),
            'transforms.json_select': FunctionEntry(run=json_select, is_bound=False, tags=self.transform_tag)}
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
        self.cache.cache_apps(os.path.join('.', 'tests', 'testapps'))
        from tests.testapps.HelloWorldBounded.main import Main, global1
        from tests.testapps.HelloWorldBounded.conditions import (top_level_flag, flag1, flag2, flag3, sub1_top_flag,
                                                                 regMatch, count)
        from tests.testapps.HelloWorldBounded.transforms import (top_level_filter, filter1, filter2, filter3,
                                                                 complex_filter,
                                                                 length, json_select, sub1_top_filter)
        from tests.testapps.HelloWorldBounded.actions import global2
        from tests.testapps.DailyQuote.main import Main as DailyMain
        self.assert_cache_has_main(Main, app='HelloWorldBounded')
        hello_world_expected = {
            'main.Main.helloWorld': FunctionEntry(run=Main.helloWorld, is_bound=True, tags=self.action_tag),
            'main.Main.repeatBackToMe': FunctionEntry(run=Main.repeatBackToMe, is_bound=True, tags=self.action_tag),
            'main.Main.returnPlusOne': FunctionEntry(run=Main.returnPlusOne, is_bound=True, tags=self.action_tag),
            'main.Main.pause': FunctionEntry(run=Main.pause, is_bound=True, tags=self.action_tag),
            'main.Main.addThree': FunctionEntry(run=Main.addThree, is_bound=True, tags=self.action_tag),
            'main.Main.buggy_action': FunctionEntry(run=Main.buggy_action, is_bound=True, tags=self.action_tag),
            'main.Main.json_sample': FunctionEntry(run=Main.json_sample, is_bound=True, tags=self.action_tag),
            'main.global1': FunctionEntry(run=global1, is_bound=False, tags=self.action_tag),
            'actions.global2': FunctionEntry(run=global2, is_bound=False, tags=self.action_tag),
            'conditions.top_level_flag': FunctionEntry(run=top_level_flag, is_bound=False, tags=self.condition_tag),
            'conditions.flag1': FunctionEntry(run=flag1, is_bound=False, tags=self.condition_tag),
            'conditions.flag2': FunctionEntry(run=flag2, is_bound=False, tags=self.condition_tag),
            'conditions.flag3': FunctionEntry(run=flag3, is_bound=False, tags=self.condition_tag),
            'conditions.sub1_top_flag': FunctionEntry(run=sub1_top_flag, is_bound=False, tags=self.condition_tag),
            'conditions.regMatch': FunctionEntry(run=regMatch, is_bound=False, tags=self.condition_tag),
            'conditions.count': FunctionEntry(run=count, is_bound=False, tags=self.condition_tag),
            'transforms.top_level_filter': FunctionEntry(run=top_level_filter, is_bound=False, tags=self.transform_tag),
            'transforms.filter2': FunctionEntry(run=filter2, is_bound=False, tags=self.transform_tag),
            'transforms.sub1_top_filter': FunctionEntry(run=sub1_top_filter, is_bound=False, tags=self.transform_tag),
            'transforms.filter3': FunctionEntry(run=filter3, is_bound=False, tags=self.transform_tag),
            'transforms.filter1': FunctionEntry(run=filter1, is_bound=False, tags=self.transform_tag),
            'transforms.complex_filter': FunctionEntry(run=complex_filter, is_bound=False, tags=self.transform_tag),
            'transforms.length': FunctionEntry(run=length, is_bound=False, tags=self.transform_tag),
            'transforms.json_select': FunctionEntry(run=json_select, is_bound=False, tags=self.transform_tag)}
        self.assert_cached_app_has_actions(app='HelloWorldBounded', actions=hello_world_expected)
        self.assert_cache_has_main(DailyMain, app='DailyQuote')
        daily_quote_expected = {
            'main.Main.quoteIntro': FunctionEntry(run=DailyMain.quoteIntro, is_bound=True, tags=self.action_tag),
            'main.Main.repeatBackToMe':
                FunctionEntry(run=DailyMain.repeatBackToMe, is_bound=True, tags=self.action_tag),
            'main.Main.forismaticQuote':
                FunctionEntry(run=DailyMain.forismaticQuote, is_bound=True, tags=self.action_tag),
            'main.Main.getQuote': FunctionEntry(run=DailyMain.getQuote, is_bound=True, tags=self.action_tag)}
        self.assert_cache_has_apps({'HelloWorldBounded', 'HelloWorld', 'DailyQuote'})
        self.assert_cached_app_has_actions(app='DailyQuote', actions=daily_quote_expected)

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

    def test_get_app_missing_main(self):
        def x(): pass

        self.cache._cache_action(x, 'A', 'tests.test_app_cache.TestAppCache', 'action', cls=TestAppCache)
        with self.assertRaises(UnknownApp):
            self.cache.get_app('A')

    def test_get_app(self):
        class A: pass

        class B: pass

        self.cache_app(A)
        self.cache._cache_app(B, 'B', 'tests.test_app_cache.TestAppCache')
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

        self.cache_app(A)
        with self.assertRaises(UnknownApp):
            self.cache.is_app_action_bound('B', 'tests.test_app_cache.B.x')

    def test_is_app_action_bound_no_actions(self):
        class A: pass

        self.cache_app(A)
        with self.assertRaises(UnknownAppAction):
            self.cache.is_app_action_bound('A', 'tests.test_app_cache.A.x')

    def test_is_app_action_bound_unknown_action(self):
        class A:
            @action
            def x(self): pass

            @action
            def y(self): pass

        self.cache_app(A)
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

        self.cache_app(A)
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

        self.cache_app(A)
        self.cache._cache_app(B, 'B', 'tests.test_app_cache.TestAppCache')
        self.cache._cache_action(xx, 'A', 'tests.test_app_cache.TestAppCache', 'action', cls=TestAppCache)
        self.assertFalse(self.cache.is_app_action_bound('A', 'xx'))


