import json
import threading
import time

from flask import current_app

from tests.util import execution_db_help
from tests.util.servertestcase import ServerTestCase
from walkoff.events import WalkoffEvent
from walkoff.executiondb import ExecutionDatabase
from walkoff.executiondb.device import App, Device
from walkoff.server.returncodes import *

try:
    from importlib import reload
except ImportError:
    from imp import reload


class TestTriggersServer(ServerTestCase):
    patch = False

    def setUp(self):
        self.action_events = ['Action Execution Success', 'Trigger Action Awaiting Data', 'Trigger Action Taken',
                              'Trigger Action Not Taken']
        app = ExecutionDatabase.instance.session.query(App).filter_by(name='HelloWorldBounded').first()
        device = Device('__device__', [], [], 'something')
        app.devices.append(device)
        ExecutionDatabase.instance.session.commit()

    def test_trigger_execute(self):
        workflow = execution_db_help.load_workflow('triggerActionWorkflow', 'triggerActionWorkflow')
        action_id = workflow.actions[0].id

        expected_events = (
            WalkoffEvent.TriggerActionAwaitingData,
            WalkoffEvent.TriggerActionTaken,
            WalkoffEvent.ActionExecutionSuccess)

        callback_count = {event: 0 for event in expected_events}

        def wait_thread():
            time.sleep(0.1)
            executed_ids = set()
            timeout = 0
            threshold = 5
            data = {"execution_ids": ids, "data_in": {"data": "1"}}
            while len(executed_ids) != len(ids) and timeout < threshold:
                trigger_response = self.put_with_status_check('/api/triggers/send_data', headers=self.headers,
                                                              data=json.dumps(data), status_code=SUCCESS,
                                                              content_type='application/json')
                executed_ids.update(set.intersection(set(ids), set(trigger_response)))
                time.sleep(0.1)
                timeout += 0.1

        @WalkoffEvent.TriggerActionAwaitingData.connect
        def send_data(sender, **kwargs):
            callback_count[WalkoffEvent.TriggerActionAwaitingData] += 1
            self.assertEqual(sender['id'], str(action_id))
            threading.Thread(target=wait_thread).start()

        @WalkoffEvent.TriggerActionTaken.connect
        def trigger_taken_callback(sender, **kwargs):
            self.assertEqual(sender.id, action_id)
            callback_count[WalkoffEvent.TriggerActionTaken] += 1

        @WalkoffEvent.ActionExecutionSuccess.connect
        def action_success_callback(sender, **kwargs):
            self.assertEqual(sender['id'], str(action_id))
            callback_count[WalkoffEvent.ActionExecutionSuccess] += 1

        execute_data = {"workflow_id": str(workflow.id)}
        response = self.post_with_status_check(
            '/api/workflowqueue',
            headers=self.headers,
            status_code=SUCCESS_ASYNC,
            content_type="application/json",
            data=json.dumps(execute_data))
        ids = [response['id']]

        current_app.running_context.executor.wait_and_reset(1)

        for count in callback_count.values():
            self.assertEqual(count, 1)

    def test_trigger_execute_multiple_workflows(self):
        workflow = execution_db_help.load_workflow('triggerActionWorkflow', 'triggerActionWorkflow')

        ids = []

        num_workflows = 2

        expected_events = (
            WalkoffEvent.TriggerActionAwaitingData,
            WalkoffEvent.TriggerActionTaken,
            WalkoffEvent.ActionExecutionSuccess)

        callback_count = {event: 0 for event in expected_events}

        def wait_thread():
            time.sleep(0.1)
            executed_ids = set()
            timeout = 0
            threshold = 5
            while len(ids) == num_workflows and len(executed_ids) != len(ids) and timeout < threshold:
                data = {"execution_ids": ids, "data_in": {"data": "1"}}

                trigger_response = self.put_with_status_check(
                    '/api/triggers/send_data',
                    headers=self.headers,
                    data=json.dumps(data),
                    status_code=SUCCESS, content_type='application/json')
                executed_ids.update(set.intersection(set(ids), set(trigger_response)))
                time.sleep(0.1)
                timeout += 0.1

        @WalkoffEvent.TriggerActionAwaitingData.connect
        def send_data(sender, **kwargs):
            callback_count[WalkoffEvent.TriggerActionAwaitingData] += 1
            if callback_count[WalkoffEvent.TriggerActionAwaitingData] == num_workflows:
                threading.Thread(target=wait_thread).start()

        @WalkoffEvent.TriggerActionTaken.connect
        def trigger_taken_callback(sender, **kwargs):
            callback_count[WalkoffEvent.TriggerActionTaken] += 1

        @WalkoffEvent.ActionExecutionSuccess.connect
        def action_success_callback(sender, **kwargs):
            callback_count[WalkoffEvent.ActionExecutionSuccess] += 1

        execute_data = {"workflow_id": str(workflow.id)}
        for _ in range(num_workflows):
            response = self.post_with_status_check(
                '/api/workflowqueue',
                headers=self.headers,
                status_code=SUCCESS_ASYNC,
                content_type="application/json",
                data=json.dumps(execute_data))
            ids.append(response['id'])

        current_app.running_context.executor.wait_and_reset(num_workflows)

        for count in callback_count.values():
            self.assertEqual(count, num_workflows)

    # TODO: Is this test really necessary?
    def test_trigger_execute_multiple_data(self):
        workflow = execution_db_help.load_workflow('triggerActionWorkflow', 'triggerActionWorkflow')

        expected_events = (
            WalkoffEvent.TriggerActionAwaitingData,
            WalkoffEvent.TriggerActionTaken,
            WalkoffEvent.TriggerActionNotTaken,
            WalkoffEvent.ActionExecutionSuccess)

        callback_count = {event: 0 for event in expected_events}

        def wait_thread():
            data = {"execution_ids": ids, "data_in": {"data": "aaa"}}
            time.sleep(0.1)
            executed_ids = set()
            threshold = 5
            trigger_response = self.put_with_status_check(
                '/api/triggers/send_data',
                headers=self.headers,
                data=json.dumps(data),
                status_code=SUCCESS,
                content_type='application/json')
            executed_ids.update(set.intersection(set(ids), set(trigger_response)))

            data_correct = {"execution_ids": [response['id']], "data_in": {"data": "1"}}
            executed_ids = set()
            timeout = 0
            while len(executed_ids) != len(ids) and timeout < threshold:
                trigger_response = self.put_with_status_check(
                    '/api/triggers/send_data',
                    headers=self.headers,
                    data=json.dumps(data_correct),
                    status_code=SUCCESS,
                    content_type='application/json')
                executed_ids.update(set.intersection(set(ids), set(trigger_response)))
                time.sleep(0.1)
                timeout += 0.1

        @WalkoffEvent.TriggerActionAwaitingData.connect
        def send_data(sender, **kwargs):
            callback_count[WalkoffEvent.TriggerActionAwaitingData] += 1
            threading.Thread(target=wait_thread).start()

        @WalkoffEvent.TriggerActionTaken.connect
        def trigger_taken_callback(sender, **kwargs):
            callback_count[WalkoffEvent.TriggerActionTaken] += 1

        @WalkoffEvent.TriggerActionNotTaken.connect
        def trigger_not_taken_callback(sender, **kwargs):
            callback_count[WalkoffEvent.TriggerActionNotTaken] += 1

        @WalkoffEvent.ActionExecutionSuccess.connect
        def action_success_callback(sender, **kwargs):
            callback_count[WalkoffEvent.ActionExecutionSuccess] += 1

        execute_data = {"workflow_id": str(workflow.id)}

        response = self.post_with_status_check(
            '/api/workflowqueue',
            headers=self.headers,
            status_code=SUCCESS_ASYNC,
            content_type="application/json",
            data=json.dumps(execute_data))
        ids = [response['id']]

        current_app.running_context.executor.wait_and_reset(1)

        for event, count in callback_count.items():
            self.assertEqual(count, 1)

    def test_trigger_execute_change_input(self):
        workflow = execution_db_help.load_workflow('triggerActionWorkflow', 'triggerActionWorkflow')

        expected_events = (
            WalkoffEvent.TriggerActionAwaitingData,
            WalkoffEvent.TriggerActionTaken,
            WalkoffEvent.ActionExecutionSuccess)

        callback_count = {event: 0 for event in expected_events}

        def wait_thread():
            data = {"execution_ids": ids, "data_in": {"data": "1"},
                    "arguments": [{"name": "call", "value": "CHANGE INPUT"}]}
            time.sleep(0.1)
            executed_ids = set()
            timeout = 0
            threshold = 5
            while len(executed_ids) != len(ids) and timeout < threshold:
                resp = self.put_with_status_check(
                    '/api/triggers/send_data',
                    headers=self.headers,
                    data=json.dumps(data),
                    status_code=SUCCESS,
                    content_type='application/json')
                executed_ids.update(set.intersection(set(ids), set(resp)))
                time.sleep(0.1)
                timeout += 0.1
            return

        @WalkoffEvent.TriggerActionAwaitingData.connect
        def send_data(sender, **kwargs):
            callback_count[WalkoffEvent.TriggerActionAwaitingData] += 1
            threading.Thread(target=wait_thread).start()

        @WalkoffEvent.TriggerActionTaken.connect
        def trigger_taken_callback(sender, **kwargs):
            callback_count[WalkoffEvent.TriggerActionTaken] += 1

        @WalkoffEvent.ActionExecutionSuccess.connect
        def action_success_callback(sender, **kwargs):
            self.assertDictEqual(kwargs['data']['data'], {'result': 'REPEATING: CHANGE INPUT', 'status': 'Success'})
            callback_count[WalkoffEvent.ActionExecutionSuccess] += 1

        execute_data = {"workflow_id": str(workflow.id)}
        response = self.post_with_status_check(
            '/api/workflowqueue',
            headers=self.headers,
            status_code=SUCCESS_ASYNC,
            content_type="application/json",
            data=json.dumps(execute_data))
        ids = [response['id']]

        current_app.running_context.executor.wait_and_reset(1)

        for event, count in callback_count.items():
            self.assertEqual(count, 1)
