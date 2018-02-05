import unittest

from walkoff.core.scheduler import *


class MockWorkflow(object):
    def __init__(self, id_, name=''):
        self.id = id_
        self.name = name
        self.other = 'other'
        self.children = []

    def execute(self):
        pass

    def read(self, reader=None):
        return {'name': self.name, 'id': self.id, 'other': self.other}

    def as_json(self):
        return {'name': self.name, 'id': self.id, 'other': self.other}


def execute(workflow_id):
    pass


class TestScheduler(unittest.TestCase):
    def setUp(self):
        self.scheduler = Scheduler()
        self.trigger = DateTrigger(run_date='2050-12-31 23:59:59')
        self.trigger2 = DateTrigger(run_date='2050-12-31 23:59:59')

    def test_init(self):
        self.assertEqual(self.scheduler.id, 'controller')

    def assertSchedulerHasJobs(self, expected_jobs):
        self.assertSetEqual({job.id for job in self.scheduler.scheduler.get_jobs()}, expected_jobs)

    def assertSchedulerStateIs(self, state):
        self.assertEqual(self.scheduler.scheduler.state, state)

    def add_tasks(self, task_id, workflow_ids, trigger):
        self.scheduler.schedule_workflows(task_id, execute, workflow_ids, trigger)

    def add_task_set_one(self):
        task_id = 'task'
        workflow_ids = ['a', 'b', 'c']
        self.add_tasks(task_id, workflow_ids, self.trigger)
        return task_id, workflow_ids

    def add_task_set_two(self):
        task_id = 'task2'
        workflow_ids = ['d', 'e', 'f']
        self.add_tasks(task_id, workflow_ids, self.trigger2)
        return task_id, workflow_ids

    def test_schedule_workflows(self):
        task_id, workflow_ids = self.add_task_set_one()
        self.assertSchedulerHasJobs({construct_task_id(task_id, workflow_id) for workflow_id in workflow_ids})
        for job in self.scheduler.scheduler.get_jobs():
            self.assertEqual(job.trigger, self.trigger)


    def test_get_all_scheduled_workflows(self):
        task_id, workflow_ids = self.add_task_set_one()
        task_id2, workflow_ids2 = self.add_task_set_two()
        expected = {task_id: workflow_ids, task_id2: workflow_ids2}
        self.assertDictEqual(self.scheduler.get_all_scheduled_workflows(), expected)

    def test_get_all_scheduled_workflows_no_workflows(self):
        self.assertDictEqual(self.scheduler.get_all_scheduled_workflows(), {})

    def test_get_scheduled_workflows(self):
        task_id, workflow_ids = self.add_task_set_one()
        task_id2, workflow_ids2 = self.add_task_set_two()
        self.assertListEqual(self.scheduler.get_scheduled_workflows(task_id), workflow_ids)
        self.assertListEqual(self.scheduler.get_scheduled_workflows(task_id2), workflow_ids2)

    def test_get_scheduled_workflows_no_workflows_in_scheduler(self):
        self.assertListEqual(self.scheduler.get_scheduled_workflows('any'), [])

    def test_get_scheduled_workflows_no_matching_task_id(self):
        self.add_task_set_one()
        self.add_task_set_two()
        self.assertListEqual(self.scheduler.get_scheduled_workflows('invalid'), [])

    def test_update_workflows(self):
        task_id, _ = self.add_task_set_one()
        self.scheduler.update_workflows(task_id, self.trigger2)
        for job in self.scheduler.scheduler.get_jobs():
            self.assertEqual(job.trigger, self.trigger2)

    def test_update_workflows_no_matching_task_id(self):
        self.add_task_set_one()
        self.scheduler.update_workflows('invalid', self.trigger2)
        for job in self.scheduler.scheduler.get_jobs():
            self.assertEqual(job.trigger, self.trigger)

    def test_unschedule_workflows_all_for_task_id(self):
        task_id, workflow_ids = self.add_task_set_one()
        task_id2, workflow_ids2 = self.add_task_set_two()
        self.scheduler.unschedule_workflows(task_id, workflow_ids)
        self.assertDictEqual(self.scheduler.get_all_scheduled_workflows(), {task_id2: workflow_ids2})

    def test_unschedule_workflows_some_for_task_id(self):
        task_id, workflow_ids = self.add_task_set_one()
        ids_to_remove, remaining = workflow_ids[:2], workflow_ids[2:]
        task_id2, workflow_ids2 = self.add_task_set_two()
        self.scheduler.unschedule_workflows(task_id, ids_to_remove)
        self.assertDictEqual(self.scheduler.get_all_scheduled_workflows(),
                             {task_id: remaining, task_id2: workflow_ids2})

    def test_unschedule_workflows_some_for_task_id_with_invalid(self):
        task_id, workflow_ids = self.add_task_set_one()
        workflow_ids.extend(['junk1', 'junk2', 'junk3'])
        task_id2, workflow_ids2 = self.add_task_set_two()
        self.scheduler.unschedule_workflows(task_id, workflow_ids)
        self.assertDictEqual(self.scheduler.get_all_scheduled_workflows(), {task_id2: workflow_ids2})

    def test_start_from_stopped(self):
        self.assertEqual(self.scheduler.start(), STATE_RUNNING)
        self.assertSchedulerStateIs(STATE_RUNNING)

    def test_stop_from_stopped(self):
        self.scheduler.start()
        self.assertEqual(self.scheduler.stop(), STATE_STOPPED)
        self.assertSchedulerStateIs(STATE_STOPPED)

    def test_pause_from_stopped(self):
        self.scheduler.start()
        self.assertEqual(self.scheduler.pause(), STATE_PAUSED)
        self.assertSchedulerStateIs(STATE_PAUSED)

    def test_resume_from_stopped(self):
        self.scheduler.start()
        self.assertEqual(self.scheduler.resume(), "Scheduler is not in PAUSED state and cannot be resumed.")
        self.assertSchedulerStateIs(STATE_RUNNING)

    def test_start_from_running(self):
        self.scheduler.start()
        self.assertEqual(self.scheduler.start(), "Scheduler already running.")
        self.assertSchedulerStateIs(STATE_RUNNING)

    def test_stop_from_running(self):
        self.scheduler.start()
        self.assertEqual(self.scheduler.stop(), STATE_STOPPED)
        self.assertSchedulerStateIs(STATE_STOPPED)

    def test_pause_from_running(self):
        self.scheduler.start()
        self.assertEqual(self.scheduler.pause(), STATE_PAUSED)
        self.assertSchedulerStateIs(STATE_PAUSED)

    def test_resume_from_running(self):
        self.scheduler.start()
        self.assertEqual(self.scheduler.resume(), "Scheduler is not in PAUSED state and cannot be resumed.")
        self.assertSchedulerStateIs(STATE_RUNNING)

    def test_start_from_paused(self):
        self.scheduler.start()
        self.scheduler.pause()
        self.assertEqual(self.scheduler.start(), "Scheduler already running.")
        self.assertSchedulerStateIs(STATE_PAUSED)

    def test_stop_from_paused(self):
        self.scheduler.start()
        self.scheduler.pause()
        self.assertEqual(self.scheduler.stop(), STATE_STOPPED)
        self.assertSchedulerStateIs(STATE_STOPPED)

    def test_pause_from_paused(self):
        self.scheduler.start()
        self.scheduler.pause()
        self.assertEqual(self.scheduler.pause(), "Scheduler already paused.")
        self.assertSchedulerStateIs(STATE_PAUSED)

    def test_resume_from_paused(self):
        self.scheduler.start()
        self.scheduler.pause()
        self.assertEqual(self.scheduler.resume(), STATE_RUNNING)
        self.assertSchedulerStateIs(STATE_RUNNING)
    