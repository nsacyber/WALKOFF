import unittest
import uuid

import apps
import core.config.config
from core.argument import Argument
from core.decorators import ActionResult
from core.events import WalkoffEvent
from core.executionelements.action import Action
from core.executionelements.branch import Branch
from core.executionelements.condition import Condition
from core.executionelements.workflow import Workflow
from tests.config import test_apps_path


class TestBranch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        apps.cache_apps(test_apps_path)
        core.config.config.load_app_apis(apps_path=test_apps_path)

    @classmethod
    def tearDownClass(cls):
        apps.clear_cache()

    def __compare_init(self, elem, source_uid, destination_uid, conditions=None, status='Success', uid=None,
                       priority=999):
        self.assertEqual(elem.source_uid, source_uid)
        self.assertEqual(elem.destination_uid, destination_uid)
        self.assertEqual(elem.status, status)
        self.assertEqual(elem.priority, priority)
        if conditions:
            self.assertListEqual([condition.action_name for condition in elem.conditions],
                                 [condition['action_name'] for condition in conditions])
        if uid is None:
            self.assertIsNotNone(elem.uid)
        else:
            self.assertEqual(elem.uid, uid)

    def test_init(self):
        branch = Branch(source_uid="1", destination_uid="2")
        self.__compare_init(branch, "1", "2")

    def test_init_wth_uid(self):
        uid = uuid.uuid4().hex
        branch = Branch(source_uid="1", destination_uid="2", uid=uid)
        self.__compare_init(branch, "1", "2", uid=uid)

    def test_init_with_status(self):
        branch = Branch(source_uid="1", destination_uid="2", status='test_status')
        self.__compare_init(branch, "1", "2", status='test_status')

    def test_init_with_empty_conditions(self):
        branch = Branch(source_uid="1", destination_uid="2", conditions=[])
        self.__compare_init(branch, '1', '2')

    def test_init_with_conditions(self):
        conditions = [Condition('HelloWorld', 'Top Condition'), Condition('HelloWorld', 'mod1_flag1')]
        expected_condition_json = [{'action_name': 'Top Condition', 'args': [], 'filters': []},
                                   {'action_name': 'mod1_flag1', 'args': [], 'filters': []}]
        branch = Branch("1", "2", conditions=conditions)
        self.__compare_init(branch, "1", "2", expected_condition_json)

    def test_eq(self):
        conditions = [Condition('HelloWorld', 'mod1_flag1'), Condition('HelloWorld', 'Top Condition')]
        branches = [Branch(source_uid="1", destination_uid="2"),
                    Branch(source_uid="1", destination_uid="2", status='TestStatus'),
                    Branch(source_uid="1", destination_uid="2", conditions=conditions)]
        for i in range(len(branches)):
            for j in range(len(branches)):
                if i == j:
                    self.assertEqual(branches[i], branches[j])
                else:
                    self.assertNotEqual(branches[i], branches[j])

    def test_execute(self):
        conditions1 = [Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='(.*)')])]
        conditions2 = [Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='(.*)')]),
                       Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='a')])]

        inputs = [('name1', [], ActionResult('aaaa', 'Success'), True),
                  ('name2', conditions1, ActionResult('anyString', 'Success'), True),
                  ('name3', conditions2, ActionResult('anyString', 'Success'), True),
                  ('name4', conditions2, ActionResult('bbbb', 'Success'), False),
                  ('name4', conditions2, ActionResult('aaaa', 'Custom'), False)]

        for name, conditions, input_str, expect_name in inputs:
            branch = Branch(source_uid="1", destination_uid="2", conditions=conditions)
            if expect_name:
                expected_name = branch.destination_uid
                self.assertEqual(branch.execute(input_str, {}), expected_name)
            else:
                self.assertIsNone(branch.execute(input_str, {}))

    def test_get_branch_no_branchs(self):
        workflow = Workflow()
        self.assertIsNone(workflow.get_branch(None, {}))

    def test_get_branch_invalid_action(self):
        flag = Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='aaa')])
        branch = Branch(source_uid="1", destination_uid='next', conditions=[flag])
        action = Action('HelloWorld', 'helloWorld', uid="2")
        action._output = ActionResult(result='bbb', status='Success')
        workflow = Workflow(actions=[action], branches=[branch])
        self.assertIsNone(workflow.get_branch(action, {}))

    def test_get_branch(self):
        flag = Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='aaa')])
        branch = Branch(source_uid="1", destination_uid="2", conditions=[flag])
        action = Action('HelloWorld', 'helloWorld', uid="1")
        action._output = ActionResult(result='aaa', status='Success')
        workflow = Workflow(actions=[action], branches=[branch])

        result = {'triggered': False}

        def validate_sent_data(sender, **kwargs):
            if isinstance(sender, Branch):
                self.assertIn('event', kwargs)
                self.assertEqual(kwargs['event'], WalkoffEvent.BranchTaken)
                result['triggered'] = True

        WalkoffEvent.CommonWorkflowSignal.connect(validate_sent_data)

        self.assertEqual(workflow.get_branch(action, {}), '2')
        self.assertTrue(result['triggered'])

    def test_branch_with_priority(self):
        flag = Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='aaa')])
        branch_one = Branch(source_uid="1", destination_uid='five', conditions=[flag], priority="5")
        branch_two = Branch(source_uid="1", destination_uid='one', conditions=[flag], priority="1")
        action = Action('HelloWorld', 'helloWorld', uid="1")
        action._output = ActionResult(result='aaa', status='Success')
        workflow = Workflow(actions=[action], branches=[branch_one, branch_two])
        self.assertEqual(workflow.get_branch(action, {}), "one")
