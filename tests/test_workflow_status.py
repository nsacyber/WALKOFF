import json
import walkoff.case.database as case_database
from walkoff.events import WalkoffEvent
from walkoff.server import flaskserver as flask_server
from walkoff.server.returncodes import *
from tests.util.case_db_help import setup_subscriptions_for_action
from tests.util.servertestcase import ServerTestCase
import walkoff.coredb.devicedb as devicedb
from walkoff.coredb.workflowresults import WorkflowStatus, ActionStatus
from walkoff.coredb.workflow import Workflow
from uuid import uuid4
from tests.util import device_db_help
import walkoff.coredb.devicedb as db
from walkoff.core.multiprocessedexecutor.multiprocessedexecutor import MultiprocessedExecutor


def mock_pause_workflow(self, execution_id):
    WalkoffEvent.WorkflowPaused.send({"workflow_execution_id": execution_id, "id": "123"})


def mock_resume_workflow(self, execution_id):
    WalkoffEvent.WorkflowResumed.send({"workflow_execution_id": execution_id, "id": "123"})


class TestWorkflowServer(ServerTestCase):

    def setUp(self):
        MultiprocessedExecutor.pause_workflow = mock_pause_workflow
        MultiprocessedExecutor.resume_workflow = mock_resume_workflow
        case_database.initialize()

    def tearDown(self):
        device_db_help.cleanup_device_db()

        case_database.case_db.session.query(case_database.Event).delete()
        case_database.case_db.session.query(case_database.Case).delete()
        case_database.case_db.session.commit()

    def test_read_all_workflow_status_no_action(self):
        exec_id = uuid4()
        wf_id = uuid4()
        workflow_status = WorkflowStatus(exec_id, wf_id, 'test')
        workflow_status.running()

        db.device_db.session.add(workflow_status)
        db.device_db.session.commit()

        response = self.get_with_status_check('/api/workflowqueue', headers=self.headers)

        self.assertEqual(len(response), 1)
        response = response[0]

        self.assertIn('started_at', response)
        response.pop('started_at')

        expected = {'execution_id': str(exec_id),
                    'workflow_id': str(wf_id),
                    'name': 'test',
                    'status': 'running'}

        self.assertDictEqual(response, expected)

    def test_read_all_workflow_status_with_action(self):
        wf_exec_id = uuid4()
        wf_id = uuid4()
        workflow_status = WorkflowStatus(wf_exec_id, wf_id, 'test')
        workflow_status.running()

        action_exec_id = uuid4()
        action_id = uuid4()
        action_status = ActionStatus(action_exec_id, action_id, 'name', 'test_app', 'test_action')
        workflow_status._action_statuses.append(action_status)

        db.device_db.session.add(workflow_status)
        db.device_db.session.commit()

        response = self.get_with_status_check('/api/workflowqueue', headers=self.headers)

        self.assertEqual(len(response), 1)
        response = response[0]

        self.assertIn('started_at', response)
        response.pop('started_at')

        expected = {'execution_id': str(wf_exec_id),
                    'workflow_id': str(wf_id),
                    'name': 'test',
                    'status': 'running',
                    'current_action_execution_id': str(action_exec_id),
                    'current_action_id': str(action_id),
                    'current_action_name': 'name',
                    'current_app_name': 'test_app'}

        self.assertDictEqual(response, expected)

    def test_read_workflow_status(self):
        wf_exec_id = uuid4()
        wf_id = uuid4()
        workflow_status = WorkflowStatus(wf_exec_id, wf_id, 'test')
        workflow_status.running()

        action_exec_id = uuid4()
        action_id = uuid4()
        action_status = ActionStatus(action_exec_id, action_id, 'name', 'test_app', 'test_action')
        workflow_status._action_statuses.append(action_status)

        db.device_db.session.add(workflow_status)
        db.device_db.session.commit()

        response = self.get_with_status_check('/api/workflowqueue/{}'.format(str(wf_exec_id)), headers=self.headers)

        self.assertIn('started_at', response)
        response.pop('started_at')

        self.assertIn('action_statuses', response)
        self.assertIn('started_at', response['action_statuses'][-1])
        response['action_statuses'][-1].pop('started_at')

        expected = {'execution_id': str(wf_exec_id),
                    'workflow_id': str(wf_id),
                    'name': 'test',
                    'status': 'running',
                    'action_statuses': [{
                        'execution_id': str(action_exec_id),
                        'action_id': str(action_id),
                        'name': 'name',
                        'app_name': 'test_app',
                        'action_name': 'test_action',
                        'status': 'executing',
                        'arguments': []
                    }]}

        self.assertDictEqual(response, expected)

    def test_read_workflow_status_invalid_id(self):
        self.get_with_status_check('/api/workflowqueue/{}'.format(str(uuid4())), headers=self.headers,
                                   status_code=OBJECT_DNE_ERROR)

    def test_execute_workflow(self):
        playbook = device_db_help.standard_load()

        workflow = devicedb.device_db.session.query(Workflow).filter_by(_playbook_id=playbook.id).first()
        action_ids = [action.id for action in workflow.actions if action.name == 'start']
        setup_subscriptions_for_action(workflow.id, action_ids)

        result = {'count': 0}

        @WalkoffEvent.ActionExecutionSuccess.connect
        def y(sender, **kwargs):
            result['count'] += 1
            result['data'] = kwargs['data']

        response = self.post_with_status_check(
            '/api/workflowqueue',
            headers=self.headers,
            status_code=SUCCESS_ASYNC,
            content_type="application/json", data=json.dumps({'workflow_id': str(workflow.id)}))
        flask_server.running_context.controller.wait_and_reset(1)
        self.assertIn('id', response)
        self.assertEqual(result['count'], 1)
        self.assertDictEqual(result['data'], {'status': 'Success', 'result': 'REPEATING: Hello World'})

        workflow_status = devicedb.device_db.session.query(WorkflowStatus).filter_by(
            execution_id=response['id']).first()
        self.assertIsNotNone(workflow_status)
        self.assertEqual(workflow_status.status.name, 'completed')

    def test_execute_workflow_change_arguments(self):

        playbook = device_db_help.standard_load()
        workflow = devicedb.device_db.session.query(Workflow).filter_by(_playbook_id=playbook.id).first()

        action_ids = [action.id for action in workflow.actions if action.name == 'start']
        setup_subscriptions_for_action(workflow.id, action_ids)

        result = {'count': 0}

        @WalkoffEvent.ActionExecutionSuccess.connect
        def y(sender, **kwargs):
            result['count'] += 1
            result['data'] = kwargs['data']

        data = {"workflow_id": str(workflow.id),
                "arguments": [{"name": "call",
                               "value": "CHANGE INPUT"}]}

        self.post_with_status_check('/api/workflowqueue', headers=self.headers, status_code=SUCCESS_ASYNC,
                                    content_type="application/json", data=json.dumps(data))

        flask_server.running_context.controller.wait_and_reset(1)

        self.assertEqual(result['count'], 1)
        self.assertDictEqual(result['data'], {'status': 'Success', 'result': 'REPEATING: CHANGE INPUT'})

    def test_execute_workflow_pause_resume(self):

        result = {'paused': False, 'resumed': False}
        wf_exec_id = uuid4()
        wf_id = uuid4()

        @WalkoffEvent.WorkflowPaused.connect
        def workflow_paused_listener(sender, **kwargs):
            data = {'execution_id': str(wf_exec_id),
                    'status': 'resume'}

            result['paused'] = True

            wf_status = devicedb.device_db.session.query(WorkflowStatus).filter_by(
                execution_id=str(wf_exec_id)).first()
            self.assertIsNotNone(wf_status)

            self.patch_with_status_check('/api/workflowqueue', headers=self.headers, status_code=SUCCESS,
                                         content_type="application/json", data=json.dumps(data))

        @WalkoffEvent.WorkflowResumed.connect
        def workflow_resumed_listener(sender, **kwargs):
            result['resumed'] = True

        workflow_status = WorkflowStatus(wf_exec_id, wf_id, 'test')
        workflow_status.running()
        db.device_db.session.add(workflow_status)
        db.device_db.session.commit()

        data = {'execution_id': str(wf_exec_id),
                'status': 'pause'}
        self.patch_with_status_check('/api/workflowqueue', headers=self.headers, status_code=SUCCESS,
                                     content_type="application/json", data=json.dumps(data))

        self.assertTrue(result['paused'])
        self.assertTrue(result['resumed'])

    def test_abort_workflow(self):
        device_db_help.load_playbook('testGeneratedWorkflows/pauseWorkflowTest')

        workflow = devicedb.device_db.session.query(Workflow).filter_by(name='pauseWorkflow').first()

        action_ids = [action.id for action in workflow.actions if action.name == 'start']
        setup_subscriptions_for_action(workflow.id, action_ids)

        result = {"aborted": False}

        @WalkoffEvent.ActionExecutionSuccess.connect
        def y(sender, **kwargs):

            data = {'execution_id': response['id'],
                    'status': 'abort'}
            self.patch_with_status_check('/api/workflowqueue', headers=self.headers, status_code=SUCCESS,
                                         content_type="application/json", data=json.dumps(data))

        @WalkoffEvent.WorkflowAborted.connect
        def workflow_aborted_listener(sender, **kwargs):
            result['aborted'] = True

        response = self.post_with_status_check('/api/workflowqueue', headers=self.headers, status_code=SUCCESS_ASYNC,
                                               content_type="application/json",
                                               data=json.dumps({'workflow_id': str(workflow.id)}))

        flask_server.running_context.controller.wait_and_reset(1)
        self.assertIn('id', response)
        self.assertTrue(result['aborted'])

        workflow_status = devicedb.device_db.session.query(WorkflowStatus).filter_by(
            execution_id=response['id']).first()
        self.assertIsNotNone(workflow_status)
        self.assertEqual(workflow_status.status.name, 'aborted')
