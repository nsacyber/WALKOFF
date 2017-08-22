import unittest
from server.scheduledtasks import ScheduledTask
from server.database import db
import json


class TestScheduledTask(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db.create_all()

    def setUp(self):
        self.date_scheduler = {'type': 'date', 'args': {'date': '2017-01-25 10:00:00'}}

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
            self.assertSetEqual({workflow.uid for workflow in task.workflows}, workflows)
        else:
            self.assertSetEqual({workflow.uid for workflow in task.workflows}, set())
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
        self.__compare_init(task, 'test', workflows={'uid1', 'uid2', 'uid3', 'uid4'})

    def test_init_with_scheduler(self):
        task = ScheduledTask(name='test', scheduler=self.date_scheduler)
        self.__compare_init(task, 'test', scheduler_type='date', scheduler_args={'date': '2017-01-25 10:00:00'})

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
        self.assertSetEqual({workflow.uid for workflow in task.workflows}, {'a', 'b', 'c'})

    def test_update_scheduler(self):
        task = ScheduledTask(name='test', scheduler=self.date_scheduler)
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

    def assertJsonIsCorrect(self, task, expected):
        actual_json = task.as_json()
        actual_json['workflows'] = set(actual_json['workflows'])
        self.assertDictEqual(actual_json, expected)
        pass

    def test_as_json_name_desc_only(self):
        task = ScheduledTask(name='test', description='desc')
        expected = {'id': None,
                    'name': 'test',
                    'description': 'desc',
                    'enabled': False,
                    'workflows': set(),
                    'scheduler': {'type': 'unspecified',
                                  'args': {}}}
        self.assertJsonIsCorrect(task, expected)

    def test_as_json_with_workflows(self):
        task = ScheduledTask(name='test', workflows=['b', 'c', 'd'])
        expected = {'id': None,
                    'name': 'test',
                    'description': '',
                    'enabled': False,
                    'workflows': {'b', 'c', 'd'},
                    'scheduler': {'type': 'unspecified',
                                  'args': {}}}
        self.assertJsonIsCorrect(task, expected)

    def test_as_json_with_workflows_with_duplicates(self):
        task = ScheduledTask(name='test', workflows=['b', 'c', 'd', 'd', 'c', 'b'])
        expected = {'id': None,
                    'name': 'test',
                    'description': '',
                    'enabled': False,
                    'workflows': {'b', 'c', 'd'},
                    'scheduler': {'type': 'unspecified',
                                  'args': {}}}
        self.assertJsonIsCorrect(task, expected)

    def test_as_json_with_scheduler(self):
        task = ScheduledTask(name='test', scheduler=self.date_scheduler)
        expected = {'id': None,
                    'name': 'test',
                    'description': '',
                    'enabled': False,
                    'workflows': set(),
                    'scheduler': self.date_scheduler}
        self.assertJsonIsCorrect(task, expected)

    def test_as_json_enabled(self):
        task = ScheduledTask(name='test', enabled=True)
        expected = {'id': None,
                    'name': 'test',
                    'description': '',
                    'enabled': True,
                    'workflows': set(),
                    'scheduler': {'type': 'unspecified',
                                  'args': {}}}
        self.assertJsonIsCorrect(task, expected)