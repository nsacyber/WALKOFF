import json
import os
from copy import deepcopy
from os import path
from threading import Event

import walkoff.case.database as case_database
import walkoff.config.paths
from walkoff import helpers
from walkoff.coredb.argument import Argument
from walkoff.events import WalkoffEvent
from walkoff.coredb.action import Action
from walkoff.coredb.branch import Branch
from walkoff.server import flaskserver as flask_server
from walkoff.server.returncodes import *
from tests.util.assertwrappers import orderless_list_compare
from tests.util.case_db_help import setup_subscriptions_for_action
from tests.util.servertestcase import ServerTestCase
import walkoff.coredb.devicedb
from walkoff.coredb.playbook import Playbook
from walkoff.coredb.workflow import Workflow


class TestWorkflowServer(ServerTestCase):
    def setUp(self):
        self.playbooks_added = []
        self.workflows_added = []
        self.add_playbook_name = 'add_playbook'
        self.change_playbook_name = 'change_playbook'
        self.add_workflow_name = 'add_workflow'
        self.change_workflow_name = 'change_workflow'
        self.update_playbooks = False
        self.update_workflows = False
        self.empty_workflow_json = \
            {'actions': [
                {"app_name": "HelloWorld", "action_name": "helloWorld", "name": "helloworld", "id": -1, "triggers": [],
                 "arguments": []}],
                'name': self.add_workflow_name,
                'start': -1,
                'branches': []}

        case_database.initialize()

    def tearDown(self):
        if self.update_playbooks:
            playbook = walkoff.coredb.devicedb.device_db.session.query(Playbook).filter_by(
                name=self.add_playbook_name).first()
            if playbook:
                walkoff.coredb.devicedb.device_db.session.delete(playbook)
            playbook = walkoff.coredb.devicedb.device_db.session.query(Playbook).filter_by(
                name=self.change_playbook_name).first()
            if playbook:
                walkoff.coredb.devicedb.device_db.session.delete(playbook)

        if self.update_workflows:
            workflow = walkoff.coredb.devicedb.device_db.session.query(Workflow).filter_by(
                name=self.add_workflow_name).first()
            if workflow:
                walkoff.coredb.devicedb.device_db.session.delete(workflow)
            workflow = walkoff.coredb.devicedb.device_db.session.query(Workflow).filter_by(
                name=self.change_workflow_name).first()
            if workflow:
                walkoff.coredb.devicedb.device_db.session.delete(workflow)

        walkoff.coredb.devicedb.device_db.session.commit()

        case_database.case_db.tear_down()
        walkoff.coredb.devicedb.device_db.tear_down()

    def copy_playbook(self):
        data = {'playbook_name': self.add_playbook_name}
        self.update_playbooks = True
        response = self.post_with_status_check('/api/playbooks/1/copy', data=json.dumps(data), headers=self.headers,
                                               content_type='application/json', status_code=OBJECT_CREATED)
        return response

    def copy_workflow(self):
        data = {'workflow_name': self.add_workflow_name}
        self.update_workflows = True
        response = self.post_with_status_check('/api/playbooks/1/workflows/1/copy', data=json.dumps(data),
                                               headers=self.headers,
                                               content_type='application/json', status_code=OBJECT_CREATED)
        return response

    @staticmethod
    def strip_uids(element):
        element.pop('uid', None)
        for key, value in element.items():
            if isinstance(value, list):
                for list_element in (list_element_ for list_element_ in value if isinstance(list_element_, dict)):
                    TestWorkflowServer.strip_uids(list_element)
            elif isinstance(value, dict):
                for dict_element in (element for element in value.values() if isinstance(element, dict)):
                    TestWorkflowServer.strip_uids(dict_element)

    def test_display_all_playbooks(self):
        num_playbooks = len(walkoff.coredb.devicedb.device_db.session.query(Playbook).all())
        response = self.get_with_status_check('/api/playbooks', headers=self.headers)
        for playbook in response:
            for workflow in playbook['workflows']:
                workflow.pop('id')

        for playbook in response:
            if playbook['name'] == 'test':
                self.assertEqual(playbook['workflows'], [{'name': 'helloWorldWorkflow'}])
            elif playbook['name'] == 'triggerActionWorkflow':
                self.assertEqual(playbook['workflows'], [{"name": "triggerActionWorkflow"}])
            elif playbook['name'] == 'pauseWorkflowTest':
                self.assertEqual(playbook['workflows'], [{"name": "pauseWorkflow"}])

        self.assertEqual(len(response), num_playbooks)

    def test_display_playbook_workflows(self):
        playbook = walkoff.coredb.devicedb.device_db.session.query(Playbook).filter_by(name='test').first()
        response = self.get_with_status_check('/api/playbooks/{}'.format(playbook.id), headers=self.headers)

        workflows = [workflow.read() for workflow in playbook.workflows]

        self.assertEqual(response['name'], 'test')
        self.assertEqual(len(response['workflows']), len(workflows))
        self.assertListEqual(response['workflows'], workflows)

    def test_display_playbook_workflows_invalid_id(self):
        self.get_with_status_check('/api/playbooks/0', error='Playbook does not exist.', headers=self.headers,
                                   status_code=OBJECT_DNE_ERROR)

    def test_display_workflow_invalid_id(self):
        self.get_with_status_check('/api/playbooks/2/workflows/0',
                                   error='Workflow does not exist',
                                   headers=self.headers, status_code=OBJECT_DNE_ERROR)

    def test_add_playbook(self):
        expected_playbooks = walkoff.coredb.devicedb.device_db.session.query(Playbook).all()
        original_length = len(list(expected_playbooks))
        data = {"name": self.add_playbook_name}
        self.update_playbooks = True
        response = self.put_with_status_check('/api/playbooks', headers=self.headers,
                                              status_code=OBJECT_CREATED, data=json.dumps(data),
                                              content_type="application/json")

        response.pop('id')

        self.assertDictEqual(response, {'name': self.add_playbook_name, 'workflows': []})
        self.assertEqual(len(list(walkoff.coredb.devicedb.device_db.session.query(Playbook).all())),
                         original_length + 1)

    def test_add_playbook_already_exists(self):
        data = {"name": self.add_playbook_name}
        self.playbooks_added.append(self.add_playbook_name)
        self.update_playbooks = True
        self.put_with_status_check('/api/playbooks',
                                   data=json.dumps(data), headers=self.headers, status_code=OBJECT_CREATED,
                                   content_type="application/json")
        self.put_with_status_check('/api/playbooks',
                                   error='Unique constraint failed.',
                                   data=json.dumps(data), headers=self.headers, status_code=OBJECT_EXISTS_ERROR,
                                   content_type="application/json")

    def test_edit_playbook_name(self):
        response = self.copy_playbook()

        data = {'id': response['id'], 'name': self.change_playbook_name}
        response = self.post_with_status_check('/api/playbooks',
                                               data=json.dumps(data),
                                               headers=self.headers,
                                               content_type='application/json')
        self.assertEqual(response['name'], self.change_playbook_name)

    def test_edit_playbook_invalid_id(self):
        expected = walkoff.coredb.devicedb.device_db.session.query(Playbook).all()
        data = {"id": 0}
        response = self.app.post('/api/playbooks', headers=self.headers, content_type="application/json",
                                 data=json.dumps(data))
        self.assertEqual(response._status_code, 461)
        self.assertListEqual(walkoff.coredb.devicedb.device_db.session.query(Playbook).all(), expected)

    def test_add_workflow(self):
        response = self.copy_playbook()

        initial_playbooks = walkoff.coredb.devicedb.device_db.session.query(Playbook).all()
        initial_workflows = next(
            playbook.workflows for playbook in initial_playbooks if playbook.name == self.add_playbook_name)
        initial_workflows_len = len(initial_workflows)

        self.update_workflows = True
        response = self.put_with_status_check('/api/playbooks/{}/workflows'.format(response['id']),
                                              headers=self.headers, status_code=OBJECT_CREATED,
                                              data=json.dumps(self.empty_workflow_json),
                                              content_type="application/json")
        self.empty_workflow_json['id'] = response['id']

        final_playbooks = walkoff.coredb.devicedb.device_db.session.query(Playbook).all()
        final_workflows = next(
            playbook.workflows for playbook in final_playbooks if playbook.name == self.add_playbook_name)
        self.assertEqual(len(final_workflows), initial_workflows_len + 1)

        workflow = walkoff.coredb.devicedb.device_db.session.query(Workflow).join(Workflow._playbook).filter(
            Workflow.name == self.add_workflow_name, Playbook.name == self.add_playbook_name).first()
        self.assertIsNotNone(workflow)

    def test_edit_workflow_name_only(self):
        response = self.copy_workflow()
        workflow = walkoff.coredb.devicedb.device_db.session.query(Workflow).filter_by(id=response['id']).first()
        expected_json = workflow.read()
        expected_json['name'] = self.change_workflow_name
        response = self.post_with_status_check('/api/playbooks/1/workflows',
                                               data=json.dumps(expected_json),
                                               headers=self.headers,
                                               content_type='application/json')

        self.assertDictEqual(response, expected_json)

        self.assertIsNotNone(
            walkoff.coredb.devicedb.device_db.session.query(Workflow).filter_by(id=workflow.id).first())
        self.assertIsNone(
            walkoff.coredb.devicedb.device_db.session.query(Workflow).join(Workflow._playbook).filter(
                Workflow.name == self.add_workflow_name).first())

    def test_edit_workflow_invalid_id(self):
        playbook = walkoff.coredb.devicedb.device_db.session.query(Playbook).filter_by(name='test').first()
        workflow = playbook.workflows[0].read()
        workflow['id'] = 0
        initial_workflows = walkoff.coredb.devicedb.device_db.session.query(Workflow).all()
        self.post_with_status_check('/api/playbooks/{}/workflows'.format(playbook.id),
                                    data=json.dumps(workflow), headers=self.headers, content_type="application/json",
                                    status_code=OBJECT_DNE_ERROR)
        final_workflows = walkoff.coredb.devicedb.device_db.session.query(Workflow).all()
        self.assertSetEqual(set(final_workflows), set(initial_workflows))

    def test_delete_playbook(self):
        response = self.copy_playbook()

        self.delete_with_status_check('/api/playbooks/{}'.format(response['id']), headers=self.headers)

        self.assertIsNone(
            walkoff.coredb.devicedb.device_db.session.query(Playbook).filter_by(id=response['id']).first())

    def test_delete_playbook_invalid_id(self):
        response = self.copy_playbook()
        self.delete_with_status_check('/api/playbooks/0', headers=self.headers, status_code=OBJECT_DNE_ERROR)

        self.assertIsNotNone(
            walkoff.coredb.devicedb.device_db.session.query(Playbook).filter_by(id=response['id']).first())

    def test_delete_workflow(self):
        response = self.copy_workflow()

        self.delete_with_status_check('/api/playbooks/1/workflows/{}'.format(response['id']), headers=self.headers)
        self.assertIsNone(
            walkoff.coredb.devicedb.device_db.session.query(Workflow).filter_by(id=response['id']).first())

    def test_delete_workflow_invalid_id(self):
        self.delete_with_status_check('/api/playbooks/1/workflows/0',
                                      headers=self.headers, status_code=OBJECT_DNE_ERROR)

    def test_copy_workflow(self):
        self.update_workflows = True
        response = self.post_with_status_check('/api/playbooks/1/workflows/1/copy',
                                               headers=self.headers, status_code=OBJECT_CREATED,
                                               data=json.dumps({'workflow_name': self.add_workflow_name}),
                                               content_type="application/json")
        playbook = walkoff.coredb.devicedb.device_db.session.query(Playbook).filter_by(id=1).first()
        self.assertEqual(len(playbook.workflows), 2)

        for workflow in playbook.workflows:
            self.assertIn(workflow.name, ['helloWorldWorkflow', self.add_workflow_name])
            if workflow.name == 'helloWorldWorkflow':
                workflow_original = workflow
            elif workflow.name == self.add_workflow_name:
                workflow_copy = workflow

        copy_workflow_json = workflow_copy.read()
        original_workflow_json = workflow_original.read()
        copy_workflow_json.pop('name', None)
        original_workflow_json.pop('name', None)
        self.assertNotEqual(original_workflow_json['start'], copy_workflow_json['start'])
        copy_workflow_json.pop('start')
        original_workflow_json.pop('start')
        self.assertEqual(len(workflow_original.actions), len(workflow_copy.actions))

    def test_copy_workflow_different_playbook(self):
        self.update_workflows = True
        data = {"workflow_name": self.add_workflow_name, "playbook_id": 2}
        self.post_with_status_check('/api/playbooks/1/workflows/1/copy', data=json.dumps(data),
                                    headers=self.headers, status_code=OBJECT_CREATED, content_type="application/json")

        original_playbook = walkoff.coredb.devicedb.device_db.session.query(Playbook).filter_by(id=1).first()
        new_playbook = walkoff.coredb.devicedb.device_db.session.query(Playbook).filter_by(id=2).first()
        for workflow in original_playbook.workflows:
            if workflow.name == 'helloWorldWorkflow':
                original_workflow = workflow
        copy_workflow = walkoff.coredb.devicedb.device_db.session.query(Workflow).filter_by(name=self.add_workflow_name).first()

        self.assertEqual(len(original_playbook.workflows), 1)
        self.assertEqual(len(new_playbook.workflows), 2)
        self.assertIsNotNone(copy_workflow)

        self.assertNotEqual(original_workflow.start, copy_workflow.start)
        self.assertEqual(len(original_workflow.actions), len(copy_workflow.actions))

    def test_copy_playbook(self):
        response = self.copy_playbook()

        original_playbook = walkoff.coredb.devicedb.device_db.session.query(Playbook).filter_by(name='test').first()
        copy_playbook = walkoff.coredb.devicedb.device_db.session.query(Playbook).filter_by(name=self.add_playbook_name).first()

        self.assertIsNotNone(original_playbook)
        self.assertIsNotNone(copy_playbook)

        self.assertEqual(len(original_playbook.workflows), len(copy_playbook.workflows))

    def test_execute_workflow_playbook_dne(self):
        self.post_with_status_check('/api/playbooks/0/workflows/1/execute',
                                    error='Workflow does not exist',
                                    headers=self.headers, status_code=OBJECT_DNE_ERROR,
                                    content_type="application/json", data=json.dumps({}))

    def test_execute_workflow_workflow_dne(self):
        self.post_with_status_check('/api/playbooks/1/workflows/0/execute',
                                    error='Workflow does not exist',
                                    headers=self.headers, status_code=OBJECT_DNE_ERROR,
                                    content_type="application/json", data=json.dumps({}))

    def test_execute_workflow(self):
        sync = Event()
        workflow = walkoff.coredb.devicedb.device_db.session.query(Workflow).filter_by(id=1).first()
        action_uids = [action.id for action in workflow.actions if action.name == 'start']
        setup_subscriptions_for_action(workflow.id, action_uids)

        @WalkoffEvent.WorkflowShutdown.connect
        def wait_for_completion(sender, **kwargs):
            sync.set()

        result = {'count': 0}

        @WalkoffEvent.ActionExecutionSuccess.connect
        def y(sender, **kwargs):
            result['count'] += 1
            result['data'] = kwargs['data']

        response = self.post_with_status_check('/api/playbooks/1/workflows/1/execute',
                                               headers=self.headers,
                                               status_code=SUCCESS_ASYNC,
                                               content_type="application/json", data=json.dumps({}))
        flask_server.running_context.controller.wait_and_reset(1)
        self.assertIn('id', response)
        sync.wait(timeout=10)
        self.assertEqual(result['count'], 1)
        self.assertDictEqual(result['data'], {'status': 'Success', 'result': 'REPEATING: Hello World'})

    def test_execute_workflow_pause_resume(self):
        sync = Event()

        workflow = walkoff.coredb.devicedb.device_db.session.query(Workflow).filter_by(name='pauseWorkflow').first()

        action_uids = [action.id for action in workflow.actions if action.name == 'start']
        setup_subscriptions_for_action(workflow.id, action_uids)

        result = {'paused': False, 'count': 0, 'data': []}

        @WalkoffEvent.ActionExecutionSuccess.connect
        def y(sender, **kwargs):
            result['count'] += 1
            result['data'].append(kwargs['data'])
            if not result['paused']:
                result['response2'] = self.post_with_status_check(
                    '/api/playbooks/{0}/workflows/{1}/pause'.format(workflow._playbook_id, workflow.id),
                    headers=self.headers,
                    status_code=SUCCESS,
                    content_type="application/json", data=json.dumps(response))

        @WalkoffEvent.WorkflowPaused.connect
        def workflow_paused_listener(sender, **kwargs):
            result['paused'] = True
            result['response3'] = self.post_with_status_check(
                '/api/playbooks/{0}/workflows/{1}/resume'.format(workflow._playbook_id, workflow.id),
                headers=self.headers,
                status_code=SUCCESS,
                content_type="application/json", data=json.dumps(response))

        @WalkoffEvent.WorkflowResumed.connect
        def workflow_resumed_listner(sender, **kwargs):
            result['resumed'] = True

        @WalkoffEvent.WorkflowShutdown.connect
        def wait_for_completion(sender, **kwargs):
            sync.set()

        response = self.post_with_status_check('/api/playbooks/{0}/workflows/{1}/execute'.format(workflow._playbook_id, workflow.id),
                                               headers=self.headers,
                                               status_code=SUCCESS_ASYNC,
                                               content_type="application/json", data=json.dumps({}))

        flask_server.running_context.controller.wait_and_reset(1)
        sync.wait(timeout=10)
        self.assertIn('id', response)
        self.assertTrue(result['paused'])
        self.assertTrue(result['resumed'])
        self.assertEqual(result['count'], 3)
        self.assertDictEqual(result['response2'], {'info': 'Workflow paused'})
        self.assertDictEqual(result['response3'], {'info': 'Workflow resumed'})
        expected_data = [{'status': 'Success', 'result': {'message': 'HELLO WORLD'}},
                         {'status': 'Success', 'result': None}, {'status': 'Success', 'result': None}]
        self.assertEqual(len(result['data']), len(expected_data))
        for exp, act in zip(expected_data, result['data']):
            self.assertDictEqual(exp, act)

    def test_execute_workflow_change_arguments(self):

        response = self.copy_workflow()
        workflow = walkoff.coredb.devicedb.device_db.session.query(Workflow).filter_by(id=response['id']).first()

        action_uids = [action.id for action in workflow.actions if action.name == 'start']
        setup_subscriptions_for_action(workflow.id, action_uids)

        result = {'count': 0}

        @WalkoffEvent.ActionExecutionSuccess.connect
        def y(sender, **kwargs):
            result['count'] += 1
            result['data'] = kwargs['data']

        data = {"arguments": [{"name": "call",
                               "value": "CHANGE INPUT"}]}

        self.post_with_status_check('/api/playbooks/1/workflows/{}/execute'.format(workflow.id),
                                    headers=self.headers,
                                    status_code=SUCCESS_ASYNC,
                                    content_type="application/json", data=json.dumps(data))

        flask_server.running_context.controller.wait_and_reset(1)

        self.assertEqual(result['count'], 1)
        self.assertDictEqual(result['data'], {'status': 'Success', 'result': 'REPEATING: CHANGE INPUT'})

    def test_read_results(self):

        workflow = walkoff.coredb.devicedb.device_db.session.query(Workflow).filter_by(id=1).first()
        workflow.execute('a')
        workflow.execute('b')
        workflow.execute('c')

        response = self.get_with_status_check('/api/workflowresults/a', headers=self.headers)
        self.assertSetEqual(set(response.keys()), {'status', 'id', 'results', 'started_at', 'completed_at', 'name'})

    def test_read_all_results(self):
        workflow = walkoff.coredb.devicedb.device_db.session.query(Workflow).filter_by(id=1).first()

        workflow.execute('a')
        workflow.execute('b')
        workflow.execute('c')

        flask_server.running_context.controller.wait_and_reset(3)

        response = self.get_with_status_check('/api/workflowresults', headers=self.headers)
        self.assertEqual(len(response), 3)

        for result in response:
            self.assertSetEqual(set(result.keys()), {'status', 'completed_at', 'started_at', 'name', 'results', 'id'})
            for action_result in result['results']:
                self.assertSetEqual(set(action_result.keys()),
                                    {'input', 'type', 'name', 'timestamp', 'result', 'app_name', 'action_name'})

    def test_execute_workflow_trigger_action(self):
        sync = Event()
        workflow = walkoff.coredb.devicedb.device_db.session.query(Workflow).filter_by(id=1).first()
        action_uids = [action.id for action in workflow.actions if action.name == 'start']
        setup_subscriptions_for_action(workflow.id, action_uids)

        @WalkoffEvent.WorkflowShutdown.connect
        def wait_for_completion(sender, **kwargs):
            sync.set()

        result = {'count': 0}

        @WalkoffEvent.ActionExecutionSuccess.connect
        def y(sender, **kwargs):
            result['count'] += 1
            result['data'] = kwargs['data']

        response = self.post_with_status_check('/api/playbooks/1/workflows/1/execute',
                                               headers=self.headers,
                                               status_code=SUCCESS_ASYNC,
                                               content_type="application/json", data=json.dumps({}))

        flask_server.running_context.controller.wait_and_reset(1)
        self.assertIn('id', response)
        sync.wait(timeout=10)
        self.assertEqual(result['count'], 1)
        self.assertDictEqual(result['data'], {'status': 'Success', 'result': 'REPEATING: Hello World'})
