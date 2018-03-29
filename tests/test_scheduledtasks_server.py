import json
from uuid import uuid4

from tests.util.servertestcase import ServerTestCase
from walkoff.extensions import db
from walkoff.server.returncodes import *
from walkoff.serverdb.scheduledtasks import ScheduledTask, ScheduledWorkflow


class TestScheduledTasksServer(ServerTestCase):
    def setUp(self):
        self.date_scheduler = {'type': 'date', 'args': {'run_date': '2017-01-25 10:00:00'}}

    def tearDown(self):
        tasks = ScheduledTask.query.all()
        if tasks:
            ScheduledTask.query.delete()
        scheduled_workflows = ScheduledWorkflow.query.all()
        if scheduled_workflows:
            ScheduledWorkflow.query.delete()
        db.session.commit()

    def test_read_all_scheduled_tasks_no_tasks(self):
        response = self.get_with_status_check('/api/scheduledtasks', headers=self.headers)
        self.assertListEqual(response, [])

    def test_read_all_scheduled_tasks_with_tasks(self):
        tasks = [ScheduledTask(name='test-{}'.format(i)) for i in range(4)]
        db.session.add_all(tasks)
        expected = [task.as_json() for task in ScheduledTask.query.all()]
        response = self.get_with_status_check('/api/scheduledtasks', headers=self.headers)
        self.assertListEqual(response, expected)

    def test_create_scheduled_task(self):
        workflow_ids = [str(uuid4()) for _ in range(3)]
        data = {"name": 'test', "workflows": workflow_ids, "task_trigger": self.date_scheduler}
        response = self.post_with_status_check('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                               content_type='application/json', status_code=OBJECT_CREATED)
        expected = {'name': 'test',
                    'workflows': set(workflow_ids),
                    'status': 'running',
                    'task_trigger': self.date_scheduler,
                    'description': ''}
        response.pop('id')
        response['workflows'] = set(response['workflows'])
        self.assertDictEqual(response, expected)
        self.assertSetEqual({task.name for task in ScheduledTask.query.all()}, {'test'})

    def test_create_scheduled_task_already_exists(self):
        workflow_ids = [str(uuid4()) for _ in range(3)]
        data = {"name": 'test', "workflows": workflow_ids, "task_trigger": self.date_scheduler}
        self.app.post('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                      content_type='application/json')
        self.post_with_status_check('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                    content_type='application/json', status_code=OBJECT_EXISTS_ERROR)
        self.assertSetEqual({task.name for task in ScheduledTask.query.all()}, {'test'})

    def test_create_scheduled_task_invalid_uuids(self):
        data = {"name": 'test', "workflows": [str(uuid4()), '43hbs', '78'], "task_trigger": self.date_scheduler}
        self.post_with_status_check('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                    content_type='application/json', status_code=BAD_REQUEST)
        self.assertIsNone(ScheduledTask.query.filter_by(name='test').first())

    def test_read_scheduled_task(self):
        workflow_ids = [str(uuid4()) for _ in range(3)]
        data = {"name": 'test', "workflows": workflow_ids, "task_trigger": self.date_scheduler}
        response = json.loads(self.app.post('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                            content_type='application/json').get_data(as_text=True))
        task_id = response['id']
        response = self.get_with_status_check('/api/scheduledtasks/{}'.format(task_id), headers=self.headers,
                                              content_type='application/json', status_code=SUCCESS)
        expected = {'id': task_id,
                    'name': 'test',
                    'workflows': set(workflow_ids),
                    'status': 'running',
                    'task_trigger': self.date_scheduler,
                    'description': ''}
        response['workflows'] = set(response['workflows'])
        self.assertDictEqual(response, expected)

    def test_read_scheduled_task_does_not_exist(self):
        self.get_with_status_check('/api/scheduledtasks/404', headers=self.headers,
                                   content_type='application/json', status_code=OBJECT_DNE_ERROR)

    def test_update_scheduled_task_name_desc_only(self):
        workflow_ids = [str(uuid4()) for _ in range(3)]
        data = {"name": 'test', "workflows": workflow_ids, "task_trigger": self.date_scheduler}
        response = json.loads(self.app.post('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                            content_type='application/json').get_data(as_text=True))
        task_id = response['id']
        update = {'name': 'renamed', 'description': 'desc', 'id': task_id}
        response = self.put_with_status_check('/api/scheduledtasks', data=json.dumps(update), headers=self.headers,
                                              content_type='application/json', status_code=SUCCESS)
        expected = {'id': task_id,
                    'name': 'renamed',
                    'workflows': set(workflow_ids),
                    'status': 'running',
                    'task_trigger': self.date_scheduler,
                    'description': 'desc'}
        response['workflows'] = set(response['workflows'])
        self.assertDictEqual(response, expected)

    def test_update_scheduled_task_invalid_workflows(self):
        workflow_ids = [str(uuid4()) for _ in range(3)]
        data = {"name": 'test', "workflows": workflow_ids, "task_trigger": self.date_scheduler}
        response = json.loads(self.app.post('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                            content_type='application/json').get_data(as_text=True))
        task_id = response['id']
        update = {'workflows': ['a', 'b'], 'id': task_id}
        response = self.put_with_status_check('/api/scheduledtasks', data=json.dumps(update), headers=self.headers,
                                              content_type='application/json', status_code=BAD_REQUEST)

    def test_update_scheduled_task_workflows(self):
        workflow_ids = [str(uuid4()) for _ in range(3)]
        data = {"name": 'test', "workflows": workflow_ids, "task_trigger": self.date_scheduler}
        response = json.loads(self.app.post('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                            content_type='application/json').get_data(as_text=True))
        task_id = response['id']
        update = {'workflows': workflow_ids, 'id': task_id}
        response = self.put_with_status_check('/api/scheduledtasks', data=json.dumps(update), headers=self.headers,
                                              content_type='application/json', status_code=SUCCESS)
        expected = {'id': task_id,
                    'name': 'test',
                    'workflows': set(workflow_ids),
                    'status': 'running',
                    'task_trigger': self.date_scheduler,
                    'description': ''}
        response['workflows'] = set(response['workflows'])
        self.assertDictEqual(response, expected)

    def test_update_scheduled_task_scheduler(self):
        workflow_ids = [str(uuid4()) for _ in range(3)]
        data = {"name": 'test', "workflows": workflow_ids, "task_trigger": self.date_scheduler}
        response = json.loads(self.app.post('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                            content_type='application/json').get_data(as_text=True))
        task_id = response['id']
        update = {'workflows': workflow_ids, 'id': task_id}
        response = self.put_with_status_check('/api/scheduledtasks', data=json.dumps(update), headers=self.headers,
                                              content_type='application/json', status_code=SUCCESS)
        expected = {'id': task_id,
                    'name': 'test',
                    'workflows': set(workflow_ids),
                    'status': 'running',
                    'task_trigger': self.date_scheduler,
                    'description': ''}
        response['workflows'] = set(response['workflows'])
        self.assertDictEqual(response, expected)

    def test_update_scheduled_task_does_not_exist(self):
        update = {'workflows': [str(uuid4()) for _ in range(3)], 'id': 404}
        self.put_with_status_check('/api/scheduledtasks', data=json.dumps(update), headers=self.headers,
                                   content_type='application/json', status_code=OBJECT_DNE_ERROR)

    def test_update_scheduled_task_name_already_exists_same_id(self):
        data = {"name": 'test1', "workflows": [str(uuid4()) for _ in range(3)], "task_trigger": self.date_scheduler}
        response = json.loads(self.app.post('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                            content_type='application/json').get_data(as_text=True))
        task_id = response['id']
        update = {'name': 'test1', 'description': 'desc', 'id': task_id}
        self.put_with_status_check('/api/scheduledtasks', data=json.dumps(update), headers=self.headers,
                                   content_type='application/json', status_code=SUCCESS)

    def test_update_scheduled_task_name_already_exists_different_id(self):
        workflow_ids = [str(uuid4()) for _ in range(3)]
        data = {"name": 'test1', "workflows": workflow_ids, "task_trigger": self.date_scheduler}
        self.app.post('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                      content_type='application/json')
        data = {"name": 'test2', "workflows": workflow_ids, "task_trigger": self.date_scheduler}
        response = json.loads(self.app.post('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                            content_type='application/json').get_data(as_text=True))
        task_id2 = response['id']
        update = {'name': 'test1', 'description': 'desc', 'id': task_id2}
        self.put_with_status_check('/api/scheduledtasks', data=json.dumps(update), headers=self.headers,
                                   content_type='application/json', status_code=OBJECT_EXISTS_ERROR)

    def test_delete_scheduled_task(self):
        data = {"name": 'test', "workflows": [str(uuid4()) for _ in range(3)], "task_trigger": self.date_scheduler}
        response = json.loads(self.app.post('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                            content_type='application/json').get_data(as_text=True))
        task_id = response['id']
        self.delete_with_status_check('/api/scheduledtasks/{}'.format(task_id), headers=self.headers,
                                      content_type='application/json', status_code=NO_CONTENT)
        self.assertSetEqual({task.name for task in ScheduledTask.query.all()}, set())

    def test_delete_scheduled_task_does_not_exist(self):
        self.delete_with_status_check('/api/scheduledtasks/404', headers=self.headers,
                                      content_type='application/json', status_code=OBJECT_DNE_ERROR)

    def take_action(self, task_id, action, status_code=SUCCESS):
        data = {'id': task_id, 'action': action}
        self.patch_with_status_check('/api/scheduledtasks', headers=self.headers, data=json.dumps(data),
                                     content_type='application/json', status_code=status_code)

    def test_start_from_started(self):
        data = {"name": 'test1', "workflows": [str(uuid4()) for _ in range(3)], "task_trigger": self.date_scheduler,
                'status': 'running'}
        response = json.loads(self.app.post('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                            content_type='application/json').get_data(as_text=True))
        task_id = response['id']
        self.take_action(task_id, 'start')
        self.assertEqual(ScheduledTask.query.filter_by(id=task_id).first().status, 'running')

    def test_start_from_stopped(self):
        data = {"name": 'test1', "workflows": [str(uuid4()) for _ in range(3)], "task_trigger": self.date_scheduler}
        response = json.loads(self.app.post('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                            content_type='application/json').get_data(as_text=True))
        task_id = response['id']
        self.take_action(task_id, 'start')
        self.assertEqual(ScheduledTask.query.filter_by(id=task_id).first().status, 'running')

    def test_start_does_not_exist(self):
        self.take_action(404, 'start', status_code=OBJECT_DNE_ERROR)

    def test_stop_from_started(self):
        data = {"name": 'test1', "workflows": [str(uuid4()) for _ in range(3)], "task_trigger": self.date_scheduler,
                'status': 'running'}
        response = json.loads(self.app.post('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                            content_type='application/json').get_data(as_text=True))
        task_id = response['id']
        self.take_action(task_id, 'stop')
        self.assertEqual(ScheduledTask.query.filter_by(id=task_id).first().status, 'stopped')

    def test_stop_from_stopped(self):
        data = {"name": 'test1', "workflows": [str(uuid4()) for _ in range(3)], "task_trigger": self.date_scheduler}
        response = json.loads(self.app.post('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                            content_type='application/json').get_data(as_text=True))
        task_id = response['id']
        self.take_action(task_id, 'stop')
        self.assertEqual(ScheduledTask.query.filter_by(id=task_id).first().status, 'stopped')

    def test_stop_does_not_exist(self):
        self.take_action(404, 'stop', status_code=OBJECT_DNE_ERROR)
