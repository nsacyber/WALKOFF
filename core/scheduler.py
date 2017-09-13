from apscheduler.events import (EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_REMOVED,
                                EVENT_SCHEDULER_START, EVENT_SCHEDULER_SHUTDOWN,
                                EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED)
from apscheduler.schedulers.base import STATE_PAUSED, STATE_RUNNING, STATE_STOPPED
from apscheduler.schedulers.gevent import GeventScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.base import JobLookupError
import logging
from core.case import callbacks

logger = logging.getLogger(__name__)


class InvalidTriggerArgs(Exception):
    def __init__(self, message):
        super(Exception, self).__init__(message)


def construct_trigger(trigger_args):
    trigger_type = trigger_args['type']
    trigger_args = trigger_args['args']
    try:
        if trigger_type == 'date':
            return DateTrigger(**trigger_args)
        elif trigger_type == 'interval':
            return IntervalTrigger(**trigger_args)
        elif trigger_type == 'cron':
            return CronTrigger(**trigger_args)
        else:
            raise InvalidTriggerArgs(
                'Invalid scheduler type {0} with args {1}.'.format(trigger_type, trigger_args))
    except (KeyError, ValueError, TypeError):
        raise InvalidTriggerArgs('Invalid scheduler arguments')

task_id_separator = '-'


def construct_task_id(scheduled_task_id, workflow_uid):
    """
    Constructs a task id

    Args:
        scheduled_task_id (int|str): Id of the scheduled task (presumably from the database)
        workflow_uid (str): UUID of the workflow to execute

    Returns:
        (str) A task id to use in the scheduler
    """
    return '{0}{1}{2}'.format(scheduled_task_id, task_id_separator, workflow_uid)


def split_task_id(task_id):
    """
    Extracts the scheduled task id and workflow id from the task id

    Args:
        task_id (str): The task id

    Returns:
        (list[str]) A list in which the first two elements are the scheduled task id and the workflow id respectively
    """
    return task_id.split(task_id_separator)[:2]


# A thin wrapper around APScheduler
class Scheduler(object):

    def __init__(self):
        self.scheduler = GeventScheduler()
        self.scheduler.add_listener(self.__scheduler_listener(),
                                    EVENT_SCHEDULER_START | EVENT_SCHEDULER_SHUTDOWN
                                    | EVENT_SCHEDULER_PAUSED | EVENT_SCHEDULER_RESUMED
                                    | EVENT_JOB_ADDED | EVENT_JOB_REMOVED
                                    | EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        self.uid = 'controller'

    def schedule_workflows(self, task_id, executable, workflows, trigger):
        """
        Schedules a workflow for execution

        Args:
            task_id (int): Id of the scheduled task
            executable (func): A callable to execute must take in two arguments -- a playbook name and a workflow name
            workflows (tuple(str)): A tuple of playbook name, workflow name, and workflow uid
            trigger (Trigger): The trigger to use for this scheduled task
        """
        for playbook_name, workflow_name, uid in workflows:
            self.scheduler.add_job(executable, args=(playbook_name, workflow_name),
                                   id=construct_task_id(task_id, uid),
                                   trigger=trigger, replace_existing=True)

    def get_all_scheduled_workflows(self):
        """
        Gets all the scheduled workflows

        Returns:
             (dict{str: list[str]}) A dict of task_id to workflow uids
        """
        tasks = {}
        for job in self.scheduler.get_jobs():
            task, workflow_uid = split_task_id(job.id)
            if task not in tasks:
                tasks[task] = [workflow_uid]
            else:
                tasks[task].append(workflow_uid)
        return tasks

    def get_scheduled_workflows(self, task_id):
        """
        Gets all the scheduled worfklows for a given task id

        Args:
            task_id (str): The task id

        Returns:
            (list[str]) A list fo workflow uid associated with this task id
        """
        tasks = []
        for job in self.scheduler.get_jobs():
            task, workflow_uid = split_task_id(job.id)
            if task == task_id:
                tasks.append(workflow_uid)
        return tasks

    def update_workflows(self, task_id, trigger):
        """
        Updates the workflows for a given task id to use a different trigger

        Args:
            task_id (str|int): The task id to update
            trigger (Trigger): The new trigger to use
        """
        existing_tasks = {construct_task_id(task_id, uid) for uid in self.get_scheduled_workflows(task_id)}
        for job_id in existing_tasks:
            self.scheduler.reschedule_job(job_id=job_id, trigger=trigger)

    def unschedule_workflows(self, task_id, workflow_uids):
        """
        Unschedules a workflow

        Args:
            task_id (str|int): The task ID to unschedule
            workflow_uids (list[str]): The list of workflow UIDs to update
        """
        for workflow_uid in workflow_uids:
            try:
                self.scheduler.remove_job(construct_task_id(task_id, workflow_uid))
            except JobLookupError:
                logger.warning('Cannot delete task {}. '
                               'No task found in scheduler'.format(construct_task_id(task_id, workflow_uid)))

    def start(self):
        """Starts the scheduler for active execution. This function must be called before any workflows are executed.

        Returns:
            The state of the scheduler if successful, error message if scheduler is in "stopped" state.
        """
        if self.scheduler.state == STATE_STOPPED:
            logger.info('Starting scheduler')
            self.scheduler.start()
        else:
            logger.warning('Cannot start scheduler. Scheduler is already running or is paused')
            return "Scheduler already running."
        return self.scheduler.state

    def stop(self, wait=True):
        """Stops active execution.

        Args:
            wait (bool, optional): Boolean to synchronously or asynchronously wait for the scheduler to shutdown.
                Default is True.

        Returns:
            The state of the scheduler if successful, error message if scheduler is already in "stopped" state.
        """
        if self.scheduler.state != STATE_STOPPED:
            logger.info('Stopping scheduler')
            self.scheduler.shutdown(wait=wait)
        else:
            logger.warning('Cannot stop scheduler. Scheduler is already stopped')
            return "Scheduler already stopped."
        return self.scheduler.state

    def pause(self):
        """Pauses active execution.

        Returns:
            The state of the scheduler if successful, error message if scheduler is not in the "running" state.
        """
        if self.scheduler.state == STATE_RUNNING:
            logger.info('Pausing scheduler')
            self.scheduler.pause()
        elif self.scheduler.state == STATE_PAUSED:
            logger.warning('Cannot pause scheduler. Scheduler is already paused')
            return "Scheduler already paused."
        elif self.scheduler.state == STATE_STOPPED:
            logger.warning('Cannot pause scheduler. Scheduler is stopped')
            return "Scheduler is in STOPPED state and cannot be paused."
        return self.scheduler.state

    def resume(self):
        """Resumes active execution.

        Returns:
            The state of the scheduler if successful, error message if scheduler is not in the "paused" state.
        """
        if self.scheduler.state == STATE_PAUSED:
            logger.info('Resuming scheduler')
            self.scheduler.resume()
        else:
            logger.warning("Scheduler is not in PAUSED state and cannot be resumed.")
            return "Scheduler is not in PAUSED state and cannot be resumed."
        return self.scheduler.state

    def pause_workflows(self, task_id, workflow_uids):
        """
        Pauses some workflows associated with a task

        Args:
            task_id (int|str): The id of the task to pause
            workflow_uids (list[str]): The list of workflow UIDs to pause
        """
        for workflow_uid in workflow_uids:
            job_id = construct_task_id(task_id, workflow_uid)
            try:
                self.scheduler.pause_job(job_id=job_id)
                logger.info('Paused job {0}'.format(job_id))
            except JobLookupError:
                logger.warning('Cannot pause scheduled workflow {}. Workflow ID not found'.format(job_id))

    def resume_workflows(self, task_id, workflow_uids):
        """
        Resumes some workflows associated with a task 

        Args:
            task_id (int|str): The id of the task to pause
            workflow_uids (list[str]): The list of workflow UIDs to resume
        """
        for workflow_uid in workflow_uids:
            job_id = construct_task_id(task_id, workflow_uid)
            try:
                self.scheduler.resume_job(job_id=job_id)
                logger.info('Resumed job {0}'.format(job_id))
            except JobLookupError:
                logger.warning('Cannot resume scheduled workflow {}. Workflow ID not found'.format(job_id))

    def __scheduler_listener(self):
        event_selector_map = {EVENT_SCHEDULER_START: (lambda: callbacks.SchedulerStart.send(self)),
                              EVENT_SCHEDULER_SHUTDOWN: (lambda: callbacks.SchedulerShutdown.send(self)),
                              EVENT_SCHEDULER_PAUSED: (lambda: callbacks.SchedulerPaused.send(self)),
                              EVENT_SCHEDULER_RESUMED: (lambda: callbacks.SchedulerResumed.send(self)),
                              EVENT_JOB_ADDED: (lambda: callbacks.SchedulerJobAdded.send(self)),
                              EVENT_JOB_REMOVED: (lambda: callbacks.SchedulerJobRemoved.send(self)),
                              EVENT_JOB_EXECUTED: (lambda: callbacks.SchedulerJobExecuted.send(self)),
                              EVENT_JOB_ERROR: (lambda: callbacks.SchedulerJobError.send(self))}

        def event_selector(event):
            try:
                event_selector_map[event.code]()
            except KeyError:
                logger.error('Unknown event sent triggered in scheduler {}'.format(event))

        return event_selector
