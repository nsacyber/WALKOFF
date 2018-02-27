from sqlalchemy import and_

from walkoff import executiondb
import walkoff.server.metrics as metrics
from walkoff.server import flaskserver as server
from tests.util.assertwrappers import orderless_list_compare
from tests.util.servertestcase import ServerTestCase
from walkoff.executiondb.playbook import Playbook
from walkoff.executiondb.workflow import Workflow
from tests.util import execution_db_help


class MetricsTest(ServerTestCase):
    def setUp(self):
        metrics.app_metrics = {}
        metrics.workflow_metrics = {}

    def tearDown(self):
        execution_db_help.cleanup_device_db()

    def test_action_metrics(self):
        playbook = execution_db_help.load_playbook('multiactionError')
        workflow_id = executiondb.execution_db.session.query(Workflow).filter(and_(
            Workflow.name == 'multiactionErrorWorkflow', Workflow._playbook_id == playbook.id)).first().id

        server.running_context.executor.execute_workflow(workflow_id)

        server.running_context.executor.wait_and_reset(1)
        self.assertListEqual(list(metrics.app_metrics.keys()), ['HelloWorldBounded'])
        orderless_list_compare(self, list(metrics.app_metrics['HelloWorldBounded'].keys()), ['count', 'actions'])
        self.assertEqual(metrics.app_metrics['HelloWorldBounded']['count'], 3)
        orderless_list_compare(self,
                               list(metrics.app_metrics['HelloWorldBounded']['actions'].keys()),
                               ['repeatBackToMe', 'helloWorld', 'Buggy'])
        orderless_list_compare(self,
                               list(metrics.app_metrics['HelloWorldBounded']['actions']['repeatBackToMe'].keys()),
                               ['success'])
        for form in ['success']:
            orderless_list_compare(self,
                                   list(metrics.app_metrics['HelloWorldBounded']['actions']['repeatBackToMe'][
                                            form].keys()),
                                   ['count', 'avg_time'])
            self.assertEqual(metrics.app_metrics['HelloWorldBounded']['actions']['repeatBackToMe'][form]['count'], 1)
        orderless_list_compare(self,
                               list(metrics.app_metrics['HelloWorldBounded']['actions']['helloWorld'].keys()),
                               ['success'])
        orderless_list_compare(self,
                               list(
                                   metrics.app_metrics['HelloWorldBounded']['actions']['helloWorld']['success'].keys()),
                               ['count', 'avg_time'])
        self.assertEqual(metrics.app_metrics['HelloWorldBounded']['actions']['helloWorld']['success']['count'], 1)

    def test_workflow_metrics(self):
        execution_db_help.load_playbooks(['multiactionError', 'multiactionWorkflowTest'])
        error_id = executiondb.execution_db.session.query(Workflow).join(Workflow._playbook).filter(and_(
            Workflow.name == 'multiactionErrorWorkflow', Playbook.name == 'multiactionError')).first().id
        test_id = executiondb.execution_db.session.query(Workflow).join(Workflow._playbook).filter(and_(
            Workflow.name == 'multiactionWorkflow', Playbook.name == 'multiactionWorkflowTest')).first().id

        error_key = 'multiactionErrorWorkflow'
        multiaction_key = 'multiactionWorkflow'
        server.running_context.executor.execute_workflow(error_id)
        server.running_context.executor.execute_workflow(error_id)
        server.running_context.executor.execute_workflow(test_id)

        server.running_context.executor.wait_and_reset(3)

        keys = [error_key, multiaction_key]
        orderless_list_compare(self,
                               list(metrics.workflow_metrics.keys()),
                               keys)

        for key in keys:
            orderless_list_compare(self, metrics.workflow_metrics[key], ['count', 'avg_time'])

        self.assertEqual(metrics.workflow_metrics[error_key]['count'], 2)
        self.assertEqual(metrics.workflow_metrics[multiaction_key]['count'], 1)
