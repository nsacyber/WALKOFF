from sqlalchemy import and_

from tests.util import execution_db_help
from tests.util.servertestcase import ServerTestCase
from walkoff.executiondb.playbook import Playbook
from walkoff.executiondb.workflow import Workflow
from walkoff.server import flaskserver as server
from walkoff.executiondb.metrics import AppMetric, WorkflowMetric


class MetricsTest(ServerTestCase):

    def tearDown(self):
        execution_db_help.cleanup_execution_db()

    def test_action_metrics(self):
        playbook = execution_db_help.load_playbook('multiactionError')
        workflow_id = server.app.running_context.execution_db.session.query(Workflow).filter(and_(
            Workflow.name == 'multiactionErrorWorkflow', Workflow.playbook_id == playbook.id)).first().id

        server.app.running_context.executor.execute_workflow(workflow_id)

        server.app.running_context.executor.wait_and_reset(1)

        app_metrics = server.app.running_context.execution_db.session.query(AppMetric).all()
        self.assertEqual(len(app_metrics), 1)
        app_metric = app_metrics[0]

        self.assertEqual(app_metric.app, 'HelloWorldBounded')
        self.assertEqual(app_metric.count, 3)
        self.assertEqual(len(app_metric.actions), 3)

        action_names = ['repeatBackToMe', 'helloWorld', 'Buggy']
        for action in app_metric.actions:
            self.assertIn(action.action_name, action_names)
            action_names.remove(action.action_name)
            if action.action_name in ['repeatBackToMe', 'helloWorld']:
                self.assertEqual(len(action.action_statuses), 1)
                self.assertEqual(action.action_statuses[0].status, 'success')
                self.assertEqual(action.action_statuses[0].count, 1)
                self.assertGreater(action.action_statuses[0].avg_time, 0)
            elif action.action_name == 'Buggy':
                self.assertEqual(len(action.action_statuses), 1)
                self.assertEqual(action.action_statuses[0].status, 'error')
                self.assertEqual(action.action_statuses[0].count, 1)
                self.assertGreater(action.action_statuses[0].avg_time, 0)

    def test_workflow_metrics(self):
        execution_db_help.load_playbooks(['multiactionError', 'multiactionWorkflowTest'])
        error_id = server.app.running_context.execution_db.session.query(Workflow).join(Workflow.playbook).filter(and_(
            Workflow.name == 'multiactionErrorWorkflow', Playbook.name == 'multiactionError')).first().id
        test_id = server.app.running_context.execution_db.session.query(Workflow).join(Workflow.playbook).filter(and_(
            Workflow.name == 'multiactionWorkflow', Playbook.name == 'multiactionWorkflowTest')).first().id

        error_key = 'multiactionErrorWorkflow'
        multiaction_key = 'multiactionWorkflow'
        server.app.running_context.executor.execute_workflow(error_id)
        server.app.running_context.executor.execute_workflow(error_id)
        server.app.running_context.executor.execute_workflow(test_id)

        server.app.running_context.executor.wait_and_reset(3)

        keys = [error_key, multiaction_key]
        workflow_metrics = server.app.running_context.execution_db.session.query(WorkflowMetric).all()
        self.assertEqual(len(workflow_metrics), len(keys))

        for workflow in workflow_metrics:
            self.assertIn(workflow.workflow_name, keys)
            self.assertIsNotNone(workflow.avg_time)
            self.assertIsNotNone(workflow.count)
            self.assertGreater(workflow.avg_time, 0)
            if workflow.workflow_name == error_key:
                self.assertEqual(workflow.count, 2)
            elif workflow.workflow_name == multiaction_key:
                self.assertEqual(workflow.count, 1)
