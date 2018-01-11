import unittest

import walkoff.appgateway
import walkoff.config.config
import walkoff.config.paths
from walkoff.coredb.argument import Argument
from walkoff.core.actionresult import ActionResult
from walkoff.events import WalkoffEvent
from walkoff.coredb.action import Action
from walkoff.coredb.branch import Branch
from walkoff.coredb.condition import Condition
from walkoff.coredb.workflow import Workflow
from tests.config import test_apps_path
import walkoff.coredb.devicedb
import tests.config
from walkoff import initialize_databases


class TestBranch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        walkoff.config.paths.db_path = tests.config.test_db_path
        walkoff.config.paths.case_db_path = tests.config.test_case_db_path
        walkoff.config.paths.device_db_path = tests.config.test_device_db_path
        initialize_databases()
        walkoff.appgateway.cache_apps(test_apps_path)
        walkoff.config.config.load_app_apis(apps_path=test_apps_path)

    @classmethod
    def tearDownClass(cls):
        walkoff.appgateway.clear_cache()

    def __compare_init(self, elem, source_id, destination_id, conditions=None, status='Success', priority=999):
        self.assertEqual(elem.source_id, source_id)
        self.assertEqual(elem.destination_id, destination_id)
        self.assertEqual(elem.status, status)
        self.assertEqual(elem.priority, priority)
        if conditions:
            self.assertListEqual(elem.conditions, conditions)

    def test_init(self):
        branch = Branch(source_id=1, destination_id=2)
        self.__compare_init(branch, 1, 2)

    def test_init_with_status(self):
        branch = Branch(source_id=1, destination_id=2, status='test_status')
        self.__compare_init(branch, 1, 2, status='test_status')

    def test_init_with_empty_conditions(self):
        branch = Branch(source_id=1, destination_id=2, conditions=[])
        self.__compare_init(branch, 1, 2)

    # def test_init_with_conditions(self):
    #     conditions = [Condition('HelloWorld', 'Top Condition'), Condition('HelloWorld', 'mod1_flag1')]
    #     expected_condition_json = [{'action_name': 'Top Condition', 'args': [], 'filters': []},
    #                                {'action_name': 'mod1_flag1', 'args': [], 'filters': []}]
    #     branch = Branch("1", "2", conditions=conditions)
    #     self.__compare_init(branch, "1", "2", expected_condition_json)

    def test_eq(self):
        conditions = [Condition('HelloWorld', 'mod1_flag1'), Condition('HelloWorld', 'Top Condition')]
        branches = [Branch(source_id=1, destination_id=2),
                    Branch(source_id=1, destination_id=2, status='TestStatus'),
                    Branch(source_id=1, destination_id=2, conditions=conditions)]
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
            branch = Branch(source_id=1, destination_id=2, conditions=conditions)
            if expect_name:
                expected_name = branch.destination_id
                self.assertEqual(branch.execute(input_str, {}), expected_name)
            else:
                self.assertIsNone(branch.execute(input_str, {}))

    def test_get_branch_no_branchs(self):
        workflow = Workflow()
        self.assertIsNone(workflow.get_branch(None, {}))

    def test_get_branch_invalid_action(self):
        flag = Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='aaa')])
        branch = Branch(source_id=1, destination_id=2, conditions=[flag])
        action = Action('HelloWorld', 'helloWorld')
        action._output = ActionResult(result='bbb', status='Success')
        workflow = Workflow(actions=[action], branches=[branch])
        self.assertIsNone(workflow.get_branch(action, {}))

    def test_get_branch(self):
        action = Action('HelloWorld', 'helloWorld')
        walkoff.coredb.devicedb.device_db.session.add(action)
        walkoff.coredb.devicedb.device_db.session.commit()

        condition = Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='aaa')])
        branch = Branch(source_id=action.id, destination_id=2, conditions=[condition])
        action._output = ActionResult(result='aaa', status='Success')
        workflow = Workflow(actions=[action], branches=[branch])

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
        action = Action('HelloWorld', 'helloWorld')
        walkoff.coredb.devicedb.device_db.session.add(action)
        walkoff.coredb.devicedb.device_db.session.commit()

        condition = Condition('HelloWorld', action_name='regMatch', arguments=[Argument('regex', value='aaa')])

        branch_one = Branch(source_id=action.id, destination_id=5, conditions=[condition], priority=5)
        branch_two = Branch(source_id=action.id, destination_id=1, conditions=[condition], priority=1)

        action._output = ActionResult(result='aaa', status='Success')
        workflow = Workflow(actions=[action], branches=[branch_one, branch_two])
        walkoff.coredb.devicedb.device_db.session.add(workflow)
        walkoff.coredb.devicedb.device_db.session.commit()

        self.assertEqual(workflow.get_branch(action, {}), 1)
