import unittest

from core import instance
from tests.config import test_apps_path
from tests.apps import App
from core.helpers import import_all_apps
import importlib

class TestInstance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        App.registry = {}
        import_all_apps(path=test_apps_path, reload=True)

    def test_create_instance(self):
        # extra janky way to import this because we still need a more predictable and consistent way to import modules
        hello_world_main = importlib.import_module('tests.apps.HelloWorld.main')
        hello_world_main_class = getattr(hello_world_main, 'Main')
        inst = instance.Instance.create("HelloWorld", "testDevice")
        self.assertIsInstance(inst, instance.Instance)
        self.assertIsInstance(inst.instance, hello_world_main_class)
        self.assertEqual(inst.state, instance.OK)

    def test_create_invalid_app_name(self):
        self.assertIsNone(instance.Instance.create("InvalidAppName", "testDevice"))

    def test_call(self):
        inst = instance.Instance.create("HelloWorld", "testDevice")
        created_app = inst()
        hello_world_main = importlib.import_module('tests.apps.HelloWorld.main')
        hello_world_main_class = getattr(hello_world_main, 'Main')
        self.assertIsInstance(created_app, hello_world_main_class)

    def test_shutdown(self):
        inst = instance.Instance.create("HelloWorld", "testDevice")
        self.assertEqual(inst.state, instance.OK)
        inst.shutdown()
        self.assertEqual(inst.state, instance.SHUTDOWN)
