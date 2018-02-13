import unittest

import walkoff.appgateway
import walkoff.config.config
from walkoff.coredb.conditionalexpression import ConditionalExpression
from walkoff.coredb.argument import Argument
from walkoff.coredb.condition import Condition
from tests.config import test_apps_path
import walkoff.config.paths
from tests.util import device_db_help
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

    def assert_construction(self, expression, operator='and', is_inverted=False, child_expressions=None, conditions=None):
        self.assertEqual(expression.operator, operator)
        self.assertEqual(expression.is_inverted, is_inverted)
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
        expression = ConditionalExpression()
        self.assert_construction(expression)

    def test_init_with_operator(self):
        expression = ConditionalExpression(operator='or')
        self.assert_construction(expression, operator='or')

    def test_init_inverted(self):
        expression = ConditionalExpression(is_inverted=True)
        self.assert_construction(expression, is_inverted=True)

    def test_init_with_conditions(self):
        conditions = [self.get_always_true_condition(), Condition('HelloWorld', 'mod1_flag1')]
        expression = ConditionalExpression(operator='or', conditions=conditions)
        self.assert_construction(expression, operator='or', conditions=conditions)

    def test_init_with_child_expressions(self):
        children = [ConditionalExpression() for _ in range(3)]
        expression = ConditionalExpression(child_expressions=children)
        self.assert_construction(expression, child_expressions=children)

    def test_execute_no_conditions(self):
        for operator in ('and', 'or', 'xor'):
            expression = ConditionalExpression(operator=operator)
            self.assertTrue(expression.execute('', {}))

    def test_execute_inverted(self):
        expression = ConditionalExpression(is_inverted=True)
        self.assertFalse(expression.execute('', {}))

    def test_execute_and_conditions_only(self):
        expression = ConditionalExpression(conditions=[self.get_regex_condition(), self.get_regex_condition('aa')])
        self.assertTrue(expression.execute('aaa', {}))
        self.assertFalse(expression.execute('bbb', {}))

    def test_execute_and_expressions_only(self):
        expression = ConditionalExpression(
            child_expressions=[
                ConditionalExpression(conditions=[self.get_regex_condition('aa')]),
                ConditionalExpression(conditions=[self.get_regex_condition('bb')])])
        self.assertTrue(expression.execute('aabb', {}))
        for false_pattern in ('aa', 'bb', 'cc'):
            self.assertFalse(expression.execute(false_pattern, {}))

    def test_execute_and_with_conditions_and_expressions(self):
        expression = ConditionalExpression(
            conditions=[self.get_regex_condition('aa')],
            child_expressions=[
                ConditionalExpression(conditions=[self.get_regex_condition('bb')]),
                ConditionalExpression(conditions=[self.get_regex_condition('cc')])])
        self.assertTrue(expression.execute('aabbcc', {}))
        for false_pattern in ('aa', 'bb', 'cc', 'dd'):
            self.assertFalse(expression.execute(false_pattern, {}))

    def test_execute_or_conditions_only(self):
        expression = ConditionalExpression(
            operator='or', conditions=[self.get_regex_condition('bb'), self.get_regex_condition('aa')])
        for true_pattern in ('aa', 'bb', 'aabb'):
            self.assertTrue(expression.execute(true_pattern, {}))
        self.assertFalse(expression.execute('ccc', {}))

    def test_execute_or_expressions_only(self):
        expression = ConditionalExpression(
            operator='or',
            child_expressions=[
                ConditionalExpression(conditions=[self.get_regex_condition('aa')]),
                ConditionalExpression(conditions=[self.get_regex_condition('bb')])])
        for true_pattern in ('aa', 'bb', 'aabb'):
            self.assertTrue(expression.execute(true_pattern, {}))
        self.assertFalse(expression.execute('ccc', {}))

    def test_execute_or_with_conditions_and_expressions(self):
        expression = ConditionalExpression(
            operator='or',
            conditions=[self.get_regex_condition('aa')],
            child_expressions=[
                ConditionalExpression(conditions=[self.get_regex_condition('bb')]),
                ConditionalExpression(conditions=[self.get_regex_condition('cc')])])
        for true_pattern in ('aa', 'bb', 'cc', 'aabb', 'bbcc', 'aacc'):
            self.assertTrue(expression.execute(true_pattern, {}))
        self.assertFalse(expression.execute('d', {}))

    def test_execute_xor_conditions_only(self):
        expression = ConditionalExpression(
            operator='xor', conditions=[self.get_regex_condition('bb'), self.get_regex_condition('aa')])
        for true_pattern in ('aa', 'bb'):
            self.assertTrue(expression.execute(true_pattern, {}))
        for false_pattern in ('aabb', 'cc'):
            self.assertFalse(expression.execute(false_pattern, {}))

    def test_execute_xor_expressions_only(self):
        expression = ConditionalExpression(
            operator='xor',
            child_expressions=[
                ConditionalExpression(conditions=[self.get_regex_condition('aa')]),
                ConditionalExpression(conditions=[self.get_regex_condition('bb')])])
        for true_pattern in ('aa', 'bb'):
            self.assertTrue(expression.execute(true_pattern, {}))
        for false_pattern in ('aabb', 'cc'):
            self.assertFalse(expression.execute(false_pattern, {}))

    def test_execute_xor_with_conditions_and_expressions(self):
        expression = ConditionalExpression(
            operator='xor',
            conditions=[self.get_regex_condition('aa')],
            child_expressions=[
                ConditionalExpression(conditions=[self.get_regex_condition('bb')]),
                ConditionalExpression(conditions=[self.get_regex_condition('cc')])])
        for true_pattern in ('aa', 'bb', 'cc'):
            self.assertTrue(expression.execute(true_pattern, {}))
        for false_pattern in ('aabb', 'bbcc', 'aacc', 'd'):
            self.assertFalse(expression.execute(false_pattern, {}))

    def test_execute_true_sends_event(self):
        expression = ConditionalExpression(conditions=[self.get_always_true_condition()])
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
        expression = ConditionalExpression(conditions=[self.get_always_true_condition()], is_inverted=True)
        result = {'triggered': False}

        @WalkoffEvent.CommonWorkflowSignal.connect
        def callback_is_sent(sender, **kwargs):
            if isinstance(sender, ConditionalExpression):
                self.assertIn('event', kwargs)
                self.assertEqual(kwargs['event'], WalkoffEvent.ConditionalExpressionFalse)
                result['triggered'] = True

        expression.execute('3.4', {})

        self.assertTrue(result['triggered'])

    def test_execute_error_sends_event(self):
        expression = ConditionalExpression(conditions=[Condition('HelloWorld', 'mod1_flag1')])
        result = {'triggered': False}

        @WalkoffEvent.CommonWorkflowSignal.connect
        def callback_is_sent(sender, **kwargs):
            if isinstance(sender, ConditionalExpression):
                self.assertIn('event', kwargs)
                self.assertEqual(kwargs['event'], WalkoffEvent.ConditionalExpressionError)
                result['triggered'] = True

        self.assertFalse(expression.execute('any', {}))
        self.assertTrue(result['triggered'])

    def test_read_does_not_infinitely_recurse(self):
        expression = ConditionalExpression(
            operator='xor',
            conditions=[self.get_regex_condition('aa')],
            child_expressions=[
                ConditionalExpression(conditions=[self.get_regex_condition('bb')]),
                ConditionalExpression(conditions=[self.get_regex_condition('cc')])])
        expression.read()