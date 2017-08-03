import json
from os import path
from tests.util.servertestcase import ServerTestCase
from tests.util.assertwrappers import orderless_list_compare
from tests.util.case_db_help import executed_steps, setup_subscriptions_for_step
from datetime import datetime
from server import flaskserver as flask_server
from core import helpers
import core.case.subscription
import os
import core.config.paths
from gevent.event import Event
from core.case.callbacks import WorkflowShutdown
from server.return_codes import *
import server.workflowresults
from core.step import Step


class TestWorkflowServer(ServerTestCase):
    def setUp(self):
        # This looks awful, I know
        self.empty_workflow_json = \
            {'workflow': {'steps': [],
                          'name': 'test_name',
                          'options': {'children': {},
                                      'enabled': 'True',
                                      'scheduler': {'args': {'interval': '0.1',
                                                             'eDT': '2016-3-15 12:00:00',
                                                             'sDT': '2016-1-1 12:00:00'},
                                                    'autorun': 'false',
                                                    'type': 'cron'}},
                          'start': 'start'}}
        self.hello_world_json = {
            'workflow': {
                'start': 'start',
                'steps': [{'group': 'nodes', 'data': {'id': 'start',
                                                      'parameters': {
                                                          'errors': [{
                                                              'flags': [],
                                                              'name': '1'}],
                                                          'name': 'start',
                                                          'app': 'HelloWorld',
                                                          'next': [{
                                                              'flags': [
                                                                  {
                                                                      'action': 'regMatch',
                                                                      'args': [{
                                                                              'value': '(.*)',
                                                                              'name': 'regex'}],
                                                                      'filters': [
                                                                          {
                                                                              'action': 'length',
                                                                              'args': []}]}],
                                                              'name': '1'}],
                                                          'device': 'hwTest',
                                                          'action': 'repeatBackToMe',
                                                          'input': {
                                                              'call': 'Hello World'},
                                                          'widgets': [],
                                                          'risk': 0}},
                           'position': {}}], 'name': 'test_name',
                'options': {'enabled': 'True', 'children': {}, 'scheduler': {
                    'args': {'hours': '*', 'minutes': '*/0.1', 'day': '*',
                             'month': '11-12'}, 'type': 'cron', 'autorun': 'false'}}}}

    def tearDown(self):
        flask_server.running_context.controller.workflows = {}

    # def test_display_all_playbooks(self):
    #     response = self.get_with_status_check('/api/playbooks', headers=self.headers)
    #     self.assertIn('playbooks', response)
    #     self.assertDictEqual(response['playbooks'], {'test': ['helloWorldWorkflow']})
    #
    # def test_display_playbook_workflows(self):
    #     response = self.get_with_status_check('/api/playbooks/test', headers=self.headers)
    #     self.assertIn('workflows', response)
    #     self.assertListEqual(response['workflows'], ['helloWorldWorkflow'])
    #
    # def test_display_playbook_workflows_invalid_name(self):
    #     self.get_with_status_check('/api/playbooks/junkName', error='Playbook does not exist.', headers=self.headers,
    #                                status_code=OBJECT_DNE_ERROR)
    #
    # def test_display_available_workflow_templates(self):
    #     response = self.get_with_status_check('/api/playbooks/templates', headers=self.headers)
    #     self.assertIn('templates', response)
    #     self.assertDictEqual(response['templates'], {'basicWorkflow': ['helloWorldWorkflow'],
    #                                                  'emptyWorkflow': ['emptyWorkflow']})
    #
    # def test_display_workflow_element(self):
    #     workflow_filename = os.path.join(".", "tests", "testWorkflows", 'multiactionWorkflowTest.playbook')
    #     flask_server.running_context.controller.load_workflows_from_file(path=workflow_filename)
    #     workflow = flask_server.running_context.controller.get_workflow('multiactionWorkflowTest',
    #                                                                     'multiactionWorkflow')
    #     ancestries_to_json = [([], {"steps": ['start', '1']}),
    #                           (['start'], workflow.steps['start'].as_json(with_children=False)),
    #                           (['1'], workflow.steps['1'].as_json(with_children=False)),
    #                           (['start', '1'], workflow.steps['start'].conditionals[0].as_json(with_children=False)),
    #                           (['start', '1', 'regMatch'],
    #                            workflow.steps['start'].conditionals[0].flags[0].as_json(with_children=False)),
    #                           (['start', '1', 'regMatch', 'length'],
    #                            workflow.steps['start'].conditionals[0].flags[0].filters[0].as_json())]
    #     for ancestry, expected_output in ancestries_to_json:
    #         data = {"ancestry": ancestry}
    #         response = self.get_with_status_check('/api/playbooks/multiactionWorkflowTest/workflows/multiactionWorkflow',
    #                                               data=json.dumps(data),
    #                                               content_type='application/json',
    #                                               headers=self.headers)
    #         self.assertIn('element', response)
    #         orderless_list_compare(self, response['element'], expected_output)
    #
    # def test_display_workflow_element_not_found(self):
    #     workflow_filename = os.path.join(".", "tests", "testWorkflows", 'multiactionWorkflowTest.playbook')
    #     flask_server.running_context.controller.load_workflows_from_file(path=workflow_filename)
    #
    #     ancestries = [['starta'],
    #                   ['1a'],
    #                   ['start', '1a'],
    #                   ['start', '1', 'regMatcha'],
    #                   ['start', '1', 'regMatch', 'lengtha']]
    #     for ancestry in ancestries:
    #         self.get_with_status_check('/api/playbooks/multiactionWorkflowTest/workflows/multiactionWorkflow',
    #                                    error='Element not found.',
    #                                    data=json.dumps({"ancestry": ancestry}),
    #                                    content_type='application/json',
    #                                    headers=self.headers, status_code=INVALID_INPUT_ERROR)
    #
    # def test_display_workflow_element_invalid_json(self):
    #     workflow_filename = os.path.join(".", "tests", "testWorkflows", 'multiactionWorkflowTest.playbook')
    #     flask_server.running_context.controller.load_workflows_from_file(path=workflow_filename)
    #     data = {"invalid_field_name": "grepgrepgrepspamsapmsapm"}
    #     self.get_with_status_check('/api/playbooks/multiactionWorkflowTest/workflows/multiactionWorkflow',
    #                                error='Malformed JSON.',
    #                                data=json.dumps(data),
    #                                content_type='application/json',
    #                                headers=self.headers, status_code=INVALID_INPUT_ERROR)
    #
    # def test_display_workflow_invalid_name(self):
    #     self.get_with_status_check('/api/playbooks/multiactionWorkflowTest/workflows/multiactionWorkflow',
    #                                error='Playbook or workflow does not exist.',
    #                                headers=self.headers, status_code=OBJECT_DNE_ERROR)
    #
    # def test_add_playbook_default(self):
    #     expected_playbooks = flask_server.running_context.controller.get_all_workflows()
    #     original_length = len(list(expected_playbooks.keys()))
    #     data = {"name" : "test_playbook"}
    #     response = self.put_with_status_check('/api/playbooks', headers=self.headers,
    #                                           status_code=OBJECT_CREATED, data=json.dumps(data), content_type="application/json")
    #     self.assertIn('playbooks', response)
    #     expected_playbooks['test_playbook'] = ['emptyWorkflow']
    #     self.assertDictEqual(response['playbooks'], expected_playbooks)
    #     self.assertDictEqual(flask_server.running_context.controller.get_all_workflows(), expected_playbooks)
    #     self.assertEqual(len(list(flask_server.running_context.controller.workflows)), original_length + 1)
    #
    # def test_add_playbook_template(self):
    #     expected_playbooks = flask_server.running_context.controller.get_all_workflows()
    #     data = {'playbook_template': 'basicWorkflow', "name": "test_playbook"}
    #     response = self.put_with_status_check('/api/playbooks',
    #                                           data=json.dumps(data), headers=self.headers, status_code=OBJECT_CREATED,
    #                                           content_type="application/json")
    #     self.assertIn('playbooks', response)
    #     expected_playbooks['test_playbook'] = ['helloWorldWorkflow']
    #     self.assertDictEqual(response['playbooks'], expected_playbooks)
    #     self.assertDictEqual(flask_server.running_context.controller.get_all_workflows(), expected_playbooks)
    #     self.assertEqual(len(list(flask_server.running_context.controller.workflows)), 2)
    #
    # def test_add_playbook_template_invalid_name(self):
    #     expected_playbooks = flask_server.running_context.controller.get_all_workflows()
    #     data = {'playbook_template': 'junkPlaybookTemplate', "name": "test_playbook"}
    #     response = self.put_with_status_check('/api/playbooks',
    #                                           data=json.dumps(data), headers=self.headers, status_code=SUCCESS_WITH_WARNING,
    #                                           content_type="application/json")
    #     self.assertIn('playbooks', response)
    #     expected_playbooks['test_playbook'] = ['emptyWorkflow']
    #     self.assertDictEqual(response['playbooks'], expected_playbooks)
    #     self.assertDictEqual(flask_server.running_context.controller.get_all_workflows(), expected_playbooks)
    #     self.assertEqual(len(list(flask_server.running_context.controller.workflows)), 2)
    #
    # def test_add_playbook_already_exists(self):
    #     data = {'playbook_template': 'junkPlaybookTemplate', "name": "test_playbook"}
    #     self.put_with_status_check('/api/playbooks',
    #                                data=json.dumps(data), headers=self.headers, status_code=SUCCESS_WITH_WARNING,
    #                                content_type="application/json")
    #     self.put_with_status_check('/api/playbooks',
    #                                error='Playbook already exists.',
    #                                data=json.dumps(data), headers=self.headers, status_code=OBJECT_EXISTS_ERROR,
    #                                content_type="application/json")
    #
    # def test_add_workflow(self):
    #     initial_workflows = list(flask_server.running_context.controller.workflows.keys())
    #     data = {"name": "test_name"}
    #     response = self.put_with_status_check('/api/playbooks/test/workflows',
    #                                           headers=self.headers, status_code=OBJECT_CREATED, data=json.dumps(data),
    #                                           content_type="application/json")
    #     self.assertDictEqual(response, self.empty_workflow_json)
    #
    #     final_workflows = flask_server.running_context.controller.workflows.keys()
    #     self.assertEqual(len(final_workflows), len(initial_workflows) + 1)
    #     self.assertTrue(flask_server.running_context.controller.is_workflow_registered('test', 'test_name'))
    #
    # def test_add_templated_workflow(self):
    #     initial_workflows = list(flask_server.running_context.controller.workflows.keys())
    #     data = {"playbook_template": 'basicWorkflow',
    #             "workflow_template": 'helloWorldWorkflow',
    #             "name": "test_name"}
    #     response = self.put_with_status_check('/api/playbooks/test/workflows',
    #                                           data=json.dumps(data), headers=self.headers, status_code=OBJECT_CREATED,
    #                                           content_type="application/json")
    #     self.assertIn('workflow', response)
    #
    #     final_workflows = flask_server.running_context.controller.workflows.keys()
    #     self.assertEqual(len(final_workflows), len(initial_workflows) + 1)
    #     self.assertTrue(flask_server.running_context.controller.is_workflow_registered('test', 'test_name'))
    #
    # def test_add_templated_workflow_invalid_template(self):
    #     initial_workflows = list(flask_server.running_context.controller.workflows.keys())
    #     data = {"playbook_template": 'basicWorkflow',
    #             "workflow_template": "junktemplatename",
    #             "name": "test_name"}
    #     self.put_with_status_check('/api/playbooks/test/workflows',
    #                                data=json.dumps(data), headers=self.headers, status_code=SUCCESS_WITH_WARNING,
    #                                content_type="application/json")
    #
    #     final_workflows = flask_server.running_context.controller.workflows.keys()
    #     self.assertEqual(len(final_workflows), len(initial_workflows) + 1)
    #     self.assertTrue(flask_server.running_context.controller.is_workflow_registered('test', 'test_name'))
    #
    # def test_add_templated_workflow_invalid_template_playbook(self):
    #     initial_workflows = list(flask_server.running_context.controller.workflows.keys())
    #     data = {"playbook_template": 'junkTemplatePlaybook',
    #             "workflow_template": "helloWorldWorkflow",
    #             "name": "test_name"}
    #     response = self.put_with_status_check('/api/playbooks/test/workflows',
    #                                           data=json.dumps(data), headers=self.headers, status_code=SUCCESS_WITH_WARNING,
    #                                           content_type="application/json")
    #     self.assertDictEqual(response, self.empty_workflow_json)
    #
    #     final_workflows = flask_server.running_context.controller.workflows.keys()
    #     self.assertEqual(len(final_workflows), len(initial_workflows) + 1)
    #     self.assertTrue(flask_server.running_context.controller.is_workflow_registered('test', 'test_name'))
    #
    # def test_edit_playbook(self):
    #     expected_keys = flask_server.running_context.controller.get_all_workflows()
    #     new_playbook_name = 'editedPlaybookName'
    #     data = {'new_name': new_playbook_name, "name": "test"}
    #     response = self.post_with_status_check('/api/playbooks',
    #                                            data=json.dumps(data),
    #                                            headers=self.headers,
    #                                            content_type='application/json')
    #     expected_keys['editedPlaybookName'] = expected_keys.pop('test')
    #     self.assertIn('playbooks', response)
    #     self.assertDictEqual(response['playbooks'], expected_keys)
    #     self.assertDictEqual(flask_server.running_context.controller.get_all_workflows(), expected_keys)
    #     self.assertTrue(
    #         os.path.isfile(os.path.join(core.config.paths.workflows_path, 'editedPlaybookName.playbook')))
    #     self.assertFalse(os.path.isfile(os.path.join(core.config.paths.workflows_path, 'test.playbook')))
    #
    # def test_edit_playbook_no_name(self):
    #     expected_keys = flask_server.running_context.controller.get_all_workflows()
    #     # response = self.post_with_status_check('/playbooks/test', 'error: invalid json', headers=self.headers)
    #     response = self.app.post('/api/playbooks', headers=self.headers, content_type="application/json", data=json.dumps({}))
    #     self.assertEqual(response._status_code, 400)
    #     # self.assertIn('playbooks', response)
    #     # self.assertDictEqual(response['playbooks'], expected_keys)
    #     self.assertDictEqual(flask_server.running_context.controller.get_all_workflows(), expected_keys)
    #     self.assertTrue(os.path.isfile(os.path.join(core.config.paths.workflows_path, 'test.playbook')))
    #
    # def test_edit_playbook_invalid_name(self):
    #     expected_keys = flask_server.running_context.controller.get_all_workflows()
    #     # response = self.post_with_status_check('/playbooks/junkPlaybookName',
    #     #                                        'error: playbook name not found', headers=self.headers)
    #     data = {"name": "junkPlaybookName"}
    #     response = self.app.post('/api/playbooks', headers=self.headers, content_type="application/json", data=json.dumps(data))
    #     self.assertEqual(response._status_code, 461)
    #     # self.assertIn('playbooks', response)
    #     # self.assertDictEqual(response['playbooks'], expected_keys)
    #     self.assertDictEqual(flask_server.running_context.controller.get_all_workflows(), expected_keys)
    #
    #     self.assertFalse(
    #         os.path.isfile(os.path.join(core.config.paths.workflows_path, 'junkPlaybookName.playbook')))
    #     self.assertTrue(os.path.isfile(os.path.join(core.config.paths.workflows_path, 'test.playbook')))
    #
    # def test_edit_playbook_no_file(self):
    #     data = {"name": "test2"}
    #     self.app.put('/api/playbooks', headers=self.headers, data=json.dumps(data), content_type="application/json")
    #     expected_keys = flask_server.running_context.controller.get_all_workflows()
    #     new_playbook_name = 'editedPlaybookName'
    #     data = {'new_name': new_playbook_name, "name": "test2"}
    #     response = self.post_with_status_check('/api/playbooks',
    #                                            data=json.dumps(data),
    #                                            headers=self.headers,
    #                                            content_type='application/json')
    #     expected_keys['editedPlaybookName'] = expected_keys.pop('test2')
    #     self.assertIn('playbooks', response)
    #     self.assertDictEqual(response['playbooks'], expected_keys)
    #     self.assertDictEqual(flask_server.running_context.controller.get_all_workflows(), expected_keys)
    #
    #     self.assertFalse(os.path.isfile(os.path.join(core.config.paths.workflows_path, 'test2.playbook')))
    #     self.assertFalse(
    #         os.path.isfile(os.path.join(core.config.paths.workflows_path, 'editedPlaybookName.playbook')))
    #     self.assertTrue(os.path.isfile(os.path.join(core.config.paths.workflows_path, 'test.playbook')))
    #
    # def test_edit_workflow_name_only(self):
    #     workflow_name = "test_name"
    #     data = {"new_name": workflow_name, "name": "helloWorldWorkflow"}
    #     response = self.post_with_status_check('/api/playbooks/test/workflows',
    #                                            data=json.dumps(data),
    #                                            headers=self.headers,
    #                                            content_type='application/json')
    #     expected_json = {'workflow': {'name': workflow_name,
    #                                   'options': {'enabled': 'True',
    #                                               'children': {},
    #                                               'scheduler': {'args': {'hours': '*',
    #                                                                      'minutes': '*/0.1',
    #                                                                      'day': '*',
    #                                                                      'month': '11-12'},
    #                                                             'type': 'cron',
    #                                                             'autorun': 'false'}},
    #                                   'start': 'start'}}
    #
    #     self.assertDictEqual(response, expected_json)
    #
    #     self.assertEqual(len(flask_server.running_context.controller.workflows.keys()), 1)
    #     self.assertTrue(flask_server.running_context.controller.is_workflow_registered('test', 'test_name'))
    #     self.assertFalse(
    #         flask_server.running_context.controller.is_workflow_registered('test', 'helloWorldWorkflow'))
    #
    #     workflow = flask_server.running_context.controller.get_workflow('test', 'test_name')
    #     for step in workflow.steps:
    #         self.assertTrue('test-test_name' in workflow.steps[step].ancestry)
    #         for next_step in workflow.steps[step].conditionals:
    #             self.assertTrue('test-test_name' in next_step.ancestry)
    #             for flag in next_step.flags:
    #                 self.assertTrue('test-test_name' in flag.ancestry)
    #                 for filter_element in flag.filters:
    #                     self.assertTrue('test-test_name' in filter_element.ancestry)
    #
    # def test_edit_workflow_empty_name(self):
    #     data = {"new_name": "", "name": "helloWorldWorkflow"}
    #     response = self.post_with_status_check('/api/playbooks/test/workflows',
    #                                            data=json.dumps(data),
    #                                            headers=self.headers,
    #                                            content_type='application/json')
    #     expected_json = {'workflow': {'name': 'helloWorldWorkflow',
    #                                   'options': {'enabled': 'True',
    #                                               'children': {},
    #                                               'scheduler': {'args': {'hours': '*',
    #                                                                      'minutes': '*/0.1',
    #                                                                      'day': '*',
    #                                                                      'month': '11-12'},
    #                                                             'type': 'cron',
    #                                                             'autorun': 'false'}},
    #                                   'start': 'start'}}
    #
    #     self.assertDictEqual(response, expected_json)
    #
    #     self.assertEqual(len(flask_server.running_context.controller.workflows.keys()), 1)
    #     self.assertFalse(flask_server.running_context.controller.is_workflow_registered('test', 'test_name'))
    #     self.assertTrue(
    #         flask_server.running_context.controller.is_workflow_registered('test', 'helloWorldWorkflow'))
    #
    # def test_edit_workflow_options_only(self):
    #     expected_args = json.dumps({"arg1": "val1", "arg2": "val2", "agr3": "val3"})
    #     data = {"scheduler": {"enabled": "true",
    #                           "scheduler_type": "test_scheduler",
    #                           "autorun": 'true',
    #                           "args": expected_args},
    #             "name": "helloWorldWorkflow"}
    #     response = self.post_with_status_check('/api/playbooks/test/workflows',
    #                                            data=json.dumps(data),
    #                                            headers=self.headers,
    #                                            content_type='application/json')
    #     expected_json = {'workflow': {'name': 'helloWorldWorkflow',
    #                                   'options': {'enabled': 'true',
    #                                               'children': {},
    #                                               'scheduler': {'args': {'arg1': 'val1',
    #                                                                      'arg2': 'val2',
    #                                                                      'agr3': 'val3'},
    #                                                             'type': 'test_scheduler',
    #                                                             'autorun': 'true'}},
    #                                   'start': 'start'}}
    #
    #     self.assertDictEqual(response, expected_json)
    #
    #     options = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow').options
    #     self.assertTrue(options.enabled)
    #     self.assertEqual(options.scheduler['type'], 'test_scheduler')
    #     self.assertEqual(options.scheduler['autorun'], 'true')
    #     self.assertEqual(options.scheduler['args'], json.loads(expected_args))
    #     self.assertTrue(
    #         flask_server.running_context.controller.is_workflow_registered('test', 'helloWorldWorkflow'))
    #
    # def test_edit_workflow_(self):
    #     expected_args = json.dumps({"arg1": "val1", "arg2": "val2", "agr3": "val3"})
    #     workflow_name = "test_name"
    #     data = {"new_name": workflow_name,
    #             "scheduler": {"enabled": "true",
    #                           "scheduler_type": "test_scheduler",
    #                           "autorun": 'true',
    #                           "args": expected_args},
    #             "name": "helloWorldWorkflow"}
    #     response = self.post_with_status_check('/api/playbooks/test/workflows',
    #                                            data=json.dumps(data),
    #                                            headers=self.headers,
    #                                            content_type='application/json')
    #     expected_json = {'workflow': {'name': 'test_name',
    #                                   'options': {'enabled': 'true',
    #                                               'children': {},
    #                                               'scheduler': {'args': {'arg1': 'val1',
    #                                                                      'arg2': 'val2',
    #                                                                      'agr3': 'val3'},
    #                                                             'type': 'test_scheduler',
    #                                                             'autorun': 'true'}},
    #                                   'start': 'start'}}
    #     self.assertDictEqual(response, expected_json)
    #
    #     options = flask_server.running_context.controller.get_workflow('test', workflow_name).options
    #     self.assertTrue(options.enabled)
    #     self.assertEqual(options.scheduler['type'], 'test_scheduler')
    #     self.assertEqual(options.scheduler['autorun'], 'true')
    #     self.assertEqual(options.scheduler['args'], json.loads(expected_args))
    #     self.assertTrue(flask_server.running_context.controller.is_workflow_registered('test', 'test_name'))
    #     self.assertFalse(
    #         flask_server.running_context.controller.is_workflow_registered('test', 'helloWorldWorkflow'))
    #
    # def test_edit_workflow_invalid_workflow(self):
    #     workflow_name = 'test_name'
    #     data = {"new_name": workflow_name, "name": "junkworkflow"}
    #     initial_workflows = flask_server.running_context.controller.workflows.keys()
    #     self.post_with_status_check('/api/playbooks/test/workflows',
    #                                 error='Playbook or workflow does not exist.',
    #                                 data=json.dumps(data), headers=self.headers, content_type="application/json",
    #                                 status_code=OBJECT_DNE_ERROR)
    #     final_workflows = flask_server.running_context.controller.workflows.keys()
    #     self.assertSetEqual(set(final_workflows), set(initial_workflows))
    #
    # def test_save_workflow(self):
    #     workflow_name = list(flask_server.running_context.controller.workflows.keys())[0].workflow
    #     initial_workflow = flask_server.running_context.controller.get_workflow('test', workflow_name)
    #     initial_steps = [step.as_json() for step in initial_workflow.steps.values()]
    #     initial_steps[0]['position']['x'] = 0.0
    #     initial_steps[0]['position']['y'] = 0.0
    #     added_step = Step(name='new_id', app='HelloWorld', action='pause', inputs={'seconds': 5}, position={'x': 0, 'y': 0}).as_json()
    #
    #     initial_steps.append(added_step)
    #     data = {"steps": initial_steps}
    #     self.post_with_status_check('/api/playbooks/test/workflows/{0}/save'.format(workflow_name),
    #                                 data=json.dumps(data),
    #                                 headers=self.headers,
    #                                 content_type='application/json')
    #
    #     resulting_workflow = flask_server.running_context.controller.get_workflow('test', workflow_name)
    #
    #     # compare the steps in initial and final workflow
    #     self.assertEqual(len(resulting_workflow.steps.keys()), len(list(initial_steps)))
    #     for initial_step in initial_steps:
    #         self.assertIn(initial_step['name'], resulting_workflow.steps.keys())
    #         self.assertDictEqual(initial_step, resulting_workflow.steps[initial_step['name']].as_json())
    #
    #     # assert that the file has been saved to a file
    #     workflows = [path.splitext(workflow)[0]
    #                  for workflow in os.listdir(core.config.paths.workflows_path) if workflow.endswith('.playbook')]
    #     matching_workflows = [workflow for workflow in workflows if workflow == 'test']
    #     self.assertEqual(len(matching_workflows), 1)
    #
    #     # assert that the file loads properly after being saved
    #     flask_server.running_context.controller.workflows = {}
    #     flask_server.running_context.controller.load_workflows_from_file(os.path.join(core.config.paths.workflows_path,
    #                                                                                   'test.playbook'))
    #     orderless_list_compare(self,
    #                            [key.workflow for key in flask_server.running_context.controller.workflows.keys()],
    #                            ['helloWorldWorkflow'])
    #     loaded_workflow = flask_server.running_context.controller.get_workflow('test', workflow_name)
    #
    #     # compare the steps in loaded and expected workflow
    #     self.assertEqual(len(loaded_workflow.steps.keys()), len(list(resulting_workflow.steps.keys())))
    #     for step_name, loaded_step in loaded_workflow.steps.items():
    #         self.assertIn(step_name, resulting_workflow.steps.keys())
    #         self.assertDictEqual(loaded_step.as_json(), resulting_workflow.steps[step_name].as_json())
    #
    # def test_save_workflow_invalid_app(self):
    #     workflow_name = list(flask_server.running_context.controller.workflows.keys())[0].workflow
    #     initial_workflow = flask_server.running_context.controller.get_workflow('test', workflow_name)
    #     initial_steps = [step.as_json() for step in initial_workflow.steps.values()]
    #     initial_steps[0]['position']['x'] = 0.0
    #     initial_steps[0]['position']['y'] = 0.0
    #     added_step = Step(name='new_id', app='HelloWorld', action='pause', inputs={'seconds': 5},
    #                       position={'x': 0, 'y': 0}).as_json()
    #     added_step['app'] = 'Invalid'
    #
    #     initial_steps.append(added_step)
    #     data = {"steps": initial_steps}
    #     self.post_with_status_check('/api/playbooks/test/workflows/{0}/save'.format(workflow_name),
    #                                 data=json.dumps(data),
    #                                 headers=self.headers,
    #                                 content_type='application/json',
    #                                 status_code=INVALID_INPUT_ERROR)
    #
    # def test_save_workflow_invalid_action(self):
    #     workflow_name = list(flask_server.running_context.controller.workflows.keys())[0].workflow
    #     initial_workflow = flask_server.running_context.controller.get_workflow('test', workflow_name)
    #     initial_steps = [step.as_json() for step in initial_workflow.steps.values()]
    #     initial_steps[0]['position']['x'] = 0.0
    #     initial_steps[0]['position']['y'] = 0.0
    #     added_step = Step(name='new_id', app='HelloWorld', action='pause', inputs={'seconds': 5},
    #                       position={'x': 0, 'y': 0}).as_json()
    #     added_step['action'] = 'Invalid'
    #
    #     initial_steps.append(added_step)
    #     data = {"steps": initial_steps}
    #     self.post_with_status_check('/api/playbooks/test/workflows/{0}/save'.format(workflow_name),
    #                                 data=json.dumps(data),
    #                                 headers=self.headers,
    #                                 content_type='application/json',
    #                                 status_code=INVALID_INPUT_ERROR)

    def test_save_workflow_invalid_input_name(self):
        workflow_name = list(flask_server.running_context.controller.workflows.keys())[0].workflow
        initial_workflow = flask_server.running_context.controller.get_workflow('test', workflow_name)
        initial_steps = [step.as_json() for step in initial_workflow.steps.values()]
        initial_steps[0]['position']['x'] = 0.0
        initial_steps[0]['position']['y'] = 0.0
        added_step = Step(name='new_id', app='HelloWorld', action='pause', inputs={'seconds': 5},
                          position={'x': 0, 'y': 0}).as_json()
        added_step['input'] = [{'name': 'Invalid', 'value': 5}]

        initial_steps.append(added_step)
        data = {"steps": initial_steps}
        self.post_with_status_check('/api/playbooks/test/workflows/{0}/save'.format(workflow_name),
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type='application/json',
                                    status_code=INVALID_INPUT_ERROR)

    # def test_save_workflow_invalid_input_format(self):
    #     workflow_name = list(flask_server.running_context.controller.workflows.keys())[0].workflow
    #     initial_workflow = flask_server.running_context.controller.get_workflow('test', workflow_name)
    #     initial_steps = [step.as_json() for step in initial_workflow.steps.values()]
    #     initial_steps[0]['position']['x'] = 0.0
    #     initial_steps[0]['position']['y'] = 0.0
    #     added_step = Step(name='new_id', app='HelloWorld', action='pause', inputs={'seconds': 5},
    #                       position={'x': 0, 'y': 0}).as_json()
    #     added_step['inputs'][0]['value'] = 'aaaa'
    #
    #     initial_steps.append(added_step)
    #     data = {"steps": initial_steps}
    #     self.post_with_status_check('/api/playbooks/test/workflows/{0}/save'.format(workflow_name),
    #                                 data=json.dumps(data),
    #                                 headers=self.headers,
    #                                 content_type='application/json',
    #                                 status_code=INVALID_INPUT_ERROR)
    #
    # def test_save_workflow_new_start_step(self):
    #     workflow_name = list(flask_server.running_context.controller.workflows.keys())[0].workflow
    #     initial_workflow = flask_server.running_context.controller.get_workflow('test', workflow_name)
    #     initial_steps = [step.as_json() for step in initial_workflow.steps.values()]
    #     initial_steps[0]['position']['x'] = 0.0
    #     initial_steps[0]['position']['y'] = 0.0
    #     added_step = Step(name='new_id', app='HelloWorld', action='pause', inputs={'seconds': 5},
    #                       position={'x': 0, 'y': 0}).as_json()
    #
    #     initial_steps.append(added_step)
    #     data = {"steps": initial_steps, "start": "new_start"}
    #     self.post_with_status_check('/api/playbooks/test/workflows/{0}/save'.format(workflow_name),
    #                                 data=json.dumps(data),
    #                                 headers=self.headers,
    #                                 content_type='application/json')
    #
    #     resulting_workflow = flask_server.running_context.controller.get_workflow('test', workflow_name)
    #     self.assertEqual(resulting_workflow.start_step, "new_start")
    #
    # def test_save_workflow_invalid_name(self):
    #     data = {"steps": []}
    #     self.post_with_status_check('/api/playbooks/test/workflows/junkworkflowname/save',
    #                                 error='Playbook or workflow does not exist.',
    #                                 headers=self.headers, status_code=OBJECT_DNE_ERROR, data=json.dumps(data),
    #                                 content_type="application/json")
    #
    # def test_delete_playbook(self):
    #     response = self.delete_with_status_check('/api/playbooks/test', headers=self.headers)
    #     self.assertDictEqual(response, {'playbooks': {}})
    #
    #     self.assertFalse(flask_server.running_context.controller.is_playbook_registered('test'))
    #
    #     playbooks = [os.path.splitext(playbook)[0]
    #                  for playbook in helpers.locate_workflows_in_directory(core.config.paths.workflows_path)]
    #     self.assertEqual(len(playbooks), 0)
    #
    # def test_delete_playbook_no_file(self):
    #     initial_playbooks = flask_server.running_context.controller.get_all_workflows()
    #     initial_playbook_files = [os.path.splitext(playbook)[0] for playbook in
    #                               helpers.locate_workflows_in_directory()]
    #     data = {"name": "test_playbook"}
    #     self.app.put('/api/playbooks', headers=self.headers, content_type="application/json", data=json.dumps(data))
    #     response = self.delete_with_status_check('/api/playbooks/test_playbook', headers=self.headers)
    #     self.assertDictEqual(response, {'playbooks': initial_playbooks})
    #
    #     self.assertTrue(flask_server.running_context.controller.is_playbook_registered('test'))
    #     self.assertFalse(flask_server.running_context.controller.is_playbook_registered('test_playbook'))
    #
    #     final_playbook_files = [os.path.splitext(playbook)[0] for playbook in
    #                             helpers.locate_workflows_in_directory()]
    #     orderless_list_compare(self, final_playbook_files, initial_playbook_files)
    #
    # def test_delete_playbook_invalid_name(self):
    #     initial_playbooks = flask_server.running_context.controller.get_all_workflows()
    #     initial_playbook_files = [os.path.splitext(playbook)[0] for playbook in
    #                               helpers.locate_workflows_in_directory()]
    #     response = self.delete_with_status_check('/api/playbooks/junkPlaybookName', error='Playbook does not exist.',
    #                                              headers=self.headers,
    #                                              status_code=OBJECT_DNE_ERROR)
    #     self.assertDictEqual(response, {'error': 'Playbook does not exist.', 'playbooks': initial_playbooks})
    #     self.assertFalse(flask_server.running_context.controller.is_playbook_registered('junkPlaybookName'))
    #     final_playbook_files = [os.path.splitext(playbook)[0] for playbook in
    #                             helpers.locate_workflows_in_directory()]
    #     orderless_list_compare(self, final_playbook_files, initial_playbook_files)
    #
    # def test_delete_workflow(self):
    #     workflow_name = 'test_name2'
    #     data = {"name": "test_name2"}
    #     self.app.put('/api/playbooks/test/workflows', headers=self.headers, data=json.dumps(data), content_type="application/json")
    #
    #     initial_workflow = flask_server.running_context.controller.get_workflow('test', workflow_name)
    #     initial_steps = [step.as_json() for step in initial_workflow.steps.values()]
    #
    #     data = {"steps": initial_steps}
    #     self.app.post('/api/playbooks/test/workflows/{0}/save'.format(workflow_name),
    #                   data=json.dumps(data),
    #                   headers=self.headers,
    #                   content_type='application/json')
    #     response = self.delete_with_status_check('/api/playbooks/test/workflows/{0}'.format(workflow_name),
    #                                              headers=self.headers)
    #     self.assertSetEqual(set(list(response.keys())), set(list(['playbooks'])))
    #     self.assertDictEqual(response['playbooks'], {'test': ['helloWorldWorkflow']})
    #
    #     self.assertFalse(flask_server.running_context.controller.is_workflow_registered('test', workflow_name))
    #
    # def test_delete_workflow_invalid(self):
    #     workflow_name = 'junkworkflowname'
    #     response = self.delete_with_status_check('/api/playbooks/test/workflows/{0}'.format(workflow_name),
    #                                              error='Playbook or workflow does not exist.',
    #                                              headers=self.headers, status_code=OBJECT_DNE_ERROR)
    #     self.assertSetEqual(set(list(response.keys())), set(list(['error', 'playbooks'])))
    #     self.assertDictEqual(response['playbooks'], {'test': ['helloWorldWorkflow']})
    #
    #     self.assertFalse(flask_server.running_context.controller.is_workflow_registered('test', workflow_name))
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
    # def test_copy_workflow(self):
    #     self.post_with_status_check('/api/playbooks/test/workflows/helloWorldWorkflow/copy',
    #                                 headers=self.headers, status_code=OBJECT_CREATED, data=json.dumps({}),
    #                                 content_type="application/json")
    #     self.assertEqual(len(flask_server.running_context.controller.workflows.keys()), 2)
    #     self.assertTrue(flask_server.running_context.controller.is_workflow_registered('test', 'helloWorldWorkflow'))
    #     self.assertTrue(
    #         flask_server.running_context.controller.is_workflow_registered('test', 'helloWorldWorkflow_Copy'))
    #
    #     workflow_original = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow')
    #     workflow_copy = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow_Copy')
    #     new_workflow_name = helpers.construct_workflow_name_key('test', 'helloWorldWorkflow_Copy')
    #     self.assertEqual(workflow_copy.name, new_workflow_name)
    #     copy_workflow_json = workflow_copy.as_json()
    #     original_workflow_json = workflow_original.as_json()
    #     copy_workflow_json.pop('name', None)
    #     original_workflow_json.pop('name', None)
    #     self.assertDictEqual(copy_workflow_json, original_workflow_json)
    #     self.assertEqual(len(workflow_original.steps), len(workflow_copy.steps))
    #     for step in workflow_copy.steps:
    #         self.assertEqual(new_workflow_name, workflow_copy.steps[step].ancestry[1])
    #         self.assertEqual(len(workflow_original.steps[step].conditionals),
    #                          len(workflow_copy.steps[step].conditionals))
    #         for next_step in workflow_copy.steps[step].conditionals:
    #             self.assertEqual(new_workflow_name, next_step.ancestry[1])
    #             for flag in next_step.flags:
    #                 self.assertEqual(new_workflow_name, flag.ancestry[1])
    #                 for filter_element in flag.filters:
    #                     self.assertEqual(new_workflow_name, filter_element.ancestry[1])
    #
    # def test_copy_workflow_invalid_name(self):
    #     data = {"workflow": "helloWorldWorkflow"}
    #     self.post_with_status_check('/api/playbooks/test/workflows/helloWorldWorkflow/copy',
    #                                 error='Playbook or workflow already exists.', data=json.dumps(data),
    #                                 headers=self.headers, status_code=OBJECT_EXISTS_ERROR, content_type="application/json")
    #
    #     self.assertEqual(len(flask_server.running_context.controller.workflows.keys()), 1)
    #     self.assertTrue(flask_server.running_context.controller.is_workflow_registered('test', 'helloWorldWorkflow'))
    #
    # def test_copy_workflow_different_playbook(self):
    #     data = {"name": "new_playbook"}
    #     self.put_with_status_check('/api/playbooks', headers=self.headers,
    #                                status_code=OBJECT_CREATED, content_type="application/json", data=json.dumps(data))
    #     data = {"playbook": "new_playbook"}
    #     self.post_with_status_check('/api/playbooks/test/workflows/helloWorldWorkflow/copy', data=json.dumps(data),
    #                                 headers=self.headers, status_code=OBJECT_CREATED, content_type="application/json")
    #
    #     self.assertEqual(len(flask_server.running_context.controller.workflows.keys()), 3)
    #     self.assertTrue(flask_server.running_context.controller.is_workflow_registered('test', 'helloWorldWorkflow'))
    #     self.assertTrue(
    #         flask_server.running_context.controller.is_workflow_registered('new_playbook', 'helloWorldWorkflow_Copy'))
    #
    #     workflow_original = flask_server.running_context.controller.get_workflow('test', 'helloWorldWorkflow')
    #     workflow_copy = flask_server.running_context.controller.get_workflow('new_playbook', 'helloWorldWorkflow_Copy')
    #     new_workflow_name = helpers.construct_workflow_name_key('new_playbook', 'helloWorldWorkflow_Copy')
    #     self.assertEqual(workflow_copy.name, new_workflow_name)
    #     copy_workflow_json = workflow_copy.as_json()
    #     original_workflow_json = workflow_original.as_json()
    #     copy_workflow_json.pop('name', None)
    #     original_workflow_json.pop('name', None)
    #     self.assertDictEqual(copy_workflow_json, original_workflow_json)
    #
    #     self.assertEqual(len(workflow_original.steps), len(workflow_copy.steps))
    #     for step in workflow_copy.steps:
    #         self.assertTrue(new_workflow_name in workflow_copy.steps[step].ancestry)
    #         self.assertEqual(len(workflow_original.steps[step].conditionals),
    #                          len(workflow_copy.steps[step].conditionals))
    #         for nextstep in workflow_copy.steps[step].conditionals:
    #             self.assertTrue(new_workflow_name in nextstep.ancestry)
    #             for flag in nextstep.flags:
    #                 self.assertTrue(new_workflow_name in flag.ancestry)
    #                 for filter_element in flag.filters:
    #                     self.assertTrue(new_workflow_name in filter_element.ancestry)
    #
    # def test_copy_playbook(self):
    #     self.post_with_status_check('/api/playbooks/test/copy',
    #                                 headers=self.headers, status_code=OBJECT_CREATED, data=json.dumps({}),
    #                                 content_type="application/json")
    #
    #     self.assertEqual(len(flask_server.running_context.controller.get_all_playbooks()), 2)
    #     self.assertTrue(flask_server.running_context.controller.is_playbook_registered('test'))
    #     self.assertTrue(flask_server.running_context.controller.is_playbook_registered('test_Copy'))
    #
    #     workflows_original = flask_server.running_context.controller.get_all_workflows_by_playbook('test')
    #     workflows_copy = flask_server.running_context.controller.get_all_workflows_by_playbook('test_Copy')
    #
    #     self.assertEqual(len(workflows_original), len(workflows_copy))
    #
    # def test_copy_playbook_invalid_name(self):
    #     data = {"playbook": "test"}
    #     self.post_with_status_check('/api/playbooks/test/copy', error='Playbook already exists.', data=json.dumps(data),
    #                                 headers=self.headers, status_code=OBJECT_EXISTS_ERROR, content_type="application/json")
    #
    #     self.assertEqual(len(flask_server.running_context.controller.get_all_playbooks()), 1)
    #     self.assertTrue(flask_server.running_context.controller.is_playbook_registered('test'))
    #
    # def test_execute_workflow_playbook_dne(self):
    #     self.post_with_status_check('/api/playbooks/junkPlay/workflows/helloWorldWorkflow/execute',
    #                                 error='Playbook or workflow does not exist.',
    #                                 headers=self.headers, status_code=OBJECT_DNE_ERROR)
    #
    # def test_execute_workflow_workflow_dne(self):
    #     self.post_with_status_check('/api/playbooks/test/workflows/junkWorkflow/execute',
    #                                 error='Playbook or workflow does not exist.',
    #                                 headers=self.headers, status_code=OBJECT_DNE_ERROR)
    #
    # def test_execute_workflow(self):
    #     sync = Event()
    #     workflow_name = helpers.construct_workflow_name_key('test', 'helloWorldWorkflow')
    #     setup_subscriptions_for_step(workflow_name, ['start'])
    #     start = datetime.utcnow()
    #
    #     def wait_for_completion(sender, **kwargs):
    #         sync.set()
    #
    #     WorkflowShutdown.connect(wait_for_completion)
    #
    #     response = self.post_with_status_check('/api/playbooks/test/workflows/helloWorldWorkflow/execute',
    #                                            headers=self.headers,
    #                                            status_code=SUCCESS_ASYNC)
    #     self.assertIn('id', response)
    #     sync.wait(timeout=10)
    #     steps = executed_steps('defaultController', workflow_name, start, datetime.utcnow())
    #     self.assertEqual(len(steps), 1)
    #     step = steps[0]
    #     ancestry = step['ancestry'].split(',')
    #     self.assertEqual(ancestry[-1], "start")
    #     result = json.loads(step['data'])
    #     self.assertEqual(result['result'], {'status': 'Success', 'result': 'REPEATING: Hello World'})
    #
    # # TODO: FIX THIS TEST
    # def test_execute_workflow_in_memory(self):
    #     sync = Event()
    #     data = {"playbook_template": 'basicWorkflow',
    #             "workflow_template": 'helloWorldWorkflow',
    #             "name": "test_name"}
    #
    #     def wait_for_completion(sender, **kwargs):
    #         sync.set()
    #
    #     WorkflowShutdown.connect(wait_for_completion)
    #
    #     self.put_with_status_check('/api/playbooks/basicWorkflow/workflows',
    #                                data=json.dumps(data), headers=self.headers, status_code=OBJECT_CREATED,
    #                                content_type="application/json")
    #
    #     workflow_name = helpers.construct_workflow_name_key('basicWorkflow', 'test_name')
    #     setup_subscriptions_for_step(workflow_name, ['start'])
    #     start = datetime.utcnow()
    #     response = self.post_with_status_check('/api/playbooks/basicWorkflow/workflows/test_name/execute',
    #                                            headers=self.headers,
    #                                            status_code=SUCCESS_ASYNC)
    #     self.assertIn('id', response)
    #     sync.wait(timeout=10)
    #     steps = executed_steps('defaultController', workflow_name, start, datetime.utcnow())
    #     self.assertEqual(len(steps), 1)
    #     step = steps[0]
    #     ancestry = step['ancestry'].split(',')
    #     self.assertEqual(ancestry[-1], "start")
    #     result = json.loads(step['data'])
    #     self.assertDictEqual(result['result'], {'status': 'Success', 'result': 'REPEATING: Hello World'})
    #
    # def test_read_results(self):
    #     server.workflowresults.results.clear()
    #     self.app.post('/api/playbooks/test/workflows/helloWorldWorkflow/execute', headers=self.headers)
    #     self.app.post('/api/playbooks/test/workflows/helloWorldWorkflow/execute', headers=self.headers)
    #     self.app.post('/api/playbooks/test/workflows/helloWorldWorkflow/execute', headers=self.headers)
    #
    #     with flask_server.running_context.flask_app.app_context():
    #         flask_server.running_context.shutdown_threads()
    #
    #     response = self.get_with_status_check('/workflowresults', headers=self.headers)
    #     self.assertEqual(len(response), 3)
    #     for result in response:
    #         self.assertIn('timestamp', result)
    #         self.assertIn('result', result)
    #         self.assertIn('name', result)
    #
    # def test_read_all_results(self):
    #     server.workflowresults.results.clear()
    #     self.app.post('/api/playbooks/test/workflows/helloWorldWorkflow/execute', headers=self.headers)
    #     self.app.post('/api/playbooks/test/workflows/helloWorldWorkflow/execute', headers=self.headers)
    #     self.app.post('/api/playbooks/test/workflows/helloWorldWorkflow/execute', headers=self.headers)
    #
    #     with flask_server.running_context.flask_app.app_context():
    #         flask_server.running_context.shutdown_threads()
    #
    #     response = self.get_with_status_check('/workflowresults/all', headers=self.headers)
    #     self.assertEqual(len(response), 3)
    #
    #     for result in response.values():
    #         self.assertSetEqual(set(result.keys()), {'status', 'completed_at', 'started_at', 'name', 'results'})
    #         for step_result in result['results']:
    #             self.assertSetEqual(set(step_result.keys()), {'input', 'type', 'name', 'timestamp', 'result'})
