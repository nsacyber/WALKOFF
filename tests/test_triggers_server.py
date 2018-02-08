import json
import threading
import time

import walkoff.case.database as case_database
import walkoff.case.subscription
import walkoff.config.paths
import walkoff.controller
from walkoff.events import WalkoffEvent
from walkoff.server import flaskserver as flask_server
from walkoff.server.returncodes import *
from tests.util.servertestcase import ServerTestCase
import walkoff.coredb.devicedb
from tests.util import device_db_help
from tests.util.case_db_help import *

try:
    from importlib import reload
except ImportError:
    from imp import reload


class TestTriggersServer(ServerTestCase):
    patch = False

    def setUp(self):
        self.controller = walkoff.controller.controller
        self.start = datetime.utcnow()
        walkoff.case.subscription.subscriptions = {}
        case_database.initialize()

    def tearDown(self):
        device_db_help.cleanup_device_db()
        walkoff.case.subscription.clear_subscriptions()
        for case in case_database.case_db.session.query(case_database.Case).all():
            case_database.case_db.session.delete(case)
        case_database.case_db.session.commit()

    # def test_trigger_execute(self):
    #     workflow = device_db_help.load_workflow('testGeneratedWorkflows/triggerActionWorkflow', 'triggerActionWorkflow')
    #     action_ids = [action.id for action in workflow.actions if action.name == 'start']
    #     setup_subscriptions_for_action(workflow.id, action_ids)
    #
    #     response = self.post_with_status_check(
    #         '/api/playbooks/{0}/workflows/{1}/execute'.format(workflow._playbook_id, workflow.id),
    #         headers=self.headers, status_code=SUCCESS_ASYNC, content_type="application/json", data=json.dumps({}))
    #
    #     ids = [response['id']]
    #
    #     data = {"execution_ids": ids,
    #             "data_in": {"data": "1"}}
    #
    #     result = {"result": False}
    #
    #     def wait_thread():
    #         time.sleep(0.1)
    #         execd_ids = set([])
    #         timeout = 0
    #         threshold = 5
    #         while len(execd_ids) != len(ids) and timeout < threshold:
    #             resp = self.put_with_status_check('/api/triggers/send_data', headers=self.headers,
    #                                                data=json.dumps(data),
    #                                                status_code=SUCCESS, content_type='application/json')
    #             execd_ids.update(set.intersection(set(ids), set(resp)))
    #             time.sleep(0.1)
    #             timeout += 0.1
    #         return
    #
    #     @WalkoffEvent.TriggerActionAwaitingData.connect
    #     def send_data(sender, **kwargs):
    #         threading.Thread(target=wait_thread).start()
    #
    #     @WalkoffEvent.TriggerActionTaken.connect
    #     def trigger_taken(sender, **kwargs):
    #         result['result'] = True
    #
    #     flask_server.running_context.controller.wait_and_reset(1)
    #     self.assertTrue(result['result'])
    #
    #     actions = []
    #     for id_ in action_ids:
    #         actions.extend(executed_actions(id_, self.start, datetime.utcnow()))
    #     self.assertEqual(len(actions), 1)
    #     action = actions[0]
    #     result = action['data']
    #     self.assertDictEqual(result, {'result': "REPEATING: Hello World", 'status': 'Success'})
    #
    # def test_trigger_multiple_workflows(self):
    #     workflow = device_db_help.load_workflow('testGeneratedWorkflows/triggerActionWorkflow', 'triggerActionWorkflow')
    #
    #     ids = []
    #
    #     response = self.post_with_status_check(
    #         '/api/playbooks/{0}/workflows/{1}/execute'.format(workflow._playbook_id, workflow.id),
    #         headers=self.headers, status_code=SUCCESS_ASYNC, content_type="application/json",
    #         data=json.dumps({}))
    #     ids.append(response['id'])
    #
    #     response = self.post_with_status_check(
    #         '/api/playbooks/{0}/workflows/{1}/execute'.format(workflow._playbook_id, workflow.id),
    #         headers=self.headers, status_code=SUCCESS_ASYNC, content_type="application/json",
    #         data=json.dumps({}))
    #     ids.append(response['id'])
    #
    #     data = {"execution_ids": ids,
    #             "data_in": {"data": "1"}}
    #
    #     result = {"result": 0,
    #               "num_trigs": 0}
    #
    #     def wait_thread():
    #         time.sleep(0.1)
    #         execd_ids = set([])
    #         timeout = 0
    #         threshold = 5
    #         while len(execd_ids) != len(ids) and timeout < threshold:
    #             resp = self.put_with_status_check('/api/triggers/send_data', headers=self.headers,
    #                                                data=json.dumps(data),
    #                                                status_code=SUCCESS, content_type='application/json')
    #             execd_ids.update(set.intersection(set(ids), set(resp)))
    #             time.sleep(0.1)
    #             timeout += 0.1
    #         return
    #
    #     @WalkoffEvent.TriggerActionAwaitingData.connect
    #     def send_data(sender, **kwargs):
    #         if result["num_trigs"] == 1:
    #             threading.Thread(target=wait_thread).start()
    #         else:
    #             result["num_trigs"] += 1
    #
    #     @WalkoffEvent.TriggerActionTaken.connect
    #     def trigger_taken(sender, **kwargs):
    #         result['result'] += 1
    #
    #     flask_server.running_context.controller.wait_and_reset(2)
    #     self.assertEqual(result['result'], 2)
    #
    # def test_trigger_execute_multiple_data(self):
    #     workflow = device_db_help.load_workflow('testGeneratedWorkflows/triggerActionWorkflow', 'triggerActionWorkflow')
    #
    #     response = self.post_with_status_check(
    #         '/api/playbooks/{0}/workflows/{1}/execute'.format(workflow._playbook_id, workflow.id),
    #         headers=self.headers, status_code=SUCCESS_ASYNC, content_type="application/json", data=json.dumps({}))
    #
    #     ids = [response['id']]
    #
    #     data = {"execution_ids": ids,
    #             "data_in": {"data": "aaa"}}
    #
    #     result = {"result": 0}
    #
    #     def wait_thread():
    #         time.sleep(0.1)
    #         execd_ids = set([])
    #         timeout = 0
    #         threshold = 5
    #         print("Sending first set")
    #         resp = self.put_with_status_check('/api/triggers/send_data', headers=self.headers,
    #                                            data=json.dumps(data),
    #                                            status_code=SUCCESS, content_type='application/json')
    #         execd_ids.update(set.intersection(set(ids), set(resp)))
    #
    #         data_correct = {"execution_ids": [response['id']], "data_in": {"data": "1"}}
    #         execd_ids = set([])
    #         timeout = 0
    #         print("Sending second set")
    #         while len(execd_ids) != len(ids) and timeout < threshold:
    #             resp = self.put_with_status_check('/api/triggers/send_data', headers=self.headers,
    #                                                data=json.dumps(data_correct),
    #                                                status_code=SUCCESS, content_type='application/json')
    #             execd_ids.update(set.intersection(set(ids), set(resp)))
    #             time.sleep(0.1)
    #             timeout += 0.1
    #         return
    #
    #     @WalkoffEvent.TriggerActionAwaitingData.connect
    #     def send_data(sender, **kwargs):
    #         threading.Thread(target=wait_thread).start()
    #
    #     @WalkoffEvent.TriggerActionTaken.connect
    #     def trigger_taken(sender, **kwargs):
    #         result['result'] += 1
    #
    #     flask_server.running_context.controller.wait_and_reset(1)
    #     self.assertEqual(result['result'], 1)
    #
    # def test_trigger_execute_change_input(self):
    #     workflow = device_db_help.load_workflow('testGeneratedWorkflows/triggerActionWorkflow', 'triggerActionWorkflow')
    #
    #     response = self.post_with_status_check(
    #         '/api/playbooks/{0}/workflows/{1}/execute'.format(workflow._playbook_id, workflow.id),
    #         headers=self.headers, status_code=SUCCESS_ASYNC, content_type="application/json", data=json.dumps({}))
    #
    #     ids = [response['id']]
    #
    #     data = {"execution_ids": ids,
    #             "data_in": {"data": "1"},
    #             "arguments": [{"name": "call",
    #                            "value": "CHANGE INPUT"}]}
    #
    #     result = {"value": None}
    #
    #     @WalkoffEvent.ActionExecutionSuccess.connect
    #     def action_finished_listener(sender, **kwargs):
    #         result['value'] = kwargs['data']
    #
    #     def wait_thread():
    #         time.sleep(0.1)
    #         execd_ids = set([])
    #         timeout = 0
    #         threshold = 5
    #         while len(execd_ids) != len(ids) and timeout < threshold:
    #             resp = self.put_with_status_check('/api/triggers/send_data', headers=self.headers,
    #                                                data=json.dumps(data),
    #                                                status_code=SUCCESS, content_type='application/json')
    #             execd_ids.update(set.intersection(set(ids), set(resp)))
    #             time.sleep(0.1)
    #             timeout += 0.1
    #         return
    #
    #     @WalkoffEvent.TriggerActionAwaitingData.connect
    #     def send_data(sender, **kwargs):
    #         threading.Thread(target=wait_thread).start()
    #
    #     flask_server.running_context.controller.wait_and_reset(1)
    #
    #     self.assertDictEqual(result['value'], {'result': 'REPEATING: CHANGE INPUT', 'status': 'Success'})

    # TODO: Fix this test...broken. And then fix pause/resume (change the way it's done).
    def test_trigger_execute_with_change_input_invalid_input(self):
        workflow = device_db_help.load_workflow('testGeneratedWorkflows/triggerActionWorkflow', 'triggerActionWorkflow')

        response = self.post_with_status_check(
            '/api/playbooks/{0}/workflows/{1}/execute'.format(workflow._playbook_id, workflow.id),
            headers=self.headers, status_code=SUCCESS_ASYNC, content_type="application/json", data=json.dumps({}))

        ids = [response['id']]

        data = {"execution_ids": ids,
                "data_in": {"data": "1"},
                "arguments": [{"name": "invalid",
                               "value": "CHANGE INPUT"}]}

        result = {"result": False}

        @WalkoffEvent.ActionArgumentsInvalid.connect
        def action_input_invalids(sender, **kwargs):
            result['result'] = True

        def wait_thread():
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

        flask_server.running_context.controller.wait_and_reset(1)
        self.assertTrue(result['result'])
