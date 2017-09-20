from tests.util.servertestcase import ServerTestCase
from tests.util.case_db_help import executed_steps, setup_subscriptions_for_step
from datetime import datetime
from server import flaskserver as flask_server
import core.case.subscription
import core.case.database as case_database
import core.config.paths
from threading import Event
from core.case.callbacks import WorkflowShutdown
from server.returncodes import *
import core.controller
from gevent import monkey
import socket
try:
    from importlib import reload
except ImportError:
    from imp import reload

class TestWorkflowServer(ServerTestCase):
    patch = False

    def setUp(self):
        # This looks awful, I know
        self.empty_workflow_json = \
            {'steps': [],
             'name': 'test_name',
             'start': 'start',
             'accumulated_risk': 0.0}
        core.case.subscription.subscriptions = {}
        case_database.initialize()
        monkey.patch_socket()

    def tearDown(self):
        flask_server.running_context.controller.shutdown_pool(0)
        core.controller.workflows = {}
        case_database.case_db.tear_down()
        reload(socket)

    def test_execute_workflow(self):
        flask_server.running_context.controller.initialize_threading()
        sync = Event()
        workflow = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow')
        step_uids = [step.uid for step in workflow.steps.values() if step.name == 'start']
        setup_subscriptions_for_step(workflow.uid, step_uids)
        start = datetime.utcnow()

        @WorkflowShutdown.connect
        def wait_for_completion(sender, **kwargs):
            sync.set()

        WorkflowShutdown.connect(wait_for_completion)

        response = self.post_with_status_check('/api/playbooks/test/workflows/helloWorldWorkflow/execute',
                                               headers=self.headers,
                                               status_code=SUCCESS_ASYNC)
        flask_server.running_context.controller.shutdown_pool(1)
        self.assertIn('id', response)
        sync.wait(timeout=10)
        steps = []
        for uid in step_uids:
            steps.extend(executed_steps(uid, start, datetime.utcnow()))
        self.assertEqual(len(steps), 1)
        step = steps[0]
        result = step['data']
        self.assertEqual(result['result'], {'status': 'Success', 'result': 'REPEATING: Hello World'})

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
                self.assertSetEqual(set(step_result.keys()), {'input', 'type', 'name', 'timestamp', 'result'})
