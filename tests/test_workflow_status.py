import json
from uuid import uuid4, UUID

from flask import current_app

import walkoff.executiondb.schemas
from tests.util import execution_db_help
from tests.util.servertestcase import ServerTestCase
from walkoff.events import WalkoffEvent
from walkoff.executiondb import WorkflowStatusEnum, ActionStatusEnum
from walkoff.executiondb.executionelement import ExecutionElement
from walkoff.executiondb.workflow import Workflow
from walkoff.executiondb.workflowresults import WorkflowStatus, ActionStatus
from walkoff.multiprocessedexecutor.multiprocessedexecutor import MultiprocessedExecutor
from walkoff.server.returncodes import *
import walkoff.server.workflowresults


class MockWorkflow(ExecutionElement):
    def __init__(self, execution_id):
        self.execution_id = execution_id
        self.id = '123'
        self.name = 'workflow'

    def get_execution_id(self):
        return self.execution_id

    def as_json(self):
        return {'id': self.id, 'name': self.name, 'execution_id': self.execution_id}


class MockWorkflowSchema(object):
    @staticmethod
    def dump(workflow):
        class Dummy:
            def __init__(self, data):
                self.data = data

        return Dummy({'id': str(workflow.id), 'name': workflow.name, 'execution_id': str(workflow.execution_id)})


def mock_pause_workflow(self, execution_id):
    WalkoffEvent.WorkflowPaused.send({'execution_id': execution_id, 'id': '123', 'name': 'workflow'})


def mock_resume_workflow(self, execution_id):
    WalkoffEvent.WorkflowResumed.send(MockWorkflow(execution_id), data={"execution_id": execution_id})


class TestWorkflowStatus(ServerTestCase):

    def setUp(self):
        MultiprocessedExecutor.pause_workflow = mock_pause_workflow
        MultiprocessedExecutor.resume_workflow = mock_resume_workflow
        walkoff.executiondb.schemas._schema_lookup[MockWorkflow] = MockWorkflowSchema

    def tearDown(self):
        execution_db_help.cleanup_execution_db()
        walkoff.executiondb.schemas._schema_lookup.pop(MockWorkflow, None)

    def act_on_workflow(self, execution_id, action):
        data = {'execution_id': execution_id, 'status': action}
        self.patch_with_status_check('/api/workflowqueue', headers=self.headers, status_code=NO_CONTENT,
                                     content_type="application/json", data=json.dumps(data))

    @staticmethod
    def make_generic_workflow_status():
        return WorkflowStatus(uuid4(), uuid4(), 'wf1')

    @staticmethod
    def make_generic_action_statuses(number):
        return [ActionStatus(uuid4(), uuid4(), 'app', 'action', 'name') for _ in range(number)]

    def test_read_all_workflow_status_no_action(self):
        exec_id = uuid4()
        wf_id = uuid4()
        workflow_status = WorkflowStatus(exec_id, wf_id, 'test')
        workflow_status.running()

        self.app.running_context.execution_db.session.add(workflow_status)
        self.app.running_context.execution_db.session.commit()

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

        self.app.running_context.execution_db.session.add(workflow_status)
        self.app.running_context.execution_db.session.commit()

        response = self.get_with_status_check('/api/workflowqueue', headers=self.headers)

        self.assertEqual(len(response), 1)
        response = response[0]

        self.assertIn('started_at', response)
        response.pop('started_at')
        expected = {'execution_id': str(wf_exec_id),
                    'workflow_id': str(wf_id),
                    'name': 'test',
                    'status': 'running',
                    'current_action': {
                        'execution_id': str(action_exec_id),
                        'action_id': str(action_id),
                        'action_name': 'test_action',
                        'app_name': 'test_app',
                        'name': 'name'}}
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

        self.app.running_context.execution_db.session.add(workflow_status)
        self.app.running_context.execution_db.session.commit()

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
        playbook = execution_db_help.standard_load()

        workflow = self.app.running_context.execution_db.session.query(Workflow).filter_by(
            playbook_id=playbook.id).first()

        result = {'count': 0}

        @WalkoffEvent.ActionExecutionSuccess.connect
        def y(sender, **kwargs):
            result['count'] += 1

        response = self.post_with_status_check(
            '/api/workflowqueue',
            headers=self.headers,
            status_code=SUCCESS_ASYNC,
            content_type="application/json", data=json.dumps({'workflow_id': str(workflow.id)}))
        current_app.running_context.executor.wait_and_reset(1)
        self.assertIn('id', response)
        self.assertEqual(result['count'], 1)

        workflow_status = self.app.running_context.execution_db.session.query(WorkflowStatus).filter_by(
            execution_id=response['id']).first()
        self.assertIsNotNone(workflow_status)
        self.assertEqual(workflow_status.status.name, 'completed')

    def test_execute_workflow_change_arguments(self):
        playbook = execution_db_help.standard_load()
        workflow = self.app.running_context.execution_db.session.query(Workflow).filter_by(
            playbook_id=playbook.id).first()

        result = {'count': 0}

        @WalkoffEvent.ActionExecutionSuccess.connect
        def y(sender, **kwargs):
            result['count'] += 1
            result['output'] = kwargs['data']['data']['result']

        data = {"workflow_id": str(workflow.id),
                "arguments": [{"name": "call",
                               "value": "CHANGE INPUT"}]}

        response = self.post_with_status_check('/api/workflowqueue', headers=self.headers, status_code=SUCCESS_ASYNC,
                                               content_type="application/json", data=json.dumps(data))

        current_app.running_context.executor.wait_and_reset(1)

        self.assertEqual(result['count'], 1)
        self.assertEqual(result['output'], 'REPEATING: CHANGE INPUT')

    def test_execute_workflow_change_env_vars(self):
        playbook = execution_db_help.standard_load()
        workflow = self.app.running_context.execution_db.session.query(Workflow).filter_by(
            playbook_id=playbook.id).first()
        env_var_id = str(uuid4())
        workflow.actions[0].arguments[0].value = None
        workflow.actions[0].arguments[0].reference = env_var_id

        result = {'count': 0, 'output': None}

        @WalkoffEvent.ActionExecutionSuccess.connect
        def y(sender, **kwargs):
            result['count'] += 1
            result['output'] = kwargs['data']['data']['result']

        data = {"workflow_id": str(workflow.id),
                "environment_variables": [{"id": env_var_id, "value": "CHANGE INPUT"}]}

        response = self.post_with_status_check('/api/workflowqueue', headers=self.headers, status_code=SUCCESS_ASYNC,
                                               content_type="application/json", data=json.dumps(data))

        current_app.running_context.executor.wait_and_reset(1)

        self.assertEqual(result['count'], 1)
        self.assertEqual(result['output'], 'REPEATING: CHANGE INPUT')

        action = current_app.running_context.execution_db.session.query(ActionStatus).filter(
            ActionStatus._workflow_status_id == UUID(response['id'])).first()
        arguments = json.loads(action.arguments)
        self.assertEqual(arguments[0]["name"], "call")
        self.assertIn('reference', arguments[0])

    def test_execute_workflow_pause_resume(self):
        result = {'paused': False, 'resumed': False}
        wf_exec_id = uuid4()
        wf_id = uuid4()

        @WalkoffEvent.WorkflowPaused.connect
        def workflow_paused_listener(sender, **kwargs):
            result['paused'] = True

            wf_status = self.app.running_context.execution_db.session.query(WorkflowStatus).filter_by(
                execution_id=str(wf_exec_id)).first()
            self.assertIsNotNone(wf_status)

            self.act_on_workflow(str(wf_exec_id), 'resume')

        @WalkoffEvent.WorkflowResumed.connect
        def workflow_resumed_listener(sender, **kwargs):
            result['resumed'] = True

        workflow_status = WorkflowStatus(wf_exec_id, wf_id, 'test')
        workflow_status.running()
        self.app.running_context.execution_db.session.add(workflow_status)
        self.app.running_context.execution_db.session.commit()

        self.act_on_workflow(str(wf_exec_id), 'pause')

        self.assertTrue(result['paused'])
        self.assertTrue(result['resumed'])

    def test_abort_workflow(self):
        execution_db_help.load_playbook('pauseWorkflowTest')

        workflow = self.app.running_context.execution_db.session.query(Workflow).filter_by(name='pauseWorkflow').first()

        result = {"aborted": False}

        @WalkoffEvent.ActionExecutionSuccess.connect
        def y(sender, **kwargs):
            self.act_on_workflow(response['id'], 'abort')

        @WalkoffEvent.WorkflowAborted.connect
        def workflow_aborted_listener(sender, **kwargs):
            result['aborted'] = True

        response = self.post_with_status_check('/api/workflowqueue', headers=self.headers, status_code=SUCCESS_ASYNC,
                                               content_type="application/json",
                                               data=json.dumps({'workflow_id': str(workflow.id)}))

        current_app.running_context.executor.wait_and_reset(1)
        self.assertIn('id', response)
        self.assertTrue(result['aborted'])

        workflow_status = self.app.running_context.execution_db.session.query(WorkflowStatus).filter_by(
            execution_id=response['id']).first()
        self.assertIsNotNone(workflow_status)
        self.assertEqual(workflow_status.status.name, 'aborted')

    def test_abort_statuses_no_actions(self):
        workflow_status = self.make_generic_workflow_status()
        workflow_status.aborted()
        self.assertEqual(workflow_status.status, WorkflowStatusEnum.aborted)

    def test_abort_statuses_with_actions_not_paused_or_awaiting_data(self):
        workflow_status = self.make_generic_workflow_status()
        actions = self.make_generic_action_statuses(3)
        workflow_status._action_statuses = actions
        workflow_status.aborted()
        self.assertEqual(workflow_status.status, WorkflowStatusEnum.aborted)
        self.assertEqual(actions[-1].status, ActionStatusEnum.executing)

    def test_abort_statuses_with_actions_last_awaiting_data(self):
        workflow_status = self.make_generic_workflow_status()
        actions = self.make_generic_action_statuses(3)
        actions[-1].status = ActionStatusEnum.awaiting_data
        workflow_status._action_statuses = actions
        workflow_status.aborted()
        self.assertEqual(workflow_status.status, WorkflowStatusEnum.aborted)
        self.assertEqual(actions[-1].status, ActionStatusEnum.aborted)

    def test_workflowqueue_pagination(self):
        for i in range(40):
            workflow_status = WorkflowStatus(uuid4(), uuid4(), 'test')
            workflow_status.running()
            self.app.running_context.execution_db.session.add(workflow_status)
            self.app.running_context.execution_db.session.commit()

        response = self.get_with_status_check('/api/workflowqueue', headers=self.headers)
        self.assertEqual(len(response), 20)

        response = self.get_with_status_check('/api/workflowqueue?page=2', headers=self.headers)
        self.assertEqual(len(response), 20)

        response = self.get_with_status_check('/api/workflowqueue?page=3', headers=self.headers)
        self.assertEqual(len(response), 0)
