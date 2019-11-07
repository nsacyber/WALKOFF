import logging
from uuid import UUID

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.base import JobLookupError
from apscheduler.schedulers.base import STATE_PAUSED, STATE_RUNNING, STATE_STOPPED
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from starlette.requests import Request

from api.server.utils.problems import InvalidInputException

logger = logging.getLogger("API")


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


def construct_task_id(scheduled_task_id, workflow_id):
    """
    Constructs a task id

    Args:
        scheduled_task_id (UUID): Id of the scheduled task (presumably from the database)
        workflow_id (UUID): ID of the workflow to execute

    Returns:
        (str) A task id to use in the scheduler
    """
    return f"{scheduled_task_id}{task_id_separator}{workflow_id}"


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
    def __init__(self, app=None):
        self.scheduler = AsyncIOScheduler()
        self.id = 'controller'
        self.app = app

    def schedule_workflows(self, task_id, executable, workflow_ids, trigger):
        """
        Schedules a workflow for execution

        Args:
            task_id (UUID): Id of the scheduled task
            executable (func): A callable to execute must take in one argument -- a workflow id
            workflow_ids (iterable(UUID)): An iterable of workflow ids
            trigger (Trigger): The trigger to use for this scheduled task
        """

        # def execute(id_):
        #     with self.app.app_context():
        #         executable(id_)

        for workflow_id in workflow_ids:
            self.scheduler.add_job(executable, args=(workflow_id,),
                                   id=construct_task_id(task_id, workflow_id),
                                   trigger=trigger, replace_existing=True)

    def get_all_scheduled_workflows(self):
        """
        Gets all the scheduled workflows

        Returns:
             (dict{str: list[str]}) A dict of task_id to workflow execution ids
        """
        tasks = {}
        for job in self.scheduler.get_jobs():
            task, workflow_execution_id = split_task_id(job.id)
            if task not in tasks:
                tasks[task] = [workflow_execution_id]
            else:
                tasks[task].append(workflow_execution_id)
        return tasks

    def get_scheduled_workflows(self, task_id):
        """
        Gets all the scheduled workflow for a given task id

        Args:
            task_id (str): The task id

        Returns:
            (list[str]) A list fo workflow execution id associated with this task id
        """
        tasks = []
        for job in self.scheduler.get_jobs():
            task, workflow_execution_id = split_task_id(job.id)
            if task == task_id:
                tasks.append(workflow_execution_id)
        return tasks

    def update_workflows(self, task_id, trigger):
        """
        Updates the workflows for a given task id to use a different trigger

        Args:
            task_id (str|int): The task id to update
            trigger (Trigger): The new trigger to use
        """
        existing_tasks = {construct_task_id(task_id, workflow_execution_id) for workflow_execution_id in
                          self.get_scheduled_workflows(task_id)}
        for job_id in existing_tasks:
            self.scheduler.reschedule_job(job_id=job_id, trigger=trigger)

    def unschedule_workflows(self, task_id, workflow_execution_ids):
        """
        Unschedule a workflow

        Args:
            task_id (UUID): The task ID to unschedule
            workflow_execution_ids (list[UUID]): The list of workflow execution IDs to update
        """
        for workflow_execution_id in workflow_execution_ids:
            try:
                self.scheduler.remove_job(construct_task_id(task_id, workflow_execution_id))
            except JobLookupError:
                logger.warning('Cannot delete task {}. '
                               'No task found in scheduler'.format(construct_task_id(task_id, workflow_execution_id)))

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
            # return "Scheduler already running."
            raise InvalidInputException("start", "Scheduler", "", errors={"error": "Scheduler is already started"})

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
            self.scheduler.state = STATE_STOPPED
        else:
            logger.warning('Cannot stop scheduler. Scheduler is already stopped')
            # return "Scheduler already stopped."
            raise InvalidInputException("stopped", "Scheduler", "", errors={"error": "Scheduler is already stopped"})

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
            # return "Scheduler already paused."
            raise InvalidInputException("pause", "Scheduler", "", errors={"error": "Scheduler is already paused"})
        elif self.scheduler.state == STATE_STOPPED:
            logger.warning('Cannot pause scheduler. Scheduler is stopped')
            # return "Scheduler is in STOPPED state and cannot be paused."
            raise InvalidInputException("pause", "Scheduler", "", errors={"error": "Scheduler is  stopped"})
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
            # return "Scheduler is not in PAUSED state and cannot be resumed."
            raise InvalidInputException("resume", "Scheduler", "", errors={"error": "Scheduler already running."})
        return self.scheduler.state

    def pause_workflows(self, task_id, workflow_execution_ids):
        """
        Pauses some workflows associated with a task

        Args:
            task_id (int|str): The id of the task to pause
            workflow_execution_ids (list[str]): The list of workflow execution IDs to pause
        """
        for workflow_execution_id in workflow_execution_ids:
            job_id = construct_task_id(task_id, workflow_execution_id)
            try:
                self.scheduler.pause_job(job_id=job_id)
                logger.info('Paused job {0}'.format(job_id))
            except JobLookupError:
                logger.warning('Cannot pause scheduled workflow {}. Workflow ID not found'.format(job_id))

    def resume_workflows(self, task_id, workflow_execution_ids):
        """
        Resumes some workflows associated with a task

        Args:
            task_id: The id of the task to pause
            workflow_execution_i The list of workflow execution IDs to resume
        """
        for workflow_execution_id in workflow_execution_ids:
            job_id = construct_task_id(task_id, workflow_execution_id)
            try:
                self.scheduler.resume_job(job_id=job_id)
                logger.info('Resumed job {0}'.format(job_id))
            except JobLookupError:
                logger.warning('Cannot resume scheduled workflow {}. Workflow ID not found'.format(job_id))


def get_scheduler(request: Request):
    return request.state.scheduler
