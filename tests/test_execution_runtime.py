from datetime import datetime
import unittest
from core.helpers import construct_workflow_name_key, import_all_apps, import_all_filters, import_all_flags
from tests import config
from core.case import subscription
import core.config.config
import core.case.database as case_database
from tests.util.case_db_help import executed_steps, setup_subscriptions_for_step
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
        self.start = datetime.utcnow()
        initialize_threading()
        case_database.initialize()
        self.controller = Controller(workflows_path=config.test_workflows_path)

    def tearDown(self):
        subscription.clear_subscriptions()

    def test_templated_workflow(self):
        step_names = ['start', '1']

        workflow = self.controller.get_workflow('templatedWorkflowTest', 'templatedWorkflow')
        step_uids = [step.uid for step in workflow.steps.values() if step.name in step_names]
        setup_subscriptions_for_step(workflow.uid, step_uids)
        self.controller.execute_workflow('templatedWorkflowTest', 'templatedWorkflow')

        shutdown_pool()

        steps = []
        for uid in step_uids:
            steps.extend(executed_steps(uid, self.start, datetime.utcnow()))
        self.assertEqual(len(steps), 2, 'Unexpected number of steps executed. '
                                        'Expected {0}, got {1}'.format(2, len(steps)))

    def test_simple_tiered_workflow(self):
        workflow_name1 = construct_workflow_name_key('tieredWorkflow', 'parentWorkflow')
        workflow_name2 = construct_workflow_name_key('tieredWorkflow', 'childWorkflow')
        workflow1 = self.controller.get_workflow('tieredWorkflow', 'parentWorkflow')
        workflow2 = self.controller.get_workflow('tieredWorkflow', 'childWorkflow')
        step_names = ['start', '1']
        step_uids = [step.uid for step in workflow1.steps.values() if step.name in step_names]
        step_uids.extend([step.uid for step in workflow2.steps.values() if step.name in step_names])
        setup_subscriptions_for_step([workflow_name1, workflow_name2], step_uids)
        self.controller.execute_workflow('tieredWorkflow', 'parentWorkflow')

        shutdown_pool()
        steps = []
        for uid in step_uids:
            steps.extend(executed_steps(uid, self.start, datetime.utcnow()))
        expected_results = [{'status': 'Success', 'result': 'REPEATING: Parent Step One'},
                            {'status': 'Success', 'result': 'REPEATING: Child Step One'},
                            {'status': 'Success', 'result': 'REPEATING: Parent Step Two'}]
        self.assertEqual(len(steps), 3)
        for result in [step['data']['result'] for step in steps]:
            self.assertIn(result, expected_results)

    def test_loop(self):
        from gevent import monkey
        from gevent.event import Event
        from core.case.callbacks import WorkflowShutdown
        monkey.patch_all()

        workflow = self.controller.get_workflow('loopWorkflow', 'loopWorkflow')
        step_names = ['start', '1']
        step_uids = [step.uid for step in workflow.steps.values() if step.name in step_names]
        setup_subscriptions_for_step(workflow.uid, step_uids)

        waiter = Event()

        def wait_for_shutdown(sender, **kwargs):
            waiter.set()

        WorkflowShutdown.connect(wait_for_shutdown)
        self.controller.execute_workflow('loopWorkflow', 'loopWorkflow')
        shutdown_pool()
        steps = []
        for uid in step_uids:
            steps.extend(executed_steps(uid, self.start, datetime.utcnow()))

        self.assertEqual(len(steps), 5)
