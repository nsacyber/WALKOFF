import unittest

import walkoff.appgateway
import walkoff.config.config
import walkoff.config.paths
from walkoff.executiondb.argument import Argument
from walkoff.appgateway.actionresult import ActionResult
from walkoff.events import WalkoffEvent
from walkoff.executiondb.action import Action
from walkoff.executiondb.branch import Branch
from walkoff.executiondb.condition import Condition
from walkoff.executiondb.conditionalexpression import ConditionalExpression
from walkoff.executiondb.workflow import Workflow
from tests.config import test_apps_path
from tests.util import device_db_help


class TestBranch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        device_db_help.setup_dbs()
        walkoff.appgateway.cache_apps(test_apps_path)
        walkoff.config.config.load_app_apis(apps_path=test_apps_path)

    @classmethod
    def tearDownClass(cls):
        walkoff.appgateway.clear_cache()
        device_db_help.tear_down_device_db()

    def __compare_init(self, elem, source_id, destination_id, condition=None, status='Success', priority=999):
        self.assertEqual(elem.source_id, source_id)
        self.assertEqual(elem.destination_id, destination_id)
        self.assertEqual(elem.status, status)
        self.assertEqual(elem.priority, priority)
        if condition:
            self.assertEqual(elem.condition.operator, condition.operator)

    def test_init(self):
        branch = Branch(source_id=1, destination_id=2)
        self.__compare_init(branch, 1, 2)

    def test_init_with_status(self):
        branch = Branch(source_id=1, destination_id=2, status='test_status')
        self.__compare_init(branch, 1, 2, status='test_status')

    def test_init_with_conditions(self):
         condition = ConditionalExpression(
             'and',
             conditions=[Condition('HelloWorld', 'Top Condition'), Condition('HelloWorld', 'mod1_flag1')])
         branch = Branch(1, 2, condition=condition)
         self.__compare_init(branch, 1, 2, condition=condition)

    def test_eq(self):
        condition = ConditionalExpression(
            'and',
            conditions=[Condition('HelloWorld', 'mod1_flag1'), Condition('HelloWorld', 'Top Condition')])
        branches = [Branch(source_id=1, destination_id=2),
                    Branch(source_id=1, destination_id=2, status='TestStatus'),
                    Branch(source_id=1, destination_id=2, condition=condition)]
        for i in range(len(branches)):
            for j in range(len(branches)):
                if i == j:
                    self.assertEqual(branches[i], branches[j])
                else:
                    self.assertNotEqual(branches[i], branches[j])

    def test_execute(self):
        condition1 = ConditionalExpression(
            'and',
            conditions=[Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='(.*)')])])
        condition2 = ConditionalExpression(
            'and',
            conditions=[Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='(.*)')]),
                        Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='a')])])

        inputs = [('name1', None, ActionResult('aaaa', 'Success'), True),
                  ('name2', condition1, ActionResult('anyString', 'Success'), True),
                  ('name3', condition2, ActionResult('anyString', 'Success'), True),
                  ('name4', condition2, ActionResult('bbbb', 'Success'), False),
                  ('name4', condition2, ActionResult('aaaa', 'Custom'), False)]

        for name, condition, input_str, expect_name in inputs:
            branch = Branch(source_id=1, destination_id=2, condition=condition)
            if expect_name:
                expected_name = branch.destination_id
                self.assertEqual(branch.execute(input_str, {}), expected_name)
            else:
                self.assertIsNone(branch.execute(input_str, {}))

    def test_get_branch_no_branchs(self):
        workflow = Workflow('test', 1)
        self.assertIsNone(workflow.get_branch(None, {}))

    def test_get_branch_invalid_action(self):
        condition = ConditionalExpression(
            'and',
            conditions=[Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='aaa')])])
        branch = Branch(source_id=1, destination_id=2, condition=condition)
        action = Action('HelloWorld', 'helloWorld', 'helloWorld')
        action._output = ActionResult(result='bbb', status='Success')
        workflow = Workflow('test', 1, actions=[action], branches=[branch])
        self.assertIsNone(workflow.get_branch(action, {}))

    def test_get_branch(self):
        action = Action('HelloWorld', 'helloWorld', 'helloWorld', id=10)

        condition = ConditionalExpression(
            'and',
            conditions=[Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='aaa')])])
        branch = Branch(source_id=action.id, destination_id=2, condition=condition)
        action._output = ActionResult(result='aaa', status='Success')
        workflow = Workflow("helloWorld", 1, actions=[action], branches=[branch])

        result = {'triggered': False}

        def validate_sent_data(sender, **kwargs):
            if isinstance(sender, Branch):
                self.assertIn('event', kwargs)
                self.assertEqual(kwargs['event'], WalkoffEvent.BranchTaken)
                result['triggered'] = True

        WalkoffEvent.CommonWorkflowSignal.connect(validate_sent_data)

        self.assertEqual(workflow.get_branch(action, {}), 2)
        self.assertTrue(result['triggered'])

    def test_branch_with_priority(self):
        action = Action('HelloWorld', 'helloWorld', 'helloWorld', id=10)

        condition = ConditionalExpression(
            'and',
            conditions=[Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='aaa')])])

        branch_one = Branch(source_id=action.id, destination_id=5, condition=condition, priority=5)
        branch_two = Branch(source_id=action.id, destination_id=1, condition=condition, priority=1)

        action._output = ActionResult(result='aaa', status='Success')
        workflow = Workflow('test', 1, actions=[action], branches=[branch_one, branch_two])

        self.assertEqual(workflow.get_branch(action, {}), 1)
