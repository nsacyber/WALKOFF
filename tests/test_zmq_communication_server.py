from tests.util.servertestcase import ServerTestCase
from tests.util.case_db_help import executed_steps, setup_subscriptions_for_step
from datetime import datetime
from server import flaskserver as flask_server
import core.case.subscription
import core.case.database as case_database
from core.case import callbacks
import core.config.paths
from server.returncodes import *
import core.controller
from gevent import monkey
import socket
import json
try:
    from importlib import reload
except ImportError:
    from imp import reload


class TestWorkflowServer(ServerTestCase):
    patch = False

    def setUp(self):
        monkey.patch_socket()
        core.case.subscription.subscriptions = {}
        case_database.initialize()

    def tearDown(self):
        core.controller.workflows = {}
        core.case.subscription.clear_subscriptions()
        for case in core.case.database.case_db.session.query(core.case.database.Case).all():
            core.case.database.case_db.session.delete(case)
        core.case.database.case_db.session.commit()
        reload(socket)

    def test_execute_workflow(self):
        flask_server.running_context.controller.initialize_threading()
        workflow = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow')
        step_uids = [step.uid for step in workflow.steps.values() if step.name == 'start']
        setup_subscriptions_for_step(workflow.uid, step_uids)
        start = datetime.utcnow()

        response = self.post_with_status_check('/api/playbooks/test/workflows/helloWorldWorkflow/execute',
                                               headers=self.headers,
                                               status_code=SUCCESS_ASYNC)
        flask_server.running_context.controller.shutdown_pool(1)
        self.assertIn('id', response)
        steps = []
        for uid in step_uids:
            steps.extend(executed_steps(uid, start, datetime.utcnow()))
        self.assertEqual(len(steps), 1)
        step = steps[0]
        result = step['data']
        self.assertEqual(result['result'], {'status': 'Success', 'result': 'REPEATING: Hello World'})

    def test_trigger_multiple_workflows(self):
        flask_server.running_context.controller.initialize_threading()

        ids = []

        response=self.post_with_status_check(
            '/api/playbooks/triggerStepWorkflow/workflows/triggerStepWorkflow/execute',
            headers=self.headers, status_code=SUCCESS_ASYNC)
        ids.append(response['id'])

        response = self.post_with_status_check(
            '/api/playbooks/triggerStepWorkflow/workflows/triggerStepWorkflow/execute',
            headers=self.headers, status_code=SUCCESS_ASYNC)
        ids.append(response['id'])

        data = {"execution_uids": ids,
                "data_in": {"data": "1"}}

        result = {"result": 0,
                  "num_trigs": 0}

        @callbacks.TriggerStepAwaitingData.connect
        def send_data(sender, **kwargs):
            if result["num_trigs"] == 1:
                self.post_with_status_check('/api/triggers/send_data', headers=self.headers, data=json.dumps(data),
                                            status_code=SUCCESS, content_type='application/json')
            else:
                result["num_trigs"] += 1

        @callbacks.TriggerStepTaken.connect
        def trigger_taken(sender, **kwargs):
            result['result'] += 1

        import time
        time.sleep(1)
        flask_server.running_context.controller.shutdown_pool(2)
        self.assertEqual(result['result'], 2)

    def test_read_all_results(self):
        flask_server.running_context.controller.initialize_threading()
        self.app.post('/api/playbooks/test/workflows/helloWorldWorkflow/execute', headers=self.headers)
        self.app.post('/api/playbooks/test/workflows/helloWorldWorkflow/execute', headers=self.headers)
        self.app.post('/api/playbooks/test/workflows/helloWorldWorkflow/execute', headers=self.headers)

        with flask_server.running_context.flask_app.app_context():
            flask_server.running_context.controller.shutdown_pool(3)

        response = self.get_with_status_check('/api/workflowresults', headers=self.headers)
        self.assertEqual(len(response), 3)

        for result in response:
            self.assertSetEqual(set(result.keys()), {'status', 'completed_at', 'started_at', 'name', 'results', 'uid'})
            for step_result in result['results']:
                self.assertSetEqual(set(step_result.keys()), {'input', 'type', 'name', 'timestamp', 'result', 'app', 'action'})
