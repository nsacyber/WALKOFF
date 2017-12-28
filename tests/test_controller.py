import unittest

import apps
import walkoff.appgateway
import walkoff.config.config
from walkoff.core.controller import Controller
from tests import config


class TestController(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        walkoff.appgateway.cache_apps(config.test_apps_path)
        walkoff.config.config.load_app_apis(apps_path=config.test_apps_path)

    def setUp(self):
        self.controller = Controller()

    @classmethod
    def tearDownClass(cls):
        walkoff.appgateway.clear_cache()

    def test_create_controller(self):
        self.assertEqual(self.controller.uid, "controller")
