import json

import apps
import core.config.config
from core.case import callbacks
from server import flaskserver as server
from server.returncodes import *
from tests import config
from tests.util.servertestcase import ServerTestCase


class TestTriggers(ServerTestCase):
    def setUp(self):
        apps.cache_apps(config.test_apps_path)
        core.config.config.load_app_apis(apps_path=config.test_apps_path)

    def tearDown(self):
        server.running_context.controller.workflows = {}
        if False:
            print()

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

        server.running_context.controller.wait_and_reset(1)
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

        server.running_context.controller.wait_and_reset(1)
        self.assertEqual(result['result'], 1)

    def test_trigger_execute_change_input(self):

        response = self.post_with_status_check(
            '/api/playbooks/triggerActionWorkflow/workflows/triggerActionWorkflow/execute',
            headers=self.headers, status_code=SUCCESS_ASYNC)

        data = {"execution_uids": [response['id']],
                "data_in": {"data": "1"},
                "arguments": [{"name": "call",
                              "value": "CHANGE INPUT"}]}

        result = {"value": None}

        @callbacks.FunctionExecutionSuccess.connect
        def action_finished_listener(sender, **kwargs):
            result['value'] = kwargs['data']

        @callbacks.TriggerActionAwaitingData.connect
        def send_data(sender, **kwargs):
            print("About to send data")
            self.post_with_status_check('/api/triggers/send_data', headers=self.headers, data=json.dumps(data),
                                        status_code=SUCCESS, content_type='application/json')

        server.running_context.controller.wait_and_reset(1)

        self.assertDictEqual(result['value'], {'result': 'REPEATING: CHANGE INPUT', 'status': 'Success'})

    def test_trigger_execute_with_change_input_invalid_input(self):

        response = self.post_with_status_check(
            '/api/playbooks/triggerActionWorkflow/workflows/triggerActionWorkflow/execute',
            headers=self.headers, status_code=SUCCESS_ASYNC)

        data = {"execution_uids": [response['id']],
                "data_in": {"data": "1"},
                "arguments": [{"name": "invalid",
                              "value": "CHANGE INPUT"}]}

        result = {"result": False}

        @callbacks.ActionArgumentsInvalid.connect
        def action_input_invalids(sender, **kwargs):
            result['result'] = True

        @callbacks.TriggerActionAwaitingData.connect
        def send_data(sender, **kwargs):
            self.post_with_status_check('/api/triggers/send_data', headers=self.headers, data=json.dumps(data),
                                        status_code=SUCCESS, content_type='application/json')

        server.running_context.controller.wait_and_reset(1)
        self.assertTrue(result['result'])
