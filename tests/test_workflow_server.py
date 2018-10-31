import json
import os
from uuid import uuid4, UUID

from tests.util import execution_db_help
from tests.util.servertestcase import ServerTestCase
from walkoff.executiondb.playbook import Playbook
from walkoff.executiondb.schemas import PlaybookSchema, WorkflowSchema
from walkoff.executiondb.workflow import Workflow
from walkoff.server.returncodes import *


class TestWorkflowServer(ServerTestCase):

    def setUp(self):
        self.add_playbook_name = 'add_playbook'
        self.change_playbook_name = 'change_playbook'
        self.add_workflow_name = 'add_workflow'
        self.change_workflow_name = 'change_workflow'
        action_id = str(uuid4())
        self.empty_workflow_json = \
            {'actions': [
                {"app_name": "HelloWorld",
                 "action_name": "helloWorld",
                 "name": "helloworld",
                 "id": action_id,
                 "arguments": []}],
                'name': self.add_workflow_name,
                'start': action_id,
                'branches': [],
                'environment_variables': []}
        self.verb_lookup = {'get': self.get_with_status_check,
                            'put': self.put_with_status_check,
                            'post': self.post_with_status_check,
                            'delete': self.delete_with_status_check,
                            'patch': self.patch_with_status_check}

    def tearDown(self):
        execution_db_help.cleanup_execution_db()

    @staticmethod
    def strip_ids(element):
        element.pop('id', None)
        for key, value in element.items():
            if isinstance(value, list):
                for list_element in (list_element_ for list_element_ in value if isinstance(list_element_, dict)):
                    TestWorkflowServer.strip_ids(list_element)
            elif isinstance(value, dict):
                for dict_element in (element for element in value.values() if isinstance(element, dict)):
                    TestWorkflowServer.strip_ids(dict_element)
        return element

    def check_invalid_uuid(self, verb, path, element_type, **kwargs):
        self.verb_lookup[verb](path, headers=self.headers, status_code=BAD_REQUEST, **kwargs)

    def check_invalid_id(self, verb, path, element_type, **kwargs):
        self.verb_lookup[verb](path, headers=self.headers, status_code=OBJECT_DNE_ERROR, **kwargs)

    def test_read_all_playbooks(self):
        playbook_names = ['basicWorkflowTest', 'dataflowTest']
        execution_db_help.load_playbooks(playbook_names)
        response = self.get_with_status_check('/api/playbooks', headers=self.headers)
        for playbook in response:
            for workflow in playbook['workflows']:
                workflow.pop('id')
        self.assertEqual(len(response), len(playbook_names))
        for playbook in response:
            self.assertIn(playbook['name'], playbook_names)

    # All the reads

    def test_read_playbook(self):
        playbook = execution_db_help.standard_load()
        response = self.get_with_status_check('/api/playbooks/{}'.format(playbook.id), headers=self.headers)
        expected_workflows = [self.strip_ids(WorkflowSchema().dump(workflow).data) for workflow in playbook.workflows]
        self.assertEqual(response['name'], 'test')
        self.assertEqual(len(response['workflows']), len(expected_workflows))
        self.assertListEqual([self.strip_ids(workflow) for workflow in response['workflows']], expected_workflows)

    def test_read_playbook_invalid_id(self):
        self.check_invalid_id('get', '/api/playbooks/{}'.format(uuid4()), 'playbook')

    def test_read_playbook_invalid_id_format(self):
        self.check_invalid_uuid('get', '/api/playbooks/0', 'playbook')

    def test_read_workflows(self):
        execution_db_help.standard_load()
        workflows = {str(workflow.id) for workflow in
                     self.app.running_context.execution_db.session.query(Workflow).all()}
        response = self.get_with_status_check('/api/workflows', headers=self.headers)
        self.assertSetEqual({workflow['id'] for workflow in response}, workflows)

    def test_read_playbook_workflows(self):
        playbook = execution_db_help.standard_load()
        response = self.get_with_status_check('/api/playbooks/{}/workflows'.format(playbook.id), headers=self.headers)

        expected_workflows = [self.strip_ids(WorkflowSchema().dump(workflow).data) for workflow in playbook.workflows]

        self.assertEqual(len(response), len(expected_workflows))
        self.assertListEqual([self.strip_ids(workflow) for workflow in response], expected_workflows)

    def test_read_playbook_workflows_invalid_id(self):
        self.check_invalid_id('get', '/api/playbooks/{}/workflows'.format(uuid4()), 'playbook')

    def test_read_playbook_workflows_invalid_id_format(self):
        self.check_invalid_uuid('get', '/api/playbooks/0/workflows', 'playbook')

    def test_read_playbook_workflows_from_query(self):
        playbook = execution_db_help.standard_load()
        response = self.get_with_status_check('/api/workflows?playbook={}'.format(playbook.id), headers=self.headers)

        expected_workflows = [self.strip_ids(WorkflowSchema().dump(workflow).data) for workflow in playbook.workflows]

        self.assertEqual(len(response), len(expected_workflows))
        self.assertListEqual([self.strip_ids(workflow) for workflow in response], expected_workflows)

    def test_read_playbook_workflows_invalid_id_from_query(self):
        self.check_invalid_id('get', '/api/workflows?playbook={}'.format(uuid4()), 'playbook')

    def test_read_playbook_workflows_invalid_id_format_from_query(self):
        self.check_invalid_uuid('get', '/api/workflows?playbook=0', 'playbook')

    def test_read_workflow(self):
        playbook = execution_db_help.standard_load()
        target_workflow = playbook.workflows[0]
        response = self.get_with_status_check(
            '/api/workflows/{}'.format(target_workflow.id),
            headers=self.headers)
        self.assertDictEqual(self.strip_ids(response), self.strip_ids(WorkflowSchema().dump(target_workflow).data))

    def test_read_workflow_invalid_workflow_id(self):
        self.check_invalid_id('get', '/api/workflows/{}'.format(uuid4()), 'workflow')

    def test_read_workflow_invalid_workflow_id_format(self):
        execution_db_help.standard_load()
        self.check_invalid_uuid('get', '/api/workflows/42', 'workflow')

    # All the deletes

    def test_delete_playbook(self):
        playbook = execution_db_help.standard_load()
        self.delete_with_status_check('/api/playbooks/{}'.format(playbook.id), headers=self.headers,
                                      status_code=NO_CONTENT)

        self.assertIsNone(
            self.app.running_context.execution_db.session.query(Playbook).filter_by(id=playbook.id).first())

    def test_delete_playbook_invalid_id(self):
        execution_db_help.standard_load()
        previous_num_playbooks = len(self.app.running_context.execution_db.session.query(Playbook).all())
        self.check_invalid_id('delete', '/api/playbooks/{}'.format(uuid4()), 'playbook')
        self.assertEqual(previous_num_playbooks,
                         len(self.app.running_context.execution_db.session.query(Playbook).all()))

    def test_delete_playbook_invalid_id_format(self):
        execution_db_help.standard_load()
        previous_num_playbooks = len(self.app.running_context.execution_db.session.query(Playbook).all())
        self.check_invalid_id('delete', '/api/playbooks/{}'.format(uuid4()), 'playbook')
        self.assertEqual(previous_num_playbooks,
                         len(self.app.running_context.execution_db.session.query(Playbook).all()))

    def test_delete_workflow(self):
        execution_db_help.standard_load()

        workflows = [Workflow('wf{}'.format(i), uuid4()) for i in range(2)]

        for workflow in workflows:
            self.app.running_context.execution_db.session.add(workflow)

        target_playbook = Playbook('play1', workflows=workflows)
        self.app.running_context.execution_db.session.add(target_playbook)
        self.app.running_context.execution_db.session.flush()
        workflow_ids = [workflow.id for workflow in workflows]
        original_num_playbooks = len(self.app.running_context.execution_db.session.query(Playbook).all())
        self.delete_with_status_check('/api/workflows/{}'.format(workflow_ids[0]),

                                      headers=self.headers, status_code=NO_CONTENT)
        self.assertEqual(len(list(target_playbook.workflows)), len(workflow_ids) - 1)
        self.assertNotIn(workflow_ids[0], [workflow.id for workflow in target_playbook.workflows])
        self.assertEqual(len(self.app.running_context.execution_db.session.query(Playbook).all()),
                         original_num_playbooks)

    def test_delete_last_workflow(self):
        execution_db_help.standard_load()

        workflow = Workflow('wf', uuid4())
        self.app.running_context.execution_db.session.add(workflow)
        target_playbook = Playbook('play1', workflows=[workflow])
        self.app.running_context.execution_db.session.add(target_playbook)
        self.app.running_context.execution_db.session.flush()
        original_num_playbooks = len(self.app.running_context.execution_db.session.query(Playbook).all())
        self.delete_with_status_check('/api/workflows/{}'.format(workflow.id),
                                      headers=self.headers, status_code=NO_CONTENT)
        self.assertIsNone(self.app.running_context.execution_db.session.query(Playbook).filter_by(name='play1').first())
        self.assertEqual(len(self.app.running_context.execution_db.session.query(Playbook).all()),
                         original_num_playbooks - 1)

    def test_delete_workflow_invalid_workflow_id(self):
        execution_db_help.standard_load()
        original_num_playbooks = len(self.app.running_context.execution_db.session.query(Playbook).all())
        self.check_invalid_id('delete', '/api/workflows/{}'.format(uuid4()), 'workflow')
        self.assertEqual(len(self.app.running_context.execution_db.session.query(Playbook).all()),
                         original_num_playbooks)

    def test_delete_workflow_invalid_workflow_id_format(self):
        execution_db_help.standard_load()
        original_num_playbooks = len(self.app.running_context.execution_db.session.query(Playbook).all())
        self.check_invalid_uuid('delete', '/api/workflows/37b', 'workflow')
        self.assertEqual(len(self.app.running_context.execution_db.session.query(Playbook).all()),
                         original_num_playbooks)

    # All the creates

    def test_create_playbook(self):
        expected_playbooks = self.app.running_context.execution_db.session.query(Playbook).all()
        original_length = len(list(expected_playbooks))
        start = str(uuid4())
        data = {"name": self.add_playbook_name, 'workflows': [{'name': 'wf1', 'start': start}]}
        self.update_playbooks = True
        response = self.post_with_status_check('/api/playbooks', headers=self.headers,
                                               status_code=OBJECT_CREATED, data=json.dumps(data),
                                               content_type="application/json")
        response.pop('id')
        response['workflows'][0].pop('id')
        self.assertDictEqual(response, {'name': self.add_playbook_name,
                                        'workflows': [{'name': 'wf1', 'start': start, 'is_valid': True}]})
        self.assertEqual(len(list(self.app.running_context.execution_db.session.query(Playbook).all())),
                         original_length + 1)

    def test_create_playbook_already_exists(self):
        data = {"name": self.add_playbook_name}
        self.post_with_status_check('/api/playbooks',
                                    data=json.dumps(data), headers=self.headers, status_code=OBJECT_CREATED,
                                    content_type="application/json")
        self.post_with_status_check('/api/playbooks',
                                    error='Unique constraint failed.',
                                    data=json.dumps(data), headers=self.headers, status_code=OBJECT_EXISTS_ERROR,
                                    content_type="application/json")

    def test_create_playbook_bad_id_in_workflow(self):
        workflow = Workflow('wf1', uuid4())
        self.app.running_context.execution_db.session.add(workflow)
        self.app.running_context.execution_db.session.flush()
        workflow_json = WorkflowSchema().dump(workflow).data
        workflow_json['id'] = 'garbage'
        data = {'name': self.add_playbook_name, 'workflows': [workflow_json]}
        self.post_with_status_check('/api/playbooks',
                                    data=json.dumps(data), headers=self.headers, status_code=BAD_REQUEST,
                                    content_type="application/json")

    def test_create_workflow(self):
        playbook = execution_db_help.standard_load()
        initial_workflows_len = len(playbook.workflows)
        self.empty_workflow_json['playbook_id'] = str(playbook.id)
        response = self.post_with_status_check('/api/workflows',
                                               headers=self.headers, status_code=OBJECT_CREATED,
                                               data=json.dumps(self.empty_workflow_json),
                                               content_type="application/json")

        self.empty_workflow_json['id'] = response['id']

        final_workflows = playbook.workflows
        self.assertEqual(len(final_workflows), initial_workflows_len + 1)

        workflow = next((workflow for workflow in final_workflows if workflow.name == self.add_workflow_name), None)
        self.assertIsNotNone(workflow)

    def test_create_workflow_invalid_id_format(self):
        self.empty_workflow_json['playbook_id'] = '87fgb'
        self.check_invalid_uuid('post', '/api/workflows', 'playbook',
                                data=json.dumps(self.empty_workflow_json),
                                content_type="application/json")

    def test_create_workflow_with_errors(self):
        playbook = execution_db_help.standard_load()
        self.empty_workflow_json['actions'][0]['action_name'] = 'invalid'
        self.empty_workflow_json['start'] = str(uuid4())
        self.empty_workflow_json['playbook_id'] = str(playbook.id)
        response = self.post_with_status_check('/api/workflows',
                                               headers=self.headers, status_code=OBJECT_CREATED,
                                               data=json.dumps(self.empty_workflow_json),
                                               content_type="application/json")
        self.assertEqual(len(response['errors']), 1)
        self.assertEqual(len(response['actions'][0]['errors']), 1)

    def test_create_workflow_with_env_vars(self):
        playbook = execution_db_help.standard_load()
        self.empty_workflow_json['playbook_id'] = str(playbook.id)
        self.empty_workflow_json['environment_variables'].append({'name': 'call', 'value': 'changeme',
                                                                  'description': 'test description'})
        self.post_with_status_check('/api/workflows',
                                    headers=self.headers, status_code=OBJECT_CREATED,
                                    data=json.dumps(self.empty_workflow_json),
                                    content_type="application/json")

        final_workflows = playbook.workflows
        workflow = next((workflow for workflow in final_workflows if workflow.name == self.add_workflow_name), None)

        self.assertEqual(len(workflow.environment_variables), 1)
        self.assertIsNotNone(workflow.environment_variables[0].id)
        self.assertEqual(workflow.environment_variables[0].name, 'call')
        self.assertEqual(workflow.environment_variables[0].value, 'changeme')
        self.assertEqual(workflow.environment_variables[0].description, 'test description')

    # All the updates

    def test_update_playbook_name(self):
        playbook = execution_db_help.standard_load()

        data = {'id': str(playbook.id), 'name': self.change_playbook_name}
        response = self.patch_with_status_check('/api/playbooks',
                                                data=json.dumps(data),
                                                headers=self.headers,
                                                content_type='application/json')
        self.assertEqual(response['name'], self.change_playbook_name)

    def test_update_playbook_duplicate_name(self):
        playbook = execution_db_help.standard_load()

        data = {'id': str(playbook.id), 'name': 'dataflowTest'}
        self.patch_with_status_check('/api/playbooks',
                                     data=json.dumps(data),
                                     headers=self.headers,
                                     content_type='application/json',
                                     status_code=OBJECT_EXISTS_ERROR)

    def test_update_playbook_invalid_id(self):
        execution_db_help.standard_load()
        expected = {playbook.name for playbook in self.app.running_context.execution_db.session.query(Playbook).all()}
        data = {'id': str(uuid4()), 'name': self.change_playbook_name}
        self.check_invalid_id('patch', '/api/playbooks', 'playbook', content_type="application/json",
                              data=json.dumps(data))
        self.assertSetEqual(
            {playbook.name for playbook in self.app.running_context.execution_db.session.query(Playbook).all()},
            expected)

    def test_update_playbook_invalid_id_format(self):
        execution_db_help.standard_load()
        expected = {playbook.name for playbook in self.app.running_context.execution_db.session.query(Playbook).all()}
        data = {'id': '475', 'name': self.change_playbook_name}
        self.check_invalid_uuid('patch', '/api/playbooks', 'playbook', content_type="application/json",
                                data=json.dumps(data))
        self.assertSetEqual(
            {playbook.name for playbook in self.app.running_context.execution_db.session.query(Playbook).all()},
            expected)

    def test_update_workflow(self):
        from walkoff.executiondb.schemas import WorkflowSchema
        playbook = execution_db_help.standard_load()
        workflow = playbook.workflows[0]
        expected_json = WorkflowSchema().dump(workflow).data
        expected_json['name'] = self.change_workflow_name
        response = self.put_with_status_check('/api/workflows',
                                              data=json.dumps(expected_json),
                                              headers=self.headers,
                                              content_type='application/json')

        self.assertDictEqual(response, expected_json)

        self.assertIsNotNone(
            self.app.running_context.execution_db.session.query(Workflow).filter_by(id=workflow.id).first())
        self.assertIsNone(
            self.app.running_context.execution_db.session.query(Workflow).join(Workflow.playbook).filter(
                Workflow.name == self.add_workflow_name).first())

    def test_update_workflow_invalid_new_workflow(self):
        from walkoff.executiondb.schemas import WorkflowSchema
        from walkoff.executiondb import ExecutionDatabase
        playbook = execution_db_help.standard_load()
        workflow = playbook.workflows[0]
        expected_json = WorkflowSchema().dump(workflow).data
        expected_json['name'] = self.change_workflow_name
        expected_json['actions'][0]['action_name'] = 'invalid'
        response = self.put_with_status_check('/api/workflows',
                                              data=json.dumps(expected_json),
                                              headers=self.headers,
                                              content_type='application/json')
        errors = response['actions'][0].pop('errors')
        self.assertEqual(len(errors), 1)
        self.assertDictEqual(response, expected_json)

        self.assertIsNotNone(
            ExecutionDatabase.instance.session.query(Workflow).filter_by(id=workflow.id).first())
        self.assertIsNone(
            ExecutionDatabase.instance.session.query(Workflow).join(Workflow.playbook).filter(
                Workflow.name == self.add_workflow_name).first())

    def test_copy_workflow(self):
        playbook = execution_db_help.standard_load()
        for workflow in playbook.workflows:
            workflow_id = workflow.id
        response = self.post_with_status_check('/api/workflows?source={0}'.format(workflow_id),
                                               headers=self.headers, status_code=OBJECT_CREATED,
                                               data=json.dumps(
                                                   {'name': self.add_workflow_name, 'playbook_id': str(playbook.id)}),
                                               content_type="application/json")
        self.assertEqual(len(playbook.workflows), 2)

        for workflow in playbook.workflows:
            self.assertIn(workflow.name, ['helloWorldWorkflow', self.add_workflow_name])
            if workflow.name == 'helloWorldWorkflow':
                workflow_original = workflow
            elif workflow.name == self.add_workflow_name:
                workflow_copy = workflow

        copy_workflow_json = WorkflowSchema().dump(workflow_copy).data
        original_workflow_json = WorkflowSchema().dump(workflow_original).data
        copy_workflow_json.pop('name', None)
        original_workflow_json.pop('name', None)
        self.assertNotEqual(original_workflow_json['start'], copy_workflow_json['start'])
        copy_workflow_json.pop('start')
        original_workflow_json.pop('start')
        self.assertEqual(len(workflow_original.actions), len(workflow_copy.actions))

    def test_copy_workflow_different_playbook(self):
        playbook = execution_db_help.standard_load()
        for workflow in playbook.workflows:
            workflow_id = workflow.id

        transfer_playbook = self.app.running_context.execution_db.session.query(Playbook).filter_by(
            name='dataflowTest').first()

        data = {"name": self.add_workflow_name, "playbook_id": str(transfer_playbook.id)}
        self.post_with_status_check('/api/workflows?source={}'.format(workflow_id),
                                    data=json.dumps(data),
                                    headers=self.headers, status_code=OBJECT_CREATED, content_type="application/json")

        for workflow in playbook.workflows:
            if workflow.name == 'helloWorldWorkflow':
                original_workflow = workflow
        copy_workflow = self.app.running_context.execution_db.session.query(Workflow).filter_by(
            name=self.add_workflow_name).first()

        self.assertEqual(len(playbook.workflows), 1)
        self.assertEqual(len(transfer_playbook.workflows), 2)
        self.assertIsNotNone(copy_workflow)

        self.assertNotEqual(original_workflow.start, copy_workflow.start)
        self.assertEqual(len(original_workflow.actions), len(copy_workflow.actions))

    def test_copy_playbook(self):
        playbook = execution_db_help.standard_load()

        data = {"name": self.add_playbook_name}
        self.post_with_status_check('/api/playbooks?source={}'.format(playbook.id),
                                    data=json.dumps(data),
                                    headers=self.headers, status_code=OBJECT_CREATED, content_type="application/json")

        copy_playbook = self.app.running_context.execution_db.session.query(Playbook).filter_by(
            name=self.add_playbook_name).first()

        self.assertIsNotNone(copy_playbook)

        self.assertEqual(len(playbook.workflows), len(copy_playbook.workflows))

    def test_copy_playbook_duplicate_name(self):
        playbook = execution_db_help.standard_load()

        data = {"name": 'dataflowTest'}
        self.post_with_status_check('/api/playbooks?source={}'.format(playbook.id),
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    status_code=OBJECT_EXISTS_ERROR,
                                    content_type="application/json")

    def test_get_uuid(self):
        response = self.get_with_status_check('/api/uuid', status_code=OBJECT_CREATED)
        self.assertIn('uuid', response)
        UUID(response['uuid'])

    def test_import_workflow(self):
        path = os.path.join(self.conf.WORKFLOWS_PATH, 'basicWorkflowTest.playbook')
        files = {'file': (path, open(path, 'r'), 'application/json')}

        response = self.post_with_status_check('/api/playbooks', headers=self.headers, status_code=OBJECT_CREATED,
                                               data=files, content_type='multipart/form-data')
        playbook = self.app.running_context.execution_db.session.query(Playbook).filter_by(id=response['id']).first()
        self.assertIsNotNone(playbook)
        self.assertDictEqual(PlaybookSchema().dump(playbook).data, response)

    def test_export_workflow(self):
        from walkoff.helpers import strip_device_ids, strip_argument_ids
        playbook = execution_db_help.standard_load()

        response = self.get_with_status_check('/api/playbooks/{}?mode=export'.format(playbook.id), headers=self.headers)
        expected = PlaybookSchema().dump(playbook).data
        strip_device_ids(expected)
        strip_argument_ids(expected)
        self.assertDictEqual(response, expected)
