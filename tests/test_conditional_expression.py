import unittest

import walkoff.appgateway
import walkoff.config.config
from walkoff.coredb.conditionalexpression import ConditionalExpression
from walkoff.coredb.argument import Argument
from walkoff.coredb.condition import Condition
from tests.config import test_apps_path
import walkoff.config.paths
from tests.util import device_db_help
import walkoff.coredb.devicedb as devicedb


class TestCondition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        device_db_help.setup_dbs()
        walkoff.appgateway.clear_cache()
        walkoff.appgateway.cache_apps(path=test_apps_path)
        walkoff.config.config.load_app_apis(test_apps_path)

    def tearDown(self):
        for class_ in (ConditionalExpression, Condition, Argument):
            for expression in devicedb.device_db.session.query(class_).all():
                devicedb.device_db.session.delete(expression)
        devicedb.device_db.session.commit()

    @classmethod
    def tearDownClass(cls):
        device_db_help.tear_down_device_db()
        walkoff.appgateway.clear_cache()        

    def assert_construction(self, expression, operator, child_expression_ids=None, condition_ids=None):
        self.assertEqual(expression.operator, operator)
        if child_expression_ids is None:
            child_expression_ids = set()
        self.assertSetEqual({expr.id for expr in expression.child_expressions}, set(child_expression_ids))
        if condition_ids is None:
            condition_ids = []