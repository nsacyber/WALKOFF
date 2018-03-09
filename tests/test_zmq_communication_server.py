import json
from datetime import datetime

import walkoff.case.database as case_database
import walkoff.case.subscription
import walkoff.config.paths
from tests.util import execution_db_help
from tests.util.case_db_help import executed_actions, setup_subscriptions_for_action
from tests.util.servertestcase import ServerTestCase
from walkoff.events import WalkoffEvent
from walkoff.server import flaskserver as flask_server
from walkoff.server.returncodes import *

try:
    from importlib import reload
except ImportError:
    from imp import reload


class TestZmqCommunicationServer(ServerTestCase):
    patch = False

    def setUp(self):
        walkoff.case.subscription.subscriptions = {}
        case_database.initialize()

    def tearDown(self):
        execution_db_help.cleanup_execution_db()
        for case in case_database.case_db.session.query(case_database.Case).all():
            case_database.case_db.session.delete(case)
        case_database.case_db.session.commit()

    def test_execute_workflow(self):
        workflow = execution_db_help.load_workflow('test', 'helloWorldWorkflow')
        action_ids = [action.id for action in workflow.actions if action.name == 'start']
        setup_subscriptions_for_action(workflow.id, action_ids)
        start = datetime.utcnow()

        data = {"workflow_id": str(workflow.id)}

        response = self.post_with_status_check('/api/workflowqueue', headers=self.headers, data=json.dumps(data),
                                               status_code=SUCCESS_ASYNC, content_type="application/json")
        flask_server.running_context.executor.wait_and_reset(1)
        self.assertIn('id', response)
        actions = []
        for id_ in action_ids:
            actions.extend(executed_actions(id_, start, datetime.utcnow()))
        self.assertEqual(len(actions), 1)
        action = actions[0]
        result = action['data']
        self.assertEqual(result, {'status': 'Success', 'result': 'REPEATING: Hello World'})

    def test_execute_workflow_change_arguments(self):
        workflow = execution_db_help.load_workflow('test', 'helloWorldWorkflow')

        action_ids = [action.id for action in workflow.actions if action.name == 'start']
        setup_subscriptions_for_action(workflow.id, action_ids)

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

        flask_server.running_context.executor.wait_and_reset(1)

        self.assertEqual(result['count'], 1)
        self.assertDictEqual(result['data'], {'status': 'Success', 'result': 'REPEATING: CHANGE INPUT'})
