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
from tests.util.thread_control import modified_setup_worker_env

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
        flask_server.running_context.controller.initialize_threading(worker_environment_setup=modified_setup_worker_env)

        ids = []

        response=self.post_with_status_check(
            '/api/playbooks/triggerStepWorkflow/workflows/triggerStepWorkflow/execute',
            headers=self.headers, status_code=SUCCESS_ASYNC)
        ids.append(response['id'])

        response = self.post_with_status_check(
            '/api/playbooks/triggerStepWorkflow/workflows/triggerStepWorkflow/execute',
            headers=self.headers, status_code=SUCCESS_ASYNC)
        ids.append(response['id'])

        data = {"execution_uids": ids,
                "data_in": {"data": "1"}}

        result = {"result": 0,
                  "num_trigs": 0}

        @callbacks.TriggerStepAwaitingData.connect
        def send_data(sender, **kwargs):
            if result["num_trigs"] == 1:
                self.post_with_status_check('/api/triggers/send_data', headers=self.headers, data=json.dumps(data),
                                            status_code=SUCCESS, content_type='application/json')
            else:
                result["num_trigs"] += 1

        @callbacks.TriggerStepTaken.connect
        def trigger_taken(sender, **kwargs):
            result['result'] += 1

        import time
        time.sleep(1)
        flask_server.running_context.controller.shutdown_pool(2)
        self.assertEqual(result['result'], 2)
