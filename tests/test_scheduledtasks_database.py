import json
import unittest

import walkoff.server.flaskserver as server
from tests.util.execution_db_help import setup_dbs
from walkoff.scheduler import InvalidTriggerArgs
from walkoff.serverdb import db
from walkoff.serverdb.scheduledtasks import ScheduledTask


class TestScheduledTask(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = server.app.test_request_context()
        cls.context.push()
        setup_dbs()

    def setUp(self):
        self.date_trigger = {'type': 'date', 'args': {'run_date': '2017-01-25 10:00:00'}}

    def tearDown(self):
        db.session.rollback()
        for task in db.session.query(ScheduledTask).all():
            db.session.delete(task)
        server.running_context.scheduler.scheduler.remove_all_jobs()
        server.running_context.scheduler.stop()
        db.session.commit()

    def assertSchedulerWorkflowsRunningEqual(self, workflows=None):
        if workflows is None:
            self.assertDictEqual(server.running_context.scheduler.get_all_scheduled_workflows(), {})
        else:
            scheduled_workflows = server.running_context.scheduler.get_all_scheduled_workflows()
            self.assertSetEqual(set(scheduled_workflows['None']), set(workflows))

    def assertJsonIsCorrect(self, task, expected):
        actual_json = task.as_json()
        actual_json['workflows'] = set(actual_json['workflows'])
        self.assertDictEqual(actual_json, expected)

    def assertStructureIsCorrect(self, task, name, description='', status='running', workflows=None,
                                 trigger_type='unspecified', trigger_args=None, expected_running_workflows=None):
        self.assertEqual(task.name, name)
        self.assertEqual(task.description, description)
        self.assertEqual(task.status, status)
        self.assertEqual(task.trigger_type, trigger_type)
        if workflows is not None:
            self.assertSetEqual({workflow.workflow_id for workflow in task.workflows}, workflows)
        else:
            self.assertSetEqual({workflow.workflow_id for workflow in task.workflows}, set())
        if trigger_args is not None:
            self.assertDictEqual(json.loads(task.trigger_args), trigger_args)
        else:
            self.assertEqual(task.trigger_args, '{}')
        self.assertSchedulerWorkflowsRunningEqual(expected_running_workflows)

    def test_init_default(self):
        task = ScheduledTask(name='test')
        self.assertStructureIsCorrect(task, 'test')

    def test_init_with_description(self):
        task = ScheduledTask(name='test', description='desc')
        self.assertStructureIsCorrect(task, 'test', description='desc')

    def test_init_with_invalid_status(self):
        task = ScheduledTask(name='test', status='invalid')
        self.assertStructureIsCorrect(task, 'test')

    def test_init_with_workflows(self):
        task = ScheduledTask(name='test', workflows=['id1', 'id2', 'id3', 'id4'])

        self.assertStructureIsCorrect(task, 'test', workflows={'id1', 'id2', 'id3', 'id4'})

    def test_init_with_trigger(self):
        task = ScheduledTask(name='test', task_trigger=self.date_trigger)
        self.assertStructureIsCorrect(task, 'test', trigger_type='date',
                                      trigger_args={'run_date': '2017-01-25 10:00:00'})

    def test_init_with_invalid_trigger(self):
        trigger = {'type': 'date', 'args': {'run_date': '2017-100-25 10:00:00'}}
        with self.assertRaises(InvalidTriggerArgs):
            ScheduledTask(name='test', task_trigger=trigger)

    def test_init_stopped(self):
        task = ScheduledTask(name='test', status='stopped')
        self.assertStructureIsCorrect(task, 'test', status='stopped')

    def test_init_with_status_with_trigger_with_workflows(self):
        workflows = ['id1', 'id2', 'id3', 'id4']
        task = ScheduledTask(name='test', task_trigger=self.date_trigger, status='running', workflows=workflows)
        self.assertStructureIsCorrect(task, 'test', trigger_type='date',
                                      trigger_args={'run_date': '2017-01-25 10:00:00'},
                                      status='running', workflows=set(workflows), expected_running_workflows=workflows)

    def test_init_with_status_with_trigger_without_workflows(self):
        task = ScheduledTask(name='test', task_trigger=self.date_trigger, status='running')
        self.assertStructureIsCorrect(task, 'test', trigger_type='date',
                                      trigger_args={'run_date': '2017-01-25 10:00:00'},
                                      status='running')

    def test_init_with_status_trigger_unspecified(self):
        workflows = ['id1', 'id2', 'id3', 'id4']
        task = ScheduledTask(name='test', status='running', workflows=['id1', 'id2', 'id3', 'id4'])
        self.assertStructureIsCorrect(task, 'test', status='running', workflows=set(workflows))

    def test_update_name_desc_only(self):
        task = ScheduledTask(name='test')
        update = {'name': 'updated_name', 'description': 'desc'}
        task.update(update)
        self.assertEqual(task.name, 'updated_name')
        self.assertEqual(task.description, 'desc')

    def test_update_workflows_none_existing_stopped(self):
        task = ScheduledTask(name='test', status='stopped')
        update = {'workflows': ['a', 'b', 'c']}
        task.update(update)
        self.assertListEqual([workflow.workflow_id for workflow in task.workflows], ['a', 'b', 'c'])
        self.assertSchedulerWorkflowsRunningEqual(workflows=None)

    def test_update_workflows_none_existing_running(self):
        workflows = ['a', 'b', 'c', 'd']
        task = ScheduledTask(name='test', task_trigger=self.date_trigger, status='running')
        update = {'workflows': ['a', 'b', 'c']}
        task.update(update)
        self.assertListEqual([workflow.workflow_id for workflow in task.workflows], ['a', 'b', 'c'])
        self.assertSchedulerWorkflowsRunningEqual(['a', 'b', 'c'])

    def test_update_workflows_with_existing_workflows_stopped(self):
        task = ScheduledTask(name='test', workflows=['b', 'c', 'd'])
        update = {'workflows': ['a', 'b', 'c']}
        task.update(update)
        self.assertSetEqual({workflow.workflow_id for workflow in task.workflows}, {'a', 'b', 'c'})
        self.assertSchedulerWorkflowsRunningEqual(workflows=None)

    def test_update_workflows_with_existing_workflows_running_new_only(self):
        workflows = ['a', 'b', 'c', 'd']
        task = ScheduledTask(name='test', task_trigger=self.date_trigger, workflows=['b', 'c', 'd'], status='running')
        update = {'workflows': workflows}
        task.update(update)
        self.assertSetEqual({workflow.workflow_id for workflow in task.workflows}, {'a', 'b', 'c', 'd'})
        self.assertSchedulerWorkflowsRunningEqual(workflows)

    def test_update_workflows_with_existing_workflows_running_remove_only(self):
        workflows = ['a', 'b', 'c', 'd']
        task = ScheduledTask(name='test', task_trigger=self.date_trigger, workflows=workflows, status='running')
        update = {'workflows': ['b', 'c']}
        task.update(update)
        self.assertSetEqual({workflow.workflow_id for workflow in task.workflows}, {'b', 'c'})
        self.assertSchedulerWorkflowsRunningEqual(['b', 'c'])

    def test_update_workflows_with_existing_workflows_running_add_and_remove(self):
        workflows = ['a', 'b', 'c', 'd']
        task = ScheduledTask(name='test', task_trigger=self.date_trigger, workflows=['b', 'c', 'd'], status='running')
        update = {'workflows': ['a', 'b']}
        task.update(update)
        self.assertSetEqual({workflow.workflow_id for workflow in task.workflows}, {'a', 'b'})
        self.assertSchedulerWorkflowsRunningEqual(['a', 'b'])

    def test_update_scheduler(self):
        task = ScheduledTask(name='test', task_trigger=self.date_trigger)
        update = {'task_trigger': {'type': 'interval', 'args': {'hours': 1, 'weeks': 4}}}
        task.update(update)
        self.assertEqual(task.trigger_type, 'interval')
        self.assertDictEqual(json.loads(task.trigger_args), {'hours': 1, 'weeks': 4})
        self.assertSchedulerWorkflowsRunningEqual(workflows=None)

    def test_update_scheduler_invalid_scheduler(self):
        task = ScheduledTask(name='test', task_trigger=self.date_trigger)
        update = {'name': 'renamed', 'task_trigger': {'type': 'interval', 'args': {'invalid': 1, 'weeks': 4}}}
        with self.assertRaises(InvalidTriggerArgs):
            task.update(update)
        self.assertEqual(task.name, 'test')
        self.assertSchedulerWorkflowsRunningEqual(workflows=None)

    def test_start_from_running(self):
        task = ScheduledTask(name='test', status='running')
        task.start()
        self.assertEqual(task.status, 'running')
        self.assertSchedulerWorkflowsRunningEqual(workflows=None)

    def test_start_from_stopped_unspecified_trigger(self):
        task = ScheduledTask(name='test')
        task.start()
        self.assertEqual(task.status, 'running')
        self.assertSchedulerWorkflowsRunningEqual(workflows=None)

    def test_start_from_stopped_with_trigger(self):
        workflows = ['a', 'b', 'c', 'd']
        task = ScheduledTask(name='test', task_trigger=self.date_trigger, workflows=['b', 'c', 'd'])
        task.start()
        self.assertEqual(task.status, 'running')
        self.assertSchedulerWorkflowsRunningEqual(['b', 'c', 'd'])

    def test_stop_from_running_no_workflows(self):
        task = ScheduledTask(name='test', status='running')
        task.stop()
        self.assertEqual(task.status, 'stopped')
        self.assertSchedulerWorkflowsRunningEqual(workflows=None)

    def test_stop_from_running_with_workflows(self):
        task = ScheduledTask(name='test', task_trigger=self.date_trigger, workflows=['b', 'c', 'd'])
        task.stop()
        self.assertEqual(task.status, 'stopped')
        self.assertSchedulerWorkflowsRunningEqual(workflows=None)

    def test_stop_from_stopped(self):
        task = ScheduledTask(name='test')
        task.stop()
        self.assertEqual(task.status, 'stopped')

    def test_as_json_name_desc_only(self):
        task = ScheduledTask(name='test', description='desc')
        expected = {'id': None,
                    'name': 'test',
                    'description': 'desc',
                    'status': 'running',
                    'workflows': set(),
                    'task_trigger': {'type': 'unspecified',
                                     'args': {}}}
        self.assertJsonIsCorrect(task, expected)

    def test_as_json_with_workflows(self):
        task = ScheduledTask(name='test', workflows=['b', 'c', 'd'])
        expected = {'id': None,
                    'name': 'test',
                    'description': '',
                    'status': 'running',
                    'workflows': {'b', 'c', 'd'},
                    'task_trigger': {'type': 'unspecified',
                                     'args': {}}}
        self.assertJsonIsCorrect(task, expected)

    def test_as_json_with_workflows_with_duplicates(self):
        task = ScheduledTask(name='test', workflows=['b', 'c', 'd', 'd', 'c', 'b'])
        expected = {'id': None,
                    'name': 'test',
                    'description': '',
                    'status': 'running',
                    'workflows': {'b', 'c', 'd'},
                    'task_trigger': {'type': 'unspecified',
                                     'args': {}}}
        self.assertJsonIsCorrect(task, expected)

    def test_as_json_with_scheduler(self):
        task = ScheduledTask(name='test', task_trigger=self.date_trigger)
        expected = {'id': None,
                    'name': 'test',
                    'description': '',
                    'status': 'running',
                    'workflows': set(),
                    'task_trigger': self.date_trigger}
        self.assertJsonIsCorrect(task, expected)

    def test_as_json_running(self):
        task = ScheduledTask(name='test', status='stopped')
        expected = {'id': None,
                    'name': 'test',
                    'description': '',
                    'status': 'stopped',
                    'workflows': set(),
                    'task_trigger': {'type': 'unspecified',
                                     'args': {}}}
        self.assertJsonIsCorrect(task, expected)
