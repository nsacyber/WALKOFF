import unittest
from core.helpers import import_all_apps
from tests.config import test_apps_path
from tests.apps import *
import importlib
try:
    from importlib import reload
except ImportError:
    from imp import reload


class TestAppsRegistration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import_all_apps(path=test_apps_path)

    def test_app_names_registered(self):
        self.assertSetEqual(set(App.registry.keys()), {'HelloWorld', 'DailyQuote'})

    def test_get_app_main_valid_app(self):
        hello_world_main = importlib.import_module('tests.apps.HelloWorld.main')
        hello_world_main_class = getattr(hello_world_main, 'Main')
        quote_main = importlib.import_module('tests.apps.DailyQuote.main')
        quote_main_class = getattr(quote_main, 'Main')
        self.assertEqual(get_app('HelloWorld'), hello_world_main_class)
        self.assertEqual(get_app('DailyQuote'), quote_main_class)

    def test_get_app_main_invalid_app(self):
        with self.assertRaises(UnknownApp):
            get_app('Invalid')

    def test_get_all_app_actions_valid_app(self):
        actions = get_all_actions_for_app('HelloWorld')
        expected_actions = {'pause', 'helloWorld', 'returnPlusOne', 'repeatBackToMe', 'addThree', 'buggy_action'}
        self.assertSetEqual(set(actions.keys()), expected_actions)
        hello_world_main = importlib.import_module('tests.apps.HelloWorld.main')
        hello_world_main_class = getattr(hello_world_main, 'Main')
        for action_name in expected_actions:
            self.assertEqual(actions[action_name], getattr(hello_world_main_class, action_name))

    def test_get_all_app_actions_invalid_app(self):
        with self.assertRaises(UnknownApp):
            get_all_actions_for_app('Invalid')

    def test_action_can_be_called_with_app_instance(self):
        hello_world_main = importlib.import_module('tests.apps.HelloWorld.main')
        hello_world_main_class = getattr(hello_world_main, 'Main')
        instance = hello_world_main_class()
        self.assertDictEqual(getattr(hello_world_main_class, 'helloWorld')(instance), {'message': 'HELLO WORLD'})

    def test_get_app_action_valid(self):
        hello_world_main = importlib.import_module('tests.apps.HelloWorld.main')
        hello_world_main_class = getattr(hello_world_main, 'Main')
        actions = {'pause', 'helloWorld', 'returnPlusOne', 'repeatBackToMe', 'addThree'}
        for action_name in actions:
            self.assertEquals(get_app_action('HelloWorld', action_name), getattr(hello_world_main_class, action_name))

    def test_get_app_action_invalid_app(self):
        with self.assertRaises(UnknownApp):
            get_app_action('InvalidApp', 'pause')

    def test_get_app_action_invalid_action(self):
        with self.assertRaises(UnknownAppAction):
            get_app_action('HelloWorld', 'invalid')

    def test_get_app_display(self):
        hello_world_display = importlib.import_module('tests.apps.HelloWorld.display')
        display_func = getattr(hello_world_display, 'load')
        self.assertEquals(get_app_display('HelloWorld'), display_func)

    def test_get_app_display_invalid_app(self):
        with self.assertRaises(UnknownApp):
            get_app_display('InvalidApp')