import logging
from core.scheduler import Scheduler
import core.config.config
import core.config.paths
import core.workflowExecutor
from core.playbookstore import PlaybookStore

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
        self.playbook_store = PlaybookStore()
        self.scheduler = Scheduler()
        self.executor = core.workflowExecutor.WorkflowExecutor()

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

    def load_workflow(self, resource, workflow_name, name_override=None, playbook_override=None):
        """Loads a workflow from a file.

        Args:
            resource (str): Path to the workflow.
            workflow_name (str): Name of the workflow to load.
            name_override (str, optional): Name that the workflow should be changed to.
            playbook_override (str, optional): Name that the playbook should be changed to.

        Returns:
            True on success, False otherwise.
        """
        return self.playbook_store.load_workflow(resource, workflow_name)

    def load_playbook(self, resource, name_override=None, playbook_override=None):
        """Loads multiple workloads from a file.

        Args:
            resource (str): Path to the workflow.
            name_override (str, optional): Name that the workflow should be changed to.
            playbook_override (str, optional): Name that the playbook should be changed to.
        """
        return self.playbook_store.load_playbook(resource)

    def load_playbooks(self, resource_collection=None):
        """Loads all workflows from a directory.

        Args:
            resource_collection (str, optional): Path to the directory to load from. Defaults to the configuration workflows_path.
        """
        return self.playbook_store.load_playbooks(resource_collection)

    def schedule_workflows(self, task_id, workflow_uids, trigger):
        playbook_workflows = self.playbook_store.get_workflows_by_uid(workflow_uids)
        schedule_workflows = []
        for playbook_name, workflows in playbook_workflows.items():
            for workflow in workflows:
                schedule_workflows.append((playbook_name, workflow.name, workflow.uid))
        self.scheduler.schedule_workflows(task_id, self.execute_workflow, schedule_workflows, trigger)

    def create_workflow(self, playbook_name, workflow_name):
        """Creates a workflow from a workflow template.
        
        Args:
            playbook_name (str): The name of the new playbook. 
            workflow_name (str): The name of the new workflow.

        Returns:
            True on success, False if otherwise.
        """
        return self.playbook_store.create_workflow(playbook_name, workflow_name)

    def create_playbook(self, playbook_name, workflows=None):
        """Creates a playbook from a playbook template.

        Args:
            playbook_name (str): The name of the new playbook.
        """
        return self.playbook_store.create_playbook(playbook_name, workflows)

    def remove_workflow(self, playbook_name, workflow_name):
        """Removes a workflow.
        
        Args:
            playbook_name (str): Playbook name under which the workflow is located.
            workflow_name (str): The name of the workflow to remove.
            
        Returns:
            True on success, False otherwise.
        """
        self.playbook_store.remove_workflow(playbook_name, workflow_name)

    def remove_playbook(self, playbook_name):
        """Removes a playbook and all workflows within it.
        
        Args:
            playbook_name (str): The name of the playbook to remove.
            
        Returns:
            True on success, False otherwise.
        """
        self.playbook_store.remove_playbook(playbook_name)

    def get_all_workflows(self, full_representation=False, reader=None):
        """Gets all of the currently loaded workflows.

        Args:
            full_representation (bool, optional): A boolean specifying whether or not to include the JSON representation
                of all the workflows, or just their names. Defaults to false.
        
        Returns:
            A dict with key being the playbook, mapping to a list of workflow names for each playbook.
        """
        return self.playbook_store.get_all_workflows(full_representation, reader=None)

    def get_all_playbooks(self):
        """Gets a list of all playbooks.
        
        Returns:
            A list containing all currently loaded playbook names.
        """
        return self.playbook_store.get_all_playbooks()

    def is_workflow_registered(self, playbook_name, workflow_name):
        """Checks whether or not a workflow is currently registered in the system.
        
        Args:
            playbook_name (str): Playbook name under which the workflow is located.
            workflow_name (str): The name of the workflow.
            
        Returns:
            True if the workflow is registered, false otherwise.
        """
        return self.playbook_store.is_workflow_registered(playbook_name, workflow_name)

    def is_playbook_registered(self, playbook_name):
        """Checks whether or not a playbook is currently registered in the system.
        
        Args:
            playbook_name (str): The name of the playbook.
            
        Returns:
            True if the playbook is registered, false otherwise.
        """
        return self.playbook_store.is_playbook_registered(playbook_name)

    def update_workflow_name(self, old_playbook, old_workflow, new_playbook, new_workflow):
        """Update the name of a workflow.
        
        Args:
            old_playbook (str): Name of the current playbook.
            old_workflow (str): Name of the current workflow.
            new_playbook (str): The new name of the playbook.
            new_workflow (str): The new name of the workflow.
        """
        self.playbook_store.update_workflow_name(old_playbook, old_workflow, new_playbook, new_workflow)

    def update_playbook_name(self, old_playbook, new_playbook):
        """Update the name of a playbook.
        
        Args:
            old_playbook (str): Name of the current playbook.
            new_playbook (str): The new name of the playbook.
        """
        self.playbook_store.update_playbook_name(old_playbook, new_playbook)

    def add_workflow_breakpoint_steps(self, playbook_name, workflow_name, steps):
        """Adds a breakpoint (for debugging purposes) in the specified steps.
        
        Args:
            playbook_name (str): Playbook name under which the workflow is located.
            workflow_name (str): The name of the workflow under which the steps are located.
            steps (list[str]): The list of step names for which the user would like to pause execution.
        """
        self.playbook_store.add_workflow_breakpoint_steps(playbook_name, workflow_name, steps)

    def execute_workflow(self, playbook_name, workflow_name, start=None, start_input=None):
        """Executes a workflow.

        Args:
            playbook_name (str): Playbook name under which the workflow is located.
            workflow_name (str): Workflow to execute.
            start (str, optional): The name of the first, or starting step. Defaults to "start".
            start_input (dict, optional): The input to the starting step of the workflow
        """
        if self.playbook_store.is_workflow_registered(playbook_name, workflow_name):
            workflow = self.playbook_store.get_workflow(playbook_name, workflow_name)
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
        return self.playbook_store.get_workflow(playbook_name, workflow_name)

    def get_all_workflows_by_playbook(self, playbook_name):
        """Get a list of all workflow objects in a playbook.
        
        Args:
            playbook_name: The name of the playbook.
            
        Returns:
            A list of all workflow objects in a playbook.
        """
        return self.playbook_store.get_all_workflows_by_playbook(playbook_name)

    def get_playbook_representation(self, playbook_name, writer=None):
        """Returns the JSON representation of a playbook.

        Args:
            playbook_name: The name of the playbook.

        Returns:
            The JSON representation of the playbook if the playbook has any workflows under it, else None.
        """
        return self.playbook_store.get_playbook_representation(playbook_name, writer=writer)

    def copy_workflow(self, old_playbook_name, new_playbook_name, old_workflow_name, new_workflow_name):
        """Duplicates a workflow into its current playbook, or a different playbook.
        
        Args:
            old_playbook_name (str): Playbook name under which the workflow is located.
            new_playbook_name (str): The new playbook name for the duplicated workflow.
            old_workflow_name (str): The name of the workflow to be copied.
            new_workflow_name (str): The new name of the duplicated workflow.
        """
        self.playbook_store.copy_workflow(old_playbook_name, new_playbook_name, old_workflow_name, new_workflow_name)

    def copy_playbook(self, old_playbook_name, new_playbook_name):
        """Copies a playbook.
        
        Args:
            old_playbook_name (str): The name of the playbook to be copied.
            new_playbook_name (str): The new name of the duplicated playbook.
        """
        self.playbook_store.copy_playbook(old_playbook_name, new_playbook_name)

    #TODO: This method needs to be implemented somewhere
    def get_workflow_status(self, uid):
        pass
        # return self.workflow_status.get(uid, None)

controller = Controller()
