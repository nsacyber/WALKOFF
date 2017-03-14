import unittest
import json
from os import path
import os

from tests.config import testWorkflowsPath
from tests.util.assertwrappers import orderless_list_comapre
from core.config import workflowsPath as coreWorkflows
from server import flaskServer as flask_server
from core.controller import Controller


class TestWorkflowServer(unittest.TestCase):
    def setUp(self):
        self.app = flask_server.app.test_client(self)
        self.app.testing = True
        self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)
        response = self.app.post('/key', data=dict(email='admin', password='admin'),
                                 follow_redirects=True).get_data(as_text=True)

        self.key = json.loads(response)["auth_token"]
        self.headers = {"Authentication-Token": self.key}
        flask_server.running_context.controller.load_all_workflows_from_directory()

        self.empty_workflow_json = \
            {'status': 'success',
             'workflow': {'steps': [],
                          'name': 'test_name',
                          'options': {'children': {},
                                      'enabled': 'True',
                                      'scheduler': {'args': {'interval': '0.1',
                                                             'eDT': '2016-3-15 12:00:00',
                                                             'sDT': '2016-1-1 12:00:00'},
                                                    'autorun': u'false',
                                                    'type': u'cron'}}}}
        self.hello_world_json = []

    def tearDown(self):
        flask_server.running_context.controller.workflows = {}
        workflows = [path.splitext(workflow)[0]
                     for workflow in os.listdir(coreWorkflows) if workflow.endswith('.workflow')]
        matching_workflows = [workflow for workflow in workflows if (workflow == 'test_name'
                                                                     or workflow == 'helloWorldWorkflow')]

        # cleanup
        for workflow in matching_workflows:
            os.remove(path.join(coreWorkflows, '{0}.workflow'.format(workflow)))

    def test_display_workflows(self):
        expected_workflows = ['helloWorldWorkflow']
        response = self.app.get('/workflows', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertEqual(len(expected_workflows), len(response['workflows']))
        self.assertSetEqual(set(expected_workflows), set(response['workflows']))

    def test_display_available_workflow_templates(self):
        expected_workflows = ['emptyWorkflow', 'helloWorldWorkflow']
        response = self.app.get('/workflows/templates', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertEqual(len(expected_workflows), len(response['templates']))
        self.assertSetEqual(set(expected_workflows), set(response['templates']))

    def test_display_workflow(self):
        workflow_filename = os.path.join(testWorkflowsPath, 'multiactionWorkflowTest.workflow')
        flask_server.running_context.controller.loadWorkflowsFromFile(path=workflow_filename)
        steps_data = flask_server.running_context.controller.workflows['multiactionWorkflow'].get_cytoscape_data()
        options_data = flask_server.running_context.controller.workflows['multiactionWorkflow'].options.as_json()
        expected_response = {'status': 'success',
                             'steps': steps_data,
                             'options': options_data}
        response = self.app.get('/workflow/multiactionWorkflow', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, expected_response)

    def test_display_workflow_invalid_name(self):
        response = self.app.get('/workflow/multiactionWorkflow', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, {"status": "error: name multiactionWorkflow not found"})

    def test_add_workflow(self):
        initial_workflows = list(flask_server.running_context.controller.workflows.keys())
        workflow_name = 'test_name'
        response = self.app.post('/workflow/{0}/add'.format(workflow_name), headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, self.empty_workflow_json)

        final_workflows = flask_server.running_context.controller.workflows.keys()
        self.assertEqual(len(final_workflows), len(initial_workflows) + 1)

        added_workflow = set(final_workflows) - set(initial_workflows)
        self.assertEqual(list(added_workflow)[0], workflow_name)

    def test_add_templated_workflow(self):
        initial_workflows = list(flask_server.running_context.controller.workflows.keys())
        workflow_name = 'test_name'
        data = {"template": 'basicWorkflow'}
        response = self.app.post('/workflow/{0}/add'.format(workflow_name), data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        # TODO: the two responses look right, but fail in Python 3

        final_workflows = flask_server.running_context.controller.workflows.keys()
        self.assertEqual(len(final_workflows), len(initial_workflows) + 1)

        added_workflow = set(final_workflows) - set(initial_workflows)
        self.assertEqual(list(added_workflow)[0], workflow_name)

    def test_add_templated_workflow_invalid_template(self):
        initial_workflows = list(flask_server.running_context.controller.workflows.keys())
        workflow_name = 'test_name'
        data = {"template": "junktemplatename"}
        response = self.app.post('/workflow/{0}/add'.format(workflow_name), data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.empty_workflow_json['status'] = 'warning: template not found. Using default template'

        self.assertDictEqual(response, self.empty_workflow_json)

        final_workflows = flask_server.running_context.controller.workflows.keys()
        self.assertEqual(len(final_workflows), len(initial_workflows) + 1)

        added_workflow = set(final_workflows) - set(initial_workflows)
        self.assertEqual(list(added_workflow)[0], workflow_name)

    def test_edit_workflow_name_only(self):
        workflow_name = 'test_name'
        data = {"new_name": workflow_name}
        response = self.app.post('/workflow/helloWorldWorkflow/edit', data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        expected_json = {'status': 'success',
                         'workflow': {'name': 'test_name',
                                      'options': {'enabled': 'False',
                                                  'children': {},
                                                  'scheduler': {'args': {},
                                                                'type': 'chron',
                                                                'autorun': 'false'}}}}

        self.assertDictEqual(response, expected_json)

        self.assertEqual(len(flask_server.running_context.controller.workflows.keys()), 1)
        self.assertEqual(list(flask_server.running_context.controller.workflows.keys())[0], workflow_name)

    def test_edit_workflow_options_only(self):
        expected_args = json.dumps({"arg1": "val1", "arg2": "val2", "agr3": "val3"})
        data = {"enabled": "true",
                "scheduler_type": "test_scheduler",
                "autoRun": 'true',
                "scheduler_args": expected_args}
        response = self.app.post('/workflow/helloWorldWorkflow/edit', data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        expected_json = {'status': 'success',
                         'workflow': {'name': 'helloWorldWorkflow',
                                      'options': {'enabled': 'True',
                                                  'children': {},
                                                  'scheduler': {'args': {'arg1': 'val1',
                                                                         'arg2': 'val2',
                                                                         'agr3': 'val3'},
                                                                'type': 'test_scheduler',
                                                                'autorun': 'true'}}}}
        self.assertDictEqual(response, expected_json)

        options = flask_server.running_context.controller.workflows['helloWorldWorkflow'].options
        self.assertTrue(options.enabled)
        self.assertEqual(options.scheduler['type'], 'test_scheduler')
        self.assertEqual(options.scheduler['autorun'], 'true')
        self.assertEqual(options.scheduler['args'], json.loads(expected_args))
        self.assertEqual(list(flask_server.running_context.controller.workflows.keys())[0], 'helloWorldWorkflow')

    def test_edit_workflow_(self):
        expected_args = json.dumps({"arg1": "val1", "arg2": "val2", "agr3": "val3"})
        workflow_name = 'test_name'
        data = {"new_name": workflow_name,
                "enabled": "true",
                "scheduler_type": "test_scheduler",
                "autoRun": 'true',
                "scheduler_args": expected_args}
        response = self.app.post('/workflow/helloWorldWorkflow/edit', data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        expected_json = {'status': 'success',
                         'workflow': {'name': u'test_name',
                                      'options': {'enabled': 'True',
                                                  'children': {},
                                                  'scheduler': {'args': {'arg1': 'val1',
                                                                         'arg2': 'val2',
                                                                         'agr3': 'val3'},
                                                                'type': 'test_scheduler',
                                                                'autorun': 'true'}}}}
        self.assertDictEqual(response, expected_json)

        options = flask_server.running_context.controller.workflows[workflow_name].options
        self.assertTrue(options.enabled)
        self.assertEqual(options.scheduler['type'], 'test_scheduler')
        self.assertEqual(options.scheduler['autorun'], 'true')
        self.assertEqual(options.scheduler['args'], json.loads(expected_args))
        self.assertEqual(list(flask_server.running_context.controller.workflows.keys())[0], workflow_name)

    def test_edit_workflow_invalid_workflow(self):
        workflow_name = 'test_name'
        data = {"new_name": workflow_name}
        initial_workflows = flask_server.running_context.controller.workflows.keys()
        response = self.app.post('/workflow/junkworkflow/edit', data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, {'status': 'error: workflow junkworkflow is not valid'})
        final_workflows = flask_server.running_context.controller.workflows.keys()
        self.assertSetEqual(set(final_workflows), set(initial_workflows))

    def test_save_workflow(self):
        workflow_name = list(flask_server.running_context.controller.workflows.keys())[0]
        initial_workflow = flask_server.running_context.controller.workflows[workflow_name]
        initial_steps = dict(initial_workflow.steps)
        initial_workflow_cytoscape = list(initial_workflow.get_cytoscape_data())
        added_step_cytoscape = {'data': {'id': 'new_id',
                                         'parameters': {'errors': [],
                                                        'name': 'new_id',
                                                        'app': 'new_app',
                                                        'next': [],
                                                        'device': 'new_device',
                                                        'action': 'new_action',
                                                        'input': {}}},
                                'group': 'nodes'}
        initial_workflow_cytoscape.insert(0, added_step_cytoscape)
        data = {"filename": "test_name",
                "cytoscape": json.dumps(initial_workflow_cytoscape)}

        response = self.app.post('/workflow/{0}/save'.format(workflow_name), data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertEqual(response['status'], 'success')

        resulting_workflow = flask_server.running_context.controller.workflows[workflow_name]

        # compare the steps in initial and final workflow
        self.assertEqual(len(resulting_workflow.steps.keys()), len(list(initial_steps.keys()))+1)
        for step_name, initial_step in initial_steps.items():
            self.assertIn(step_name, resulting_workflow.steps.keys())
            self.assertDictEqual(initial_step.as_json(), resulting_workflow.steps[step_name].as_json())

        # assert that the file has been saved properly
        workflows = [path.splitext(workflow)[0]
                     for workflow in os.listdir(coreWorkflows) if workflow.endswith('.workflow')]
        matching_workflows = [workflow for workflow in workflows if workflow == 'test_name']
        self.assertEqual(len(matching_workflows), 1)

    def test_save_workflow_no_filename(self):
        workflow_name = list(flask_server.running_context.controller.workflows.keys())[0]
        initial_workflow = flask_server.running_context.controller.workflows[workflow_name]
        initial_steps = dict(initial_workflow.steps)
        initial_workflow_cytoscape = list(initial_workflow.get_cytoscape_data())
        added_step_cytoscape = {'data': {'id': 'new_id',
                                         'parameters': {'errors': [],
                                                        'name': 'new_id',
                                                        'app': 'new_app',
                                                        'next': [],
                                                        'device': 'new_device',
                                                        'action': 'new_action',
                                                        'input': {}}},
                                'group': 'nodes'}
        initial_workflow_cytoscape.insert(0, added_step_cytoscape)
        data = {"cytoscape": json.dumps(initial_workflow_cytoscape)}

        response = self.app.post('/workflow/{0}/save'.format(workflow_name), data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertEqual(response['status'], 'success')

        resulting_workflow = flask_server.running_context.controller.workflows[workflow_name]

        # compare the steps in initial and final workflow
        self.assertEqual(len(resulting_workflow.steps.keys()), len(list(initial_steps.keys())) + 1)
        for step_name, initial_step in initial_steps.items():
            self.assertIn(step_name, resulting_workflow.steps.keys())
            self.assertDictEqual(initial_step.as_json(), resulting_workflow.steps[step_name].as_json())

        # assert that the file has been saved properly
        workflows = [path.splitext(workflow)[0]
                     for workflow in os.listdir(coreWorkflows) if workflow.endswith('.workflow')]
        matching_workflows = [workflow for workflow in workflows if workflow == workflow_name]
        self.assertEqual(len(matching_workflows), 1)

    def test_save_workflow_invalid_name(self):
        response = self.app.post('/workflow/junkworkflowname/save', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, {'status': 'error: workflow junkworkflowname is not valid'})

    def test_delete_workflow(self):
        workflow_name = 'test_name2'
        self.app.post('/workflow/{0}/add'.format(workflow_name), headers=self.headers)
        data = {'cytoscape': str(flask_server.running_context.controller.workflows[workflow_name].get_cytoscape_data())}
        self.app.post('/workflow/{0}/save'.format(workflow_name), data=data, headers=self.headers)

        response = self.app.post('/workflow/{0}/delete'.format(workflow_name), headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, {'status': 'success'})

        workflows = [path.splitext(workflow)[0]
                     for workflow in os.listdir(coreWorkflows) if workflow.endswith('.workflow')]
        matching_workflows = [workflow for workflow in workflows if workflow == workflow_name]
        self.assertEqual(len(matching_workflows), 0)

    def test_delete_workflow_invalid(self):
        workflow_name = 'junkworkflowname'
        response = self.app.post('/workflow/{0}/delete'.format(workflow_name), headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, {'status': 'error: workflow {0} is not valid'.format(workflow_name)})
