import unittest

from tests.apps.HelloWorld.main import Main
import core.config.paths
from core import instance, helpers
from tests.config import test_apps_path


class TestInstance(unittest.TestCase):
    def setUp(self):
        core.config.paths.apps_path = test_apps_path

    def test_create_instance(self):
        inst = instance.Instance.create("HelloWorld", "testDevice")
        self.assertIsInstance(inst, instance.Instance)
        self.assertIsInstance(inst.instance, Main)
        self.assertEqual(inst.state, instance.OK)

    def test_create_invalid_app_name(self):
        self.assertIsNone(instance.Instance.create("InvalidAppName", "testDevice"))

    def test_call(self):
        inst = instance.Instance.create("HelloWorld", "testDevice")
        created_app = inst()
        self.assertIsInstance(created_app, Main)

    def test_shutdown(self):
        inst = instance.Instance.create("HelloWorld", "testDevice")
        self.assertEqual(inst.state, instance.OK)
        inst.shutdown()
        self.assertEqual(inst.state, instance.SHUTDOWN)
