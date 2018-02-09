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
from walkoff.helpers import InvalidExecutionElement
from walkoff.events import WalkoffEvent


class TestCondition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        device_db_help.setup_dbs()
        walkoff.appgateway.clear_cache()
        walkoff.appgateway.cache_apps(path=test_apps_path)
        walkoff.config.config.load_app_apis(test_apps_path)

    @classmethod
    def tearDownClass(cls):
        device_db_help.tear_down_device_db()
        walkoff.appgateway.clear_cache()        

    def assert_construction(self, expression, operator, child_expressions=None, conditions=None):
        self.assertEqual(expression.operator, operator)
        if child_expressions is None:
            child_expressions = []
        self.assertEqual(len(expression.child_expressions), len(child_expressions))
        if conditions is None:
            conditions = set()
        self.assertEqual(len(expression.conditions), len(conditions))

    @staticmethod
    def get_always_true_condition():
        return Condition('HelloWorld', 'Top Condition')

    @staticmethod
    def get_regex_condition(pattern='(.*)'):
        return Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value=pattern)])

    def test_init(self):
        expression = ConditionalExpression('and')
        self.assert_construction(expression, 'and')

    def test_init_with_conditions(self):
        conditions = [self.get_always_true_condition(), Condition('HelloWorld', 'mod1_flag1')]
        expression = ConditionalExpression('or', conditions=conditions)
        self.assert_construction(expression, 'or', conditions=conditions)

    def test_init_with_child_expressions(self):
        children = [ConditionalExpression('and') for _ in range(3)]
        expression = ConditionalExpression('and', child_expressions=children)
        self.assert_construction(expression, 'and', child_expressions=children)

    def assert_too_many_conditions_raises_exception(self, operator):
        conditions = [self.get_always_true_condition(), Condition('HelloWorld', 'mod1_flag1')]
        with self.assertRaises(InvalidExecutionElement):
            ConditionalExpression(operator, conditions=conditions)
        children = [ConditionalExpression('and') for _ in range(3)]
        with self.assertRaises(InvalidExecutionElement):
            ConditionalExpression(operator, child_expressions=children)
        with self.assertRaises(InvalidExecutionElement):
            ConditionalExpression(operator, child_expressions=children, conditions=conditions)

    def assert_no_conditions_raises_exception(self, operator):
        with self.assertRaises(InvalidExecutionElement):
            ConditionalExpression(operator)

    def test_init_truth_operator_too_many_conditions(self):
        self.assert_too_many_conditions_raises_exception('truth')

    def test_init_truth_operator_too_no_conditions(self):
        self.assert_no_conditions_raises_exception('truth')

    def test_init_not_operator_too_many_conditions(self):
        self.assert_too_many_conditions_raises_exception('not')

    def test_init_not_operator_too_no_conditions(self):
        self.assert_no_conditions_raises_exception('not')

    def test_execute_truth_with_condition(self):
        condition = Condition('HelloWorld', 'Top Condition')
        expression = ConditionalExpression('truth', conditions=[condition])
        self.assertTrue(expression.execute('3.4', {}))

    def test_execute_truth_with_expression(self):
        condition = ConditionalExpression('truth', conditions=[self.get_always_true_condition()])
        expression = ConditionalExpression('truth', child_expressions=[condition])
        self.assertTrue(expression.execute('3.4', {}))

    def test_execute_not_with_condition(self):
        expression = ConditionalExpression('not', conditions=[self.get_always_true_condition()])
        self.assertFalse(expression.execute('3.4', {}))

    def test_execute_not_with_expression(self):
        condition = ConditionalExpression('truth', conditions=[self.get_always_true_condition()])
        expression = ConditionalExpression('not', child_expressions=[condition])
        self.assertFalse(expression.execute('3.4', {}))

    def test_execute_and_conditions_only(self):
        expression = ConditionalExpression(
            'and', conditions=[self.get_regex_condition(), self.get_regex_condition('aa')])
        self.assertTrue(expression.execute('aaa', {}))
        self.assertFalse(expression.execute('bbb', {}))

    def test_execute_and_expressions_only(self):
        expression = ConditionalExpression(
            'and',
            child_expressions=[
                ConditionalExpression('truth', conditions=[self.get_regex_condition()]),
                ConditionalExpression('not', conditions=[self.get_regex_condition('ab')])])
        self.assertTrue(expression.execute('aaa', {}))
        self.assertFalse(expression.execute('ab', {}))

    def test_execute_and_with_conditions_and_expressions(self):
        expression = ConditionalExpression(
            'and',
            conditions=[self.get_regex_condition('aa')],
            child_expressions=[
                ConditionalExpression('truth', conditions=[self.get_regex_condition()]),
                ConditionalExpression('not', conditions=[self.get_regex_condition('ab')])])
        self.assertTrue(expression.execute('aaa', {}))
        self.assertFalse(expression.execute('aab', {}))

    def test_execute_or_conditions_only(self):
        expression = ConditionalExpression(
            'or', conditions=[self.get_regex_condition('bb'), self.get_regex_condition('aa')])
        for true_pattern in ('aa', 'bb', 'aabb'):
            self.assertTrue(expression.execute(true_pattern, {}))
        self.assertFalse(expression.execute('ccc', {}))

    def test_execute_or_expressions_only(self):
        expression = ConditionalExpression(
            'or',
            child_expressions=[
                ConditionalExpression('truth', conditions=[self.get_regex_condition('aa')]),
                ConditionalExpression('truth', conditions=[self.get_regex_condition('bb')])])
        for true_pattern in ('aa', 'bb', 'aabb'):
            self.assertTrue(expression.execute(true_pattern, {}))
        self.assertFalse(expression.execute('ccc', {}))

    def test_execute_or_with_conditions_and_expressions(self):
        expression = ConditionalExpression(
            'or',
            conditions=[self.get_regex_condition('aa')],
            child_expressions=[
                ConditionalExpression('truth', conditions=[self.get_regex_condition('bb')]),
                ConditionalExpression('truth', conditions=[self.get_regex_condition('cc')])])
        for true_pattern in ('aa', 'bb', 'cc', 'aabb', 'bbcc', 'aacc'):
            self.assertTrue(expression.execute(true_pattern, {}))
        self.assertFalse(expression.execute('d', {}))

    def test_execute_xor_conditions_only(self):
        expression = ConditionalExpression(
            'xor', conditions=[self.get_regex_condition('bb'), self.get_regex_condition('aa')])
        for true_pattern in ('aa', 'bb'):
            self.assertTrue(expression.execute(true_pattern, {}))
        for false_pattern in ('aabb', 'cc'):
            self.assertFalse(expression.execute(false_pattern, {}))

    def test_execute_xor_expressions_only(self):
        expression = ConditionalExpression(
            'xor',
            child_expressions=[
                ConditionalExpression('truth', conditions=[self.get_regex_condition('aa')]),
                ConditionalExpression('truth', conditions=[self.get_regex_condition('bb')])])
        for true_pattern in ('aa', 'bb'):
            self.assertTrue(expression.execute(true_pattern, {}))
        for false_pattern in ('aabb', 'cc'):
            self.assertFalse(expression.execute(false_pattern, {}))

    def test_execute_xor_with_conditions_and_expressions(self):
        expression = ConditionalExpression(
            'xor',
            conditions=[self.get_regex_condition('aa')],
            child_expressions=[
                ConditionalExpression('truth', conditions=[self.get_regex_condition('bb')]),
                ConditionalExpression('truth', conditions=[self.get_regex_condition('cc')])])
        for true_pattern in ('aa', 'bb', 'cc'):
            self.assertTrue(expression.execute(true_pattern, {}))
        for false_pattern in ('aabb', 'bbcc', 'aacc', 'd'):
            self.assertFalse(expression.execute(false_pattern, {}))

    def test_execute_true_sends_event(self):
        expression = ConditionalExpression('truth', conditions=[self.get_always_true_condition()])
        result = {'triggered': False}

        @WalkoffEvent.CommonWorkflowSignal.connect
        def callback_is_sent(sender, **kwargs):
            if isinstance(sender, ConditionalExpression):
                self.assertIn('event', kwargs)
                self.assertEqual(kwargs['event'], WalkoffEvent.ConditionalExpressionTrue)
                result['triggered'] = True

        expression.execute('3.4', {})

        self.assertTrue(result['triggered'])

    def test_execute_false_sends_event(self):
        expression = ConditionalExpression('not', conditions=[self.get_always_true_condition()])
        result = {'triggered': False}

        @WalkoffEvent.CommonWorkflowSignal.connect
        def callback_is_sent(sender, **kwargs):
            if isinstance(sender, ConditionalExpression):
                self.assertIn('event', kwargs)
                self.assertEqual(kwargs['event'], WalkoffEvent.ConditionalExpressionFalse)
                result['triggered'] = True

        expression.execute('3.4', {})

        self.assertTrue(result['triggered'])
