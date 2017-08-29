import json
from os import path
from tests.util.servertestcase import ServerTestCase
from tests.util.assertwrappers import orderless_list_compare
from tests.util.case_db_help import executed_steps, setup_subscriptions_for_step
from datetime import datetime
from server import flaskserver as flask_server
from core import helpers
import core.case.subscription
import core.case.database as case_database
import os
import core.config.paths
from threading import Event
from core.case.callbacks import WorkflowShutdown
from server.returncodes import *
from core.step import Step


class TestWorkflowServer(ServerTestCase):
    def setUp(self):
        # This looks awful, I know
        self.empty_workflow_json = \
            {'steps': [],
             'name': 'emptyWorkflow',
             'start': 'start',
             'accumulated_risk': 0.0}

        case_database.initialize()

    def tearDown(self):
        flask_server.running_context.controller.shutdown_pool(0)
        core.controller.workflows = {}
        case_database.case_db.tear_down()

    def test_display_all_playbooks(self):
        response = self.get_with_status_check('/api/playbooks', headers=self.headers)
        for playbook in response:
            for workflow in playbook['workflows']:
                workflow.pop('uid')
        self.assertListEqual(response, [{'name': 'test',
                                         'workflows': [{'name': 'helloWorldWorkflow'}]}])

    def test_display_playbook_workflows(self):
        response = self.get_with_status_check('/api/playbooks/test', headers=self.headers)
        for workflow in response:
            workflow.pop('uid')
        self.assertListEqual(response, [{'name': 'helloWorldWorkflow'}])

    def test_display_playbook_workflows_invalid_name(self):
        self.get_with_status_check('/api/playbooks/junkName', error='Playbook does not exist.', headers=self.headers,
                                   status_code=OBJECT_DNE_ERROR)

    def test_display_available_workflow_templates(self):
        response = self.get_with_status_check('/api/playbooks/templates', headers=self.headers)
        self.assertDictEqual(response, {'basicWorkflow': ['helloWorldWorkflow'],
                                        'emptyWorkflow': ['emptyWorkflow']})

    def test_display_workflow_invalid_name(self):
        self.get_with_status_check('/api/playbooks/multiactionWorkflowTest/workflows/multiactionWorkflow',
                                   error='Playbook or workflow does not exist.',
                                   headers=self.headers, status_code=OBJECT_DNE_ERROR)

    def test_add_playbook_default(self):
        expected_playbooks = flask_server.running_context.controller.get_all_workflows()
        original_length = len(list(expected_playbooks))
        data = {"name": "test_playbook"}
        response = self.put_with_status_check('/api/playbooks', headers=self.headers,
                                              status_code=OBJECT_CREATED, data=json.dumps(data),
                                              content_type="application/json")
        for playbook in expected_playbooks:
            if playbook['name'] == 'test_playbook':
                playbook['name'] = 'emptyWorkflow'
            for workflow in playbook['workflows']:
                workflow.pop('uid')
        response = next(playbook for playbook in response if playbook['name'] == 'test_playbook')['workflows']
        for workflow in response:
            workflow.pop('uid')
        self.assertListEqual(response, [{u'name': u'emptyWorkflow'}])
        self.assertEqual(len(list(flask_server.running_context.controller.workflows)), original_length + 1)

    def test_add_playbook_template(self):
        data = {'playbook_template': 'basicWorkflow', "name": "test_playbook"}
        response = self.put_with_status_check('/api/playbooks',
                                              data=json.dumps(data), headers=self.headers, status_code=OBJECT_CREATED,
                                              content_type="application/json")
        for playbook in response:
            for workflow in playbook['workflows']:
                workflow.pop('uid')
        expected = [{u'name': u'test', u'workflows': [{u'name': u'helloWorldWorkflow'}]},
                             {u'name': u'test_playbook', u'workflows': [{u'name': u'helloWorldWorkflow'}]}]
        for workflow in response:
            self.assertIn(workflow, expected)
        self.assertEqual(len(list(flask_server.running_context.controller.workflows)), 2)

    def test_add_playbook_template_invalid_name(self):
        data = {'playbook_template': 'junkPlaybookTemplate', "name": "test_playbook"}
        response = self.put_with_status_check('/api/playbooks',
                                              data=json.dumps(data), headers=self.headers,
                                              status_code=SUCCESS_WITH_WARNING,
                                              content_type="application/json")
        for playbook in response:
            for workflow in playbook['workflows']:
                workflow.pop('uid')
        expected = [{u'name': u'test', u'workflows': [{u'name': u'helloWorldWorkflow'}]},
                                        {u'name': u'test_playbook', u'workflows': [{u'name': u'emptyWorkflow'}]}]
        for workflow in response:
            self.assertIn(workflow, expected)
        self.assertEqual(len(list(flask_server.running_context.controller.workflows)), 2)

    def test_add_playbook_already_exists(self):
        data = {'playbook_template': 'junkPlaybookTemplate', "name": "test_playbook"}
        self.put_with_status_check('/api/playbooks',
                                   data=json.dumps(data), headers=self.headers, status_code=SUCCESS_WITH_WARNING,
                                   content_type="application/json")
        self.put_with_status_check('/api/playbooks',
                                   error='Playbook already exists.',
                                   data=json.dumps(data), headers=self.headers, status_code=OBJECT_EXISTS_ERROR,
                                   content_type="application/json")

    def test_add_workflow(self):
        initial_workflows = list(flask_server.running_context.controller.workflows.keys())
        data = {"name": "test_name"}
        response = self.put_with_status_check('/api/playbooks/test/workflows',
                                              headers=self.headers, status_code=OBJECT_CREATED, data=json.dumps(data),
                                              content_type="application/json")
        self.empty_workflow_json['uid'] = response['uid']
        self.assertDictEqual(response, self.empty_workflow_json)

        final_workflows = flask_server.running_context.controller.workflows.keys()
        self.assertEqual(len(final_workflows), len(initial_workflows) + 1)
        self.assertTrue(flask_server.running_context.controller.is_workflow_registered('test', 'test_name'))

    def test_add_templated_workflow(self):
        initial_workflows = list(flask_server.running_context.controller.workflows.keys())
        data = {"playbook_template": 'basicWorkflow',
                "workflow_template": 'helloWorldWorkflow',
                "name": "test_name"}
        self.put_with_status_check('/api/playbooks/test/workflows',
                                   data=json.dumps(data), headers=self.headers, status_code=OBJECT_CREATED,
                                   content_type="application/json")
        final_workflows = flask_server.running_context.controller.workflows.keys()
        self.assertEqual(len(final_workflows), len(initial_workflows) + 1)
        self.assertTrue(flask_server.running_context.controller.is_workflow_registered('test', 'test_name'))

    def test_add_templated_workflow_invalid_template(self):
        initial_workflows = list(flask_server.running_context.controller.workflows.keys())
        data = {"playbook_template": 'basicWorkflow',
                "workflow_template": "junktemplatename",
                "name": "test_name"}
        self.put_with_status_check('/api/playbooks/test/workflows',
                                   data=json.dumps(data), headers=self.headers, status_code=SUCCESS_WITH_WARNING,
                                   content_type="application/json")

        final_workflows = flask_server.running_context.controller.workflows.keys()
        self.assertEqual(len(final_workflows), len(initial_workflows) + 1)
        self.assertTrue(flask_server.running_context.controller.is_workflow_registered('test', 'test_name'))

    def test_add_templated_workflow_invalid_template_playbook(self):
        initial_workflows = list(flask_server.running_context.controller.workflows.keys())
        data = {"playbook_template": 'junkTemplatePlaybook',
                "workflow_template": "helloWorldWorkflow",
                "name": "test_name"}
        response = self.put_with_status_check('/api/playbooks/test/workflows',
                                              data=json.dumps(data), headers=self.headers,
                                              status_code=SUCCESS_WITH_WARNING,
                                              content_type="application/json")
        self.empty_workflow_json['uid'] = response['uid']
        self.empty_workflow_json['accumulated_risk'] = 0.0
        self.assertDictEqual(response, self.empty_workflow_json)
        final_workflows = flask_server.running_context.controller.workflows.keys()
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
        expected_json = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow').as_json()
        workflow_name = "test_name"
        data = {"new_name": workflow_name, "name": "helloWorldWorkflow"}
        response = self.post_with_status_check('/api/playbooks/test/workflows',
                                               data=json.dumps(data),
                                               headers=self.headers,
                                               content_type='application/json')

        expected_json['name'] = workflow_name

        self.assertDictEqual(response, expected_json)

        self.assertEqual(len(flask_server.running_context.controller.workflows.keys()), 1)
        self.assertTrue(flask_server.running_context.controller.is_workflow_registered('test', 'test_name'))
        self.assertFalse(
            flask_server.running_context.controller.is_workflow_registered('test', 'helloWorldWorkflow'))

    def test_edit_workflow_empty_name(self):
        expected_json = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow').as_json()
        data = {"new_name": "", "name": "helloWorldWorkflow"}
        response = self.post_with_status_check('/api/playbooks/test/workflows',
                                               data=json.dumps(data),
                                               headers=self.headers,
                                               content_type='application/json')

        self.assertDictEqual(response, expected_json)

        self.assertEqual(len(flask_server.running_context.controller.workflows.keys()), 1)
        self.assertFalse(flask_server.running_context.controller.is_workflow_registered('test', 'test_name'))
        self.assertTrue(
            flask_server.running_context.controller.is_workflow_registered('test', 'helloWorldWorkflow'))

    def test_edit_workflow_(self):
        expected_json = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow').as_json()
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
        workflow_name = list(flask_server.running_context.controller.workflows.keys())[0].workflow
        initial_workflow = flask_server.running_context.controller.get_workflow('test', workflow_name)
        initial_steps = [step.as_json() for step in initial_workflow.steps.values()]
        initial_steps[0]['position']['x'] = 0.0
        initial_steps[0]['position']['y'] = 0.0
        added_step = Step(name='new_id', app='HelloWorld', action='pause', inputs={'seconds': 5},
                          position={'x': 0, 'y': 0}).as_json()

        initial_steps.append(added_step)
        data = {"steps": initial_steps}
        self.post_with_status_check('/api/playbooks/test/workflows/{0}/save'.format(workflow_name),
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type='application/json')

        resulting_workflow = flask_server.running_context.controller.get_workflow('test', workflow_name)

        # compare the steps in initial and final workflow
        self.assertEqual(len(resulting_workflow.steps.keys()), len(list(initial_steps)))
        for initial_step in initial_steps:
            self.assertIn(initial_step['name'], resulting_workflow.steps.keys())
            self.assertDictEqual(initial_step, resulting_workflow.steps[initial_step['name']].as_json())

        # assert that the file has been saved to a file
        workflows = [path.splitext(workflow)[0]
                     for workflow in os.listdir(core.config.paths.workflows_path) if workflow.endswith('.playbook')]
        matching_workflows = [workflow for workflow in workflows if workflow == 'test']
        self.assertEqual(len(matching_workflows), 1)

        # assert that the file loads properly after being saved
        flask_server.running_context.controller.workflows = {}
        flask_server.running_context.controller.load_workflows_from_file(os.path.join(core.config.paths.workflows_path,
                                                                                      'test.playbook'))
        orderless_list_compare(self,
                               [key.workflow for key in flask_server.running_context.controller.workflows.keys()],
                               ['helloWorldWorkflow'])
        loaded_workflow = flask_server.running_context.controller.get_workflow('test', workflow_name)

        # compare the steps in loaded and expected workflow
        self.assertEqual(len(loaded_workflow.steps.keys()), len(list(resulting_workflow.steps.keys())))

        def remove_uids(step):
            step.uid = ''
            for next_step in step.conditionals:
                next_step.uid = ''
                for flag in next_step.flags:
                    flag.uid = ''
                    for filter_ in flag.filters:
                        filter_.uid = ''

        for step_name, loaded_step in loaded_workflow.steps.items():
            self.assertIn(step_name, resulting_workflow.steps.keys())
            remove_uids(loaded_step)
            remove_uids(resulting_workflow.steps[step_name])
            self.assertDictEqual(loaded_step.as_json(), resulting_workflow.steps[step_name].as_json())

    def test_save_workflow_invalid_app(self):
        workflow_name = list(flask_server.running_context.controller.workflows.keys())[0].workflow
        initial_workflow = flask_server.running_context.controller.get_workflow('test', workflow_name)
        initial_steps = [step.as_json() for step in initial_workflow.steps.values()]
        initial_steps[0]['position']['x'] = 0.0
        initial_steps[0]['position']['y'] = 0.0
        added_step = Step(name='new_id', app='HelloWorld', action='pause', inputs={'seconds': 5},
                          position={'x': 0, 'y': 0}).as_json()
        added_step['app'] = 'Invalid'

        initial_steps.append(added_step)
        data = {"steps": initial_steps}
        self.post_with_status_check('/api/playbooks/test/workflows/{0}/save'.format(workflow_name),
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type='application/json',
                                    status_code=INVALID_INPUT_ERROR)

    def test_save_workflow_invalid_action(self):
        workflow_name = list(flask_server.running_context.controller.workflows.keys())[0].workflow
        initial_workflow = flask_server.running_context.controller.get_workflow('test', workflow_name)
        initial_steps = [step.as_json() for step in initial_workflow.steps.values()]
        initial_steps[0]['position']['x'] = 0.0
        initial_steps[0]['position']['y'] = 0.0
        added_step = Step(name='new_id', app='HelloWorld', action='pause', inputs={'seconds': 5},
                          position={'x': 0, 'y': 0}).as_json()
        added_step['action'] = 'Invalid'

        initial_steps.append(added_step)
        data = {"steps": initial_steps}
        self.post_with_status_check('/api/playbooks/test/workflows/{0}/save'.format(workflow_name),
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type='application/json',
                                    status_code=INVALID_INPUT_ERROR)

    def test_save_workflow_invalid_input_name(self):
        workflow_name = list(flask_server.running_context.controller.workflows.keys())[0].workflow
        initial_workflow = flask_server.running_context.controller.get_workflow('test', workflow_name)
        initial_steps = [step.as_json() for step in initial_workflow.steps.values()]
        initial_steps[0]['position']['x'] = 0.0
        initial_steps[0]['position']['y'] = 0.0
        added_step = Step(name='new_id', app='HelloWorld', action='pause', inputs={'seconds': 5},
                          position={'x': 0, 'y': 0}).as_json()
        added_step['inputs'] = [{'name': 'Invalid', 'value': 5}]

        initial_steps.append(added_step)
        data = {"steps": initial_steps}
        self.post_with_status_check('/api/playbooks/test/workflows/{0}/save'.format(workflow_name),
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type='application/json',
                                    status_code=INVALID_INPUT_ERROR)

    def test_save_workflow_invalid_input_format(self):
        workflow_name = list(flask_server.running_context.controller.workflows.keys())[0].workflow
        initial_workflow = flask_server.running_context.controller.get_workflow('test', workflow_name)
        initial_steps = [step.as_json() for step in initial_workflow.steps.values()]
        initial_steps[0]['position']['x'] = 0.0
        initial_steps[0]['position']['y'] = 0.0
        added_step = Step(name='new_id', app='HelloWorld', action='pause', inputs={'seconds': 5},
                          position={'x': 0, 'y': 0}).as_json()
        added_step['inputs'][0]['value'] = 'aaaa'

        initial_steps.append(added_step)
        data = {"steps": initial_steps}
        self.post_with_status_check('/api/playbooks/test/workflows/{0}/save'.format(workflow_name),
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type='application/json',
                                    status_code=INVALID_INPUT_ERROR)

    def test_save_workflow_new_start_step(self):
        workflow_name = list(flask_server.running_context.controller.workflows.keys())[0].workflow
        initial_workflow = flask_server.running_context.controller.get_workflow('test', workflow_name)
        initial_steps = [step.as_json() for step in initial_workflow.steps.values()]
        initial_steps[0]['position']['x'] = 0.0
        initial_steps[0]['position']['y'] = 0.0
        added_step = Step(name='new_id', app='HelloWorld', action='pause', inputs={'seconds': 5},
                          position={'x': 0, 'y': 0}).as_json()

        initial_steps.append(added_step)
        data = {"steps": initial_steps, "start": "new_start"}
        self.post_with_status_check('/api/playbooks/test/workflows/{0}/save'.format(workflow_name),
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type='application/json')

        resulting_workflow = flask_server.running_context.controller.get_workflow('test', workflow_name)
        self.assertEqual(resulting_workflow.start_step, "new_start")

    def test_save_workflow_invalid_name(self):
        data = {"steps": []}
        self.post_with_status_check('/api/playbooks/test/workflows/junkworkflowname/save',
                                    error='Playbook or workflow does not exist.',
                                    headers=self.headers, status_code=OBJECT_DNE_ERROR, data=json.dumps(data),
                                    content_type="application/json")

    def test_delete_playbook(self):
        self.delete_with_status_check('/api/playbooks/test', headers=self.headers)

        self.assertFalse(flask_server.running_context.controller.is_playbook_registered('test'))

        playbooks = [os.path.splitext(playbook)[0]
                     for playbook in helpers.locate_workflows_in_directory(core.config.paths.workflows_path)]
        self.assertEqual(len(playbooks), 0)

    def test_delete_playbook_no_file(self):
        initial_playbook_files = [os.path.splitext(playbook)[0] for playbook in
                                  helpers.locate_workflows_in_directory()]
        data = {"name": "test_playbook"}
        self.app.put('/api/playbooks', headers=self.headers, content_type="application/json", data=json.dumps(data))
        self.delete_with_status_check('/api/playbooks/test_playbook', headers=self.headers)

        self.assertTrue(flask_server.running_context.controller.is_playbook_registered('test'))
        self.assertFalse(flask_server.running_context.controller.is_playbook_registered('test_playbook'))

        final_playbook_files = [os.path.splitext(playbook)[0] for playbook in
                                helpers.locate_workflows_in_directory()]
        orderless_list_compare(self, final_playbook_files, initial_playbook_files)

    def test_delete_playbook_invalid_name(self):
        initial_playbook_files = [os.path.splitext(playbook)[0] for playbook in
                                  helpers.locate_workflows_in_directory()]
        self.delete_with_status_check('/api/playbooks/junkPlaybookName', error='Playbook does not exist.',
                                      headers=self.headers,
                                      status_code=OBJECT_DNE_ERROR)
        self.assertFalse(flask_server.running_context.controller.is_playbook_registered('junkPlaybookName'))
        final_playbook_files = [os.path.splitext(playbook)[0] for playbook in
                                helpers.locate_workflows_in_directory()]
        orderless_list_compare(self, final_playbook_files, initial_playbook_files)

    def test_delete_workflow(self):
        workflow_name = 'test_name2'
        data = {"name": "test_name2"}
        self.app.put('/api/playbooks/test/workflows', headers=self.headers, data=json.dumps(data),
                     content_type="application/json")

        initial_workflow = flask_server.running_context.controller.get_workflow('test', workflow_name)
        initial_steps = [step.as_json() for step in initial_workflow.steps.values()]

        data = {"steps": initial_steps}
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

    def test_copy_workflow(self):
        self.post_with_status_check('/api/playbooks/test/workflows/helloWorldWorkflow/copy',
                                    headers=self.headers, status_code=OBJECT_CREATED, data=json.dumps({}),
                                    content_type="application/json")
        self.assertEqual(len(flask_server.running_context.controller.workflows.keys()), 2)
        self.assertTrue(flask_server.running_context.controller.is_workflow_registered('test', 'helloWorldWorkflow'))
        self.assertTrue(
            flask_server.running_context.controller.is_workflow_registered('test', 'helloWorldWorkflow_Copy'))

        workflow_original = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow')
        workflow_copy = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow_Copy')
        new_workflow_name = 'helloWorldWorkflow_Copy'
        self.assertEqual(workflow_copy.name, new_workflow_name)
        copy_workflow_json = workflow_copy.as_json()
        original_workflow_json = workflow_original.as_json()
        copy_workflow_json.pop('name', None)
        original_workflow_json.pop('name', None)
        self.assertDictEqual(copy_workflow_json, original_workflow_json)
        self.assertEqual(len(workflow_original.steps), len(workflow_copy.steps))
        for step in workflow_copy.steps:
            self.assertEqual(len(workflow_original.steps[step].conditionals),
                             len(workflow_copy.steps[step].conditionals))

    def test_copy_workflow_invalid_name(self):
        data = {"workflow": "helloWorldWorkflow"}
        self.post_with_status_check('/api/playbooks/test/workflows/helloWorldWorkflow/copy',
                                    error='Playbook or workflow already exists.', data=json.dumps(data),
                                    headers=self.headers, status_code=OBJECT_EXISTS_ERROR,
                                    content_type="application/json")

        self.assertEqual(len(flask_server.running_context.controller.workflows.keys()), 1)
        self.assertTrue(flask_server.running_context.controller.is_workflow_registered('test', 'helloWorldWorkflow'))

    def test_copy_workflow_different_playbook(self):
        data = {"name": "new_playbook"}
        self.put_with_status_check('/api/playbooks', headers=self.headers,
                                   status_code=OBJECT_CREATED, content_type="application/json", data=json.dumps(data))
        data = {"playbook": "new_playbook"}
        self.post_with_status_check('/api/playbooks/test/workflows/helloWorldWorkflow/copy', data=json.dumps(data),
                                    headers=self.headers, status_code=OBJECT_CREATED, content_type="application/json")

        self.assertEqual(len(flask_server.running_context.controller.workflows.keys()), 3)
        self.assertTrue(flask_server.running_context.controller.is_workflow_registered('test', 'helloWorldWorkflow'))
        self.assertTrue(
            flask_server.running_context.controller.is_workflow_registered('new_playbook', 'helloWorldWorkflow_Copy'))

        workflow_original = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow')
        workflow_copy = flask_server.running_context.controller.get_workflow('new_playbook', 'helloWorldWorkflow_Copy')
        new_workflow_name = 'helloWorldWorkflow_Copy'
        self.assertEqual(workflow_copy.name, new_workflow_name)
        copy_workflow_json = workflow_copy.as_json()
        original_workflow_json = workflow_original.as_json()
        copy_workflow_json.pop('name', None)
        original_workflow_json.pop('name', None)
        self.assertDictEqual(copy_workflow_json, original_workflow_json)

        self.assertEqual(len(workflow_original.steps), len(workflow_copy.steps))
        for step in workflow_copy.steps:
            self.assertEqual(len(workflow_original.steps[step].conditionals),
                             len(workflow_copy.steps[step].conditionals))

    def test_copy_playbook(self):
        self.post_with_status_check('/api/playbooks/test/copy',
                                    headers=self.headers, status_code=OBJECT_CREATED, data=json.dumps({}),
                                    content_type="application/json")

        self.assertEqual(len(flask_server.running_context.controller.get_all_playbooks()), 2)
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

        self.assertEqual(len(flask_server.running_context.controller.get_all_playbooks()), 1)
        self.assertTrue(flask_server.running_context.controller.is_playbook_registered('test'))

    def test_execute_workflow_playbook_dne(self):
        self.post_with_status_check('/api/playbooks/junkPlay/workflows/helloWorldWorkflow/execute',
                                    error='Playbook or workflow does not exist.',
                                    headers=self.headers, status_code=OBJECT_DNE_ERROR)

    def test_execute_workflow_workflow_dne(self):
        self.post_with_status_check('/api/playbooks/test/workflows/junkWorkflow/execute',
                                    error='Playbook or workflow does not exist.',
                                    headers=self.headers, status_code=OBJECT_DNE_ERROR)

    def test_execute_workflow(self):
        flask_server.running_context.controller.initialize_threading()
        sync = Event()
        workflow = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow')
        step_uids = [step.uid for step in workflow.steps.values() if step.name == 'start']
        setup_subscriptions_for_step(workflow.uid, step_uids)
        start = datetime.utcnow()

        @WorkflowShutdown.connect
        def wait_for_completion(sender, **kwargs):
            sync.set()

        WorkflowShutdown.connect(wait_for_completion)

        response = self.post_with_status_check('/api/playbooks/test/workflows/helloWorldWorkflow/execute',
                                               headers=self.headers,
                                               status_code=SUCCESS_ASYNC)
        flask_server.running_context.controller.shutdown_pool(1)
        self.assertIn('id', response)
        sync.wait(timeout=10)
        steps = []
        for uid in step_uids:
            steps.extend(executed_steps(uid, start, datetime.utcnow()))
        self.assertEqual(len(steps), 1)
        step = steps[0]
        result = step['data']
        self.assertEqual(result['result'], {'status': 'Success', 'result': 'REPEATING: Hello World'})

    # TODO: FIX THIS TEST
    def test_execute_workflow_in_memory(self):
        flask_server.running_context.controller.initialize_threading()
        sync = Event()
        data = {"playbook_template": 'basicWorkflow',
                "workflow_template": 'helloWorldWorkflow',
                "name": "test_name"}

        @WorkflowShutdown.connect
        def wait_for_completion(sender, **kwargs):
            sync.set()

        WorkflowShutdown.connect(wait_for_completion)

        self.put_with_status_check('/api/playbooks/basicWorkflow/workflows',
                                   data=json.dumps(data), headers=self.headers, status_code=OBJECT_CREATED,
                                   content_type="application/json")

        workflow = flask_server.running_context.controller.get_workflow('basicWorkflow', 'test_name')
        step_uids = [step.uid for step in workflow.steps.values() if step.name == 'start']
        setup_subscriptions_for_step(workflow.uid, step_uids)
        start = datetime.utcnow()
        response = self.post_with_status_check('/api/playbooks/basicWorkflow/workflows/test_name/execute',
                                               headers=self.headers,
                                               status_code=SUCCESS_ASYNC)
        flask_server.running_context.controller.shutdown_pool(1)
        self.assertIn('id', response)
        sync.wait(timeout=10)
        steps = []
        for uid in step_uids:
            steps.extend(executed_steps(uid, start, datetime.utcnow()))
        self.assertEqual(len(steps), 1)
        step = steps[0]
        result = step['data']
        self.assertDictEqual(result['result'], {'status': 'Success', 'result': 'REPEATING: Hello World'})

    def test_read_results(self):
        flask_server.running_context.controller.initialize_threading()
        self.app.post('/api/playbooks/test/workflows/helloWorldWorkflow/execute', headers=self.headers)
        self.app.post('/api/playbooks/test/workflows/helloWorldWorkflow/execute', headers=self.headers)
        self.app.post('/api/playbooks/test/workflows/helloWorldWorkflow/execute', headers=self.headers)

        with flask_server.running_context.flask_app.app_context():
            flask_server.running_context.controller.shutdown_pool(3)

        response = self.get_with_status_check('/workflowresults', headers=self.headers)
        self.assertEqual(len(response), 3)
        for result in response:
            self.assertIn('timestamp', result)
            self.assertIn('result', result)
            self.assertIn('name', result)

    def test_read_all_results(self):
        flask_server.running_context.controller.initialize_threading()
        self.app.post('/api/playbooks/test/workflows/helloWorldWorkflow/execute', headers=self.headers)
        self.app.post('/api/playbooks/test/workflows/helloWorldWorkflow/execute', headers=self.headers)
        self.app.post('/api/playbooks/test/workflows/helloWorldWorkflow/execute', headers=self.headers)

        with flask_server.running_context.flask_app.app_context():
            flask_server.running_context.controller.shutdown_pool(3)

        response = self.get_with_status_check('/workflowresults/all', headers=self.headers)
        self.assertEqual(len(response), 3)

        for result in response:
            self.assertSetEqual(set(result.keys()), {'status', 'completed_at', 'started_at', 'name', 'results', 'uid'})
            for step_result in result['results']:
                self.assertSetEqual(set(step_result.keys()), {'input', 'type', 'name', 'timestamp', 'result'})
