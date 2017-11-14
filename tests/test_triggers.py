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
        self.test_trigger_name = "testTrigger"
        self.test_trigger_workflow = "helloWorldWorkflow"

    def tearDown(self):
        with server.running_context.flask_app.app_context():
            Triggers.query.filter_by(name=self.test_trigger_name).delete()
            Triggers.query.filter_by(name="execute_me").delete()
            Triggers.query.filter_by(name="execute_one").delete()
            Triggers.query.filter_by(name="execute_two").delete()
            Triggers.query.filter_by(name="execute_three").delete()
            Triggers.query.filter_by(name="execute_four").delete()
            Triggers.query.filter_by(name="{0}rename".format(self.test_trigger_name)).delete()
            server.database.db.session.commit()
            server.running_context.controller.workflows = {}
            # server.running_context.controller.shutdown_pool(0)

    # def test_trigger_execute(self):
    #     server.running_context.controller.initialize_threading()
    #
    #     response=self.post_with_status_check('/api/playbooks/triggerStepWorkflow/workflows/triggerStepWorkflow/execute',
    #                                          headers=self.headers, status_code=SUCCESS_ASYNC)
    #
    #     data = {"execution_uids": [response['id']],
    #             "data_in": {"data": "1"}}
    #
    #     result = {"result": False}
    #
    #     @callbacks.TriggerStepAwaitingData.connect
    #     def send_data(sender, **kwargs):
    #         self.post_with_status_check('/api/triggers/send_data', headers=self.headers, data=json.dumps(data),
    #                                     status_code=SUCCESS, content_type='application/json')
    #
    #     @callbacks.TriggerStepTaken.connect
    #     def trigger_taken(sender, **kwargs):
    #         result['result'] = True
    #
    #     server.running_context.controller.shutdown_pool(1)
    #     self.assertTrue(result['result'])

    # def test_trigger_execute_multiple_data(self):
    #     server.running_context.controller.initialize_threading()
    #
    #     response = self.post_with_status_check(
    #         '/api/playbooks/triggerStepWorkflow/workflows/triggerStepWorkflow/execute',
    #         headers=self.headers, status_code=SUCCESS_ASYNC)
    #
    #     data = {"execution_uids": [response['id']],
    #             "data_in": {"data": "aaa"}}
    #
    #     result = {"result": 0}
    #
    #     @callbacks.TriggerStepAwaitingData.connect
    #     def send_data(sender, **kwargs):
    #         self.post_with_status_check('/api/triggers/send_data', headers=self.headers, data=json.dumps(data),
    #                                     status_code=SUCCESS, content_type='application/json')
    #         data_correct = {"execution_uids": [response['id']],
    #                         "data_in": {"data": "1"}}
    #         self.post_with_status_check('/api/triggers/send_data', headers=self.headers, data=json.dumps(data_correct),
    #                                     status_code=SUCCESS, content_type='application/json')
    #
    #     @callbacks.TriggerStepTaken.connect
    #     def trigger_taken(sender, **kwargs):
    #         result['result'] += 1
    #
    #     server.running_context.controller.shutdown_pool(1)
    #     self.assertEqual(result['result'], 1)

    # def test_trigger_execute_change_input(self):
    #     server.running_context.controller.initialize_threading()
    #
    #     response = self.post_with_status_check(
    #         '/api/playbooks/triggerStepWorkflow/workflows/triggerStepWorkflow/execute',
    #         headers=self.headers, status_code=SUCCESS_ASYNC)
    #
    #     data = {"execution_uids": [response['id']],
    #             "data_in": {"data": "1"},
    #             "inputs": {"call": "CHANGE INPUT"}}
    #
    #     result = {"value": None}
    #
    #     @callbacks.FunctionExecutionSuccess.connect
    #     def step_finished_listener(sender, **kwargs):
    #         result['value'] = kwargs['data']
    #
    #     @callbacks.TriggerStepAwaitingData.connect
    #     def send_data(sender, **kwargs):
    #         self.post_with_status_check('/api/triggers/send_data', headers=self.headers, data=json.dumps(data),
    #                                     status_code=SUCCESS, content_type='application/json')
    #
    #     server.running_context.controller.shutdown_pool(1)
    #
    #     self.assertDictEqual(result['value'],
    #                          {'result': {'result': 'REPEATING: CHANGE INPUT', 'status': 'Success'}})

    # def test_trigger_execute_with_change_input_invalid_input(self):
    #     server.running_context.controller.initialize_threading()
    #
    #     response = self.post_with_status_check(
    #         '/api/playbooks/triggerStepWorkflow/workflows/triggerStepWorkflow/execute',
    #         headers=self.headers, status_code=SUCCESS_ASYNC)
    #
    #     data = {"execution_uids": [response['id']],
    #             "data_in": {"data": "1"},
    #             "inputs": {"invalid": "CHANGE INPUT"}}
    #
    #     result = {"result": False}
    #
    #     @callbacks.StepInputInvalid.connect
    #     def step_input_invalids(sender, **kwargs):
    #         result['result'] = True
    #
    #     @callbacks.TriggerStepAwaitingData.connect
    #     def send_data(sender, **kwargs):
    #         self.post_with_status_check('/api/triggers/send_data', headers=self.headers, data=json.dumps(data),
    #                                     status_code=SUCCESS, content_type='application/json')
    #
    #     server.running_context.controller.shutdown_pool(1)
    #     self.assertTrue(result['result'])

    @classmethod
    def tearDownClass(cls):
        apps.clear_cache()

