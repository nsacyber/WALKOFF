import datetime
import unittest

from apscheduler.util import convert_to_datetime
from tzlocal import get_localzone

from walkoff.core.scheduler import *


class TestSchedulerUtils(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datestr1 = '2017-10-30 12:03:36'
        cls.date1 = convert_to_datetime(cls.datestr1, get_localzone(), 'run_date')

    def test_construct_task_id(self):
        task_id_workflow_id_pairs = {('task', 'work'): 'task-work',
                                      ('', 'work'): '-work',
                                      ('task', ''): 'task-'}
        for input_, output in task_id_workflow_id_pairs.items():
            self.assertEqual(construct_task_id(*input_), output)

    def test_split_task_id(self):
        task_id_workflow_id_pairs = {'task-work': ['task', 'work'],
                                      '-work': ['', 'work'],
                                      'task-': ['task', '']}
        for input_, output in task_id_workflow_id_pairs.items():
            self.assertListEqual(split_task_id(input_), output)

    def test_split_task_id_too_many_separators(self):
        id_ = task_id_separator.join(['a', 'b', 'c'])
        task_id = construct_task_id('task', id_)
        self.assertListEqual(split_task_id(task_id), ['task', 'a'])

    def test_construct_date_scheduler(self):
        args = {'type': 'date', 'args': {'run_date': self.datestr1}}
        trigger = construct_trigger(args)
        self.assertIsInstance(trigger, DateTrigger)
        self.assertEqual(trigger.run_date, self.date1)

    def test_construct_date_scheduler_invalid_date(self):
        args = {'type': 'date', 'args': {'date': '2017-14-30 12:03:36'}}
        with self.assertRaises(InvalidTriggerArgs):
            construct_trigger(args)

    def test_construct_date_scheduler_invalid_arg_structure(self):
        args = {'type': 'date', 'args': {'junk': '2017-11-30 12:03:36'}}
        with self.assertRaises(InvalidTriggerArgs):
            construct_trigger(args)

    def test_construct_interval_scheduler(self):
        args = {'type': 'interval', 'args': {'start_date': self.datestr1,
                                             'weeks': 4,
                                             'seconds': 1}}
        trigger = construct_trigger(args)
        self.assertIsInstance(trigger, IntervalTrigger)
        expected_interval = datetime.timedelta(weeks=4, seconds=1)
        self.assertEqual(trigger.interval, expected_interval)
        self.assertEqual(trigger.start_date, self.date1)

    def test_construct_interval_scheduler_invalid_interval(self):
        args = {'type': 'interval', 'args': {'date': '2017-14-30 12:03:36'}}
        with self.assertRaises(InvalidTriggerArgs):
            construct_trigger(args)

    def test_construct_interval_scheduler_invalid_arg_structure(self):
        args = {'type': 'interval', 'args': {'start_date': '2017-11-30 12:03:36',
                                             'day_of_week': 3}}
        with self.assertRaises(InvalidTriggerArgs):
            construct_trigger(args)

    def test_construct_cron_scheduler(self):
        args = {'type': 'cron', 'args': {'start_date': self.datestr1,
                                         'week': '*/4'}}
        trigger = construct_trigger(args)
        self.assertIsInstance(trigger, CronTrigger)

    def test_construct_cron_scheduler_invalid_interval(self):
        args = {'type': 'cron', 'args': {'date': '2017-14-30 12:03:36'}}
        with self.assertRaises(InvalidTriggerArgs):
            construct_trigger(args)

    def test_construct_cron_scheduler_invalid_arg_structure(self):
        args = {'type': 'cron', 'args': {'start_date': '2017-11-30 12:03:36',
                                         'day_of_week': 'aaaaaaaaa'}}
        with self.assertRaises(InvalidTriggerArgs):
            construct_trigger(args)

    def test_construct_scheduler_invalid_type(self):
        args = {'type': 'invalid', 'args': {'start_date': '2017-11-30 12:03:36',
                                            'day_of_week': 3}}
        with self.assertRaises(InvalidTriggerArgs):
            construct_trigger(args)
