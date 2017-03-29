from datetime import datetime
import unittest
from os import mkdir
from os.path import isdir

from core.config.paths import profile_visualizations_path
from core import controller
from core import graphDecorator
from core.helpers import construct_workflow_name_key
from tests import config
import core.case.subscription as case_subscription
import core.case.database as case_database
from tests.util.case_db_help import executed_steps, setup_subscriptions_for_step
from tests.util.assertwrappers import orderless_list_compare


class TestExecutionRuntime(unittest.TestCase):
    def setUp(self):
        case_database.initialize()
        self.c = controller.Controller()
        if not isdir(profile_visualizations_path):
            mkdir(profile_visualizations_path)
        self.start = datetime.utcnow()
        controller.initialize_threading()

    def tearDown(self):
        case_database.case_db.tearDown()
        case_subscription.clear_subscriptions()
        controller.shutdown_pool()

    """
        Tests the out templating function which replaces the value of an argument with the output from the workflow history.
    """

    @graphDecorator.callgraph(enabled=False)
    def test_TemplatedWorkflow(self):
        self.c.loadWorkflowsFromFile(path=config.testWorkflowsPath + 'templatedWorkflowTest.workflow')
        workflow_name = construct_workflow_name_key('templatedWorkflowTest', 'templatedWorkflow')
        step_names = ['start', '1']
        setup_subscriptions_for_step(workflow_name, step_names)
        self.c.executeWorkflow('templatedWorkflowTest', 'templatedWorkflow')

        workflow = self.c.get_workflow('templatedWorkflowTest', 'templatedWorkflow')

        # print("about to spin")
        # while (workflow.is_completed == False):
        #     continue
        #
        # print("Workflow should be completed!")

        # import time
        # print("sleeping")
        # time.sleep(3)
        # print("awake")

        from core.case.database import case_db, Event
        #print(case_db.session.query(Event).all())

        steps = executed_steps('defaultController', workflow_name, self.start, datetime.utcnow())
        self.assertEqual(len(steps), 2, 'Unexpected number of steps executed. '
                                        'Expected {0}, got {1}'.format(2, len(steps)))
        names = [step['ancestry'].split(',')[-1] for step in steps]
        orderless_list_compare(self, names, step_names)
        name_result = {'start': {"message": "HELLO WORLD"},
                       '1': "REPEATING: {'message': 'HELLO WORLD'}"}

        for step in steps:
            name = step['ancestry'].split(',')[-1]
            self.assertIn(name, name_result)
            if type(name_result[name]) == dict:
                self.assertDictEqual(step['data']['result'], name_result[name])
            else:
                self.assertEqual(step['data']['result'], name_result[name])

    """
        Tests the calling of nested workflows
    """

    @graphDecorator.callgraph(enabled=False)
    def test_SimpleTieredWorkflow(self):
        self.c.loadWorkflowsFromFile(path=config.testWorkflowsPath + 'tieredWorkflow.workflow')
        workflow_name1 = construct_workflow_name_key('tieredWorkflow', 'parentWorkflow')
        workflow_name2 = construct_workflow_name_key('tieredWorkflow', 'childWorkflow')
        step_names = ['start', '1']
        setup_subscriptions_for_step([workflow_name1, workflow_name2], step_names)
        self.c.executeWorkflow('tieredWorkflow', 'parentWorkflow')
        steps = executed_steps('defaultController', workflow_name1, self.start, datetime.utcnow())
        steps.extend(executed_steps('defaultController', workflow_name2, self.start, datetime.utcnow()))
        ancestries = [step['ancestry'].split(',') for step in steps]
        name_ids = [(ancestry[-2], ancestry[-1]) for ancestry in ancestries]
        expected_ids = [(workflow_name1, 'start'), (workflow_name1, '1'), (workflow_name2, 'start')]
        orderless_list_compare(self, name_ids, expected_ids)

        name_result = {(workflow_name1, 'start'): "REPEATING: Parent Step One",
                       (workflow_name2, 'start'): "REPEATING: Child Step One",
                       (workflow_name1, '1'): "REPEATING: Parent Step Two"}

        for step in steps:
            ancestry = step['ancestry'].split(',')
            name_id = (ancestry[-2], ancestry[-1])
            self.assertIn(name_id, name_result)
            if type(name_result[name_id]) == dict:
                self.assertDictEqual(step['data']['result'], name_result[name_id])
            else:
                self.assertEqual(step['data']['result'], name_result[name_id])

    """
        Tests a workflow that loops a few times
    """

    @graphDecorator.callgraph(enabled=False)
    def test_Loop(self):
        self.c.loadWorkflowsFromFile(path=config.testWorkflowsPath +'loopWorkflow.workflow')
        workflow_name = construct_workflow_name_key('loopWorkflow', 'loopWorkflow')
        step_names = ['start', '1']
        setup_subscriptions_for_step(workflow_name, step_names)
        self.c.executeWorkflow('loopWorkflow', 'loopWorkflow')
        steps = executed_steps('defaultController', workflow_name, self.start, datetime.utcnow())
        names = [step['ancestry'].split(',')[-1] for step in steps]
        expected_steps = ['start', 'start', 'start', 'start', '1']
        self.assertListEqual(names, expected_steps)
        self.assertEqual(len(steps), 5)

        input_output = [('start', 1), ('start', 2), ('start', 3), ('start', 4), ('1', 'REPEATING: 5')]
        for step_name, output in input_output:
            for step in steps:
                name = step['ancestry'].split(',')
                if name == step_name:
                    self.assertEqual(step['data']['result'], output)