from tests.util.servertestcase import ServerTestCase
from server import flaskserver as server
from tests import config
from tests.util.assertwrappers import orderless_list_compare
import server.metrics as metrics


class MetricsTest(ServerTestCase):

    def setUp(self):
        metrics.app_metrics = {}
        metrics.workflow_metrics = {}
        server.running_context.controller.initialize_threading()

    def test_action_metrics(self):
        server.running_context.controller.load_workflows_from_file(path=config.test_workflows_path +
                                                                        'multistepError.playbook')

        server.running_context.controller.execute_workflow('multistepError', 'multiactionErrorWorkflow')

        server.running_context.controller.shutdown_pool(1)
        self.assertListEqual(list(metrics.app_metrics.keys()), ['HelloWorld'])
        orderless_list_compare(self, list(metrics.app_metrics['HelloWorld'].keys()), ['count', 'actions'])

        self.assertEqual(metrics.app_metrics['HelloWorld']['count'], 3)
        orderless_list_compare(self,
                               list(metrics.app_metrics['HelloWorld']['actions'].keys()),
                               ['repeatBackToMe', 'helloWorld', 'Buggy'])
        orderless_list_compare(self,
                               list(metrics.app_metrics['HelloWorld']['actions']['repeatBackToMe'].keys()),
                               ['success'])
        for form in ['success']:
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
                                                                        'multistepError.playbook')
        server.running_context.controller.load_workflows_from_file(path=config.test_workflows_path +
                                                                        'multiactionWorkflowTest.playbook')

        error_key = 'multiactionErrorWorkflow'
        multiaction_key = 'multiactionWorkflow'
        server.running_context.controller.execute_workflow('multistepError', 'multiactionErrorWorkflow')
        server.running_context.controller.execute_workflow('multistepError', 'multiactionErrorWorkflow')
        server.running_context.controller.execute_workflow('multiactionWorkflowTest', 'multiactionWorkflow')

        server.running_context.controller.shutdown_pool(3)

        keys = [error_key, multiaction_key]
        orderless_list_compare(self,
                               list(metrics.workflow_metrics.keys()),
                               keys)

        for key in keys:
            orderless_list_compare(self, metrics.workflow_metrics[key], ['count', 'avg_time'])

        self.assertEqual(metrics.workflow_metrics[error_key]['count'], 2)
        self.assertEqual(metrics.workflow_metrics[multiaction_key]['count'], 1)
