from datetime import datetime
import unittest
from os import mkdir
from os.path import isdir
import json
from core.config.paths import profile_visualizations_path
from core.helpers import construct_workflow_name_key, import_all_apps, import_all_filters, import_all_flags
from tests import config
from core.case import database
from core.case import subscription
import core.config.config
from tests.util.case_db_help import executed_steps, setup_subscriptions_for_step
from tests.util.assertwrappers import orderless_list_compare
from core.controller import initialize_threading, shutdown_pool, Controller
from tests.apps import App


class TestExecutionRuntime(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        App.registry = {}
        import_all_apps(path=config.test_apps_path, reload=True)
        core.config.config.load_app_apis(apps_path=config.test_apps_path)
        core.config.config.flags = import_all_flags('tests.util.flagsfilters')
        core.config.config.filters = import_all_filters('tests.util.flagsfilters')
        core.config.config.load_flagfilter_apis(path=config.function_api_path)

    def setUp(self):
        database.initialize()
        if not isdir(profile_visualizations_path):
            mkdir(profile_visualizations_path)
        self.start = datetime.utcnow()
        initialize_threading()
        self.controller = Controller(workflows_path=config.test_workflows_path)

    def tearDown(self):
        database.case_db.tear_down()
        subscription.clear_subscriptions()

    """
        Tests the out templating function which replaces the value of an argument with the output
        from the workflow history.
    """

    def test_templated_workflow(self):
        workflow_name = construct_workflow_name_key('templatedWorkflowTest', 'templatedWorkflow')
        step_names = ['start', '1']
        setup_subscriptions_for_step(workflow_name, step_names)
        self.controller.execute_workflow('templatedWorkflowTest', 'templatedWorkflow')

        shutdown_pool()

        steps = executed_steps('defaultController', workflow_name, self.start, datetime.utcnow())
        self.assertEqual(len(steps), 2, 'Unexpected number of steps executed. '
                                        'Expected {0}, got {1}'.format(2, len(steps)))
        names = [step['ancestry'].split(',')[-1] for step in steps]
        orderless_list_compare(self, names, step_names)
        name_result = {'start': {'result': {'message': 'HELLO WORLD'}, 'status': 'Success'},
                       '1': {'status': 'Success', 'result': "REPEATING: {'message': 'HELLO WORLD'}"}}

        for step in steps:
            name = step['ancestry'].split(',')[-1]
            self.assertIn(name, name_result)
            result = json.loads(step['data'])
            self.assertDictEqual(result['result'], name_result[name])

    """
        Tests the calling of nested workflows
    """

    def test_simple_tiered_workflow(self):
        workflow_name1 = construct_workflow_name_key('tieredWorkflow', 'parentWorkflow')
        workflow_name2 = construct_workflow_name_key('tieredWorkflow', 'childWorkflow')
        step_names = ['start', '1']
        setup_subscriptions_for_step([workflow_name1, workflow_name2], step_names)
        self.controller.execute_workflow('tieredWorkflow', 'parentWorkflow')

        shutdown_pool()

        steps = executed_steps('defaultController', workflow_name1, self.start, datetime.utcnow())
        steps.extend(executed_steps('defaultController', workflow_name2, self.start, datetime.utcnow()))
        ancestries = [step['ancestry'].split(',') for step in steps]
        name_ids = [(ancestry[-2], ancestry[-1]) for ancestry in ancestries]
        expected_ids = [(workflow_name1, 'start'), (workflow_name1, '1'), (workflow_name2, 'start')]
        orderless_list_compare(self, name_ids, expected_ids)

        name_result = {(workflow_name1, 'start'):  {'status': 'Success', 'result': 'REPEATING: Parent Step One'},
                       (workflow_name2, 'start'):  {'status': 'Success', 'result': 'REPEATING: Child Step One'},
                       (workflow_name1, '1'): {'status': 'Success', 'result': 'REPEATING: Parent Step Two'}}

        for step in steps:
            ancestry = step['ancestry'].split(',')
            name_id = (ancestry[-2], ancestry[-1])
            self.assertIn(name_id, name_result)
            result = json.loads(step['data'])
            if type(name_result[name_id]) == dict:
                self.assertDictEqual(result['result'], name_result[name_id])
            else:
                self.assertEqual(result['result'], name_result[name_id])

    """
        Tests a workflow that loops a few times
    """

    def test_loop(self):
        from gevent import monkey, spawn
        from gevent.event import Event
        from core.case.callbacks import WorkflowShutdown
        monkey.patch_all()

        workflow_name = construct_workflow_name_key('loopWorkflow', 'loopWorkflow')
        step_names = ['start', '1']
        setup_subscriptions_for_step(workflow_name, step_names)

        waiter = Event()

        def wait_for_shutdown(sender, **kwargs):
            waiter.set()

        WorkflowShutdown.connect(wait_for_shutdown)
        self.controller.execute_workflow('loopWorkflow', 'loopWorkflow')
        shutdown_pool()
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
                    result = json.loads(step['data'])
                    self.assertEqual(result['result'], output)
