import unittest

import walkoff.appgateway
from tests.util import execution_db_help, initialize_test_config
from walkoff.appgateway.actionresult import ActionResult
from walkoff.events import WalkoffEvent
from walkoff.executiondb.action import Action
from walkoff.executiondb.argument import Argument
from walkoff.executiondb.branch import Branch
from walkoff.executiondb.condition import Condition
from walkoff.executiondb.conditionalexpression import ConditionalExpression
from walkoff.executiondb.workflow import Workflow
from walkoff.worker.action_exec_strategy import LocalActionExecutionStrategy
from walkoff.worker.workflow_exec_context import WorkflowExecutionContext
from walkoff.worker.workflow_exec_strategy import SerialWorkflowExecutionStrategy as Executor


class TestBranch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initialize_test_config()
        execution_db_help.setup_dbs()

    @classmethod
    def tearDownClass(cls):
        walkoff.appgateway.clear_cache()
        execution_db_help.tear_down_execution_db()

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
        class MockAction(object):
            id = 13

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

        for name, condition, previous_result, expect_name in inputs:
            branch = Branch(source_id=1, destination_id=2, condition=condition)
            acc = {MockAction.id: previous_result.result}
            status = previous_result.status
            action = MockAction()
            if expect_name:
                expected_name = branch.destination_id
                self.assertEqual(branch.execute(LocalActionExecutionStrategy(), status, action, acc), expected_name)
            else:
                self.assertIsNone(branch.execute(LocalActionExecutionStrategy(), status, action, acc))

    def test_get_branch_no_branches(self):
        workflow = Workflow('test', 1)
        wf_ctx = WorkflowExecutionContext(workflow, {}, None, None)
        self.assertIsNone(Executor.get_branch(wf_ctx, LocalActionExecutionStrategy()))

    def test_get_branch(self):
        action = Action('HelloWorld', 'helloWorld', 'helloWorld', id=10)
        action2 = Action('HelloWorld', 'helloWorld', 'helloWorld', id=2)
        condition = ConditionalExpression(
            'and',
            conditions=[Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='aaa')])])
        branch = Branch(source_id=action.id, destination_id=2, condition=condition)
        action_result = ActionResult(result='aaa', status='Success')
        workflow = Workflow("helloWorld", action.id, actions=[action, action2], branches=[branch])

        wf_ctx = WorkflowExecutionContext(workflow, {}, None, None)
        wf_ctx.accumulator[action.id] = action_result.result
        wf_ctx.last_status = action_result.status
        wf_ctx.executing_action = action

        result = {'triggered': False}

        def validate_sent_data(sender, **kwargs):
            if isinstance(sender, Branch):
                self.assertIn('event', kwargs)
                self.assertEqual(kwargs['event'], WalkoffEvent.BranchTaken)
                result['triggered'] = True

        WalkoffEvent.CommonWorkflowSignal.connect(validate_sent_data)

        self.assertEqual(Executor.get_branch(wf_ctx, LocalActionExecutionStrategy()), 2)
        self.assertTrue(result['triggered'])

    def test_branch_with_priority(self):
        action = Action('HelloWorld', 'helloWorld', 'helloWorld', id=10)
        action2 = Action('HelloWorld', 'helloWorld', 'helloWorld', id=5)
        action3 = Action('HelloWorld', 'helloWorld', 'helloWorld', id=1)

        condition = ConditionalExpression(
            'and',
            conditions=[Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='aaa')])])

        branch_one = Branch(source_id=action.id, destination_id=5, condition=condition, priority=5)
        branch_two = Branch(source_id=action.id, destination_id=1, condition=condition, priority=1)

        action_result = ActionResult(result='aaa', status='Success')
        workflow = Workflow('test', 1, actions=[action, action2, action3], branches=[branch_one, branch_two])
        wf_ctx = WorkflowExecutionContext(workflow, {}, None, None)
        wf_ctx.accumulator[action.id] = action_result.result
        wf_ctx.last_status = action_result.status
        wf_ctx.executing_action = action

        self.assertEqual(Executor.get_branch(wf_ctx, LocalActionExecutionStrategy()), 1)

    def test_branch_first_action_none(self):
        action = Action('HelloWorld', 'helloWorld', 'helloWorld', id=10)
        action2 = Action('HelloWorld', 'helloWorld', 'helloWorld', id=5)
        action3 = Action('HelloWorld', 'helloWorld', 'helloWorld', id=1)

        condition = ConditionalExpression(
            'and',
            conditions=[Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='123')])])
        condition2 = ConditionalExpression(
            'and',
            conditions=[Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='aaa')])])

        branch_one = Branch(source_id=action.id, destination_id=5, condition=condition, priority=1)
        branch_two = Branch(source_id=action.id, destination_id=1, condition=condition2, priority=5)

        action_result = ActionResult(result='aaa', status='Success')
        workflow = Workflow('test', 1, actions=[action, action2, action3], branches=[branch_one, branch_two])
        wf_ctx = WorkflowExecutionContext(workflow, {}, None, None)
        wf_ctx.accumulator[action.id] = action_result.result
        wf_ctx.last_status = action_result.status
        wf_ctx.executing_action = action
        self.assertEqual(Executor.get_branch(wf_ctx, LocalActionExecutionStrategy()), 1)

    def test_branch_counter(self):
        action = Action('HelloWorld', 'helloWorld', 'helloWorld', id=1)

        branch = Branch(source_id=action.id, destination_id=action.id)
        self.assertEqual(branch._counter, 0)

        action_result = ActionResult(result='aaa', status='Success')
        workflow = Workflow('test', 1, actions=[action], branches=[branch])
        wf_ctx = WorkflowExecutionContext(workflow, None, None)
        wf_ctx.accumulator[action.id] = action_result.result
        wf_ctx.last_status = action_result.status
        wf_ctx.executing_action = action
        Executor.get_branch(wf_ctx, LocalActionExecutionStrategy())

        self.assertEqual(branch._counter, 1)
        self.assertIn(branch.id, wf_ctx.accumulator)
        self.assertEqual(wf_ctx.accumulator[branch.id], '1')
