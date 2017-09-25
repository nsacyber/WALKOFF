import os
from copy import deepcopy
from os import sep
import logging
from core.scheduler import Scheduler
import core.config.config
import core.config.paths
from core.workflow import Workflow
import core.workflowExecutor
from core.helpers import (locate_playbooks_in_directory,
                          UnknownAppAction, UnknownApp, InvalidInput, format_exception_message)
import json
from core.playbook import Playbook


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
        self.scheduler = Scheduler()
        self.executor = core.workflowExecutor.WorkflowExecutor()

        # @callbacks.WorkflowShutdown.connect
        # def workflow_completed_callback(sender, **kwargs):
        #     self.__workflow_completed_callback(sender, **kwargs)


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

    def __add_workflow(self, playbook_name, workflow_name, json_in):
        try:
            workflow = Workflow.from_json(json_in)
            if playbook_name in self.workflows:
                self.workflows[playbook_name].add_workflow(workflow)
            else:
                self.workflows[playbook_name] = Playbook(playbook_name, [workflow])
            logger.info('Adding workflow {0} to controller'.format(workflow_name))
        except (UnknownApp, UnknownAppAction, InvalidInput) as e:
            logger.error('Cannot load workflow {0}-{1}: '
                         'Error: {2}'.format(playbook_name, workflow_name, format_exception_message(e)))

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
        with open(path, 'r') as workflow_file:
            workflow_loaded = workflow_file.read()
            try:
                json_in = json.loads(workflow_loaded)
            except json.JSONDecodeError:
                logger.error('Cannot parse {}'.format(path))
            else:
                playbook_name = playbook_override if playbook_override else json_in['name']

                for workflow in (workflow_ for workflow_ in json_in['workflows'] if workflow_['name'] == workflow_name):
                    if workflow['name'] == workflow_name:
                        workflow_name = name_override if name_override else workflow['name']
                        workflow['name'] = workflow_name
                        self.__add_workflow(playbook_name, workflow_name, workflow)
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
        with open(path, 'r') as workflow_file:
            workflow_loaded = workflow_file.read()
            try:
                json_in = json.loads(workflow_loaded)
            except json.JSONDecodeError:
                logger.error('Cannot parse {}'.format(path))
            else:
                playbook_name = playbook_override if playbook_override else json_in['name']
                for workflow in json_in['workflows']:
                    workflow_name = name_override if name_override else workflow['name']
                    self.__add_workflow(playbook_name, workflow_name, workflow)


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
        for playbook in self.workflows.values():
            playbook.set_child_workflows()

    def schedule_workflows(self, task_id, workflow_uids, trigger):
        workflows = []
        for playbook_name, playbook in self.workflows.items():
            for workflow_uid in workflow_uids:
                workflow = playbook.get_workflow_by_uid(workflow_uid)
                if workflow is not None:
                    workflows.append((playbook_name, workflow.name, workflow.uid))
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
        if playbook_name in self.workflows and self.workflows[playbook_name].has_workflow_name(workflow_name):
            logger.debug('Removed workflow {0}'.format(workflow_name))
            self.workflows[playbook_name].remove_workflow_by_name(workflow_name)
            return True
        else:
            logger.warning('Cannot remove workflow {0}. Does not exist in controller'.format(workflow_name))
            return False

    def remove_playbook(self, playbook_name):
        """Removes a playbook and all workflows within it.
        
        Args:
            playbook_name (str): The name of the playbook to remove.
            
        Returns:
            True on success, False otherwise.
        """
        if playbook_name in self.workflows:
            self.workflows.pop(playbook_name)
            logger.debug('Removed playbook {0}'.format(playbook_name))
            return True
        else:
            return False

    def get_all_workflows(self, with_json=False):
        """Gets all of the currently loaded workflows.

        Args:
            with_json (bool, optional): A boolean specifying whether or not to include the JSON representation
                of all the workflows, or just their names. Defaults to false.
        
        Returns:
            A dict with key being the playbook, mapping to a list of workflow names for each playbook.
        """
        if with_json:
            return [{'name': playbook_name, 'workflows': playbook.get_all_workflows_as_json()}
                    for playbook_name, playbook in self.workflows.items()]
        else:
            return [{'name': playbook_name, 'workflows': playbook.get_all_workflows_as_limited_json()}
                    for playbook_name, playbook in self.workflows.items()]

    def get_all_playbooks(self):
        """Gets a list of all playbooks.
        
        Returns:
            A list containing all currently loaded playbook names.
        """
        return list(self.workflows.keys())

    def is_workflow_registered(self, playbook_name, workflow_name):
        """Checks whether or not a workflow is currently registered in the system.
        
        Args:
            playbook_name (str): Playbook name under which the workflow is located.
            workflow_name (str): The name of the workflow.
            
        Returns:
            True if the workflow is registered, false otherwise.
        """
        return playbook_name in self.workflows and self.workflows[playbook_name].has_workflow_name(workflow_name)

    def is_playbook_registered(self, playbook_name):
        """Checks whether or not a playbook is currently registered in the system.
        
        Args:
            playbook_name (str): The name of the playbook.
            
        Returns:
            True if the playbook is registered, false otherwise.
        """
        return playbook_name in self.workflows

    def update_workflow_name(self, old_playbook, old_workflow, new_playbook, new_workflow):
        """Update the name of a workflow.
        
        Args:
            old_playbook (str): Name of the current playbook.
            old_workflow (str): Name of the current workflow.
            new_playbook (str): The new name of the playbook.
            new_workflow (str): The new name of the workflow.
        """
        if old_playbook in self.workflows:
            self.workflows[old_playbook].rename_workflow(old_workflow, new_workflow)
            if new_playbook != old_playbook:
                self.workflows[new_playbook] = self.workflows.pop(old_playbook)
                self.workflows[new_playbook].name = new_playbook
            logger.debug('updated workflow name from '
                         '{0}-{1} to {2}-{3}'.format(old_playbook, old_workflow, new_playbook, new_workflow))

    def update_playbook_name(self, old_playbook, new_playbook):
        """Update the name of a playbook.
        
        Args:
            old_playbook (str): Name of the current playbook.
            new_playbook (str): The new name of the playbook.
        """
        if old_playbook in self.workflows:
            self.workflows[new_playbook] = self.workflows.pop(old_playbook)
            self.workflows[new_playbook].name = new_playbook

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
        if playbook_name in self.workflows and self.workflows[playbook_name].has_workflow_name(workflow_name):
            workflow = self.workflows[playbook_name].get_workflow_by_name(workflow_name)
            return self.executor.execute_workflow(workflow, playbook_name, workflow_name, start, start_input)
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
        if playbook_name in self.workflows:
            return self.workflows[playbook_name].get_workflow_by_name(workflow_name)
        return None

    def get_all_workflows_by_playbook(self, playbook_name):
        """Get a list of all workflow objects in a playbook.
        
        Args:
            playbook_name: The name of the playbook.
            
        Returns:
            A list of all workflow objects in a playbook.
        """
        if playbook_name in self.workflows:
            return self.workflows[playbook_name].get_all_workflow_names()
        else:
            return []

    def playbook_as_json(self, playbook_name):
        """Returns the JSON representation of a playbook.

        Args:
            playbook_name: The name of the playbook.

        Returns:
            The JSON representation of the playbook if the playbook has any workflows under it, else None.
        """
        if playbook_name in self.workflows:
            return self.workflows[playbook_name].as_json()
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
        workflow_copy.name = new_workflow_name
        workflow_copy.uid = uuid.uuid4().hex

        if new_playbook_name in self.workflows:
            self.workflows[new_playbook_name].add_workflow(workflow_copy)
        else:
            self.workflows[new_playbook_name] = Playbook(new_playbook_name, [workflow_copy])
        logger.info('Workflow copied from {0}-{1} to {2}-{3}'.format(old_playbook_name, old_workflow_name,
                                                                     new_playbook_name, new_workflow_name))

    def copy_playbook(self, old_playbook_name, new_playbook_name):
        """Copies a playbook.
        
        Args:
            old_playbook_name (str): The name of the playbook to be copied.
            new_playbook_name (str): The new name of the duplicated playbook.
        """
        self.workflows[new_playbook_name] = deepcopy(self.workflows[old_playbook_name])

    #TODO: This method needs to be implemented somewhere
    def get_workflow_status(self, uid):
        pass
        # return self.workflow_status.get(uid, None)

controller = Controller()
