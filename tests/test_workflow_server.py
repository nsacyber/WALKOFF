import json
import os
from datetime import datetime
from os import path
from threading import Event
from copy import deepcopy

from core.argument import Argument
import core.case.database as case_database
import core.case.subscription
import core.config.paths
from core import helpers
from core.events import WalkoffEvent
from core.executionelements.branch import Branch
from core.executionelements.action import Action
from server import flaskserver as flask_server
from server.returncodes import *
from tests.util.assertwrappers import orderless_list_compare
from tests.util.case_db_help import executed_actions, setup_subscriptions_for_action
from tests.util.servertestcase import ServerTestCase


class TestWorkflowServer(ServerTestCase):
    def setUp(self):
        # This looks awful, I know
        self.empty_workflow_json = \
            {'actions': [],
             'name': 'test_name',
             'start': 'start',
             'accumulated_risk': 0.0,
             'branches': []}

        case_database.initialize()

    def tearDown(self):
        flask_server.running_context.controller.playbook_store.playbooks = {}
        case_database.case_db.tear_down()

    def test_display_all_playbooks(self):
        response = self.get_with_status_check('/api/playbooks', headers=self.headers)
        for playbook in response:
            for workflow in playbook['workflows']:
                workflow.pop('uid')

        for playbook in response:
            self.assertIn(playbook['name'], ['test', 'triggerActionWorkflow'])
            if playbook['name'] == 'test':
                self.assertEqual(playbook['workflows'], [{'name': 'helloWorldWorkflow'}])
            elif playbook['name'] == 'triggerActionWorkflow':
                self.assertEqual(playbook['workflows'], [{"name": "triggerActionWorkflow"}])

        self.assertEqual(len(response), 2)

    def test_display_playbook_workflows(self):
        response = self.get_with_status_check('/api/playbooks/test', headers=self.headers)
        for workflow in response:
            workflow.pop('uid')
        self.assertListEqual(response, [{'name': 'helloWorldWorkflow'}])

    def test_display_playbook_workflows_invalid_name(self):
        self.get_with_status_check('/api/playbooks/junkName', error='Playbook does not exist.', headers=self.headers,
                                   status_code=OBJECT_DNE_ERROR)

    def test_display_workflow_invalid_name(self):
        self.get_with_status_check('/api/playbooks/multiactionWorkflowTest/workflows/multiactionWorkflow',
                                   error='Playbook or workflow does not exist.',
                                   headers=self.headers, status_code=OBJECT_DNE_ERROR)

    def test_add_playbook_default(self):
        expected_playbooks = flask_server.running_context.controller.get_all_playbooks()
        original_length = len(list(expected_playbooks))
        data = {"name": "test_playbook"}
        response = self.put_with_status_check('/api/playbooks', headers=self.headers,
                                              status_code=OBJECT_CREATED, data=json.dumps(data),
                                              content_type="application/json")

        response = next(playbook for playbook in response if playbook['name'] == 'test_playbook')
        for workflow in response['workflows']:
            workflow.pop('uid')

        self.assertDictEqual(response, {'name': 'test_playbook', 'workflows': []})
        self.assertEqual(len(list(flask_server.running_context.controller.get_all_playbooks())), original_length + 1)

    def test_add_playbook_already_exists(self):
        data = {"name": "test_playbook__"}
        self.put_with_status_check('/api/playbooks',
                                   data=json.dumps(data), headers=self.headers, status_code=OBJECT_CREATED,
                                   content_type="application/json")
        self.put_with_status_check('/api/playbooks',
                                   error='Playbook already exists.',
                                   data=json.dumps(data), headers=self.headers, status_code=OBJECT_EXISTS_ERROR,
                                   content_type="application/json")

    def test_add_workflow(self):
        initial_playbooks = flask_server.running_context.controller.get_all_workflows()
        initial_workflows = next(playbook['workflows'] for playbook in initial_playbooks if playbook['name'] == 'test')

        data = {"name": "test_name"}
        response = self.put_with_status_check('/api/playbooks/test/workflows',
                                              headers=self.headers, status_code=OBJECT_CREATED, data=json.dumps(data),
                                              content_type="application/json")
        self.empty_workflow_json['uid'] = response['uid']
        self.assertDictEqual(response, self.empty_workflow_json)

        final_playbooks = flask_server.running_context.controller.get_all_workflows()
        final_workflows = next(playbook['workflows'] for playbook in final_playbooks if playbook['name'] == 'test')
        self.assertEqual(len(final_workflows), len(initial_workflows) + 1)
        self.assertTrue(flask_server.running_context.controller.is_workflow_registered('test', 'test_name'))

    def test_edit_playbook(self):
        expected_keys = next(x for x in flask_server.running_context.controller.get_all_workflows()
                             if x['name'] == 'test')['workflows']
        # expected_keys = flask_server.running_context.controller.get_all_workflows()['test']
        new_playbook_name = 'editedPlaybookName'
        data = {'new_name': new_playbook_name, "name": "test"}
        response = self.post_with_status_check('/api/playbooks',
                                               data=json.dumps(data),
                                               headers=self.headers,
                                               content_type='application/json')
        self.assertListEqual(response, expected_keys)
        self.assertTrue(
            os.path.isfile(os.path.join(core.config.paths.workflows_path, 'editedPlaybookName.playbook')))
        self.assertFalse(os.path.isfile(os.path.join(core.config.paths.workflows_path, 'test.playbook')))

    def test_edit_playbook_no_name(self):
        expected = flask_server.running_context.controller.get_all_workflows()
        response = self.app.post('/api/playbooks', headers=self.headers, content_type="application/json",
                                 data=json.dumps({}))
        self.assertEqual(response._status_code, 400)
        self.assertListEqual(flask_server.running_context.controller.get_all_workflows(), expected)
        self.assertTrue(os.path.isfile(os.path.join(core.config.paths.workflows_path, 'test.playbook')))

    def test_edit_playbook_invalid_name(self):
        expected = flask_server.running_context.controller.get_all_workflows()
        data = {"name": "junkPlaybookName"}
        response = self.app.post('/api/playbooks', headers=self.headers, content_type="application/json",
                                 data=json.dumps(data))
        self.assertEqual(response._status_code, 461)
        self.assertListEqual(flask_server.running_context.controller.get_all_workflows(), expected)

        self.assertFalse(
            os.path.isfile(os.path.join(core.config.paths.workflows_path, 'junkPlaybookName.playbook')))
        self.assertTrue(os.path.isfile(os.path.join(core.config.paths.workflows_path, 'test.playbook')))

    def test_edit_playbook_no_file(self):
        data = {"name": "test2"}
        self.app.put('/api/playbooks', headers=self.headers, data=json.dumps(data), content_type="application/json")
        expected_keys = next(x for x in flask_server.running_context.controller.get_all_workflows()
                             if x['name'] == 'test2')['workflows']
        new_playbook_name = 'editedPlaybookName'
        data = {'new_name': new_playbook_name, "name": "test2"}
        response = self.post_with_status_check('/api/playbooks',
                                               data=json.dumps(data),
                                               headers=self.headers,
                                               content_type='application/json')
        self.assertListEqual(response, expected_keys)

        self.assertFalse(os.path.isfile(os.path.join(core.config.paths.workflows_path, 'test2.playbook')))
        self.assertFalse(
            os.path.isfile(os.path.join(core.config.paths.workflows_path, 'editedPlaybookName.playbook')))
        self.assertTrue(os.path.isfile(os.path.join(core.config.paths.workflows_path, 'test.playbook')))

    def test_edit_workflow_name_only(self):
        expected_json = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow').read()
        workflow_name = "test_name"
        data = {"new_name": workflow_name, "name": "helloWorldWorkflow"}
        response = self.post_with_status_check('/api/playbooks/test/workflows',
                                               data=json.dumps(data),
                                               headers=self.headers,
                                               content_type='application/json')

        expected_json['name'] = workflow_name

        self.assertDictEqual(response, expected_json)

        self.assertTrue(flask_server.running_context.controller.is_workflow_registered('test', 'test_name'))
        self.assertFalse(
            flask_server.running_context.controller.is_workflow_registered('test', 'helloWorldWorkflow'))

    def test_edit_workflow_empty_name(self):
        expected_json = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow').read()
        data = {"new_name": "", "name": "helloWorldWorkflow"}
        response = self.post_with_status_check('/api/playbooks/test/workflows',
                                               data=json.dumps(data),
                                               headers=self.headers,
                                               content_type='application/json')

        self.assertDictEqual(response, expected_json)

        self.assertFalse(flask_server.running_context.controller.is_workflow_registered('test', 'test_name'))
        self.assertTrue(
            flask_server.running_context.controller.is_workflow_registered('test', 'helloWorldWorkflow'))
        self.assertFalse(
            flask_server.running_context.controller.is_workflow_registered('test', ''))

    def test_edit_workflow_(self):
        expected_json = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow').read()
        workflow_name = "test_name"
        data = {"new_name": workflow_name, "name": "helloWorldWorkflow"}
        response = self.post_with_status_check('/api/playbooks/test/workflows',
                                               data=json.dumps(data),
                                               headers=self.headers,
                                               content_type='application/json')

        expected_json['name'] = workflow_name
        self.assertDictEqual(response, expected_json)

        self.assertFalse(
            flask_server.running_context.controller.is_workflow_registered('test', 'helloWorldWorkflow'))

    def test_edit_workflow_invalid_workflow(self):
        workflow_name = 'test_name'
        data = {"new_name": workflow_name, "name": "junkworkflow"}
        initial_workflows = flask_server.running_context.controller.workflows.keys()
        self.post_with_status_check('/api/playbooks/test/workflows',
                                    error='Playbook or workflow does not exist.',
                                    data=json.dumps(data), headers=self.headers, content_type="application/json",
                                    status_code=OBJECT_DNE_ERROR)
        final_workflows = flask_server.running_context.controller.workflows.keys()
        self.assertSetEqual(set(final_workflows), set(initial_workflows))

    def test_save_workflow(self):
        initial_workflow = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow')
        workflow_name = initial_workflow.name
        initial_actions = [action.read() for action in initial_workflow.actions.values()]
        initial_actions[0]['position']['x'] = 0.0
        initial_actions[0]['position']['y'] = 0.0
        added_action = Action('HelloWorld', 'pause', name='new_id', arguments=[Argument("seconds", value=5)],
                              position={'x': 0, 'y': 0}, uid="2").read()

        initial_actions.append(added_action)

        action_uid = "e1db14e0cc8d4179aff5f1080a2b7e91"
        added_branch = Branch(source_uid=action_uid, destination_uid="2").read()

        data = {"actions": initial_actions, "branches": [added_branch]}
        self.post_with_status_check('/api/playbooks/test/workflows/{0}/save'.format(workflow_name),
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type='application/json')

        resulting_workflow = flask_server.running_context.controller.get_workflow('test', workflow_name)
        # compare the actions in initial and final workflow
        self.assertEqual(len(resulting_workflow.actions.keys()), len(list(initial_actions)))
        for initial_action in initial_actions:
            self.assertIn(initial_action['uid'], resulting_workflow.actions.keys())
            self.assertDictEqual(initial_action, resulting_workflow.actions[initial_action['uid']].read())

        self.assertEqual(added_branch["source_uid"], resulting_workflow.branches[action_uid][0].source_uid)
        self.assertEqual(added_branch["destination_uid"], resulting_workflow.branches[action_uid][0].destination_uid)

        # assert that the file has been saved to a file
        workflows = [path.splitext(workflow)[0]
                     for workflow in os.listdir(core.config.paths.workflows_path) if workflow.endswith('.playbook')]
        matching_workflows = [workflow for workflow in workflows if workflow == 'test']
        self.assertEqual(len(matching_workflows), 1)

        # assert that the file loads properly after being saved
        flask_server.running_context.controller.workflows = {}
        flask_server.running_context.controller.load_playbook(os.path.join(core.config.paths.workflows_path,
                                                                           'test.playbook'))
        loaded_workflow = flask_server.running_context.controller.get_workflow('test', workflow_name)
        # compare the actions in loaded and expected workflow
        self.assertEqual(len(loaded_workflow.actions.keys()), len(list(resulting_workflow.actions.keys())))

        def remove_uids(action):
            action.uid = ''

        for action_name, loaded_action in loaded_workflow.actions.items():
            self.assertIn(action_name, resulting_workflow.actions.keys())
            remove_uids(loaded_action)
            remove_uids(resulting_workflow.actions[action_name])
            self.assertDictEqual(loaded_action.read(), resulting_workflow.actions[action_name].read())

    def test_save_workflow_invalid_app_reload_actions(self):
        initial_workflow = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow')
        workflow_name = initial_workflow.name
        initial_actions = [action.read() for action in initial_workflow.actions.values()]
        actions_unmod = deepcopy(initial_actions)
        initial_actions[0]['position']['x'] = 0.0
        initial_actions[0]['position']['y'] = 0.0
        added_action = Action(name='new_id', app_name='HelloWorld', action_name='pause',
                              arguments=[Argument("seconds", value=5)],
                              position={'x': 0, 'y': 0}).read()
        added_action['app_name'] = 'Invalid'

        initial_actions.append(added_action)
        data = {"actions": initial_actions}
        self.post_with_status_check('/api/playbooks/test/workflows/{0}/save'.format(workflow_name),
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type='application/json',
                                    status_code=INVALID_INPUT_ERROR)

        workflow = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow')
        new_actions = [action.read() for action in workflow.actions.values()]
        for action in actions_unmod:
            action.pop('position')
        for action in new_actions:
            action.pop('position')
            action.pop('event')
        self.assertListEqual(actions_unmod, new_actions)

    def test_save_workflow_invalid_action(self):
        initial_workflow = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow')
        workflow_name = initial_workflow.name
        initial_actions = [action.read() for action in initial_workflow.actions.values()]
        initial_actions[0]['position']['x'] = 0.0
        initial_actions[0]['position']['y'] = 0.0
        added_action = Action(name='new_id', app_name='HelloWorld', action_name='pause',
                              arguments=[Argument("seconds", value=5)],
                              position={'x': 0, 'y': 0}).read()
        added_action['action_name'] = 'Invalid'

        initial_actions.append(added_action)
        data = {"actions": initial_actions}
        self.post_with_status_check('/api/playbooks/test/workflows/{0}/save'.format(workflow_name),
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type='application/json',
                                    status_code=INVALID_INPUT_ERROR)

    def test_save_workflow_invalid_input_name(self):
        initial_workflow = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow')
        workflow_name = initial_workflow.name
        initial_actions = [action.read() for action in initial_workflow.actions.values()]
        initial_actions[0]['position']['x'] = 0.0
        initial_actions[0]['position']['y'] = 0.0
        added_action = Action(name='new_id', app_name='HelloWorld', action_name='pause',
                              arguments=[Argument("seconds", value=5)],
                              position={'x': 0, 'y': 0}).read()
        added_action['arguments'] = [{'name': 'Invalid', 'value': 5}]

        initial_actions.append(added_action)
        data = {"actions": initial_actions}
        self.post_with_status_check('/api/playbooks/test/workflows/{0}/save'.format(workflow_name),
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type='application/json',
                                    status_code=INVALID_INPUT_ERROR)

    def test_save_workflow_invalid_input_format(self):
        initial_workflow = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow')
        workflow_name = initial_workflow.name
        initial_actions = [action.read() for action in initial_workflow.actions.values()]
        initial_actions[0]['position']['x'] = 0.0
        initial_actions[0]['position']['y'] = 0.0
        added_action = Action(name='new_id', app_name='HelloWorld', action_name='pause',
                              arguments=[Argument("seconds", value=5)],
                              position={'x': 0, 'y': 0}).read()
        added_action['arguments'][0]['value'] = 'aaaa'

        initial_actions.append(added_action)
        data = {"actions": initial_actions}
        self.post_with_status_check('/api/playbooks/test/workflows/{0}/save'.format(workflow_name),
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type='application/json',
                                    status_code=INVALID_INPUT_ERROR)

    def test_save_workflow_new_start_action(self):
        initial_workflow = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow')
        workflow_name = initial_workflow.name
        initial_actions = [action.read() for action in initial_workflow.actions.values()]
        initial_actions[0]['position']['x'] = 0.0
        initial_actions[0]['position']['y'] = 0.0
        added_action = Action(name='new_id', app_name='HelloWorld', action_name='pause',
                              arguments=[Argument('seconds', value=5)],
                              position={'x': 0, 'y': 0}).read()

        initial_actions.append(added_action)
        data = {"actions": initial_actions, "start": "new_start"}
        self.post_with_status_check('/api/playbooks/test/workflows/{0}/save'.format(workflow_name),
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type='application/json')

        resulting_workflow = flask_server.running_context.controller.get_workflow('test', workflow_name)
        self.assertEqual(resulting_workflow.start, "new_start")

    def test_save_workflow_invalid_name(self):
        data = {"actions": []}
        self.post_with_status_check('/api/playbooks/test/workflows/junkworkflowname/save',
                                    error='Playbook or workflow does not exist.',
                                    headers=self.headers, status_code=OBJECT_DNE_ERROR, data=json.dumps(data),
                                    content_type="application/json")

    def test_delete_playbook(self):
        self.delete_with_status_check('/api/playbooks/test', headers=self.headers)

        self.assertFalse(flask_server.running_context.controller.is_playbook_registered('test'))

        playbooks = [os.path.splitext(playbook)[0]
                     for playbook in helpers.locate_playbooks_in_directory(core.config.paths.workflows_path)]
        self.assertNotIn('test', playbooks)

    def test_delete_playbook_no_file(self):
        initial_playbook_files = [os.path.splitext(playbook)[0] for playbook in
                                  helpers.locate_playbooks_in_directory()]
        data = {"name": "test_playbook"}
        self.app.put('/api/playbooks', headers=self.headers, content_type="application/json", data=json.dumps(data))
        self.delete_with_status_check('/api/playbooks/test_playbook', headers=self.headers)

        self.assertTrue(flask_server.running_context.controller.is_playbook_registered('test'))
        self.assertFalse(flask_server.running_context.controller.is_playbook_registered('test_playbook'))

        final_playbook_files = [os.path.splitext(playbook)[0] for playbook in
                                helpers.locate_playbooks_in_directory()]
        orderless_list_compare(self, final_playbook_files, initial_playbook_files)

    def test_delete_playbook_invalid_name(self):
        initial_playbook_files = [os.path.splitext(playbook)[0] for playbook in
                                  helpers.locate_playbooks_in_directory()]
        self.delete_with_status_check('/api/playbooks/junkPlaybookName', error='Playbook does not exist.',
                                      headers=self.headers,
                                      status_code=OBJECT_DNE_ERROR)
        self.assertFalse(flask_server.running_context.controller.is_playbook_registered('junkPlaybookName'))
        final_playbook_files = [os.path.splitext(playbook)[0] for playbook in
                                helpers.locate_playbooks_in_directory()]
        orderless_list_compare(self, final_playbook_files, initial_playbook_files)

    def test_delete_workflow(self):
        workflow_name = 'test_name2'
        data = {"name": "test_name2"}
        self.app.put('/api/playbooks/test/workflows', headers=self.headers, data=json.dumps(data),
                     content_type="application/json")

        initial_workflow = flask_server.running_context.controller.get_workflow('test', workflow_name)
        initial_actions = [action.read() for action in initial_workflow.actions.values()]

        data = {"actions": initial_actions}
        self.app.post('/api/playbooks/test/workflows/{0}/save'.format(workflow_name),
                      data=json.dumps(data),
                      headers=self.headers,
                      content_type='application/json')
        self.delete_with_status_check('/api/playbooks/test/workflows/{0}'.format(workflow_name), headers=self.headers)
        self.assertFalse(flask_server.running_context.controller.is_workflow_registered('test', workflow_name))

    def test_delete_workflow_invalid(self):
        workflow_name = 'junkworkflowname'
        self.delete_with_status_check('/api/playbooks/test/workflows/{0}'.format(workflow_name),
                                      error='Playbook or workflow does not exist.',
                                      headers=self.headers, status_code=OBJECT_DNE_ERROR)
        self.assertFalse(flask_server.running_context.controller.is_workflow_registered('test', workflow_name))

    def test_invalid_operation_on_playbook_crud(self):
        response = self.app.post('/api/playbooks/junkPlaybookName/junkOperation',
                                 headers=self.headers)
        self.assertEqual(404, response.status_code)

    def test_invalid_operation_on_workflow_crud(self):
        response = self.app.post('/api/playbook/junkPlaybookName/workflows/helloWorldWorkflow/junkOperation',
                                 headers=self.headers)
        self.assertEqual(404, response.status_code)

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

    def test_copy_workflow(self):
        self.post_with_status_check('/api/playbooks/test/workflows/helloWorldWorkflow/copy',
                                    headers=self.headers, status_code=OBJECT_CREATED, data=json.dumps({}),
                                    content_type="application/json")
        self.assertEqual(
            len(flask_server.running_context.controller.playbook_store.get_all_workflows_by_playbook('test')), 2)
        self.assertTrue(flask_server.running_context.controller.is_workflow_registered('test', 'helloWorldWorkflow'))
        self.assertTrue(
            flask_server.running_context.controller.is_workflow_registered('test', 'helloWorldWorkflow_Copy'))

        workflow_original = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow')
        workflow_copy = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow_Copy')
        new_workflow_name = 'helloWorldWorkflow_Copy'
        self.assertEqual(workflow_copy.name, new_workflow_name)
        copy_workflow_json = workflow_copy.read()
        original_workflow_json = workflow_original.read()
        copy_workflow_json.pop('name', None)
        original_workflow_json.pop('name', None)
        self.assertNotEqual(original_workflow_json['start'], copy_workflow_json['start'])
        copy_workflow_json.pop('start', None)
        original_workflow_json.pop('start', None)
        TestWorkflowServer.strip_uids(copy_workflow_json)
        TestWorkflowServer.strip_uids(original_workflow_json)
        self.assertDictEqual(copy_workflow_json, original_workflow_json)
        self.assertEqual(len(workflow_original.actions), len(workflow_copy.actions))

    def test_copy_workflow_invalid_name(self):
        data = {"workflow": "helloWorldWorkflow"}
        self.post_with_status_check('/api/playbooks/test/workflows/helloWorldWorkflow/copy',
                                    error='Playbook or workflow already exists.', data=json.dumps(data),
                                    headers=self.headers, status_code=OBJECT_EXISTS_ERROR,
                                    content_type="application/json")

        self.assertTrue(flask_server.running_context.controller.is_workflow_registered('test', 'helloWorldWorkflow'))
        self.assertEqual(
            flask_server.running_context.controller.get_all_workflows_by_playbook('test').count('helloWorldWorkflow'),
            1)
        self.assertEqual(len(flask_server.running_context.controller.get_all_workflows_by_playbook('test')), 1)

    def test_copy_workflow_different_playbook(self):
        data = {"name": "new_playbook"}
        self.put_with_status_check('/api/playbooks', headers=self.headers,
                                   status_code=OBJECT_CREATED, content_type="application/json", data=json.dumps(data))
        data = {"playbook": "new_playbook"}
        self.post_with_status_check('/api/playbooks/test/workflows/helloWorldWorkflow/copy', data=json.dumps(data),
                                    headers=self.headers, status_code=OBJECT_CREATED, content_type="application/json")

        self.assertEqual(
            len(flask_server.running_context.controller.playbook_store.get_all_workflows_by_playbook('test')), 1)
        self.assertEqual(
            len(flask_server.running_context.controller.playbook_store.get_all_workflows_by_playbook('new_playbook')),
            1)
        self.assertTrue(flask_server.running_context.controller.is_workflow_registered('test', 'helloWorldWorkflow'))
        self.assertTrue(
            flask_server.running_context.controller.is_workflow_registered('new_playbook', 'helloWorldWorkflow_Copy'))

        workflow_original = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow')
        workflow_copy = flask_server.running_context.controller.get_workflow('new_playbook', 'helloWorldWorkflow_Copy')
        new_workflow_name = 'helloWorldWorkflow_Copy'
        self.assertEqual(workflow_copy.name, new_workflow_name)
        copy_workflow_json = workflow_copy.read()
        original_workflow_json = workflow_original.read()
        copy_workflow_json.pop('name', None)
        original_workflow_json.pop('name', None)
        self.assertNotEqual(original_workflow_json['start'], copy_workflow_json['start'])
        copy_workflow_json.pop('start', None)
        original_workflow_json.pop('start', None)
        TestWorkflowServer.strip_uids(copy_workflow_json)
        TestWorkflowServer.strip_uids(original_workflow_json)

        self.assertDictEqual(copy_workflow_json, original_workflow_json)

        self.assertEqual(len(workflow_original.actions), len(workflow_copy.actions))

    def test_copy_playbook(self):
        self.post_with_status_check('/api/playbooks/test/copy',
                                    headers=self.headers, status_code=OBJECT_CREATED, data=json.dumps({}),
                                    content_type="application/json")

        self.assertTrue(flask_server.running_context.controller.is_playbook_registered('test'))
        self.assertTrue(flask_server.running_context.controller.is_playbook_registered('test_Copy'))

        workflows_original = flask_server.running_context.controller.get_all_workflows_by_playbook('test')
        workflows_copy = flask_server.running_context.controller.get_all_workflows_by_playbook('test_Copy')

        self.assertEqual(len(workflows_original), len(workflows_copy))

    def test_copy_playbook_invalid_name(self):
        data = {"playbook": "test"}
        self.post_with_status_check('/api/playbooks/test/copy', error='Playbook already exists.', data=json.dumps(data),
                                    headers=self.headers, status_code=OBJECT_EXISTS_ERROR,
                                    content_type="application/json")

        self.assertTrue(flask_server.running_context.controller.is_playbook_registered('test'))
        self.assertEqual(flask_server.running_context.controller.get_all_playbooks().count('test'), 1)
        self.assertFalse(flask_server.running_context.controller.is_playbook_registered('test_Copy'))

    def test_execute_workflow_playbook_dne(self):
        self.post_with_status_check('/api/playbooks/junkPlay/workflows/helloWorldWorkflow/execute',
                                    error='Playbook or workflow does not exist.',
                                    headers=self.headers, status_code=OBJECT_DNE_ERROR,
                                    content_type="application/json", data=json.dumps({}))

    def test_execute_workflow_workflow_dne(self):
        self.post_with_status_check('/api/playbooks/test/workflows/junkWorkflow/execute',
                                    error='Playbook or workflow does not exist.',
                                    headers=self.headers, status_code=OBJECT_DNE_ERROR,
                                    content_type="application/json", data=json.dumps({}))

    def test_execute_workflow(self):
        sync = Event()
        workflow = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow')
        action_uids = [action.uid for action in workflow.actions.values() if action.name == 'start']
        setup_subscriptions_for_action(workflow.uid, action_uids)

        @WalkoffEvent.WorkflowShutdown.connect
        def wait_for_completion(sender, **kwargs):
            sync.set()

        result = {'count': 0}
        @WalkoffEvent.ActionExecutionSuccess.connect
        def y(sender, **kwargs):
            result['count'] += 1
            result['data'] = kwargs['data']


        response = self.post_with_status_check('/api/playbooks/test/workflows/helloWorldWorkflow/execute',
                                               headers=self.headers,
                                               status_code=SUCCESS_ASYNC,
                                               content_type="application/json", data=json.dumps({}))
        flask_server.running_context.controller.wait_and_reset(1)
        self.assertIn('id', response)
        sync.wait(timeout=10)
        self.assertEqual(result['count'], 1)
        self.assertDictEqual(result['data'], {'status': 'Success', 'result': 'REPEATING: Hello World'})

    def test_execute_workflow_change_arguments(self):

        workflow = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow')
        action_uids = [action.uid for action in workflow.actions.values() if action.name == 'start']
        setup_subscriptions_for_action(workflow.uid, action_uids)

        result = {'count': 0}

        @WalkoffEvent.ActionExecutionSuccess.connect
        def y(sender, **kwargs):
            result['count'] += 1
            result['data'] = kwargs['data']

        data = {"arguments": [{"name": "call",
                               "value": "CHANGE INPUT"}]}

        self.post_with_status_check('/api/playbooks/test/workflows/helloWorldWorkflow/execute',
                                    headers=self.headers,
                                    status_code=SUCCESS_ASYNC,
                                    content_type="application/json", data=json.dumps(data))

        flask_server.running_context.controller.wait_and_reset(1)

        self.assertEqual(result['count'], 1)
        self.assertDictEqual(result['data'], {'status': 'Success', 'result': 'REPEATING: CHANGE INPUT'})

    def test_read_results(self):

        workflow = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow')
        workflow.execute('a')
        workflow.execute('b')
        workflow.execute('c')

        response = self.get_with_status_check('/api/workflowresults/a', headers=self.headers)
        self.assertSetEqual(set(response.keys()), {'status', 'uid', 'results', 'started_at', 'completed_at', 'name'})

    def test_read_all_results(self):
        workflow = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow')

        workflow.execute('a')
        workflow.execute('b')
        workflow.execute('c')

        flask_server.running_context.controller.wait_and_reset(3)

        response = self.get_with_status_check('/api/workflowresults', headers=self.headers)
        self.assertEqual(len(response), 3)

        for result in response:
            self.assertSetEqual(set(result.keys()), {'status', 'completed_at', 'started_at', 'name', 'results', 'uid'})
            for action_result in result['results']:
                self.assertSetEqual(set(action_result.keys()),
                                    {'input', 'type', 'name', 'timestamp', 'result', 'app_name', 'action_name'})

    def test_execute_workflow_trigger_action(self):
        sync = Event()
        workflow = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow')
        action_uids = [action.uid for action in workflow.actions.values() if action.name == 'start']
        setup_subscriptions_for_action(workflow.uid, action_uids)

        @WalkoffEvent.WorkflowShutdown.connect
        def wait_for_completion(sender, **kwargs):
            sync.set()

        result = {'count': 0}

        @WalkoffEvent.ActionExecutionSuccess.connect
        def y(sender, **kwargs):
            result['count'] += 1
            result['data'] = kwargs['data']

        response = self.post_with_status_check('/api/playbooks/test/workflows/helloWorldWorkflow/execute',
                                               headers=self.headers,
                                               status_code=SUCCESS_ASYNC,
                                               content_type="application/json", data=json.dumps({}))

        flask_server.running_context.controller.wait_and_reset(1)
        self.assertIn('id', response)
        sync.wait(timeout=10)
        self.assertEqual(result['count'], 1)
        self.assertDictEqual(result['data'], {'status': 'Success', 'result': 'REPEATING: Hello World'})
