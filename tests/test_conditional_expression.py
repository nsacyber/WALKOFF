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
from uuid import UUID, uuid4

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

    def assert_construction(self, expression, operator, id=None, child_expression_ids=None, condition_ids=None):
        self.assertEqual(expression.operator, operator)
        if child_expression_ids is None:
            child_expression_ids = set()
        self.assertSetEqual({expr.id for expr in expression.child_expressions}, set(child_expression_ids))
        if condition_ids is None:
            condition_ids = set()
        self.assertSetEqual({condition.id for condition in expression.conditions}, set(condition_ids))
        if id is None:
            self.assertIsInstance(expression.id, UUID)
        else:
            self.assertEqual(expression.id, id)

    def test_init(self):
        expression = ConditionalExpression('and')
        self.assert_construction(expression, 'and')

    def test_init_with_id(self):
        id_ = uuid4()
        expression = ConditionalExpression('and', id=id_)
        self.assert_construction(expression, 'and', id=id_)

    def test_init_with_conditions(self):
        conditions = [Condition('HelloWorld', 'Top Condition'), Condition('HelloWorld', 'mod1_flag1')]
        for condition in conditions:
            devicedb.device_db.session.add(condition)
        devicedb.device_db.session.flush()
        expression = ConditionalExpression('or', conditions=conditions)
        self.assert_construction(expression, 'or', condition_ids={condition.id for condition in conditions})

    def test_init_with_child_expressions(self):
        children = [ConditionalExpression('and') for _ in range(3)]
        for child in children:
            devicedb.device_db.session.add(child)
        devicedb.device_db.session.flush()
        expression = ConditionalExpression('truth', child_expressions=children)
        self.assert_construction(expression, 'truth', child_expression_ids={expr.id for expr in children})

    def test_init_with_invalid_enum(self):
        ConditionalExpression('invalid')