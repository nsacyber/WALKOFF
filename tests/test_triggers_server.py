import json
import threading
import time
from datetime import datetime

import walkoff.case.subscription
import walkoff.config.paths
from tests.util import execution_db_help
from tests.util.assertwrappers import orderless_list_compare
from tests.util.case_db_help import *
from tests.util.servertestcase import ServerTestCase
from walkoff.server import flaskserver as flask_server
from walkoff.server.returncodes import *

try:
    from importlib import reload
except ImportError:
    from imp import reload


class TestTriggersServer(ServerTestCase):
    patch = False

    def setUp(self):
        self.start = datetime.utcnow()
        self.action_events = ['Action Execution Success', 'Trigger Action Awaiting Data', 'Trigger Action Taken',
                              'Trigger Action Not Taken']
        walkoff.case.subscription.subscriptions = {}
        case_database.initialize()

    def tearDown(self):
        execution_db_help.cleanup_device_db()
        walkoff.case.subscription.clear_subscriptions()
        for case in case_database.case_db.session.query(case_database.Case).all():
            case_database.case_db.session.delete(case)
        case_database.case_db.session.commit()

    def test_trigger_execute(self):
        workflow = execution_db_help.load_workflow('triggerActionWorkflow', 'triggerActionWorkflow')
        action_ids = [action.id for action in workflow.actions if action.name == 'start']
        setup_subscriptions_for_action(workflow.id, action_ids, action_events=self.action_events)

        def wait_thread():
            time.sleep(0.1)
            execd_ids = set([])
            timeout = 0
            threshold = 5
            data = {"execution_ids": ids, "data_in": {"data": "1"}}
            while len(execd_ids) != len(ids) and timeout < threshold:
                resp = self.put_with_status_check('/api/triggers/send_data', headers=self.headers,
                                                  data=json.dumps(data),
                                                  status_code=SUCCESS, content_type='application/json')
                execd_ids.update(set.intersection(set(ids), set(resp)))
                time.sleep(0.1)
                timeout += 0.1
            return

        @WalkoffEvent.TriggerActionAwaitingData.connect
        def send_data(sender, **kwargs):
            threading.Thread(target=wait_thread).start()

        execute_data = {"workflow_id": str(workflow.id)}
        response = self.post_with_status_check('/api/workflowqueue', headers=self.headers, status_code=SUCCESS_ASYNC,
                                               content_type="application/json", data=json.dumps(execute_data))
        ids = [response['id']]

        flask_server.running_context.executor.wait_and_reset(1)

        actions = []
        for id_ in action_ids:
            actions.extend(executed_actions(str(id_), self.start, datetime.utcnow()))
        self.assertEqual(len(actions), 3)

        events = [event['message'] for event in actions]
        expected_events = ['Trigger action awaiting data', 'Trigger action taken', 'Action executed successfully']
        self.assertListEqual(expected_events, events)

    def test_trigger_execute_multiple_workflows(self):
        workflow = execution_db_help.load_workflow('triggerActionWorkflow', 'triggerActionWorkflow')
        action_ids = [action.id for action in workflow.actions if action.name == 'start']
        setup_subscriptions_for_action(workflow.id, action_ids, action_events=self.action_events)

        ids = []
        result = {"num_trigs": 0}

        def wait_thread():
            time.sleep(0.1)
            execd_ids = set([])
            timeout = 0
            threshold = 5
            while len(ids) == 2 and len(execd_ids) != len(ids) and timeout < threshold:
                data = {"execution_ids": ids, "data_in": {"data": "1"}}

                resp = self.put_with_status_check('/api/triggers/send_data', headers=self.headers,
                                                  data=json.dumps(data),
                                                  status_code=SUCCESS, content_type='application/json')
                execd_ids.update(set.intersection(set(ids), set(resp)))
                time.sleep(0.1)
                timeout += 0.1
            return

        @WalkoffEvent.TriggerActionAwaitingData.connect
        def send_data(sender, **kwargs):
            if result["num_trigs"] == 1:
                threading.Thread(target=wait_thread).start()
            else:
                result["num_trigs"] += 1

        execute_data = {"workflow_id": str(workflow.id)}
        response = self.post_with_status_check('/api/workflowqueue', headers=self.headers, status_code=SUCCESS_ASYNC,
                                               content_type="application/json", data=json.dumps(execute_data))
        ids.append(response['id'])
        response = self.post_with_status_check('/api/workflowqueue', headers=self.headers, status_code=SUCCESS_ASYNC,
                                               content_type="application/json", data=json.dumps(execute_data))
        ids.append(response['id'])

        flask_server.running_context.executor.wait_and_reset(2)

        actions = []
        for id_ in action_ids:
            actions.extend(executed_actions(id_, self.start, datetime.utcnow()))
        self.assertEqual(len(actions), 6)

        events = [event['message'] for event in actions]
        expected_events = ['Trigger action awaiting data', 'Trigger action taken', 'Action executed successfully',
                           'Trigger action awaiting data', 'Trigger action taken', 'Action executed successfully']
        orderless_list_compare(self, expected_events, events)

    # TODO: Is this test really necessary?
    def test_trigger_execute_multiple_data(self):
        workflow = execution_db_help.load_workflow('triggerActionWorkflow', 'triggerActionWorkflow')
        action_ids = [action.id for action in workflow.actions if action.name == 'start']
        setup_subscriptions_for_action(workflow.id, action_ids, action_events=self.action_events)

        def wait_thread():
            data = {"execution_ids": ids, "data_in": {"data": "aaa"}}
            time.sleep(0.1)
            execd_ids = set([])
            threshold = 5
            resp = self.put_with_status_check('/api/triggers/send_data', headers=self.headers,
                                              data=json.dumps(data),
                                              status_code=SUCCESS, content_type='application/json')
            execd_ids.update(set.intersection(set(ids), set(resp)))

            data_correct = {"execution_ids": [response['id']], "data_in": {"data": "1"}}
            execd_ids = set([])
            timeout = 0
            while len(execd_ids) != len(ids) and timeout < threshold:
                resp = self.put_with_status_check('/api/triggers/send_data', headers=self.headers,
                                                  data=json.dumps(data_correct),
                                                  status_code=SUCCESS, content_type='application/json')
                execd_ids.update(set.intersection(set(ids), set(resp)))
                time.sleep(0.1)
                timeout += 0.1
            return

        @WalkoffEvent.TriggerActionAwaitingData.connect
        def send_data(sender, **kwargs):
            threading.Thread(target=wait_thread).start()

        execute_data = {"workflow_id": str(workflow.id)}

        response = self.post_with_status_check('/api/workflowqueue', headers=self.headers, status_code=SUCCESS_ASYNC,
                                               content_type="application/json", data=json.dumps(execute_data))
        ids = [response['id']]

        flask_server.running_context.executor.wait_and_reset(1)

        actions = []
        for id_ in action_ids:
            actions.extend(executed_actions(id_, self.start, datetime.utcnow()))
        self.assertEqual(len(actions), 4)

        events = [event['message'] for event in actions]
        expected_events = ['Trigger action awaiting data', 'Trigger action not taken', 'Trigger action taken',
                           'Action executed successfully']
        self.assertListEqual(expected_events, events)

    def test_trigger_execute_change_input(self):
        workflow = execution_db_help.load_workflow('triggerActionWorkflow', 'triggerActionWorkflow')
        action_ids = [action.id for action in workflow.actions if action.name == 'start']
        setup_subscriptions_for_action(workflow.id, action_ids, action_events=self.action_events)

        def wait_thread():
            data = {"execution_ids": ids, "data_in": {"data": "1"},
                    "arguments": [{"name": "call", "value": "CHANGE INPUT"}]}
            time.sleep(0.1)
            execd_ids = set([])
            timeout = 0
            threshold = 5
            while len(execd_ids) != len(ids) and timeout < threshold:
                resp = self.put_with_status_check('/api/triggers/send_data', headers=self.headers,
                                                  data=json.dumps(data),
                                                  status_code=SUCCESS, content_type='application/json')
                execd_ids.update(set.intersection(set(ids), set(resp)))
                time.sleep(0.1)
                timeout += 0.1
            return

        @WalkoffEvent.TriggerActionAwaitingData.connect
        def send_data(sender, **kwargs):
            threading.Thread(target=wait_thread).start()

        execute_data = {"workflow_id": str(workflow.id)}
        response = self.post_with_status_check('/api/workflowqueue', headers=self.headers, status_code=SUCCESS_ASYNC,
                                               content_type="application/json", data=json.dumps(execute_data))
        ids = [response['id']]

        flask_server.running_context.executor.wait_and_reset(1)

        actions = []
        for id_ in action_ids:
            actions.extend(executed_actions(id_, self.start, datetime.utcnow()))
        self.assertEqual(len(actions), 3)

        events = [event['message'] for event in actions]
        expected_events = ['Trigger action awaiting data', 'Trigger action taken', 'Action executed successfully']
        self.assertListEqual(expected_events, events)

        for event in actions:
            if event['message'] == 'Action executed successfully':
                self.assertDictEqual(event['data'], {'result': 'REPEATING: CHANGE INPUT', 'status': 'Success'})
