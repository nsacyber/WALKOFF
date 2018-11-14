import json

from flask import current_app

from tests.util import execution_db_help
from tests.util.servertestcase import ServerTestCase
from walkoff.events import WalkoffEvent
from walkoff.server.returncodes import *

try:
    from importlib import reload
except ImportError:
    from imp import reload


class TestZmqCommunicationServer(ServerTestCase):
    patch = False

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

        current_app.running_context.executor.wait_and_reset(1)
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

        current_app.running_context.executor.wait_and_reset(1)

        self.assertEqual(result['count'], 1)
        self.assertDictEqual(result['data'], {'status': 'Success', 'result': 'REPEATING: CHANGE INPUT'})

    def test_execute_invalid_workflow(self):
        workflow = execution_db_help.load_workflow('test', 'helloWorldWorkflow')
        workflow.is_valid = False
        from walkoff.executiondb import ExecutionDatabase
        ExecutionDatabase.instance.session.add(workflow)
        ExecutionDatabase.instance.session.commit()
        self.post_with_status_check('/api/workflowqueue', headers=self.headers, status_code=INVALID_INPUT_ERROR,
                                    content_type="application/json")

    def test_execute_workflow_change_to_invalid_arguments(self):
        workflow = execution_db_help.load_workflow('test', 'helloWorldWorkflow')
        data = {"workflow_id": str(workflow.id),
                "arguments": [{"name": "call"}]}

        self.post_with_status_check('/api/workflowqueue', headers=self.headers, status_code=INVALID_INPUT_ERROR,
                                    content_type="application/json", data=json.dumps(data))
