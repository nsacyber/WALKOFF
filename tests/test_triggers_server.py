import socket
import json

from gevent import monkey

from core.case import callbacks
import core.case.database as case_database
import core.case.subscription
import core.config.paths
import core.controller
from server import flaskserver as flask_server
from server.returncodes import *
from tests.util.servertestcase import ServerTestCase

try:
    from importlib import reload
except ImportError:
    from imp import reload


class TestTriggersServer(ServerTestCase):
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

    # def test_trigger_multiple_workflows(self):
    #
    #     # flask_server.running_context.controller.initialize_threading(worker_environment_setup=modified_setup_worker_env)
    #
    #     ids = []
    #
    #     response=self.post_with_status_check(
    #         '/api/playbooks/triggerActionWorkflow/workflows/triggerActionWorkflow/execute',
    #         headers=self.headers, status_code=SUCCESS_ASYNC)
    #     ids.append(response['id'])
    #
    #     response = self.post_with_status_check(
    #         '/api/playbooks/triggerActionWorkflow/workflows/triggerActionWorkflow/execute',
    #         headers=self.headers, status_code=SUCCESS_ASYNC)
    #     ids.append(response['id'])
    #
    #     data = {"execution_uids": ids,
    #             "data_in": {"data": "1"}}
    #
    #     result = {"result": 0,
    #               "num_trigs": 0}
    #
    #     @callbacks.TriggerActionAwaitingData.connect
    #     def send_data(sender, **kwargs):
    #         if result["num_trigs"] == 1:
    #             self.post_with_status_check('/api/triggers/send_data', headers=self.headers, data=json.dumps(data),
    #                                         status_code=SUCCESS, content_type='application/json')
    #         else:
    #             result["num_trigs"] += 1
    #
    #     @callbacks.TriggerActionTaken.connect
    #     def trigger_taken(sender, **kwargs):
    #         result['result'] += 1
    #
    #     flask_server.running_context.controller.wait_and_reset(2)
    #     self.assertEqual(result['result'], 2)

    def test_trigger_execute(self):

        response = self.post_with_status_check(
            '/api/playbooks/triggerActionWorkflow/workflows/triggerActionWorkflow/execute',
            headers=self.headers, status_code=SUCCESS_ASYNC)

        data = {"execution_uids": [response['id']],
                "data_in": {"data": "1"}}

        result = {"result": False}

        @callbacks.TriggerActionAwaitingData.connect
        def send_data(sender, **kwargs):
            self.post_with_status_check('/api/triggers/send_data', headers=self.headers, data=json.dumps(data),
                                        status_code=SUCCESS, content_type='application/json')

        @callbacks.TriggerActionTaken.connect
        def trigger_taken(sender, **kwargs):
            result['result'] = True

        flask_server.running_context.controller.wait_and_reset(1)
        self.assertTrue(result['result'])

    def test_trigger_execute_multiple_data(self):

        response = self.post_with_status_check(
            '/api/playbooks/triggerActionWorkflow/workflows/triggerActionWorkflow/execute',
            headers=self.headers, status_code=SUCCESS_ASYNC)

        data = {"execution_uids": [response['id']],
                "data_in": {"data": "aaa"}}

        result = {"result": 0}

        @callbacks.TriggerActionAwaitingData.connect
        def send_data(sender, **kwargs):
            self.post_with_status_check('/api/triggers/send_data', headers=self.headers, data=json.dumps(data),
                                        status_code=SUCCESS, content_type='application/json')
            data_correct = {"execution_uids": [response['id']],
                            "data_in": {"data": "1"}}
            self.post_with_status_check('/api/triggers/send_data', headers=self.headers, data=json.dumps(data_correct),
                                        status_code=SUCCESS, content_type='application/json')

        @callbacks.TriggerActionTaken.connect
        def trigger_taken(sender, **kwargs):
            result['result'] += 1

        flask_server.running_context.controller.wait_and_reset(1)
        self.assertEqual(result['result'], 1)

    # def test_trigger_execute_change_input(self):
    #
    #     response = self.post_with_status_check(
    #         '/api/playbooks/triggerActionWorkflow/workflows/triggerActionWorkflow/execute',
    #         headers=self.headers, status_code=SUCCESS_ASYNC)
    #
    #     data = {"execution_uids": [response['id']],
    #             "data_in": {"data": "1"},
    #             "arguments": [{"name": "call",
    #                           "value": "CHANGE INPUT"}]}
    #
    #     print(data)
    #
    #     result = {"value": None}
    #
    #     @callbacks.FunctionExecutionSuccess.connect
    #     def action_finished_listener(sender, **kwargs):
    #         result['value'] = kwargs['data']
    #
    #     @callbacks.TriggerActionAwaitingData.connect
    #     def send_data(sender, **kwargs):
    #         self.post_with_status_check('/api/triggers/send_data', headers=self.headers, data=json.dumps(data),
    #                                     status_code=SUCCESS, content_type='application/json')
    #
    #     flask_server.running_context.controller.wait_and_reset(1)
    #
    #     self.assertDictEqual(result['value'], {'result': 'REPEATING: CHANGE INPUT', 'status': 'Success'})
    #
    # def test_trigger_execute_with_change_input_invalid_input(self):
    #
    #     response = self.post_with_status_check(
    #         '/api/playbooks/triggerActionWorkflow/workflows/triggerActionWorkflow/execute',
    #         headers=self.headers, status_code=SUCCESS_ASYNC)
    #
    #     data = {"execution_uids": [response['id']],
    #             "data_in": {"data": "1"},
    #             "arguments": [{"name": "invalid",
    #                           "value": "CHANGE INPUT"}]}
    #
    #     result = {"result": False}
    #
    #     @callbacks.ActionArgumentsInvalid.connect
    #     def action_input_invalids(sender, **kwargs):
    #         result['result'] = True
    #
    #     @callbacks.TriggerActionAwaitingData.connect
    #     def send_data(sender, **kwargs):
    #         self.post_with_status_check('/api/triggers/send_data', headers=self.headers, data=json.dumps(data),
    #                                     status_code=SUCCESS, content_type='application/json')
    #
    #     flask_server.running_context.controller.wait_and_reset(1)
    #     self.assertTrue(result['result'])
