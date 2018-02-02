import json
from datetime import datetime

from tests.util.servertestcase import ServerTestCase
import walkoff.case.database as case_database
import walkoff.case.subscription
import walkoff.config.paths
import walkoff.controller
from walkoff.server import flaskserver as flask_server
from walkoff.server.returncodes import *
from tests.util.case_db_help import executed_actions, setup_subscriptions_for_action
from tests.util import device_db_help

try:
    from importlib import reload
except ImportError:
    from imp import reload


class TestWorkflowServer(ServerTestCase):
    patch = False

    def setUp(self):
        walkoff.case.subscription.subscriptions = {}
        case_database.initialize()

    def tearDown(self):
        device_db_help.cleanup_device_db()
        walkoff.controller.workflows = {}
        walkoff.case.subscription.clear_subscriptions()
        for case in case_database.case_db.session.query(case_database.Case).all():
            case_database.case_db.session.delete(case)
        case_database.case_db.session.commit()

    def test_execute_workflow(self):
        workflow = device_db_help.load_workflow('test', 'helloWorldWorkflow')
        action_ids = [action.id for action in workflow.actions if action.name == 'start']
        setup_subscriptions_for_action(workflow.id, action_ids)
        start = datetime.utcnow()

        response = self.post_with_status_check(
            '/api/playbooks/{0}/workflows/{1}/execute'.format(workflow._playbook_id, workflow.id),
            headers=self.headers, data=json.dumps({}), status_code=SUCCESS_ASYNC, content_type="application/json")
        flask_server.running_context.controller.wait_and_reset(1)
        self.assertIn('id', response)
        actions = []
        for id_ in action_ids:
            actions.extend(executed_actions(id_, start, datetime.utcnow()))
        self.assertEqual(len(actions), 1)
        action = actions[0]
        result = action['data']
        self.assertEqual(result, {'status': 'Success', 'result': 'REPEATING: Hello World'})

    def test_read_all_results(self):
        workflow = device_db_help.load_workflow('test', 'helloWorldWorkflow')
        self.app.post('/api/playbooks/{0}/workflows/{1}/execute'.format(workflow._playbook_id, workflow.id),
                      headers=self.headers,content_type="application/json", data=json.dumps({}))
        self.app.post('/api/playbooks/{0}/workflows/{1}/execute'.format(workflow._playbook_id, workflow.id),
                      headers=self.headers, content_type="application/json", data=json.dumps({}))
        self.app.post('/api/playbooks/{0}/workflows/{1}/execute'.format(workflow._playbook_id, workflow.id),
                      headers=self.headers, content_type="application/json", data=json.dumps({}))

        flask_server.running_context.controller.wait_and_reset(3)

        response = self.get_with_status_check('/api/workflowresults', headers=self.headers)
        self.assertEqual(len(response), 3)

        for result in response:
            self.assertSetEqual(set(result.keys()), {'status', 'completed_at', 'started_at', 'name', 'results', 'id'})
            for action_result in result['results']:
                self.assertSetEqual(set(action_result.keys()),
                                    {'arguments', 'type', 'name', 'timestamp', 'result', 'app_name', 'action_name'})
