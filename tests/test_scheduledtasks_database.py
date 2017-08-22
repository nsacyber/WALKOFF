import unittest
from server.scheduledtasks import ScheduledTask
from server.database import db
import json


class TestScheduledTask(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db.create_all()

    def tearDown(self):
        tasks = ScheduledTask.query.all()
        if tasks:
            ScheduledTask.query.delete()

    def __compare_init(self, task, name, description='', enabled=False, workflows=None,
                       scheduler_type='unspecified', scheduler_args=None):
        self.assertEqual(task.name, name)
        self.assertEqual(task.description, description)
        self.assertEqual(task.enabled, enabled)
        self.assertEqual(task.scheduler_type, scheduler_type)
        if workflows is not None:
            self.assertListEqual([workflow.uid for workflow in task.workflows], workflows)
        else:
            self.assertEqual(task.workflows, [])
        if scheduler_args is not None:
            self.assertDictEqual(json.loads(task.scheduler_args), scheduler_args)
        else:
            self.assertEqual(task.scheduler_args, '{}')

    def test_init_default(self):
        task = ScheduledTask(name='test')
        self.__compare_init(task, 'test')

    def test_init_with_description(self):
        task = ScheduledTask(name='test', description='desc')
        self.__compare_init(task, 'test', description='desc')

    def test_init_with_enabled(self):
        task = ScheduledTask(name='test', enabled=True)
        self.__compare_init(task, 'test', enabled=True)

    def test_init_with_workflows(self):
        task = ScheduledTask(name='test', workflows=['uid1', 'uid2', 'uid3', 'uid4'])
        self.__compare_init(task, 'test', workflows=['uid1', 'uid2', 'uid3', 'uid4'])

    def test_init_with_scheduler(self):
        task = ScheduledTask(name='test', scheduler={'type': 'DateScheduler', 'args': {'day': 1, 'month': 4}})
        self.__compare_init(task, 'test', scheduler_type='DateScheduler', scheduler_args={'day': 1, 'month': 4})

    def test_update_name_desc_only(self):
        task = ScheduledTask(name='test')
        update = {'name': 'updated_name', 'description': 'desc'}
        task.update(update)
        self.assertEqual(task.name, 'updated_name')
        self.assertEqual(task.description, 'desc')

    def test_update_workflows_none_existing(self):
        task = ScheduledTask(name='test')
        update = {'workflows': ['a', 'b', 'c']}
        task.update(update)
        self.assertListEqual([workflow.uid for workflow in task.workflows], ['a', 'b', 'c'])

    def test_update_workflows_with_existing_workflows(self):
        task = ScheduledTask(name='test', workflows=['b', 'c', 'd'])
        update = {'workflows': ['a', 'b', 'c']}
        task.update(update)
        self.assertListEqual([workflow.uid for workflow in task.workflows], ['a', 'b', 'c'])

    def test_update_scheduler(self):
        task = ScheduledTask(name='test', scheduler={'type': 'DateScheduler', 'args': {'day': 1, 'month': 4}})
        update = {'scheduler': {'type': 'IntervalScheduler', 'args': {'hour': 1, 'month': 4}}}
        task.update(update)
        self.assertEqual(task.scheduler_type, 'IntervalScheduler')
        self.assertDictEqual(json.loads(task.scheduler_args), {'hour': 1, 'month': 4})

    def test_enable_from_enabled(self):
        task = ScheduledTask(name='test', enabled=True)
        task.enable()
        self.assertTrue(task.enabled)

    def test_enable_from_disabled(self):
        task = ScheduledTask(name='test')
        task.enable()
        self.assertTrue(task.enabled)

    def test_disable_from_enabled(self):
        task = ScheduledTask(name='test', enabled=True)
        task.disable()
        self.assertFalse(task.enabled)

    def test_disable_from_disabled(self):
        task = ScheduledTask(name='test')
        task.disable()
        self.assertFalse(task.enabled)

    def test_as_json_name_desc_only(self):
        task = ScheduledTask(name='test', description='desc')
        expected = {'id': None,
                    'name': 'test',
                    'description': 'desc',
                    'enabled': False,
                    'workflows': [],
                    'scheduler': {'type': 'unspecified',
                                  'args': {}}}
        self.assertDictEqual(task.as_json(), expected)

    def test_as_json_with_workflows(self):
        task = ScheduledTask(name='test', workflows=['b', 'c', 'd'])
        expected = {'id': None,
                    'name': 'test',
                    'description': '',
                    'enabled': False,
                    'workflows': ['b', 'c', 'd'],
                    'scheduler': {'type': 'unspecified',
                                  'args': {}}}
        self.assertDictEqual(task.as_json(), expected)

    def test_as_json_with_scheduler(self):
        task = ScheduledTask(name='test', scheduler={'type': 'DateScheduler', 'args': {'day': 1, 'month': 4}})
        expected = {'id': None,
                    'name': 'test',
                    'description': '',
                    'enabled': False,
                    'workflows': [],
                    'scheduler': {'type': 'DateScheduler',
                                  'args': {'day': 1, 'month': 4}}}
        self.assertDictEqual(task.as_json(), expected)

    def test_as_json_enabled(self):
        task = ScheduledTask(name='test', enabled=True)
        expected = {'id': None,
                    'name': 'test',
                    'description': '',
                    'enabled': True,
                    'workflows': [],
                    'scheduler': {'type': 'unspecified',
                                  'args': {}}}
        self.assertDictEqual(task.as_json(), expected)