import json
from os import path
from tests.util.servertestcase import ServerTestCase
from server.scheduledtasks import ScheduledTask, ScheduledWorkflow
from server import flaskserver as flask_server
from server.returncodes import *


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
        flask_server.running_context.db.session.commit()

    def test_read_all_scheduled_tasks_no_tasks(self):
        response = self.get_with_status_check('/api/scheduledtasks', headers=self.headers)
        self.assertListEqual(response, [])

    def test_read_all_scheduled_tasks_with_tasks(self):
        tasks = [ScheduledTask(name='test-{}'.format(i)) for i in range(4)]
        flask_server.running_context.db.session.add_all(tasks)
        expected = [task.as_json() for task in flask_server.running_context.ScheduledTask.query.all()]
        response = self.get_with_status_check('/api/scheduledtasks', headers=self.headers)
        self.assertListEqual(response, expected)

    def test_create_scheduled_task(self):
        data = {"name": 'test', "workflows": ['a', 'b', 'c'], "task_trigger": self.date_scheduler}
        response = self.put_with_status_check('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                              content_type='application/json', status_code=OBJECT_CREATED)
        expected = {'name': 'test',
                    'workflows': {'a', 'b', 'c'},
                    'status': 'stopped',
                    'task_trigger': self.date_scheduler,
                    'description': ''}
        response.pop('id')
        response['workflows'] = set(response['workflows'])
        self.assertDictEqual(response, expected)
        self.assertSetEqual({task.name for task in ScheduledTask.query.all()}, {'test'})

    def test_create_scheduled_task_already_exists(self):
        data = {"name": 'test', "workflows": ['a', 'b', 'c'], "task_trigger": self.date_scheduler}
        self.app.put('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                     content_type='application/json')
        self.put_with_status_check('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                   content_type='application/json', status_code=OBJECT_EXISTS_ERROR)
        self.assertSetEqual({task.name for task in ScheduledTask.query.all()}, {'test'})

    def test_read_scheduled_task(self):
        data = {"name": 'test', "workflows": ['a', 'b', 'c'], "task_trigger": self.date_scheduler}
        response = json.loads(self.app.put('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                           content_type='application/json').get_data(as_text=True))
        task_id = response['id']
        response = self.get_with_status_check('/api/scheduledtasks/{}'.format(task_id), headers=self.headers,
                                              content_type='application/json', status_code=SUCCESS)
        expected = {'id': task_id,
                    'name': 'test',
                    'workflows': {'a', 'b', 'c'},
                    'status': 'stopped',
                    'task_trigger': self.date_scheduler,
                    'description': ''}
        response['workflows'] = set(response['workflows'])
        self.assertDictEqual(response, expected)

    def test_read_scheduled_task_does_not_exist(self):
        self.get_with_status_check('/api/scheduledtasks/404', headers=self.headers,
                                   content_type='application/json', status_code=OBJECT_DNE_ERROR)

    def test_update_scheduled_task_name_desc_only(self):
        data = {"name": 'test', "workflows": ['a', 'b', 'c'], "task_trigger": self.date_scheduler}
        response = json.loads(self.app.put('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                           content_type='application/json').get_data(as_text=True))
        task_id = response['id']
        update = {'name': 'renamed', 'description': 'desc', 'id': task_id}
        response = self.post_with_status_check('/api/scheduledtasks', data=json.dumps(update), headers=self.headers,
                                   content_type='application/json', status_code=SUCCESS)
        expected = {'id': task_id,
                    'name': 'renamed',
                    'workflows': {'a', 'b', 'c'},
                    'status': 'stopped',
                    'task_trigger': self.date_scheduler,
                    'description': 'desc'}
        response['workflows'] = set(response['workflows'])
        self.assertDictEqual(response, expected)

    def test_update_scheduled_task_workflows(self):
        data = {"name": 'test', "workflows": ['a', 'b', 'c'], "task_trigger": self.date_scheduler}
        response = json.loads(self.app.put('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                           content_type='application/json').get_data(as_text=True))
        task_id = response['id']
        update = {'workflows': ['1', '2', '3'], 'id': task_id}
        response = self.post_with_status_check('/api/scheduledtasks', data=json.dumps(update), headers=self.headers,
                                   content_type='application/json', status_code=SUCCESS)
        expected = {'id': task_id,
                    'name': 'test',
                    'workflows': {'1', '2', '3'},
                    'status': 'stopped',
                    'task_trigger': self.date_scheduler,
                    'description': ''}
        response['workflows'] = set(response['workflows'])
        self.assertDictEqual(response, expected)
        
    def test_update_scheduled_task_scheduler(self):
        data = {"name": 'test', "workflows": ['a', 'b', 'c'], "task_trigger": self.date_scheduler}
        response = json.loads(self.app.put('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                           content_type='application/json').get_data(as_text=True))
        task_id = response['id']
        update = {'workflows': ['1', '2', '3'], 'id': task_id}
        response = self.post_with_status_check('/api/scheduledtasks', data=json.dumps(update), headers=self.headers,
                                   content_type='application/json', status_code=SUCCESS)
        expected = {'id': task_id,
                    'name': 'test',
                    'workflows': {'1', '2', '3'},
                    'status': 'stopped',
                    'task_trigger': self.date_scheduler,
                    'description': ''}
        response['workflows'] = set(response['workflows'])
        self.assertDictEqual(response, expected)

    def test_update_scheduled_task_does_not_exist(self):
        update = {'workflows': ['1', '2', '3'], 'id': 404}
        self.post_with_status_check('/api/scheduledtasks', data=json.dumps(update), headers=self.headers,
                                   content_type='application/json', status_code=OBJECT_DNE_ERROR)

    def test_update_scheduled_task_name_already_exists_same_id(self):
        data = {"name": 'test1', "workflows": ['a', 'b', 'c'], "task_trigger": self.date_scheduler}
        response = json.loads(self.app.put('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                           content_type='application/json').get_data(as_text=True))
        task_id = response['id']
        update = {'name': 'test1', 'description': 'desc', 'id': task_id}
        self.post_with_status_check('/api/scheduledtasks', data=json.dumps(update), headers=self.headers,
                                   content_type='application/json', status_code=SUCCESS)

    def test_update_scheduled_task_name_already_exists_different_id(self):
        data = {"name": 'test1', "workflows": ['a', 'b', 'c'], "task_trigger": self.date_scheduler}
        self.app.put('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                           content_type='application/json')
        data = {"name": 'test2', "workflows": ['a', 'b', 'c'], "task_trigger": self.date_scheduler}
        response = json.loads(self.app.put('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                           content_type='application/json').get_data(as_text=True))
        task_id2 = response['id']
        update = {'name': 'test1', 'description': 'desc', 'id': task_id2}
        self.post_with_status_check('/api/scheduledtasks', data=json.dumps(update), headers=self.headers,
                                   content_type='application/json', status_code=OBJECT_EXISTS_ERROR)

    def test_delete_scheduled_task(self):
        data = {"name": 'test', "workflows": ['a', 'b', 'c'], "task_trigger": self.date_scheduler}
        response = json.loads(self.app.put('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                           content_type='application/json').get_data(as_text=True))
        task_id = response['id']
        self.delete_with_status_check('/api/scheduledtasks/{}'.format(task_id), headers=self.headers,
                                           content_type='application/json', status_code=SUCCESS)
        self.assertSetEqual({task.name for task in ScheduledTask.query.all()}, set())

    def test_delete_scheduled_task_does_not_exist(self):
        self.delete_with_status_check('/api/scheduledtasks/404', headers=self.headers,
                                           content_type='application/json', status_code=OBJECT_DNE_ERROR)

    def test_start_from_started(self):
        data = {"name": 'test1', "workflows": ['a', 'b', 'c'], "task_trigger": self.date_scheduler, 'status': 'running'}
        response = json.loads(self.app.put('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                           content_type='application/json').get_data(as_text=True))
        task_id = response['id']
        self.put_with_status_check('/api/scheduledtasks/{}/start'.format(task_id), headers=self.headers,
                                      content_type='application/json', status_code=SUCCESS)
        self.assertEqual(ScheduledTask.query.filter_by(id=task_id).first().status, 'running')

    def test_start_from_stopped(self):
        data = {"name": 'test1', "workflows": ['a', 'b', 'c'], "task_trigger": self.date_scheduler}
        response = json.loads(self.app.put('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                           content_type='application/json').get_data(as_text=True))
        task_id = response['id']
        self.put_with_status_check('/api/scheduledtasks/{}/start'.format(task_id), headers=self.headers,
                                   content_type='application/json', status_code=SUCCESS)
        self.assertEqual(ScheduledTask.query.filter_by(id=task_id).first().status, 'running')

    def test_start_does_not_exist(self):
        self.put_with_status_check('/api/scheduledtasks/404/start', headers=self.headers,
                                      content_type='application/json', status_code=OBJECT_DNE_ERROR)

    def test_stop_from_started(self):
        data = {"name": 'test1', "workflows": ['a', 'b', 'c'], "task_trigger": self.date_scheduler, 'status': 'running'}
        response = json.loads(self.app.put('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                           content_type='application/json').get_data(as_text=True))
        task_id = response['id']
        self.put_with_status_check('/api/scheduledtasks/{}/stop'.format(task_id), headers=self.headers,
                                      content_type='application/json', status_code=SUCCESS)
        self.assertEqual(ScheduledTask.query.filter_by(id=task_id).first().status, 'stopped')

    def test_stop_from_stopped(self):
        data = {"name": 'test1', "workflows": ['a', 'b', 'c'], "task_trigger": self.date_scheduler}
        response = json.loads(self.app.put('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                           content_type='application/json').get_data(as_text=True))
        task_id = response['id']
        self.put_with_status_check('/api/scheduledtasks/{}/stop'.format(task_id), headers=self.headers,
                                   content_type='application/json', status_code=SUCCESS)
        self.assertEqual(ScheduledTask.query.filter_by(id=task_id).first().status, 'stopped')

    def test_stop_does_not_exist(self):
        self.put_with_status_check('/api/scheduledtasks/404/stop', headers=self.headers,
                                      content_type='application/json', status_code=OBJECT_DNE_ERROR)