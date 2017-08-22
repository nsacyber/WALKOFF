import json
from os import path
from tests.util.servertestcase import ServerTestCase
from server.scheduledtasks import ScheduledTask
from server import flaskserver as flask_server
from server.returncodes import *


class TestScheduledTasksServer(ServerTestCase):

    def setUp(self):
        flask_server.running_context.db.create_all()

    def tearDown(self):
        tasks = ScheduledTask.query.all()
        if tasks:
            ScheduledTask.query.delete()
        flask_server.running_context.db.session.commit()
        print(ScheduledTask.query.all())

    def test_read_all_scheduled_tasks_no_tasks(self):
        response = self.get_with_status_check('/api/scheduledtasks', headers=self.headers)
        self.assertListEqual(response, [])

    def test_read_all_scheduled_tasks_with_tasks(self):
        tasks = [ScheduledTask(name='test-{}'.format(i)) for i in range(4)]
        flask_server.running_context.db.session.add_all(tasks)
        expected = [task.as_json() for task in flask_server.running_context.ScheduledTask.query.all()]
        response = self.get_with_status_check('/api/scheduledtasks', headers=self.headers)
        self.assertListEqual(response, expected)

    def test_create_scheduled_task_date_scheduler(self):
        scheduler = {'type': 'date',
                     'args': {'year': 2017,
                              'month': 1,
                              'day': 25,
                              'hour': 10}}
        data = {"name": 'test', "workflows": ['a', 'b', 'c']}
        response = self.app.put('/api/scheduledtasks', data=json.dumps(data), headers=self.headers,
                                              content_type='application/json')
        print(response)
        print(response.status_code)
        expected = {'name': 'test',
                    'workflows': ['a', 'b', 'c'],
                    'enabled': False,
                    'scheduler': scheduler}
        response.pop('id')
        self.assertDictEqual(response, expected)