import os
from collections import namedtuple
from concurrent import futures
from copy import deepcopy
from os import sep
from xml.etree import cElementTree
import uuid

from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, \
    EVENT_SCHEDULER_START, EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED
from apscheduler.schedulers.base import STATE_PAUSED, STATE_RUNNING, STATE_STOPPED
from apscheduler.schedulers.gevent import GeventScheduler

import core.config.config
import core.config.paths
from core import workflow as wf
from core.case import callbacks
from core.case import subscription
from core.helpers import locate_workflows_in_directory, construct_workflow_name_key, extract_workflow_name

_WorkflowKey = namedtuple('WorkflowKey', ['playbook', 'workflow'])

pool = None
workflows = None
threading_is_initialized = False


def initialize_threading():
    """Initializes the threadpool.
    """
    global pool
    global workflows
    global threading_is_initialized

    workflows = []

    pool = futures.ThreadPoolExecutor(max_workers=core.config.config.num_threads)
    threading_is_initialized = True


def shutdown_pool():
    """Shuts down the threadpool.
    """
    global pool
    global workflows
    global threading_is_initialized

    for future in futures.as_completed(workflows):
        future.result(timeout=core.config.config.threadpool_shutdown_timeout_sec)
    pool.shutdown(wait=False)

    workflows = []
    threading_is_initialized = False


def execute_workflow_worker(workflow, start, subs):
    """Executes the workflow in a multi-threaded fashion.
    Args:
        workflow (Workflow): The workflow to be executed.
        start (str, otpional): Name of the first step to be executed in the workflow.
        subs (Subscription): The current subscriptions. This is necessary for resetting the subscriptions.
    Returns:
        "Done" when the workflow has finished execution.
    """
    subscription.set_subscriptions(subs)
    workflow.execute(start=start)
    return "done"


class Controller(object):
    def __init__(self, name='defaultController', workflows_path=core.config.paths.workflows_path):
        """Initializes a Controller object.
        Args:
            name (str, optional): Name for the controller.
            workflows_path (str, optional): Path to the workflows.
        """
        self.name = name
        self.workflows = {}
        self.load_all_workflows_from_directory(path=workflows_path)
        self.instances = {}
        self.tree = None

        self.scheduler = GeventScheduler()
        self.scheduler.add_listener(self.__scheduler_listener(),
                                    EVENT_SCHEDULER_START | EVENT_SCHEDULER_SHUTDOWN
                                    | EVENT_SCHEDULER_PAUSED | EVENT_SCHEDULER_RESUMED
                                    | EVENT_JOB_ADDED | EVENT_JOB_REMOVED
                                    | EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        self.ancestry = [self.name]
        self.paused_workflows = {}

    def reconstruct_ancestry(self):
        """Reconstructs the ancestry list field of a workflow in case it changes.
        """
        for key in self.workflows:
            self.workflows[key].reconstruct_ancestry(self.ancestry)

    def load_workflow_from_file(self, path, workflow_name, name_override=None, playbook_override=None):
        """Loads a workflow from a file.
        Args:
            path (str): Path to the workflow.
            workflow_name (str): Name of the workflow to load.
            name_override (str, optional): Name that the workflow should be changed to.
            playbook_override (str, optional): Name that the playbook should be changed to.
        Returns:
            True on success, False otherwise.
        """
        self.tree = cElementTree.ElementTree(file=path)
        playbook_name = playbook_override if playbook_override else os.path.splitext(os.path.basename(path))[0]
        for workflow in self.tree.iter(tag='workflow'):
            current_workflow_name = workflow.get('name')
            if current_workflow_name == workflow_name:
                if name_override:
                    workflow_name = name_override
                name = construct_workflow_name_key(playbook_name, workflow_name)
                key = _WorkflowKey(playbook_name, workflow_name)
                self.workflows[key] = wf.Workflow(name=name,
                                                  xml=workflow,
                                                  parent_name=self.name,
                                                  playbook_name=playbook_name)
                break
        else:
            return False

        self.add_child_workflows()
        self.add_workflow_scheduled_jobs()
        return True

    def load_workflows_from_file(self, path, name_override=None, playbook_override=None):
        """Loads multiple workloads from a file
        Args:
            path (str): Path to the workflow.
            name_override (str, optional): Name that the workflow should be changed to. 
            playbook_override (str, optional): Name that the playbook should be changed to.
        """
        self.tree = cElementTree.ElementTree(file=path)
        playbook_name = playbook_override if playbook_override else os.path.splitext(os.path.basename(path))[0]
        for workflow in self.tree.iter(tag='workflow'):
            workflow_name = name_override if name_override else workflow.get('name')
            name = construct_workflow_name_key(playbook_name, workflow_name)
            key = _WorkflowKey(playbook_name, workflow_name)
            self.workflows[key] = wf.Workflow(name=name,
                                              xml=workflow,
                                              parent_name=self.name,
                                              playbook_name=playbook_name)
        self.add_child_workflows()
        self.add_workflow_scheduled_jobs()

    def load_all_workflows_from_directory(self, path=None):
        """Loads all workflows from a directory.
        Args:
            path (str, optional): Path to the directory to load from. Defaults to the configuration workflows_path. 
        """
        if path is None:
            path = core.config.paths.workflows_path
        for workflow in locate_workflows_in_directory(path):
            self.load_workflows_from_file(os.path.join(path, workflow))

    def add_child_workflows(self):
        for workflow in self.workflows:
            playbook_name = workflow.playbook
            children = self.workflows[workflow].options.children
            for child in children:
                workflow_key = _WorkflowKey(playbook_name, extract_workflow_name(child, playbook_name=playbook_name))
                if workflow_key in self.workflows:
                    children[child] = self.workflows[workflow_key]

    def add_workflow_scheduled_jobs(self):
        """Schedules the workflow to run based on workflow options.
        """
        for workflow in self.workflows:
            if (self.workflows[workflow].options.enabled
                    and self.workflows[workflow].options.scheduler['autorun'] == 'true'):
                schedule_type = self.workflows[workflow].options.scheduler['type']
                schedule = self.workflows[workflow].options.scheduler['args']
                self.scheduler.add_job(self.workflows[workflow].execute, trigger=schedule_type, replace_existing=True,
                                       **schedule)

    def create_workflow_from_template(self,
                                      playbook_name,
                                      workflow_name,
                                      template_playbook='emptyWorkflow',
                                      template_name='emptyWorkflow'):
        """Creates a workflow from a workflow template.
        Args:
            playbook_name (str): The name of the new playbook. 
            workflow_name (str): The name of the new workflow.
            template_playbook (str): The name of the playbook template to load. Default is "emptyWorkflow".
            template_name (str): The name of the workflow template to load. Default is "emptyWorkflow".
        Returns:
            True on success, False if otherwise.
        """
        path = '{0}{1}{2}.workflow'.format(core.config.paths.templates_path, sep, template_playbook)
        return self.load_workflow_from_file(path=path,
                                            workflow_name=template_name,
                                            name_override=workflow_name,
                                            playbook_override=playbook_name)

    def create_playbook_from_template(self, playbook_name,
                                      template_playbook='emptyWorkflow'):
        """Creates a playbook from a playbook template.
        Args:
            playbook_name (str): The name of the new playbook.
            template_playbook (str): The name of the playbook template to load. Default is "emptyWorkflow".
        """
        # TODO: Need a handler for returning workflow key and status
        path = '{0}{1}{2}.workflow'.format(core.config.paths.templates_path, sep, template_playbook)
        self.load_workflows_from_file(path=path, playbook_override=playbook_name)

    def remove_workflow(self, playbook_name, workflow_name):
        """Removes a workflow.
        Args:
            playbook_name (str): Playbook name under which the workflow is located.
            workflow_name (str): The name of the workflow to remove.
        Returns:
            True on success, False otherwise.
        """
        name = _WorkflowKey(playbook_name, workflow_name)
        if name in self.workflows:
            del self.workflows[name]
            return True
        return False

    def remove_playbook(self, playbook_name):
        """Removes a playbook and all workflows within it.
        Args:
            playbook_name (str): The name of the playbook to remove.
        Returns:
            True on success, False otherwise.
        """
        for name in [workflow for workflow in self.workflows if workflow.playbook == playbook_name]:
            del self.workflows[name]
            return True
        return False

    def get_all_workflows(self):
        """Gets all of the currently loaded workflows.
        Returns:
            A dict with key being the playbook, mapping to a list of workflow names for each playbook.
        """
        result = {}
        for key in self.workflows.keys():
            if key.playbook not in result:
                result[key.playbook] = []
            result[key.playbook].append(key.workflow)
        return result

    def get_all_playbooks(self):
        """Gets a list of all playbooks.
        Returns:
            A list containing all currently loaded playbook names.
        """
        return list(set(key.playbook for key in self.workflows.keys()))

    def is_workflow_registered(self, playbook_name, workflow_name):
        """Checks whether or not a workflow is currently registered in the system.
        Args:
            playbook_name (str): Playbook name under which the workflow is located.
            workflow_name (str): The name of the workflow.
        Returns:
            True if the workflow is registered, false otherwise.
        """
        return _WorkflowKey(playbook_name, workflow_name) in self.workflows

    def is_playbook_registered(self, playbook_name):
        """Checks whether or not a playbook is currently registered in the system.
        Args:
            playbook_name (str): The name of the playbook.
        Returns:
            True if the playbook is registered, false otherwise.
        """
        return any(workflow_key.playbook == playbook_name for workflow_key in self.workflows)

    def update_workflow_name(self, old_playbook, old_workflow, new_playbook, new_workflow):
        """Update the name of a workflow.
        Args:
            old_playbook (str): Name of the current playbook.
            old_workflow (str): Name of the current workflow.
            new_playbook (str): The new name of the playbook.
            new_workflow (str): The new name of the workflow.
        """
        old_key = _WorkflowKey(old_playbook, old_workflow)
        new_key = _WorkflowKey(new_playbook, new_workflow)
        self.workflows[new_key] = self.workflows.pop(old_key)
        self.workflows[new_key].name = construct_workflow_name_key(new_playbook, new_workflow)
        self.workflows[new_key].reconstruct_ancestry([self.name])

    def update_playbook_name(self, old_playbook, new_playbook):
        """Update the name of a playbook.
        Args:
            old_playbook (str): Name of the current playbook.
            new_playbook (str): The new name of the playbook.
        """
        for key in [name for name in self.workflows.keys() if name.playbook == old_playbook]:
            self.update_workflow_name(old_playbook, key.workflow, new_playbook, key.workflow)

    def add_workflow_breakpoint_steps(self, playbook_name, workflow_name, steps):
        """Adds a breakpoint (for debugging purposes) in the specified steps.
        Args:
            playbook_name (str): Playbook name under which the workflow is located.
            workflow_name (str): The name of the workflow under which the steps are located.
            steps (list[str]): The list of step names for which the user would like to pause execution.
        """
        workflow = self.get_workflow(playbook_name, workflow_name)
        if workflow:
            for step in steps:
                workflow.breakpoint_steps.append(step)

    def execute_workflow(self, playbook_name, workflow_name, start='start'):
        """Executes a workflow.
        Args:
            playbook_name (str): Playbook name under which the workflow is located.
            workflow_name (str): Workflow to execute.
            start (str, optional): The name of the first step. Defaults to "start".
        """
        global pool
        global workflows
        global threading_is_initialized

        key = _WorkflowKey(playbook_name, workflow_name)
        if key in self.workflows:
            workflow = self.workflows[key]
            subs = deepcopy(subscription.subscriptions)

            # If threading has not been initialized, initialize it.
            if not threading_is_initialized:
                initialize_threading()
            workflows.append(pool.submit(execute_workflow_worker, workflow, start, subs))
            callbacks.SchedulerJobExecuted.send(self)

    def get_workflow(self, playbook_name, workflow_name):
        """Get a workflow object.
        Args:
            playbook_name (str): Playbook name under which the workflow is located.
            workflow_name (str): The name of the workflow.
        Returns:
            The workflow object if found, else None.
        """
        key = _WorkflowKey(playbook_name, workflow_name)
        if key in self.workflows:
            return self.workflows[key]
        return None

    def get_all_workflows_by_playbook(self, playbook_name):
        """Get a list of all workflow objects in a playbook.
        Args:
            playbook_name: The name of the playbook.
        Returns:
            A list of all workflow objects in a playbook.
        """
        _workflows = []
        for key in self.workflows.keys():
            if key.playbook == playbook_name:
                _workflows.append(self.workflows[key].name)
        return _workflows

    def playbook_to_xml(self, playbook_name):
        """Returns the XML representation of a playbook.
        Args:
            playbook_name: The name of the playbook.
        Returns:
            The XML representation of the playbook if the playbook has any workflows under it, else None.
        """
        all_workflows = [workflow for key, workflow in self.workflows.items() if key.playbook == playbook_name]
        if all_workflows:
            xml = cElementTree.Element('workflows')
            for workflow in all_workflows:
                xml.append(workflow.to_xml())
            return xml
        else:
            return None

    def copy_workflow(self, old_playbook_name, new_playbook_name, old_workflow_name, new_workflow_name):
        """Duplicates a workflow into its current playbook, or a different playbook.
        Args:
            old_playbook_name (str): Playbook name under which the workflow is located.
            new_playbook_name (str): The new playbook name for the duplicated workflow.
            old_workflow_name (str): The name of the workflow to be copied.
            new_workflow_name (str): The new name of the duplicated workflow.
        """
        workflow = self.get_workflow(old_playbook_name, old_workflow_name)
        workflow_copy = deepcopy(workflow)
        workflow_copy.playbook_name = new_playbook_name
        workflow_copy.name = construct_workflow_name_key(new_playbook_name, new_workflow_name)

        key = _WorkflowKey(new_playbook_name, new_workflow_name)
        self.workflows[key] = workflow_copy
        self.workflows[key].reconstruct_ancestry([self.name])

    def copy_playbook(self, old_playbook_name, new_playbook_name):
        """Copies a playbook
        Args:
            old_playbook_name (str): The name of the playbook to be copied.
            new_playbook_name (str): The new name of the duplicated playbook.
        """
        for workflow in [workflow.workflow for workflow in self.workflows if workflow.playbook == old_playbook_name]:
            self.copy_workflow(old_playbook_name, new_playbook_name, workflow, workflow)

    def pause_workflow(self, playbook_name, workflow_name):
        """Pauses a workflow that is currently executing.
        Args:
            playbook_name (str): Playbook name under which the workflow is located.
            workflow_name (str): The name of the workflow.
        Returns:
            A randomly-generated key that needs to be used in order to resume the workflow. This feature is added for
            security purposes.
        """
        workflow = self.get_workflow(playbook_name, workflow_name)
        wf_key = _WorkflowKey(playbook_name, workflow_name)
        self.paused_workflows[wf_key] = uuid.uuid4()
        if workflow:
            workflow.pause()
        return self.paused_workflows[wf_key].hex

    def resume_workflow(self, playbook_name, workflow_name, validate_uuid):
        """Resumes a workflow that has been paused.
        Args:
            playbook_name (str): Playbook name under which the workflow is located.
            workflow_name (str): The name of the workflow.
            validate_uuid (str): The randomly-generated hexadecimal key that was returned from pause_workflow(). This
            is needed to resume a workflow for security purposes.
        Returns:
            "Success" if it is successful, or other error messages.
        """
        workflow = self.get_workflow(playbook_name, workflow_name)
        wf_key = _WorkflowKey(playbook_name, workflow_name)
        if workflow:
            if validate_uuid == self.paused_workflows[wf_key].hex:
                workflow.resume()
                return "success"
            else:
                return "invalid UUID"
        return "error: invalid playbook and/or workflow name"

    def resume_breakpoint_step(self, playbook_name, workflow_name):
        """Resumes a step that has been specified as a breakpoint.
        Args:
            playbook_name (str): Playbook name under which the workflow is located.
            workflow_name (str): The name of the workflow.
        """
        workflow = self.get_workflow(playbook_name, workflow_name)
        if workflow:
            workflow.resume_breakpoint_step()

    # Starts active execution
    def start(self):
        """Starts the scheduler for active execution. This function must be called before any workflows are executed.
        Returns:
            The state of the scheduler if successful, error message if scheduler is in "stopped" state.
        """
        if self.scheduler.state != STATE_RUNNING and self.scheduler.state != STATE_PAUSED:
            self.scheduler.start()
        else:
            return "Scheduler already running."
        return self.scheduler.state

    # Stops active execution
    def stop(self, wait=True):
        """Stops active execution. 
        Args:
            wait (bool, optional): Boolean to synchronously or asynchronously wait for the scheduler to shutdown.
                Default is True.
        Returns:
            The state of the scheduler if successful, error message if scheduler is already in "stopped" state.
        """
        if self.scheduler.state != STATE_STOPPED:
            self.scheduler.shutdown(wait=wait)
        else:
            return "Scheduler already stopped."
        return self.scheduler.state

    # Pauses active execution
    def pause(self):
        """Pauses active execution.
        Returns:
            The state of the scheduler if successful, error message if scheduler is not in the "running" state.
        """
        if self.scheduler.state == STATE_RUNNING:
            self.scheduler.pause()
        elif self.scheduler.state == STATE_PAUSED:
            return "Scheduler already paused."
        elif self.scheduler.state == STATE_STOPPED:
            return "Scheduler is in STOPPED state and cannot be paused."
        return self.scheduler.state

    # Resumes active execution
    def resume(self):
        """Resumes active execution.
        Returns:
            The state of the scheduler if successful, error message if scheduler is not in the "paused" state.
        """
        if self.scheduler.state == STATE_PAUSED:
            self.scheduler.resume()
        else:
            return "Scheduler is not in PAUSED state and cannot be resumed."
        return self.scheduler.state

    # Pauses active execution of specific job
    def pause_job(self, job_id):
        """Pauses active execution of a specific job.
        Args:
            job_id (str): ID of the job to pause.
        """
        self.scheduler.pause_job(job_id=job_id)

    # Resumes active execution of specific job
    def resume_job(self, job_id):
        """Resumes active execution of a specific job.
        Args:
            job_id (str): ID of the job to resume.
        """
        self.scheduler.resume_job(job_id=job_id)

    # Returns jobs scheduled for active execution
    def get_scheduled_jobs(self):
        """Get all actively scheduled jobs.
        Returns:
             A list of all actively scheduled jobs.
        """
        self.scheduler.get_jobs()

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
                print('Error: Unknown event sent!')

        return event_selector


controller = Controller()
