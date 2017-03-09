import unittest
import json
from os import path
import os

from tests.config import testWorkflowsPath
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

    def tearDown(self):
        flask_server.running_context.controller.workflows = {}

    def test_display_workflows(self):
        expected_workflows = ['test']
        response = self.app.post('/workflows', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertEqual(len(expected_workflows), len(response['workflows']))
        self.assertSetEqual(set(expected_workflows), set(response['workflows']))

    def test_display_available_workflow_templates(self):
        expected_workflows = ['basicWorkflow', 'emptyWorkflow']
        response = self.app.post('/workflows/templates', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertEqual(len(expected_workflows), len(response['templates']))
        self.assertSetEqual(set(expected_workflows), set(response['templates']))

    def test_add_workflow(self):
        initial_workflows = list(flask_server.running_context.controller.workflows.keys())
        workflow_name = 'test_name'
        response = self.app.post('/workflow/{0}/add'.format(workflow_name), headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, {'status': 'success'})

        final_workflows = flask_server.running_context.controller.workflows.keys()
        self.assertEqual(len(final_workflows), len(initial_workflows)+1)

        added_workflow = set(final_workflows) - set(initial_workflows)
        self.assertEqual(list(added_workflow)[0], workflow_name)

    def test_edit_workflow_name_only(self):
        workflow_name = 'test_name'
        data = {"new_name": workflow_name}
        response = self.app.post('/workflow/helloWorldWorkflow/edit', data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, {'status': 'success'})

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
        self.assertDictEqual(response, {'status': 'success'})

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
        self.assertDictEqual(response, {'status': 'success'})

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
        initial_workflows = list(flask_server.running_context.controller.workflows.keys())
        workflow_name = 'test_name'
        response = self.app.post('/workflow/{0}/add'.format(workflow_name), headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, {'status': 'success'})

        final_workflows = flask_server.running_context.controller.workflows.keys()
        self.assertEqual(len(final_workflows), len(initial_workflows) + 1)

        added_workflow = set(final_workflows) - set(initial_workflows)
        self.assertEqual(list(added_workflow)[0], workflow_name)

        response = self.app.post('/workflow/{0}/save'.format(workflow_name), headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, {'status': 'success'})

        workflows = [path.splitext(workflow)[0]
                     for workflow in os.listdir(coreWorkflows) if workflow.endswith('.workflow')]
        matching_workflows = [workflow for workflow in workflows if workflow == workflow_name]
        self.assertEqual(len(matching_workflows), 1)

        # cleanup
        os.remove(path.join(coreWorkflows, '{0}.workflow'.format(workflow_name)))

    def test_save_workflow_invalid_name(self):
        response = self.app.post('/workflow/junkworkflowname/save', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, {'status': 'error: workflow junkworkflowname is not valid'})

    def test_delete_workflow(self):
        initial_workflows = list(flask_server.running_context.controller.workflows.keys())
        workflow_name = 'test_name'
        response = self.app.post('/workflow/{0}/add'.format(workflow_name), headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, {'status': 'success'})

        response = self.app.post('/workflow/{0}/save'.format(workflow_name), headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, {'status': 'success'})

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


