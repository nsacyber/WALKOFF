import os
from collections import namedtuple
import gevent
from copy import deepcopy
from os import sep
import sys
import signal
import logging
from core.scheduler import Scheduler
import core.config.config
import core.config.paths
from core.workflow import Workflow
import core.workflowExecutor
from core.case import callbacks
from core.helpers import (locate_playbooks_in_directory,
                          UnknownAppAction, UnknownApp, InvalidInput, format_exception_message)
import uuid
import json
import multiprocessing
import threading
import zmq.green as zmq
from core import loadbalancer
from core.threadauthenticator import ThreadAuthenticator

_WorkflowKey = namedtuple('WorkflowKey', ['playbook', 'workflow'])

logger = logging.getLogger(__name__)

WORKFLOW_RUNNING = 1
WORKFLOW_PAUSED = 2
WORKFLOW_COMPLETED = 4

NUM_PROCESSES = core.config.config.num_processes


class Controller(object):
    def __init__(self, workflows_path=core.config.paths.workflows_path):
        """Initializes a Controller object.
        
        Args:
            workflows_path (str, optional): Path to the workflows.
        """
        self.uid = 'controller'
        self.workflows = {}
        self.load_all_playbooks_from_directory(path=workflows_path)
        self.instances = {}
        self.tree = None
        self.scheduler = Scheduler()

        # @callbacks.WorkflowShutdown.connect
        # def workflow_completed_callback(sender, **kwargs):
        #     self.__workflow_completed_callback(sender, **kwargs)

        self.executor = core.workflowExecutor.WorkflowExecutor()

    # def __workflow_completed_callback(self, workflow, **kwargs):
    #     self.workflows_executed += 1
    #     if workflow.uuid in self.workflow_status:
    #         self.workflow_status[workflow.uuid] = WORKFLOW_COMPLETED

    def initialize_threading(self, worker_env=None):
        self.executor.initialize_threading(worker_env)

    def shutdown_pool(self, num_workflows=0):
        self.executor.shutdown_pool(num_workflows=num_workflows)

    def pause_workflow(self, playbook_name, workflow_name, execution_uid):
        workflow = self.get_workflow(playbook_name, workflow_name)
        self.executor.pause_workflow(playbook_name, workflow_name, execution_uid, workflow)

    def resume_workflow(self, playbook_name, workflow_name, workflow_execution_uid):
        """Resumes a workflow that has been paused.

        Args:
            playbook_name (str): Playbook name under which the workflow is located.
            workflow_name (str): The name of the workflow.
            workflow_execution_uid (str): The randomly-generated hexadecimal key that was returned from
                pause_workflow(). This is needed to resume a workflow for security purposes.

        Returns:
            True if successful, false otherwise.
        """
        workflow = self.get_workflow(playbook_name, workflow_name)
        if workflow:
            self.executor.resume_workflow(playbook_name, workflow_name, workflow_execution_uid, workflow)

    def resume_breakpoint_step(self, playbook_name, workflow_name, uid):
        """Resumes a step that has been specified as a breakpoint.

        Args:
            playbook_name (str): Playbook name under which the workflow is located.
            workflow_name (str): The name of the workflow.
            uid (str): The UID of the workflow that is being executed.
        """
        workflow = self.get_workflow(playbook_name, workflow_name)
        if workflow:
            self.executor.resume_breakpoint_step(playbook_name, workflow_name, uid, workflow)

    def __add_workflow(self, key, name, json_in):
        try:
            workflow = Workflow.from_json(json_in)
            self.workflows[key] = workflow
            logger.info('Adding workflow {0} to controller'.format(name))
        except (UnknownApp, UnknownAppAction, InvalidInput) as e:
            logger.error('Cannot load workflow {0}: Error: {1}'.format(key, format_exception_message(e)))

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
        with open(path, 'r') as playbook_file:
            playbook_loaded = playbook_file.read()
            try:
                json_in = json.loads(playbook_loaded)
            except json.JSONDecodeError:
                logger.error('Cannot parse {}'.format(path))
            else:
                playbook_name = playbook_override if playbook_override else json_in['name']
                for workflow in (workflow_ for workflow_ in json_in['workflows'] if workflow_['name'] == workflow_name):
                    if workflow['name'] == workflow_name:
                        workflow_name = name_override if name_override else workflow['name']
                        workflow['name'] = workflow_name
                        key = _WorkflowKey(playbook_name, workflow_name)
                        self.__add_workflow(key, workflow_name, workflow)
                        self.add_child_workflows()
                        break
                else:
                    logger.warning('Workflow {0} not found in playbook {0}. '
                                   'Cannot load.'.format(workflow_name, playbook_name))
                    return False
                return True

    def load_playbook_from_file(self, path, name_override=None, playbook_override=None):
        """Loads multiple workloads from a file.

        Args:
            path (str): Path to the workflow.
            name_override (str, optional): Name that the workflow should be changed to.
            playbook_override (str, optional): Name that the playbook should be changed to.
        """
        with open(path, 'r') as playbook_file:
            playbook_loaded = playbook_file.read()
            try:
                json_in = json.loads(playbook_loaded)
            except json.JSONDecodeError:
                logger.error('Cannot parse {}'.format(path))
            else:
                playbook_name = playbook_override if playbook_override else json_in['name']
                for workflow in json_in['workflows']:
                    workflow_name = name_override if name_override else workflow['name']
                    key = _WorkflowKey(playbook_name, workflow_name)
                    self.__add_workflow(key, workflow_name, workflow)

        self.add_child_workflows()

    def load_all_playbooks_from_directory(self, path=None):
        """Loads all workflows from a directory.

        Args:
            path (str, optional): Path to the directory to load from. Defaults to the configuration workflows_path.
        """
        if path is None:
            path = core.config.paths.workflows_path
        for playbook in locate_playbooks_in_directory(path):
            self.load_playbook_from_file(os.path.join(path, playbook))

    def add_child_workflows(self):
        for workflow in self.workflows:
            playbook_name = workflow.playbook
            if self.workflows[workflow].children:
                children = self.workflows[workflow].children
                for child in children:
                    workflow_key = _WorkflowKey(playbook_name, child)
                    if workflow_key in self.workflows:
                        logger.info('Adding child workflow {0} '
                                    'to workflow {1}'.format(child, self.workflows[workflow_key].name))
                        children[child] = self.workflows[workflow_key]
                    else:
                        logger.warning('Could not find child workflow {0} '
                                       'for workflow {1}'.format(child, self.workflows[workflow_key].name))

    def schedule_workflows(self, task_id, workflow_uids, trigger):
        """Schedules one or more workflows to be run.

        Args:
            task_id (str|int): The task ID for this scheduled execution.
            workflow_uids (list[str]): A list of workflow UIDs to be executed.
            trigger (str): The name of the trigger that will trigger the execution of the workflows.
        """
        workflows = [(key.playbook, key.workflow, workflow.uid) for key, workflow in self.workflows.items()
                     if workflow.uid in workflow_uids]
        self.scheduler.schedule_workflows(task_id, self.execute_workflow, workflows, trigger)

    def create_workflow_from_template(self,
                                      playbook_name,
                                      workflow_name,
                                      template_playbook='emptyWorkflow',
                                      template_name='emptyWorkflow'):
        """Creates a workflow from a workflow template.
        
        Args:
            playbook_name (str): The name of the new playbook. 
            workflow_name (str): The name of the new workflow.
            template_playbook (str, optional): The name of the playbook template to load. Default is "emptyWorkflow".
            template_name (str, optional): The name of the workflow template to load. Default is "emptyWorkflow".
            
        Returns:
            True on success, False if otherwise.
        """
        path = '{0}{1}{2}.playbook'.format(core.config.paths.templates_path, sep, template_playbook)
        return self.load_workflow_from_file(path=path,
                                            workflow_name=template_name,
                                            name_override=workflow_name,
                                            playbook_override=playbook_name)

    def create_playbook_from_template(self, playbook_name,
                                      template_playbook='emptyWorkflow'):
        """Creates a playbook from a playbook template.

        Args:
            playbook_name (str): The name of the new playbook.
            template_playbook (str, optional): The name of the playbook template to load. Default is "emptyWorkflow".
        """
        # TODO: Need a handler for returning workflow key and status
        path = '{0}{1}{2}.playbook'.format(core.config.paths.templates_path, sep, template_playbook)
        self.load_playbook_from_file(path=path, playbook_override=playbook_name)

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

            logger.debug('Removed workflow {0}'.format(name))
            return True
        logger.warning('Cannot remove workflow {0}. Does not exist in controller'.format(name))
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
            logger.debug('Removed workflow {0}'.format(name))
        logger.debug('Removed playbook {0}'.format(playbook_name))
        return True

    def get_all_workflows(self, with_json=False):
        """Gets all of the currently loaded workflows.

        Args:
            with_json (bool, optional): A boolean specifying whether or not to include the JSON representation
                of all the workflows, or just their names. Defaults to false.
        
        Returns:
            A dict with key being the playbook, mapping to a list of workflow names for each playbook.
        """
        result = {}
        for key in self.workflows.keys():
            if key.playbook not in result:
                result[key.playbook] = []

            if with_json:
                result[key.playbook].append(self.get_workflow(key.playbook, key.workflow).as_json())
            else:
                workflow = self.get_workflow(key.playbook, key.workflow)
                result[key.playbook].append({'name': workflow.name, 'uid': workflow.uid})
        return [{'name': name, 'workflows': workflows} for name, workflows in result.items()]

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
        self.workflows[new_key].name = new_workflow
        self.workflows[new_key].playbook_name = new_playbook
        logger.debug('updated workflow name {0} to {1}'.format(old_key, new_key))

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
            workflow.breakpoint_steps.extend(steps)

    def execute_workflow(self, playbook_name, workflow_name, start=None, start_input=None):
        """Executes a workflow.

        Args:
            playbook_name (str): Playbook name under which the workflow is located.
            workflow_name (str): Workflow to execute.
            start (str, optional): The name of the first, or starting step. Defaults to "start".
            start_input (dict, optional): The input to the starting step of the workflow
        """
        key = _WorkflowKey(playbook_name, workflow_name)
        if key in self.workflows:
            workflow = self.workflows[key]
            uid = uuid.uuid4().hex

            if not self.threading_is_initialized:
                self.initialize_threading()

            if start is not None:
                logger.info('Executing workflow {0} for step {1}'.format(key, start))
            else:
                logger.info('Executing workflow {0} with default starting step'.format(key, start))
            self.workflow_status[uid] = WORKFLOW_RUNNING

            wf_json = workflow.as_json()
            if start:
                wf_json['start'] = start
            if start_input:
                wf_json['start_input'] = start_input
            wf_json['execution_uid'] = uid
            if workflow.breakpoint_steps:
                wf_json['breakpoint_steps'] = workflow.breakpoint_steps

            self.load_balancer.pending_workflows.put(wf_json)

            callbacks.SchedulerJobExecuted.send(self)
            # TODO: Find some way to catch a validation error. Maybe pre-validate the input in the controller?
            return uid
        else:
            logger.error('Attempted to execute playbook which does not exist in controller')
            return None, 'Attempted to execute playbook which does not exist in controller'

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

    def playbook_as_json(self, playbook_name):
        """Returns the JSON representation of a playbook.

        Args:
            playbook_name: The name of the playbook.

        Returns:
            The JSON representation of the playbook if the playbook has any workflows under it, else None.
        """
        all_workflows = [workflow.as_json() for key, workflow in self.workflows.items()
                         if key.playbook == playbook_name]

        if all_workflows:
            return {"name": playbook_name,
                    "workflows": all_workflows}
        else:
            logger.debug('No workflows are registered in controller to convert to JSON')
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
        workflow_copy.name = new_workflow_name
        workflow_copy.playbook_name = new_playbook_name

        key = _WorkflowKey(new_playbook_name, new_workflow_name)
        self.workflows[key] = workflow_copy
        logger.info('Workflow copied from {0}-{1} to {2}-{3}'.format(old_playbook_name, old_workflow_name,
                                                                     new_playbook_name, new_workflow_name))

    def copy_playbook(self, old_playbook_name, new_playbook_name):
        """Copies a playbook.
        
        Args:
            old_playbook_name (str): The name of the playbook to be copied.
            new_playbook_name (str): The new name of the duplicated playbook.
        """
        for workflow in [workflow.workflow for workflow in self.workflows if workflow.playbook == old_playbook_name]:
            self.copy_workflow(old_playbook_name, new_playbook_name, workflow, workflow)

    def get_workflow_status(self, uid):
        return self.workflow_status.get(uid, None)

controller = Controller()
