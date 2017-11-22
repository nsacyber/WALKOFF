import logging

import core.config.config
from core.multiprocessedexecutor.multiprocessedexecutor import MultiprocessedExecutor
from core.playbookstore import PlaybookStore
from core.scheduler import Scheduler

logger = logging.getLogger(__name__)

WORKFLOW_RUNNING = 1
WORKFLOW_PAUSED = 2
WORKFLOW_COMPLETED = 4

NUM_PROCESSES = core.config.config.num_processes


class Controller(object):
    def __init__(self, executor=MultiprocessedExecutor):
        """Initializes a Controller object.
        
        Args:
            executor (cls, optional): The executor to use in the controller. Defaults to MultiprocessedExecutor
        """
        self.uid = 'controller'
        self.playbook_store = PlaybookStore()
        self.scheduler = Scheduler()
        self.executor = executor()

    def initialize_threading(self, pids=None):
        """Initializes threading in the executor
        """
        self.executor.initialize_threading(pids=pids)

    def wait_and_reset(self, num_workflows):
        """Waits for the specified number of workflows to finish execution.

        Args:
            num_workflows (int): The number of workflows to wait for.
        """
        self.executor.wait_and_reset(num_workflows)

    def shutdown_pool(self):
        """Shuts down the executor
        """
        self.executor.shutdown_pool()

    def pause_workflow(self, execution_uid):
        """Pauses a workflow.

        Args:
            execution_uid (str): The execution UID of the workflow to pause
        """
        self.executor.pause_workflow(execution_uid)

    def resume_workflow(self, workflow_execution_uid):
        """Resumes a workflow that has been paused.

        Args:
            workflow_execution_uid (str): The randomly-generated hexadecimal key that was returned from
                pause_workflow(). This is needed to resume a workflow for security purposes.

        Returns:
            (bool) True if successful, False otherwise.
        """
        return self.executor.resume_workflow(workflow_execution_uid)

    def load_workflow(self, resource, workflow_name):
        """Loads a workflow from a file.

        Args:
            resource (str): Path to the workflow.
            workflow_name (str): Name of the workflow to load.

        Returns:
            True on success, False otherwise.
        """
        return self.playbook_store.load_workflow(resource, workflow_name)

    def load_playbook(self, resource):
        """Loads playbook from a file.

        Args:
            resource (str): Path to the workflow.
        """
        return self.playbook_store.load_playbook(resource)

    def load_playbooks(self, resource_collection=None):
        """Loads all playbooks from a directory.

        Args:
            resource_collection (str, optional): Path to the directory to load from. Defaults to the
                configuration workflows_path.
        """
        return self.playbook_store.load_playbooks(resource_collection)

    def schedule_workflows(self, task_id, workflow_uids, trigger):
        """Schedules workflows to be run by the scheduler

        Args:
            task_id (str|int): Id of the task to run
            workflow_uids (list[str]): UIDs of the workflows to schedule
            trigger: The type of scheduler trigger to use
        """
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
            workflows (list[Workflow], optional): An optional list of Workflows to be associated with this
                Playbook. Defaults to None.
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
                of all the workflows, or just their names. Defaults to False.
            reader (cls): The reader to specify how to display the Workflows. Defaults to None, which will show
                basic JSON representation of the Workflows.
        
        Returns:
            A dict with key being the playbook, mapping to a list of workflow names for each playbook.
        """
        return self.playbook_store.get_all_workflows(full_representation, reader=reader)

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

    def execute_workflow(self, playbook_name, workflow_name, start=None, start_arguments=None):
        """Executes a workflow.

        Args:
            playbook_name (str): Playbook name under which the workflow is located.
            workflow_name (str): Workflow to execute.
            start (str, optional): The name of the first, or starting action. Defaults to None.
            start_arguments (list[Argument JSON]): The input to the starting action of the workflow. Defaults to None.

        Returns:
            The execution UID if successful, None otherwise.
        """
        if self.playbook_store.is_workflow_registered(playbook_name, workflow_name):
            workflow = self.playbook_store.get_workflow(playbook_name, workflow_name)
            return self.executor.execute_workflow(workflow, start, start_arguments)
        else:
            logger.error('Attempted to execute playbook which does not exist in controller')
            return None, 'Attempted to execute playbook which does not exist in controller'

    def get_waiting_workflows(self):
        return self.executor.get_waiting_workflows()

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

    def get_playbook_representation(self, playbook_name, reader=None):
        """Returns the JSON representation of a playbook.

        Args:
            playbook_name: The name of the playbook.
            reader (cls, optional): An optional different way to represent the Playbook. Defaults to None,
                meaning that it will show basic JSON representation.

        Returns:
            The JSON representation of the playbook if the playbook has any workflows under it, else None.
        """
        return self.playbook_store.get_playbook_representation(playbook_name, reader=reader)

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

    def send_data_to_trigger(self, data_in, workflow_uids, arguments=None):
        """Tries to match the data in against the conditionals of all the triggers registered in the database.

        Args:
            data_in (dict): Data to be used to match against the triggers for an Action awaiting data.
            workflow_uids (list[str]): A list of workflow execution UIDs to send this data to.
            arguments (list[Argument]): An optional list of arguments to update for an Action awaiting data for a trigger.
                Defaults to None.

        Returns:
            Dictionary of {"status": <status string>}
        """
        arguments = arguments if arguments is not None else []
        if workflow_uids is not None:
            self.executor.send_data_to_trigger(data_in, workflow_uids, arguments)

    def get_workflow_status(self, execution_uid):
        """Gets the status of an executing workflow

        Args:
            execution_uid (str): Execution UID of the executing workflow

        Returns:
            (int) Status code of the executing workflow
        """
        return self.executor.get_workflow_status(execution_uid)

controller = Controller()
