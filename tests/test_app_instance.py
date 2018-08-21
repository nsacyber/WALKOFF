import importlib
import unittest

import walkoff.appgateway
from tests.util import execution_db_help, initialize_test_config
from walkoff.appgateway import appinstance
from uuid import uuid4


class TestInstance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initialize_test_config()
        execution_db_help.setup_dbs()

    @classmethod
    def tearDownClass(cls):
        execution_db_help.tear_down_execution_db()
        walkoff.appgateway.clear_cache()

    def test_create_instance(self):
        # extra janky way to import this because we still need a more predictable and consistent way to import modules
        hello_world_main = importlib.import_module('tests.testapps.HelloWorld.main')
        hello_world_main_class = getattr(hello_world_main, 'Main')
        context = {'workflow_execution_id': uuid4()}
        inst = appinstance.AppInstance.create("HelloWorld", "testDevice", context)
        self.assertIsInstance(inst, appinstance.AppInstance)
        self.assertIsInstance(inst.instance, hello_world_main_class)
        self.assertDictEqual(inst.instance.context, context)

    def test_call(self):
        context = {'workflow_execution_id': uuid4()}
        inst = appinstance.AppInstance.create("HelloWorld", "testDevice", context)
        created_app = inst()

        hello_world_main = importlib.import_module('tests.testapps.HelloWorld.main')
        hello_world_main_class = getattr(hello_world_main, 'Main')
        self.assertIsInstance(created_app, hello_world_main_class)

    def test_shutdown(self):
        context = {'workflow_execution_id': uuid4()}
        inst = appinstance.AppInstance.create("HelloWorld", "testDevice", context)
        created_app = inst()
        created_app.foo = 42
        created_app.bar = 'abc'
        cache = created_app._cache

        pattern = created_app._get_field_pattern()
        inst.shutdown()
        self.assertListEqual(list(cache.scan(pattern)), [])