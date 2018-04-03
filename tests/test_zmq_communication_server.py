import json

from tests.util import execution_db_help
from tests.util.servertestcase import ServerTestCase
from walkoff.server import flaskserver as flask_server
from walkoff.server.returncodes import *
from walkoff.events import WalkoffEvent

try:
    from importlib import reload
except ImportError:
    from imp import reload


class TestZmqCommunicationServer(ServerTestCase):
    patch = False

    def tearDown(self):
        execution_db_help.cleanup_execution_db()

    def test_execute_workflow(self):
        workflow = execution_db_help.load_workflow('test', 'helloWorldWorkflow')
        workflow_id = str(workflow.id)

        data = {"workflow_id": workflow_id}

        result = {'called': True}

        @WalkoffEvent.WorkflowExecutionStart.connect
        def workflow_started(sender, **data):
            self.assertEqual(sender['id'], workflow_id)
            result['called'] = True

        response = self.post_with_status_check('/api/workflowqueue', headers=self.headers, data=json.dumps(data),
                                               status_code=SUCCESS_ASYNC, content_type="application/json")

        flask_server.app.running_context.executor.wait_and_reset(1)
        self.assertSetEqual(set(response.keys()), {'id'})

    def test_execute_workflow_change_arguments(self):
        workflow = execution_db_help.load_workflow('test', 'helloWorldWorkflow')

        result = {'count': 0}

        @WalkoffEvent.ActionExecutionSuccess.connect
        def y(sender, **kwargs):
            result['count'] += 1
            result['data'] = kwargs['data']['data']

        data = {"workflow_id": str(workflow.id),
                "arguments": [{"name": "call",
                               "value": "CHANGE INPUT"}]}

        self.post_with_status_check('/api/workflowqueue', headers=self.headers, status_code=SUCCESS_ASYNC,
                                    content_type="application/json", data=json.dumps(data))

        flask_server.app.running_context.executor.wait_and_reset(1)

        self.assertEqual(result['count'], 1)
        self.assertDictEqual(result['data'], {'status': 'Success', 'result': 'REPEATING: CHANGE INPUT'})
