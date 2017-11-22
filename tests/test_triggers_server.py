import socket
import json
import gevent

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

    def test_trigger_multiple_workflows(self):

        ids = []

        response = self.post_with_status_check(
            '/api/playbooks/triggerActionWorkflow/workflows/triggerActionWorkflow/execute',
            headers=self.headers, status_code=SUCCESS_ASYNC, content_type="application/json",
            data=json.dumps({}))
        ids.append(response['id'])

        response = self.post_with_status_check(
            '/api/playbooks/triggerActionWorkflow/workflows/triggerActionWorkflow/execute',
            headers=self.headers, status_code=SUCCESS_ASYNC, content_type="application/json",
            data=json.dumps({}))
        ids.append(response['id'])

        data = {"execution_uids": ids,
                "data_in": {"data": "1"}}

        result = {"result": 0,
                  "num_trigs": 0}

        def gevent_wait_thread():
            execd_ids = set([])
            timeout = 0
            threshold = 5
            while len(execd_ids) != len(ids) and timeout < threshold:
                resp = self.post_with_status_check('/api/triggers/send_data', headers=self.headers,
                                                   data=json.dumps(data),
                                                   status_code=SUCCESS, content_type='application/json')
                execd_ids.update(set.intersection(set(ids), set(resp)))
                gevent.sleep(0.1)
                timeout += 0.1
            return

        @callbacks.TriggerActionAwaitingData.connect
        def send_data(sender, **kwargs):
            if result["num_trigs"] == 1:
                gevent.spawn(gevent_wait_thread)
            else:
                result["num_trigs"] += 1

        @callbacks.TriggerActionTaken.connect
        def trigger_taken(sender, **kwargs):
            result['result'] += 1

        flask_server.running_context.controller.wait_and_reset(2)
        self.assertEqual(result['result'], 2)

    def test_trigger_execute(self):

        response = self.post_with_status_check(
            '/api/playbooks/triggerActionWorkflow/workflows/triggerActionWorkflow/execute',
            headers=self.headers, status_code=SUCCESS_ASYNC, content_type="application/json", data=json.dumps({}))

        ids = [response['id']]

        data = {"execution_uids": ids,
                "data_in": {"data": "1"}}

        result = {"result": False}

        def gevent_wait_thread():
            execd_ids = set([])
            timeout = 0
            threshold = 5
            while len(execd_ids) != len(ids) and timeout < threshold:
                resp = self.post_with_status_check('/api/triggers/send_data', headers=self.headers,
                                                   data=json.dumps(data),
                                                   status_code=SUCCESS, content_type='application/json')
                execd_ids.update(set.intersection(set(ids), set(resp)))
                gevent.sleep(0.1)
                timeout += 0.1

        @callbacks.TriggerActionAwaitingData.connect
        def send_data(sender, **kwargs):
            gevent.spawn(gevent_wait_thread)

        @callbacks.TriggerActionTaken.connect
        def trigger_taken(sender, **kwargs):
            result['result'] = True

        flask_server.running_context.controller.wait_and_reset(1)
        self.assertTrue(result['result'])

    def test_trigger_execute_multiple_data(self):

        response = self.post_with_status_check(
            '/api/playbooks/triggerActionWorkflow/workflows/triggerActionWorkflow/execute',
            headers=self.headers, status_code=SUCCESS_ASYNC, content_type="application/json", data=json.dumps({}))

        ids = [response['id']]

        data = {"execution_uids": ids,
                "data_in": {"data": "aaa"}}

        result = {"result": 0}

        def gevent_wait_thread():
            execd_ids = set([])
            timeout = 0
            threshold = 5
            while len(execd_ids) != len(ids) and timeout < threshold:
                resp = self.post_with_status_check('/api/triggers/send_data', headers=self.headers,
                                                   data=json.dumps(data),
                                                   status_code=SUCCESS, content_type='application/json')
                execd_ids.update(set.intersection(set(ids), set(resp)))
                gevent.sleep(0.1)
                timeout += 0.1

            data_correct = {"execution_uids": [response['id']], "data_in": {"data": "1"}}
            execd_ids = set([])
            timeout = 0
            while len(execd_ids) != len(ids) and timeout < threshold:
                resp = self.post_with_status_check('/api/triggers/send_data', headers=self.headers,
                                                   data=json.dumps(data_correct),
                                                   status_code=SUCCESS, content_type='application/json')
                execd_ids.update(set.intersection(set(ids), set(resp)))
                gevent.sleep(0.1)
                timeout += 0.1

        @callbacks.TriggerActionAwaitingData.connect
        def send_data(sender, **kwargs):
            gevent.spawn(gevent_wait_thread)

        @callbacks.TriggerActionTaken.connect
        def trigger_taken(sender, **kwargs):
            result['result'] += 1

        flask_server.running_context.controller.wait_and_reset(1)
        self.assertEqual(result['result'], 1)

    def test_trigger_execute_change_input(self):

        response = self.post_with_status_check(
            '/api/playbooks/triggerActionWorkflow/workflows/triggerActionWorkflow/execute',
            headers=self.headers, status_code=SUCCESS_ASYNC, content_type="application/json", data=json.dumps({}))

        ids = [response['id']]

        data = {"execution_uids": ids,
                "data_in": {"data": "1"},
                "arguments": [{"name": "call",
                               "value": "CHANGE INPUT"}]}

        result = {"value": None}

        @callbacks.ActionExecutionSuccess.connect
        def action_finished_listener(sender, **kwargs):
            result['value'] = kwargs['data']

        def gevent_wait_thread():
            execd_ids = set([])
            timeout = 0
            threshold = 5
            while len(execd_ids) != len(ids) and timeout < threshold:
                resp = self.post_with_status_check('/api/triggers/send_data', headers=self.headers,
                                                   data=json.dumps(data),
                                                   status_code=SUCCESS, content_type='application/json')
                execd_ids.update(set.intersection(set(ids), set(resp)))
                gevent.sleep(0.1)
                timeout += 0.1

        @callbacks.TriggerActionAwaitingData.connect
        def send_data(sender, **kwargs):
            gevent.spawn(gevent_wait_thread)

        flask_server.running_context.controller.wait_and_reset(1)

        self.assertDictEqual(result['value'], {'result': 'REPEATING: CHANGE INPUT', 'status': 'Success'})

    def test_trigger_execute_with_change_input_invalid_input(self):

        response = self.post_with_status_check(
            '/api/playbooks/triggerActionWorkflow/workflows/triggerActionWorkflow/execute',
            headers=self.headers, status_code=SUCCESS_ASYNC, content_type="application/json", data=json.dumps({}))

        ids = [response['id']]

        data = {"execution_uids": ids,
                "data_in": {"data": "1"},
                "arguments": [{"name": "invalid",
                               "value": "CHANGE INPUT"}]}

        result = {"result": False}

        @callbacks.ActionArgumentsInvalid.connect
        def action_input_invalids(sender, **kwargs):
            result['result'] = True

        def gevent_wait_thread():
            execd_ids = set([])
            timeout = 0
            threshold = 5
            while len(execd_ids) != len(ids) and timeout < threshold:
                resp = self.post_with_status_check('/api/triggers/send_data', headers=self.headers,
                                                   data=json.dumps(data),
                                                   status_code=SUCCESS, content_type='application/json')
                execd_ids.update(set.intersection(set(ids), set(resp)))
                gevent.sleep(0.1)
                timeout += 0.1

        @callbacks.TriggerActionAwaitingData.connect
        def send_data(sender, **kwargs):
            gevent.spawn(gevent_wait_thread)

        flask_server.running_context.controller.wait_and_reset(1)
        self.assertTrue(result['result'])
