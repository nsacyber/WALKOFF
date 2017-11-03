import unittest

import apps
import core.config.config
from core.controller import Controller
from tests import config


class TestController(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        apps.cache_apps(config.test_apps_path)
        core.config.config.load_app_apis(apps_path=config.test_apps_path)

    def setUp(self):
        self.controller = Controller()

    @classmethod
    def tearDownClass(cls):
        apps.clear_cache()

    def test_create_controller(self):
        self.assertEqual(self.controller.uid, "controller")
