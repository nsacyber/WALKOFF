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
            {'actions': [],
             'name': self.add_workflow_name,
             'start': 0,
             'branches': []}

        case_database.initialize()

    def tearDown(self):
        if self.update_playbooks:
            playbooks = walkoff.coredb.devicedb.device_db.session.query(Playbook).all()
            for playbook in playbooks:
                if playbook.name == self.change_playbook_name:
                    playbook.name = 'test'
                elif playbook.name in self.playbooks_added:
                    walkoff.coredb.devicedb.device_db.session.delete(playbook)

        if self.update_workflows:
            workflows = walkoff.coredb.devicedb.device_db.session.query(Workflow).all()
            for workflow in workflows:
                if workflow.name == self.change_workflow_name:
                    workflow.name = 'helloWorldWorkflow'
                elif workflow.name in self.workflows_added:
                    walkoff.coredb.devicedb.device_db.session.delete(workflow)

        walkoff.coredb.devicedb.device_db.session.commit()

        case_database.case_db.tear_down()
        walkoff.coredb.devicedb.device_db.tear_down()

    def copy_playbook(self, playbook):
        playbook_json = playbook.read()
        playbook_json.pop('id')

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
        self.playbooks_added.append(self.add_playbook_name)
        self.update_playbooks = True
        response = self.put_with_status_check('/api/playbooks', headers=self.headers,
                                              status_code=OBJECT_CREATED, data=json.dumps(data),
                                              content_type="application/json")

        response.pop('id')

        self.assertDictEqual(response, {'name': self.add_playbook_name, 'workflows': []})
        self.assertEqual(len(list(walkoff.coredb.devicedb.device_db.session.query(Playbook).all())), original_length+1)

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

    def test_add_workflow(self):
        initial_playbooks = walkoff.coredb.devicedb.device_db.session.query(Playbook).all()
        initial_workflows = next(playbook.workflows for playbook in initial_playbooks if playbook.name == 'test')
        initial_workflows_len = len(initial_workflows)

        playbook_id = walkoff.coredb.devicedb.device_db.session.query(Playbook).filter_by(name='test').first().id

        data = {"name": self.add_workflow_name, "start": 0}
        self.workflows_added.append(self.add_workflow_name)
        self.update_workflows = True
        response = self.put_with_status_check('/api/playbooks/{}/workflows'.format(playbook_id),
                                              headers=self.headers, status_code=OBJECT_CREATED, data=json.dumps(data),
                                              content_type="application/json")
        self.empty_workflow_json['id'] = response['id']
        self.assertDictEqual(response, self.empty_workflow_json)

        final_playbooks = walkoff.coredb.devicedb.device_db.session.query(Playbook).all()
        final_workflows = next(playbook.workflows for playbook in final_playbooks if playbook.name == 'test')
        self.assertEqual(len(final_workflows), initial_workflows_len + 1)

        workflow = walkoff.coredb.devicedb.device_db.session.query(Workflow).join(Workflow._playbook).filter(
            Workflow.name == self.add_workflow_name, Playbook.name == 'test').first()
        self.assertIsNotNone(workflow)

    def test_edit_playbook(self):
        playbook = walkoff.coredb.devicedb.device_db.session.query(Playbook).filter_by(name='test').first()
        expected_workflows = [workflow.read() for workflow in playbook.workflows]
        data = {'name': self.change_playbook_name, "id": playbook.id}
        self.update_playbooks = True
        response = self.post_with_status_check('/api/playbooks',
                                               data=json.dumps(data),
                                               headers=self.headers,
                                               content_type='application/json')
        self.assertEqual(response['name'], self.change_playbook_name)
        self.assertEqual(response['id'], playbook.id)
        self.assertEqual(len(response['workflows']), len(expected_workflows))
        self.assertListEqual(response['workflows'], expected_workflows)

    def test_edit_playbook_no_name(self):
        expected = walkoff.coredb.devicedb.device_db.session.query(Playbook).all()
        response = self.app.post('/api/playbooks', headers=self.headers, content_type="application/json",
                                 data=json.dumps({}))
        self.assertEqual(response._status_code, 400)
        self.assertListEqual(walkoff.coredb.devicedb.device_db.session.query(Playbook).all(), expected)

    def test_edit_playbook_invalid_id(self):
        expected = walkoff.coredb.devicedb.device_db.session.query(Playbook).all()
        data = {"id": 0}
        response = self.app.post('/api/playbooks', headers=self.headers, content_type="application/json",
                                 data=json.dumps(data))
        self.assertEqual(response._status_code, 461)
        self.assertListEqual(walkoff.coredb .devicedb.device_db.session.query(Playbook).all(), expected)

    def test_edit_workflow_name_only(self):
        workflow = walkoff.coredb.devicedb.device_db.session.query(Workflow).join(Workflow._playbook).filter(
            Workflow.name == 'helloWorldWorkflow', Playbook.name == 'test').first()
        expected_json = workflow.read()
        workflow_name = self.change_workflow_name
        self.update_workflows = True
        expected_json['name'] = workflow_name
        response = self.post_with_status_check('/api/playbooks/{}/workflows'.format(workflow._playbook_id),
                                               data=json.dumps(expected_json),
                                               headers=self.headers,
                                               content_type='application/json')

        self.assertDictEqual(response, expected_json)

        self.assertIsNotNone(walkoff.coredb.devicedb.device_db.session.query(Workflow).join(Workflow._playbook).filter(
            Workflow.name == self.change_workflow_name, Playbook.name == 'test').first())
        self.assertIsNone(
            walkoff.coredb.devicedb.device_db.session.query(Workflow).join(Workflow._playbook).filter(
                Workflow.name == 'helloWorldWorkflow', Playbook.name == 'test').first())

    def test_edit_workflow_invalid_id(self):
        playbook = walkoff.coredb.devicedb.device_db.session.query(Playbook).filter_by(name='test').first()
        workflow = playbook.workflows[0].read()
        workflow['id'] = 0
        initial_workflows = walkoff.coredb.devicedb.device_db.session.query(Workflow).all()
        self.post_with_status_check('/api/playbooks/{}/workflows'.format(playbook.id),
                                    error='Workflow does not exist',
                                    data=json.dumps(workflow), headers=self.headers, content_type="application/json",
                                    status_code=OBJECT_DNE_ERROR)
        final_workflows = walkoff.coredb.devicedb.device_db.session.query(Workflow).all()
        self.assertSetEqual(set(final_workflows), set(initial_workflows))

    # def test_delete_playbook(self):
    #     self.delete_with_status_check('/api/playbooks/test', headers=self.headers)
    #
    #     self.assertFalse(flask_server.running_context.controller.is_playbook_registered_by_name('test'))
    #
    #     playbooks = [os.path.splitext(playbook)[0]
    #                  for playbook in helpers.locate_playbooks_in_directory(walkoff.config.paths.workflows_path)]
    #     self.assertNotIn('test', playbooks)
    #
    # def test_delete_playbook_no_file(self):
    #     initial_playbook_files = [os.path.splitext(playbook)[0] for playbook in
    #                               helpers.locate_playbooks_in_directory()]
    #     data = {"name": "test_playbook"}
    #     self.app.put('/api/playbooks', headers=self.headers, content_type="application/json", data=json.dumps(data))
    #     self.delete_with_status_check('/api/playbooks/test_playbook', headers=self.headers)
    #
    #     self.assertTrue(flask_server.running_context.controller.is_playbook_registered_by_name('test'))
    #     self.assertFalse(flask_server.running_context.controller.is_playbook_registered_by_name('test_playbook'))
    #
    #     final_playbook_files = [os.path.splitext(playbook)[0] for playbook in
    #                             helpers.locate_playbooks_in_directory()]
    #     orderless_list_compare(self, final_playbook_files, initial_playbook_files)
    #
    # def test_delete_playbook_invalid_name(self):
    #     initial_playbook_files = [os.path.splitext(playbook)[0] for playbook in
    #                               helpers.locate_playbooks_in_directory()]
    #     self.delete_with_status_check('/api/playbooks/junkPlaybookName', error='Playbook does not exist',
    #                                   headers=self.headers,
    #                                   status_code=OBJECT_DNE_ERROR)
    #     self.assertFalse(flask_server.running_context.controller.is_playbook_registered_by_name('junkPlaybookName'))
    #     final_playbook_files = [os.path.splitext(playbook)[0] for playbook in
    #                             helpers.locate_playbooks_in_directory()]
    #     orderless_list_compare(self, final_playbook_files, initial_playbook_files)
    #
    # def test_delete_workflow(self):
    #     workflow_name = 'test_name2'
    #     data = {"name": "test_name2"}
    #     self.app.put('/api/playbooks/test/workflows', headers=self.headers, data=json.dumps(data),
    #                  content_type="application/json")
    #
    #     initial_workflow = flask_server.running_context.controller.get_workflow_by_name('test', workflow_name)
    #     initial_actions = [action.read() for action in initial_workflow.actions.values()]
    #
    #     data = {"actions": initial_actions}
    #     self.app.post('/api/playbooks/test/workflows/{0}/save'.format(workflow_name),
    #                   data=json.dumps(data),
    #                   headers=self.headers,
    #                   content_type='application/json')
    #     self.delete_with_status_check('/api/playbooks/test/workflows/{0}'.format(workflow_name), headers=self.headers)
    #     self.assertFalse(flask_server.running_context.controller.is_workflow_registered_by_name('test', workflow_name))
    #
    # def test_delete_workflow_invalid(self):
    #     workflow_name = 'junkworkflowname'
    #     self.delete_with_status_check('/api/playbooks/test/workflows/{0}'.format(workflow_name),
    #                                   error='Workflow does not exist',
    #                                   headers=self.headers, status_code=OBJECT_DNE_ERROR)
    #     self.assertFalse(flask_server.running_context.controller.is_workflow_registered_by_name('test', workflow_name))
    #
    # def test_invalid_operation_on_playbook_crud(self):
    #     response = self.app.post('/api/playbooks/junkPlaybookName/junkOperation',
    #                              headers=self.headers)
    #     self.assertEqual(404, response.status_code)
    #
    # def test_invalid_operation_on_workflow_crud(self):
    #     response = self.app.post('/api/playbook/junkPlaybookName/workflows/helloWorldWorkflow/junkOperation',
    #                              headers=self.headers)
    #     self.assertEqual(404, response.status_code)
    #
    # @staticmethod
    # def strip_uids(element):
    #     element.pop('uid', None)
    #     for key, value in element.items():
    #         if isinstance(value, list):
    #             for list_element in (list_element_ for list_element_ in value if isinstance(list_element_, dict)):
    #                 TestWorkflowServer.strip_uids(list_element)
    #         elif isinstance(value, dict):
    #             for dict_element in (element for element in value.values() if isinstance(element, dict)):
    #                 TestWorkflowServer.strip_uids(dict_element)
    #
    # def test_copy_workflow(self):
    #     self.post_with_status_check('/api/playbooks/test/workflows/helloWorldWorkflow/copy',
    #                                 headers=self.headers, status_code=OBJECT_CREATED, data=json.dumps({}),
    #                                 content_type="application/json")
    #     self.assertEqual(
    #         len(flask_server.running_context.controller.playbook_store.get_all_workflows_by_playbook('test')), 2)
    #     self.assertTrue(flask_server.running_context.controller.is_workflow_registered_by_name('test', 'helloWorldWorkflow'))
    #     self.assertTrue(
    #         flask_server.running_context.controller.is_workflow_registered_by_name('test', 'helloWorldWorkflow_Copy'))
    #
    #     workflow_original = flask_server.running_context.controller.get_workflow_by_name('test', 'helloWorldWorkflow')
    #     workflow_copy = flask_server.running_context.controller.get_workflow_by_name('test', 'helloWorldWorkflow_Copy')
    #     new_workflow_name = 'helloWorldWorkflow_Copy'
    #     self.assertEqual(workflow_copy.name, new_workflow_name)
    #     copy_workflow_json = workflow_copy.read()
    #     original_workflow_json = workflow_original.read()
    #     copy_workflow_json.pop('name', None)
    #     original_workflow_json.pop('name', None)
    #     self.assertNotEqual(original_workflow_json['start'], copy_workflow_json['start'])
    #     copy_workflow_json.pop('start', None)
    #     original_workflow_json.pop('start', None)
    #     TestWorkflowServer.strip_uids(copy_workflow_json)
    #     TestWorkflowServer.strip_uids(original_workflow_json)
    #     self.assertDictEqual(copy_workflow_json, original_workflow_json)
    #     self.assertEqual(len(workflow_original.actions), len(workflow_copy.actions))
    #
    # def test_copy_workflow_invalid_name(self):
    #     data = {"workflow": "helloWorldWorkflow"}
    #     self.post_with_status_check('/api/playbooks/test/workflows/helloWorldWorkflow/copy',
    #                                 error='Playbook or workflow already exists.', data=json.dumps(data),
    #                                 headers=self.headers, status_code=OBJECT_EXISTS_ERROR,
    #                                 content_type="application/json")
    #
    #     self.assertTrue(flask_server.running_context.controller.is_workflow_registered_by_name('test', 'helloWorldWorkflow'))
    #     self.assertEqual(
    #         flask_server.running_context.controller.get_all_workflows_by_playbook('test').count('helloWorldWorkflow'),
    #         1)
    #     self.assertEqual(len(flask_server.running_context.controller.get_all_workflows_by_playbook('test')), 1)
    #
    # def test_copy_workflow_different_playbook(self):
    #     data = {"name": "new_playbook"}
    #     self.put_with_status_check('/api/playbooks', headers=self.headers,
    #                                status_code=OBJECT_CREATED, content_type="application/json", data=json.dumps(data))
    #     data = {"playbook": "new_playbook"}
    #     self.post_with_status_check('/api/playbooks/test/workflows/helloWorldWorkflow/copy', data=json.dumps(data),
    #                                 headers=self.headers, status_code=OBJECT_CREATED, content_type="application/json")
    #
    #     self.assertEqual(
    #         len(flask_server.running_context.controller.playbook_store.get_all_workflows_by_playbook('test')), 1)
    #     self.assertEqual(
    #         len(flask_server.running_context.controller.playbook_store.get_all_workflows_by_playbook('new_playbook')),
    #         1)
    #     self.assertTrue(flask_server.running_context.controller.is_workflow_registered_by_name('test', 'helloWorldWorkflow'))
    #     self.assertTrue(
    #         flask_server.running_context.controller.is_workflow_registered_by_name('new_playbook', 'helloWorldWorkflow_Copy'))
    #
    #     workflow_original = flask_server.running_context.controller.get_workflow_by_name('test', 'helloWorldWorkflow')
    #     workflow_copy = flask_server.running_context.controller.get_workflow_by_name('new_playbook', 'helloWorldWorkflow_Copy')
    #     new_workflow_name = 'helloWorldWorkflow_Copy'
    #     self.assertEqual(workflow_copy.name, new_workflow_name)
    #     copy_workflow_json = workflow_copy.read()
    #     original_workflow_json = workflow_original.read()
    #     copy_workflow_json.pop('name', None)
    #     original_workflow_json.pop('name', None)
    #     self.assertNotEqual(original_workflow_json['start'], copy_workflow_json['start'])
    #     copy_workflow_json.pop('start', None)
    #     original_workflow_json.pop('start', None)
    #     TestWorkflowServer.strip_uids(copy_workflow_json)
    #     TestWorkflowServer.strip_uids(original_workflow_json)
    #
    #     self.assertDictEqual(copy_workflow_json, original_workflow_json)
    #
    #     self.assertEqual(len(workflow_original.actions), len(workflow_copy.actions))
    #
    # def test_copy_playbook(self):
    #     self.post_with_status_check('/api/playbooks/test/copy',
    #                                 headers=self.headers, status_code=OBJECT_CREATED, data=json.dumps({}),
    #                                 content_type="application/json")
    #
    #     self.assertTrue(flask_server.running_context.controller.is_playbook_registered_by_name('test'))
    #     self.assertTrue(flask_server.running_context.controller.is_playbook_registered_by_name('test_Copy'))
    #
    #     workflows_original = flask_server.running_context.controller.get_all_workflows_by_playbook('test')
    #     workflows_copy = flask_server.running_context.controller.get_all_workflows_by_playbook('test_Copy')
    #
    #     self.assertEqual(len(workflows_original), len(workflows_copy))
    #
    # def test_copy_playbook_invalid_name(self):
    #     data = {"playbook": "test"}
    #     self.post_with_status_check('/api/playbooks/test/copy', error='Playbook already exists.', data=json.dumps(data),
    #                                 headers=self.headers, status_code=OBJECT_EXISTS_ERROR,
    #                                 content_type="application/json")
    #
    #     self.assertTrue(flask_server.running_context.controller.is_playbook_registered_by_name('test'))
    #     self.assertEqual(flask_server.running_context.controller.get_all_playbooks().count('test'), 1)
    #     self.assertFalse(flask_server.running_context.controller.is_playbook_registered_by_name('test_Copy'))
    #
    # def test_execute_workflow_playbook_dne(self):
    #     self.post_with_status_check('/api/playbooks/junkPlay/workflows/helloWorldWorkflow/execute',
    #                                 error='Workflow does not exist',
    #                                 headers=self.headers, status_code=OBJECT_DNE_ERROR,
    #                                 content_type="application/json", data=json.dumps({}))
    #
    # def test_execute_workflow_workflow_dne(self):
    #     self.post_with_status_check('/api/playbooks/test/workflows/junkWorkflow/execute',
    #                                 error='Workflow does not exist',
    #                                 headers=self.headers, status_code=OBJECT_DNE_ERROR,
    #                                 content_type="application/json", data=json.dumps({}))
    #
    # def test_execute_workflow(self):
    #     sync = Event()
    #     workflow = flask_server.running_context.controller.get_workflow_by_name('test', 'helloWorldWorkflow')
    #     action_uids = [action.uid for action in workflow.actions.values() if action.name == 'start']
    #     setup_subscriptions_for_action(workflow.uid, action_uids)
    #
    #     @WalkoffEvent.WorkflowShutdown.connect
    #     def wait_for_completion(sender, **kwargs):
    #         sync.set()
    #
    #     result = {'count': 0}
    #
    #     @WalkoffEvent.ActionExecutionSuccess.connect
    #     def y(sender, **kwargs):
    #         result['count'] += 1
    #         result['data'] = kwargs['data']
    #
    #     response = self.post_with_status_check('/api/playbooks/test/workflows/helloWorldWorkflow/execute',
    #                                            headers=self.headers,
    #                                            status_code=SUCCESS_ASYNC,
    #                                            content_type="application/json", data=json.dumps({}))
    #     flask_server.running_context.controller.wait_and_reset(1)
    #     self.assertIn('id', response)
    #     sync.wait(timeout=10)
    #     self.assertEqual(result['count'], 1)
    #     self.assertDictEqual(result['data'], {'status': 'Success', 'result': 'REPEATING: Hello World'})
    #
    # def test_execute_workflow_pause_resume(self):
    #     sync = Event()
    #
    #     flask_server.running_context.controller.load_playbook(
    #         os.path.join(".", "tests", "testWorkflows", "pauseWorkflowTest.playbook"))
    #
    #     workflow = flask_server.running_context.controller.get_workflow_by_name('pauseWorkflowTest', 'pauseWorkflow')
    #     action_uids = [action.uid for action in workflow.actions.values() if action.name == 'start']
    #     setup_subscriptions_for_action(workflow.uid, action_uids)
    #
    #     result = {'paused': False, 'count': 0, 'data': []}
    #
    #     @WalkoffEvent.ActionExecutionSuccess.connect
    #     def y(sender, **kwargs):
    #         result['count'] += 1
    #         result['data'].append(kwargs['data'])
    #         if not result['paused']:
    #             result['response2'] = self.post_with_status_check(
    #                 '/api/playbooks/pauseWorkflowTest/workflows/pauseWorkflow/pause',
    #                 headers=self.headers,
    #                 status_code=SUCCESS,
    #                 content_type="application/json", data=json.dumps(response))
    #
    #     @WalkoffEvent.WorkflowPaused.connect
    #     def workflow_paused_listener(sender, **kwargs):
    #         result['paused'] = True
    #         result['response3'] = self.post_with_status_check(
    #             '/api/playbooks/pauseWorkflowTest/workflows/pauseWorkflow/resume',
    #             headers=self.headers,
    #             status_code=SUCCESS,
    #             content_type="application/json", data=json.dumps(response))
    #
    #     @WalkoffEvent.WorkflowResumed.connect
    #     def workflow_resumed_listner(sender, **kwargs):
    #         result['resumed'] = True
    #
    #     @WalkoffEvent.WorkflowShutdown.connect
    #     def wait_for_completion(sender, **kwargs):
    #         sync.set()
    #
    #     response = self.post_with_status_check('/api/playbooks/pauseWorkflowTest/workflows/pauseWorkflow/execute',
    #                                            headers=self.headers,
    #                                            status_code=SUCCESS_ASYNC,
    #                                            content_type="application/json", data=json.dumps({}))
    #
    #     flask_server.running_context.controller.wait_and_reset(1)
    #     sync.wait(timeout=10)
    #     self.assertIn('id', response)
    #     self.assertTrue(result['paused'])
    #     self.assertTrue(result['resumed'])
    #     self.assertEqual(result['count'], 3)
    #     self.assertDictEqual(result['response2'], {'info': 'Workflow paused'})
    #     self.assertDictEqual(result['response3'], {'info': 'Workflow resumed'})
    #     expected_data = [{'status': 'Success', 'result': {'message': 'HELLO WORLD'}},
    #                      {'status': 'Success', 'result': None}, {'status': 'Success', 'result': None}]
    #     self.assertEqual(len(result['data']), len(expected_data))
    #     for exp, act in zip(expected_data, result['data']):
    #         self.assertDictEqual(exp, act)
    #
    # def test_execute_workflow_change_arguments(self):
    #
    #     workflow = flask_server.running_context.controller.get_workflow_by_name('test', 'helloWorldWorkflow')
    #     action_uids = [action.uid for action in workflow.actions.values() if action.name == 'start']
    #     setup_subscriptions_for_action(workflow.uid, action_uids)
    #
    #     result = {'count': 0}
    #
    #     @WalkoffEvent.ActionExecutionSuccess.connect
    #     def y(sender, **kwargs):
    #         result['count'] += 1
    #         result['data'] = kwargs['data']
    #
    #     data = {"arguments": [{"name": "call",
    #                            "value": "CHANGE INPUT"}]}
    #
    #     self.post_with_status_check('/api/playbooks/test/workflows/helloWorldWorkflow/execute',
    #                                 headers=self.headers,
    #                                 status_code=SUCCESS_ASYNC,
    #                                 content_type="application/json", data=json.dumps(data))
    #
    #     flask_server.running_context.controller.wait_and_reset(1)
    #
    #     self.assertEqual(result['count'], 1)
    #     self.assertDictEqual(result['data'], {'status': 'Success', 'result': 'REPEATING: CHANGE INPUT'})
    #
    # def test_read_results(self):
    #
    #     workflow = flask_server.running_context.controller.get_workflow_by_name('test', 'helloWorldWorkflow')
    #     workflow.execute('a')
    #     workflow.execute('b')
    #     workflow.execute('c')
    #
    #     response = self.get_with_status_check('/api/workflowresults/a', headers=self.headers)
    #     self.assertSetEqual(set(response.keys()), {'status', 'uid', 'results', 'started_at', 'completed_at', 'name'})
    #
    # def test_read_all_results(self):
    #     workflow = flask_server.running_context.controller.get_workflow_by_name('test', 'helloWorldWorkflow')
    #
    #     workflow.execute('a')
    #     workflow.execute('b')
    #     workflow.execute('c')
    #
    #     flask_server.running_context.controller.wait_and_reset(3)
    #
    #     response = self.get_with_status_check('/api/workflowresults', headers=self.headers)
    #     self.assertEqual(len(response), 3)
    #
    #     for result in response:
    #         self.assertSetEqual(set(result.keys()), {'status', 'completed_at', 'started_at', 'name', 'results', 'uid'})
    #         for action_result in result['results']:
    #             self.assertSetEqual(set(action_result.keys()),
    #                                 {'input', 'type', 'name', 'timestamp', 'result', 'app_name', 'action_name'})
    #
    # def test_execute_workflow_trigger_action(self):
    #     sync = Event()
    #     workflow = flask_server.running_context.controller.get_workflow_by_name('test', 'helloWorldWorkflow')
    #     action_uids = [action.uid for action in workflow.actions.values() if action.name == 'start']
    #     setup_subscriptions_for_action(workflow.uid, action_uids)
    #
    #     @WalkoffEvent.WorkflowShutdown.connect
    #     def wait_for_completion(sender, **kwargs):
    #         sync.set()
    #
    #     result = {'count': 0}
    #
    #     @WalkoffEvent.ActionExecutionSuccess.connect
    #     def y(sender, **kwargs):
    #         result['count'] += 1
    #         result['data'] = kwargs['data']
    #
    #     response = self.post_with_status_check('/api/playbooks/test/workflows/helloWorldWorkflow/execute',
    #                                            headers=self.headers,
    #                                            status_code=SUCCESS_ASYNC,
    #                                            content_type="application/json", data=json.dumps({}))
    #
    #     flask_server.running_context.controller.wait_and_reset(1)
    #     self.assertIn('id', response)
    #     sync.wait(timeout=10)
    #     self.assertEqual(result['count'], 1)
    #     self.assertDictEqual(result['data'], {'status': 'Success', 'result': 'REPEATING: Hello World'})
