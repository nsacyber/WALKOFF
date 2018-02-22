import json
import walkoff.case.database as case_database
from walkoff.server.returncodes import *
from tests.util.servertestcase import ServerTestCase
import walkoff.executiondb.devicedb as devicedb
from walkoff.executiondb.playbook import Playbook
from walkoff.executiondb.workflow import Workflow
from uuid import uuid4, UUID
from tests.util import device_db_help
import os
from tests.config import test_workflows_path


class TestWorkflowServer(ServerTestCase):

    def setUp(self):
        self.add_playbook_name = 'add_playbook'
        self.change_playbook_name = 'change_playbook'
        self.add_workflow_name = 'add_workflow'
        self.change_workflow_name = 'change_workflow'
        self.empty_workflow_json = \
            {'actions': [
                {"app_name": "HelloWorld", "action_name": "helloWorld", "name": "helloworld", "id": str(uuid4()),
                 "arguments": []}],
                'name': self.add_workflow_name,
                'start': str(uuid4()),
                'branches': []}
        self.verb_lookup = {'get': self.get_with_status_check,
                            'put': self.put_with_status_check,
                            'post': self.post_with_status_check,
                            'delete': self.delete_with_status_check,
                            'patch': self.patch_with_status_check}

        case_database.initialize()

    def tearDown(self):
        device_db_help.cleanup_device_db()

        case_database.case_db.session.query(case_database.Event).delete()
        case_database.case_db.session.query(case_database.Case).delete()
        case_database.case_db.session.commit()

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
        self.verb_lookup[verb](path, headers=self.headers,status_code=OBJECT_DNE_ERROR, **kwargs)

    def test_read_all_playbooks(self):
        playbook_names = ['basicWorkflowTest', 'dataflowTest']
        device_db_help.load_playbooks(playbook_names)
        response = self.get_with_status_check('/api/playbooks', headers=self.headers)
        for playbook in response:
            for workflow in playbook['workflows']:
                workflow.pop('id')
        self.assertEqual(len(response), len(playbook_names))
        for playbook in response:
            self.assertIn(playbook['name'], playbook_names)

    # All the reads

    def test_read_playbook(self):
        playbook = device_db_help.standard_load()
        response = self.get_with_status_check('/api/playbooks/{}'.format(playbook.id), headers=self.headers)

        expected_workflows = [self.strip_ids(workflow.read()) for workflow in playbook.workflows]

        self.assertEqual(response['name'], 'test')
        self.assertEqual(len(response['workflows']), len(expected_workflows))
        self.assertListEqual([self.strip_ids(workflow) for workflow in response['workflows']], expected_workflows)

    def test_read_playbook_invalid_id(self):
        self.check_invalid_id('get', '/api/playbooks/{}'.format(uuid4()), 'playbook')

    def test_read_playbook_invalid_id_format(self):
        self.check_invalid_uuid('get', '/api/playbooks/0', 'playbook')

    def test_read_playbook_workflows(self):
        playbook = device_db_help.standard_load()
        response = self.get_with_status_check('/api/playbooks/{}/workflows'.format(playbook.id), headers=self.headers)

        expected_workflows = [self.strip_ids(workflow.read()) for workflow in playbook.workflows]

        self.assertEqual(len(response), len(expected_workflows))
        self.assertListEqual([self.strip_ids(workflow) for workflow in response], expected_workflows)

    def test_read_playbook_workflows_invalid_id(self):
        self.check_invalid_id('get', '/api/playbooks/{}/workflows'.format(uuid4()), 'playbook')

    def test_read_playbook_workflows_invalid_id_format(self):
        self.check_invalid_uuid('get', '/api/playbooks/0/workflows', 'playbook')

    def test_read_workflow(self):
        playbook = device_db_help.standard_load()
        target_workflow = playbook.workflows[0]
        response = self.get_with_status_check(
            '/api/playbooks/{0}/workflows/{1}'.format(playbook.id, target_workflow.id),
            headers=self.headers)
        self.assertDictEqual(self.strip_ids(response), self.strip_ids(target_workflow.read()))

    def test_read_workflow_invalid_playbook_id(self):
        playbook = device_db_help.standard_load()
        target_workflow = playbook.workflows[0]
        self.check_invalid_id('get', '/api/playbooks/{0}/workflows/{1}'.format(uuid4(), target_workflow.id), 'workflow')

    def test_read_workflow_invalid_workflow_id(self):
        playbook = device_db_help.standard_load()
        self.check_invalid_id('get', '/api/playbooks/{0}/workflows/{1}'.format(playbook.id, uuid4()), 'workflow')

    def test_read_workflow_invalid_playbook_and_workflow_id(self):
        self.check_invalid_id('get', '/api/playbooks/{0}/workflows/{1}'.format(uuid4(), uuid4()), 'workflow')

    def test_read_workflow_invalid_playbook_id_format(self):
        playbook = device_db_help.standard_load()
        target_workflow = playbook.workflows[0]
        self.check_invalid_uuid('get', '/api/playbooks/1/workflows/{}'.format(target_workflow.id), 'workflow')

    def test_read_workflow_invalid_workflow_id_format(self):
        playbook = device_db_help.standard_load()
        self.check_invalid_uuid('get', '/api/playbooks/{}/workflows/42'.format(playbook.id), 'workflow')

    def test_read_workflow_invalid_playbook_and_workflow_id_format(self):
        self.check_invalid_uuid('get', '/api/playbooks/10/workflows/75a', 'workflow')

    # All the deletes

    def test_delete_playbook(self):
        playbook = device_db_help.standard_load()
        self.delete_with_status_check('/api/playbooks/{}'.format(playbook.id), headers=self.headers,
                                      status_code=NO_CONTENT)

        self.assertIsNone(
            devicedb.device_db.session.query(Playbook).filter_by(id=playbook.id).first())

    def test_delete_playbook_invalid_id(self):
        device_db_help.standard_load()
        previous_num_playbooks = len(devicedb.device_db.session.query(Playbook).all())
        self.check_invalid_id('delete', '/api/playbooks/{}'.format(uuid4()), 'playbook')
        self.assertEqual(previous_num_playbooks, len(devicedb.device_db.session.query(Playbook).all()))

    def test_delete_playbook_invalid_id_format(self):
        device_db_help.standard_load()
        previous_num_playbooks = len(devicedb.device_db.session.query(Playbook).all())
        self.check_invalid_id('delete', '/api/playbooks/{}'.format(uuid4()), 'playbook')
        self.assertEqual(previous_num_playbooks, len(devicedb.device_db.session.query(Playbook).all()))

    def test_delete_workflow(self):
        device_db_help.standard_load()

        workflows = [Workflow('wf{}'.format(i), uuid4()) for i in range(2)]

        for workflow in workflows:
            devicedb.device_db.session.add(workflow)

        target_playbook = Playbook('play1', workflows=workflows)
        devicedb.device_db.session.add(target_playbook)
        devicedb.device_db.session.flush()
        workflow_ids = [workflow.id for workflow in workflows]
        original_num_playbooks = len(devicedb.device_db.session.query(Playbook).all())
        self.delete_with_status_check('/api/playbooks/{0}/workflows/{1}'.format(target_playbook.id, workflow_ids[0]),
                                      headers=self.headers, status_code=NO_CONTENT)
        self.assertEqual(len(list(target_playbook.workflows)), len(workflow_ids) - 1)
        self.assertNotIn(workflow_ids[0], [workflow.id for workflow in target_playbook.workflows])
        self.assertEqual(len(devicedb.device_db.session.query(Playbook).all()), original_num_playbooks)

    def test_delete_last_workflow(self):
        device_db_help.standard_load()

        workflow = Workflow('wf', uuid4())
        devicedb.device_db.session.add(workflow)
        target_playbook = Playbook('play1', workflows=[workflow])
        devicedb.device_db.session.add(target_playbook)
        devicedb.device_db.session.flush()
        original_num_playbooks = len(devicedb.device_db.session.query(Playbook).all())
        self.delete_with_status_check('/api/playbooks/{0}/workflows/{1}'.format(target_playbook.id, workflow.id),
                                      headers=self.headers, status_code=NO_CONTENT)
        self.assertIsNone(devicedb.device_db.session.query(Playbook).filter_by(name='play1').first())
        self.assertEqual(len(devicedb.device_db.session.query(Playbook).all()), original_num_playbooks - 1)

    def test_delete_workflow_invalid_playbook_id(self):
        playbook = device_db_help.standard_load()
        original_num_playbooks = len(devicedb.device_db.session.query(Playbook).all())
        self.check_invalid_id('delete', '/api/playbooks/{0}/workflows/{1}'.format(uuid4(), playbook.workflows[0].id),
                              'workflow')
        self.assertEqual(len(devicedb.device_db.session.query(Playbook).all()), original_num_playbooks)

    def test_delete_workflow_invalid_workflow_id(self):
        playbook = device_db_help.standard_load()
        original_num_playbooks = len(devicedb.device_db.session.query(Playbook).all())
        self.check_invalid_id('delete', '/api/playbooks/{0}/workflows/{1}'.format(playbook.id, uuid4()), 'workflow')
        self.assertEqual(len(devicedb.device_db.session.query(Playbook).all()), original_num_playbooks)

    def test_delete_workflow_invalid_playbook_and_workflow_id(self):
        device_db_help.standard_load()
        original_num_playbooks = len(devicedb.device_db.session.query(Playbook).all())
        self.check_invalid_id('delete', '/api/playbooks/{0}/workflows/{1}'.format(uuid4(), uuid4()), 'workflow')
        self.assertEqual(len(devicedb.device_db.session.query(Playbook).all()), original_num_playbooks)

    def test_delete_workflow_invalid_playbook_id_format(self):
        playbook = device_db_help.standard_load()
        original_num_playbooks = len(devicedb.device_db.session.query(Playbook).all())
        self.check_invalid_uuid('delete', '/api/playbooks/af/workflows/{}'.format(playbook.workflows[0].id), 'workflow')
        self.assertEqual(len(devicedb.device_db.session.query(Playbook).all()), original_num_playbooks)

    def test_delete_workflow_invalid_workflow_id_format(self):
        playbook = device_db_help.standard_load()
        original_num_playbooks = len(devicedb.device_db.session.query(Playbook).all())
        self.check_invalid_uuid('delete', '/api/playbooks/{}/workflows/37b'.format(playbook.id, uuid4()), 'workflow')
        self.assertEqual(len(devicedb.device_db.session.query(Playbook).all()), original_num_playbooks)

    def test_delete_workflow_invalid_playbook_and_workflow_id_format(self):
        device_db_help.standard_load()
        original_num_playbooks = len(devicedb.device_db.session.query(Playbook).all())
        self.check_invalid_uuid('delete', '/api/playbooks/10/workflows/108', 'workflow')
        self.assertEqual(len(devicedb.device_db.session.query(Playbook).all()), original_num_playbooks)

    # All the creates

    def test_create_playbook(self):
        expected_playbooks = devicedb.device_db.session.query(Playbook).all()
        original_length = len(list(expected_playbooks))
        data = {"name": self.add_playbook_name}
        self.update_playbooks = True
        response = self.post_with_status_check('/api/playbooks', headers=self.headers,
                                               status_code=OBJECT_CREATED, data=json.dumps(data),
                                               content_type="application/json")
        response.pop('id')

        self.assertDictEqual(response, {'name': self.add_playbook_name, 'workflows': []})
        self.assertEqual(len(list(devicedb.device_db.session.query(Playbook).all())),
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
        devicedb.device_db.session.add(workflow)
        devicedb.device_db.session.flush()
        workflow_json = workflow.read()
        workflow_json['id'] = 'garbage'
        data = {'name': self.add_playbook_name, 'workflows': [workflow_json]}
        self.post_with_status_check('/api/playbooks',
                                    data=json.dumps(data), headers=self.headers, status_code=BAD_REQUEST,
                                    content_type="application/json")

    def test_create_workflow(self):
        playbook = device_db_help.standard_load()
        initial_workflows_len = len(playbook.workflows)

        response = self.post_with_status_check('/api/playbooks/{}/workflows'.format(playbook.id),
                                               headers=self.headers, status_code=OBJECT_CREATED,
                                               data=json.dumps(self.empty_workflow_json),
                                               content_type="application/json")

        self.empty_workflow_json['id'] = response['id']

        final_workflows = playbook.workflows
        self.assertEqual(len(final_workflows), initial_workflows_len + 1)

        workflow = next((workflow for workflow in final_workflows if workflow.name == self.add_workflow_name), None)
        self.assertIsNotNone(workflow)

    def test_create_workflow_invalid_id(self):
        self.check_invalid_id('post', '/api/playbooks/{}/workflows'.format(uuid4()), 'playbook',
                              data=json.dumps(self.empty_workflow_json),
                              content_type="application/json")

    def test_create_workflow_invalid_id_format(self):
        self.check_invalid_uuid('post', '/api/playbooks/87fgb/workflows', 'playbook',
                                data=json.dumps(self.empty_workflow_json),
                                content_type="application/json")

    # All the updates

    def test_update_playbook_name(self):
        playbook = device_db_help.standard_load()

        data = {'id': str(playbook.id), 'name': self.change_playbook_name}
        response = self.patch_with_status_check('/api/playbooks',
                                                data=json.dumps(data),
                                                headers=self.headers,
                                                content_type='application/json')
        self.assertEqual(response['name'], self.change_playbook_name)

    def test_update_playbook_invalid_id(self):
        device_db_help.standard_load()
        expected = {playbook.name for playbook in devicedb.device_db.session.query(Playbook).all()}
        data = {'id': str(uuid4()), 'name': self.change_playbook_name}
        self.check_invalid_id('patch', '/api/playbooks', 'playbook', content_type="application/json",
                              data=json.dumps(data))
        self.assertSetEqual({playbook.name for playbook in devicedb.device_db.session.query(Playbook).all()}, expected)

    def test_update_playbook_invalid_id_format(self):
        device_db_help.standard_load()
        expected = {playbook.name for playbook in devicedb.device_db.session.query(Playbook).all()}
        data = {'id': '475', 'name': self.change_playbook_name}
        self.check_invalid_uuid('patch', '/api/playbooks', 'playbook', content_type="application/json",
                                data=json.dumps(data))
        self.assertSetEqual({playbook.name for playbook in devicedb.device_db.session.query(Playbook).all()}, expected)

    def test_update_workflow(self):
        playbook = device_db_help.standard_load()
        workflow = playbook.workflows[0]
        expected_json = workflow.read()
        expected_json['name'] = self.change_workflow_name
        response = self.put_with_status_check('/api/playbooks/{}/workflows'.format(playbook.id),
                                              data=json.dumps(expected_json),
                                              headers=self.headers,
                                              content_type='application/json')
        self.assertDictEqual(response, expected_json)

        self.assertIsNotNone(
            devicedb.device_db.session.query(Workflow).filter_by(id=workflow.id).first())
        self.assertIsNone(
            devicedb.device_db.session.query(Workflow).join(Workflow._playbook).filter(
                Workflow.name == self.add_workflow_name).first())

    def test_update_workflow_invalid_id(self):
        playbook = device_db_help.standard_load()
        workflow = playbook.workflows[0].read()
        initial_workflows = devicedb.device_db.session.query(Workflow).all()
        self.check_invalid_id('put', '/api/playbooks/{}/workflows'.format(uuid4()), 'workflow',
                              data=json.dumps(workflow), content_type="application/json")
        final_workflows = devicedb.device_db.session.query(Workflow).all()
        self.assertSetEqual(set(final_workflows), set(initial_workflows))

    def test_update_workflow_invalid_id_format(self):
        playbook = device_db_help.standard_load()
        workflow = playbook.workflows[0].read()
        initial_workflows = devicedb.device_db.session.query(Workflow).all()
        self.check_invalid_uuid('put', '/api/playbooks/874fe/workflows', 'workflow',
                                data=json.dumps(workflow), content_type="application/json")
        final_workflows = devicedb.device_db.session.query(Workflow).all()
        self.assertSetEqual(set(final_workflows), set(initial_workflows))

    def test_copy_workflow(self):
        playbook = device_db_help.standard_load()
        for workflow in playbook.workflows:
            workflow_id = workflow.id
        response = self.post_with_status_check(
            '/api/playbooks/{0}/workflows?source={1}'.format(playbook.id, workflow_id),
            headers=self.headers, status_code=OBJECT_CREATED,
            data=json.dumps({'name': self.add_workflow_name}),
            content_type="application/json")
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
        playbook = device_db_help.standard_load()
        for workflow in playbook.workflows:
            workflow_id = workflow.id

        transfer_playbook = devicedb.device_db.session.query(Playbook).filter_by(name='dataflowTest').first()

        data = {"name": self.add_workflow_name, "playbook_id": str(transfer_playbook.id)}
        self.post_with_status_check('/api/playbooks/{0}/workflows?source={1}'.format(playbook.id, workflow_id),
                                    data=json.dumps(data),
                                    headers=self.headers, status_code=OBJECT_CREATED, content_type="application/json")

        for workflow in playbook.workflows:
            if workflow.name == 'helloWorldWorkflow':
                original_workflow = workflow
        copy_workflow = devicedb.device_db.session.query(Workflow).filter_by(name=self.add_workflow_name).first()

        self.assertEqual(len(playbook.workflows), 1)
        self.assertEqual(len(transfer_playbook.workflows), 2)
        self.assertIsNotNone(copy_workflow)

        self.assertNotEqual(original_workflow.start, copy_workflow.start)
        self.assertEqual(len(original_workflow.actions), len(copy_workflow.actions))

    def test_copy_playbook(self):
        playbook = device_db_help.standard_load()

        data = {"name": self.add_playbook_name}
        self.post_with_status_check('/api/playbooks?source={}'.format(playbook.id),
                                    data=json.dumps(data),
                                    headers=self.headers, status_code=OBJECT_CREATED, content_type="application/json")

        copy_playbook = devicedb.device_db.session.query(Playbook).filter_by(name=self.add_playbook_name).first()

        self.assertIsNotNone(copy_playbook)

        self.assertEqual(len(playbook.workflows), len(copy_playbook.workflows))

    def test_get_uuid(self):
        response = self.get_with_status_check('/api/uuid', status_code=OBJECT_CREATED)
        self.assertIn('uuid', response)
        UUID(response['uuid'])

    def test_import_workflow(self):
        path = os.path.join(test_workflows_path, 'basicWorkflowTest.playbook')
        files = {'file': (path, open(path, 'r'), 'application/json')}

        response = self.post_with_status_check('/api/playbooks', headers=self.headers, status_code=OBJECT_CREATED,
                                               data=files, content_type='multipart/form-data')
        playbook = devicedb.device_db.session.query(Playbook).filter_by(id=response['id']).first()
        self.assertIsNotNone(playbook)
        self.assertDictEqual(playbook.read(), response)

    def test_export_workflow(self):
        playbook = device_db_help.standard_load()

        response = self.get_with_status_check('/api/playbooks/{}?mode=export'.format(playbook.id), headers=self.headers)
        self.assertDictEqual(playbook.read(), response)
