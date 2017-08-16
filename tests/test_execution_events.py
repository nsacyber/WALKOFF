import unittest
import core.case.database as case_database
import core.case.subscription as case_subscription
from core.controller import Controller, shutdown_pool, initialize_threading
from core.helpers import import_all_flags, import_all_filters, import_all_apps
from tests import config
import core.config.config
from tests.apps import App


class TestExecutionEvents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        App.registry = {}
        import_all_apps(path=config.test_apps_path, reload=True)
        core.config.config.load_app_apis(apps_path=config.test_apps_path)
        core.config.config.flags = import_all_flags('tests.util.flagsfilters')
        core.config.config.filters = import_all_filters('tests.util.flagsfilters')
        core.config.config.load_flagfilter_apis(path=config.function_api_path)

    def setUp(self):
        initialize_threading()
        case_database.initialize()

    def tearDown(self):
        case_database.case_db.tear_down()

    def test_workflow_execution_events(self):
        c = Controller()
        c.load_workflows_from_file(path=config.test_workflows_path + 'multiactionWorkflowTest.playbook')
        workflow_uid = c.get_workflow('multiactionWorkflowTest', 'multiactionWorkflow').uid
        subs = {'case1': {workflow_uid: ['App Instance Created', 'Step Execution Success',
                                         'Next Step Found', 'Workflow Shutdown']}}
        case_subscription.set_subscriptions(subs)
        c.execute_workflow('multiactionWorkflowTest', 'multiactionWorkflow')

        shutdown_pool()
        execution_events = case_database.case_db.session.query(case_database.Case) \
            .filter(case_database.Case.name == 'case1').first().events.all()
        self.assertEqual(len(execution_events), 6,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(6, len(execution_events)))

    def test_step_execution_events(self):
        c = Controller()
        c.load_workflows_from_file(path=config.test_workflows_path + 'basicWorkflowTest.playbook')
        workflow = c.get_workflow('basicWorkflowTest', 'helloWorldWorkflow')
        step_uids = [step.uid for step in workflow.steps.values()]
        step_events = ['Function Execution Success', 'Input Validated', 'Conditionals Executed']
        subs = {'case1': {step_uid: step_events for step_uid in step_uids}}
        case_subscription.set_subscriptions(subs)

        c.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')

        shutdown_pool()

        execution_events = case_database.case_db.session.query(case_database.Case) \
            .filter(case_database.Case.name == 'case1').first().events.all()
        self.assertEqual(len(execution_events), 3,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(3, len(execution_events)))

    def test_flag_filters_execution_events(self):
        c = Controller()
        c.load_workflows_from_file(path=config.test_workflows_path + 'basicWorkflowTest.playbook')
        workflow = c.get_workflow('basicWorkflowTest', 'helloWorldWorkflow')
        step = workflow.steps['start']
        subs = {step.uid: ['Function Execution Success', 'Input Validated', 'Conditionals Executed']}
        next_step = next(conditional for conditional in step.conditionals if conditional.name == '1')
        subs[next_step.uid] = ['Next Step Taken', 'Next Step Not Taken']
        flag = next(flag for flag in next_step.flags if flag.action == 'regMatch')
        subs[flag.uid] = ['Flag Success', 'Flag Error']
        filter_ = next(filter_elem for filter_elem in flag.filters if filter_elem.action == 'length')
        subs[filter_.uid] = ['Filter Success', 'Filter Error']

        case_subscription.set_subscriptions({'case1': subs})

        c.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')

        shutdown_pool()

        events = case_database.case_db.session.query(case_database.Case) \
            .filter(case_database.Case.name == 'case1').first().events.all()
        self.assertEqual(len(events), 6,
                         'Incorrect length of event history. '
                         'Expected {0}, got {1}'.format(6, len(events)))
