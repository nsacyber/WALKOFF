import importlib
import unittest

import walkoff.appgateway
import walkoff.config.paths
from tests.config import test_apps_path
from tests.util import execution_db_help
from walkoff.appgateway import appinstance


class TestInstance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        execution_db_help.setup_dbs()
        walkoff.appgateway.cache_apps(test_apps_path)

    @classmethod
    def tearDownClass(cls):
        execution_db_help.tear_down_execution_db()
        walkoff.appgateway.clear_cache()

    def test_create_instance(self):
        # extra janky way to import this because we still need a more predictable and consistent way to import modules
        hello_world_main = importlib.import_module('tests.testapps.HelloWorld.main')
        hello_world_main_class = getattr(hello_world_main, 'Main')
        inst = appinstance.AppInstance.create("HelloWorld", "testDevice")
        self.assertIsInstance(inst, appinstance.AppInstance)
        self.assertIsInstance(inst.instance, hello_world_main_class)

    def test_create_invalid_app_name(self):
        instance = appinstance.AppInstance.create("InvalidAppName", "testDevice")
        self.assertIsNone(instance.instance)

    def test_call(self):
        inst = appinstance.AppInstance.create("HelloWorld", "testDevice")
        created_app = inst()
        hello_world_main = importlib.import_module('tests.testapps.HelloWorld.main')
        hello_world_main_class = getattr(hello_world_main, 'Main')
        self.assertIsInstance(created_app, hello_world_main_class)
