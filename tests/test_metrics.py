from tests.util.servertestcase import ServerTestCase
from server import flaskserver as server
from tests import config
from tests.util.assertwrappers import orderless_list_compare
import server.metrics as metrics
from core.helpers import construct_workflow_name_key


class MetricsTest(ServerTestCase):
    def setUp(self):
        metrics.app_metrics = {}
        metrics.workflow_metrics = {}

    def test_action_metrics(self):
        server.running_context.controller.load_workflows_from_file(path=config.test_workflows_path +
                                                                        'multistepError.workflow')

        server.running_context.controller.execute_workflow('multistepError', 'multiactionErrorWorkflow')

        with server.running_context.flask_app.app_context():
            server.running_context.shutdown_threads()
        self.assertListEqual(list(metrics.app_metrics.keys()), ['HelloWorld'])
        orderless_list_compare(self, list(metrics.app_metrics['HelloWorld'].keys()), ['count', 'actions'])

        self.assertEqual(metrics.app_metrics['HelloWorld']['count'], 3)
        orderless_list_compare(self,
                               list(metrics.app_metrics['HelloWorld']['actions'].keys()),
                               ['repeatBackToMe', 'helloWorld'])
        orderless_list_compare(self,
                               list(metrics.app_metrics['HelloWorld']['actions']['repeatBackToMe'].keys()),
                               ['success', 'error'])
        for form in ['success', 'error']:
            orderless_list_compare(self,
                                   list(metrics.app_metrics['HelloWorld']['actions']['repeatBackToMe'][form].keys()),
                                   ['count', 'avg_time'])
            self.assertEqual(metrics.app_metrics['HelloWorld']['actions']['repeatBackToMe'][form]['count'], 1)
        orderless_list_compare(self,
                               list(metrics.app_metrics['HelloWorld']['actions']['helloWorld'].keys()),
                               ['success'])
        orderless_list_compare(self,
                               list(metrics.app_metrics['HelloWorld']['actions']['helloWorld']['success'].keys()),
                               ['count', 'avg_time'])
        self.assertEqual(metrics.app_metrics['HelloWorld']['actions']['helloWorld']['success']['count'], 1)

    def test_workflow_metrics(self):
        server.running_context.controller.load_workflows_from_file(path=config.test_workflows_path +
                                                                       'multistepError.workflow')
        server.running_context.controller.load_workflows_from_file(path=config.test_workflows_path +
                                                                        'tieredWorkflow.workflow')
        server.running_context.controller.load_workflows_from_file(path=config.test_workflows_path +
                                                                        'multiactionWorkflowTest.workflow')
        error_key = construct_workflow_name_key('multistepError', 'multiactionErrorWorkflow')
        tiered_parent_key = construct_workflow_name_key('tieredWorkflow', 'parentWorkflow')
        tiered_child_key = construct_workflow_name_key('tieredWorkflow', 'childWorkflow')
        multiaction_key = construct_workflow_name_key('multiactionWorkflowTest', 'multiactionWorkflow')
        server.running_context.controller.execute_workflow('multistepError', 'multiactionErrorWorkflow')
        server.running_context.controller.execute_workflow('tieredWorkflow', 'parentWorkflow')
        server.running_context.controller.execute_workflow('multistepError', 'multiactionErrorWorkflow')
        server.running_context.controller.execute_workflow('tieredWorkflow', 'parentWorkflow')
        server.running_context.controller.execute_workflow('multiactionWorkflowTest', 'multiactionWorkflow')
        keys = [error_key, tiered_child_key, tiered_parent_key, multiaction_key]
        orderless_list_compare(self,
                               list(metrics.workflow_metrics.keys()),
                               keys)
        for key in keys:
            orderless_list_compare(self, metrics.workflow_metrics[key], ['count', 'avg_time'])

        self.assertEqual(metrics.workflow_metrics[error_key]['count'], 2)
        self.assertEqual(metrics.workflow_metrics[tiered_parent_key]['count'], 2)
        self.assertEqual(metrics.workflow_metrics[tiered_child_key]['count'], 2)
        self.assertEqual(metrics.workflow_metrics[multiaction_key]['count'], 1)
