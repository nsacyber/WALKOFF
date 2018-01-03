import logging
from copy import deepcopy

from walkoff.core.executionelements.playbook import Playbook
from walkoff.core.executionelements.workflow import Workflow
from walkoff.core.jsonplaybookloader import JsonPlaybookLoader

logger = logging.getLogger(__name__)


class PlaybookStore(object):
    def __init__(self):
        self.playbooks = {}

    def load_workflow(self, resource, workflow_name, loader=JsonPlaybookLoader):
        """Loads a workflow from a file.

        Args:
            resource (str): Path to the workflow.
            workflow_name (str): Name of the workflow to load.
            loader (cls): Class used to load the workflow
        Returns:
            True on success, False otherwise.
        """
        loaded = loader.load_workflow(resource, workflow_name)
        if loaded is None:
            return None
        else:
            playbook_name, workflow = loaded
        if playbook_name not in self.playbooks:
            logger.debug(
                'Playbook name {0} not found while loading workflow {1}. Adding to storage.'.format(playbook_name,
                                                                                                    workflow.uid))
            self.playbooks[playbook_name] = Playbook(playbook_name, [workflow])
        else:
            self.playbooks[playbook_name].add_workflow(workflow)
        logger.info('Loaded workflow {} into storage'.format(workflow.uid))

    def load_playbook(self, resource, loader=JsonPlaybookLoader):
        """Loads a playbook from a file.

        Args:
            resource (str): Path to the workflow.
            loader (cls): Class used to load the playbook

        """
        playbook = loader.load_playbook(resource)
        if playbook is not None:
            self.add_playbook(playbook)

    def add_playbook(self, playbook):
        """
        Adds a playbook to the store

        Args:
            playbook (Playbook): The playbook to add
        """
        if playbook.name in self.playbooks:
            logger.warning('Playbook wih name {} already exists in storage. Overwriting.'.format(playbook.name))
        self.playbooks[playbook.name] = playbook
        logger.info('Loaded playbook {} into storage'.format(playbook.name))

    def add_workflow(self, playbook_name, workflow):
        """
        Adds a workflow to the store

        Args:
            playbook_name (str): Playbook to add the workflow to
            workflow (Workflow): Workflow to add
        """
        if playbook_name in self.playbooks:
            self.playbooks[playbook_name].add_workflow(workflow)
        else:
            logger.warning('Playbook wih name {} does not exist storage. Creating.'.format(playbook_name))
            self.playbooks[playbook_name] = Playbook(playbook_name, workflows=[workflow])
        logger.info('Loaded workflow {0} into playbook {1} in storage'.format(workflow.name, playbook_name))

    def load_playbooks(self, resource_collection=None, loader=JsonPlaybookLoader):
        """Loads all playbooks from a directory.

        Args:
            resource_collection (str, optional): Path to the directory to load from. Defaults to the configuration
                workflows_path.
            loader (cls): Class used to load the playbooks

        """
        for playbook in loader.load_playbooks(resource_collection):
            self.add_playbook(playbook)

    def create_workflow(self, playbook_name, workflow_name):
        """
        Creates an empty workflow

        Args:
            playbook_name (str): Name of the playbook to add
            workflow_name (str): The name of the workflow to add
        """
        workflow = Workflow(name=workflow_name)
        self.add_workflow(playbook_name, workflow)

    def create_playbook(self, playbook_name, workflows=None):
        """Creates a playbook from a playbook template.

        Args:
            playbook_name (str): The name of the new playbook.
            workflows (list[Workflow], optional): The list of workflows to be associated with the playbook. Defaults to
                None
        """
        workflows = workflows if workflows is not None else []
        self.add_playbook(Playbook(playbook_name, workflows))

    def remove_workflow(self, playbook_name, workflow_name):
        """Removes a workflow.

        Args:
            playbook_name (str): Playbook name under which the workflow is located.
            workflow_name (str): The name of the workflow to remove.

        Returns:
            True on success, False otherwise.
        """
        if playbook_name in self.playbooks and self.playbooks[playbook_name].has_workflow_name(workflow_name):
            logger.debug('Removed workflow {0}'.format(workflow_name))
            self.playbooks[playbook_name].remove_workflow_by_name(workflow_name)
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
        if playbook_name in self.playbooks:
            self.playbooks.pop(playbook_name)
            logger.debug('Removed playbook {0}'.format(playbook_name))
            return True
        else:
            return False

    def get_all_workflows(self, full_representations=False, reader=None):
        """Gets all of the currently loaded workflows.

        Args:
            full_representations (bool, optional): A boolean specifying whether or not to include the JSON
                representation of all the workflows, or just their names. Defaults to false.
            reader (cls, None): An optional reader class that will represent the Workflows differently.
                Defaults to None.

        Returns:
            A dict with key being the playbook, mapping to a list of workflow names for each playbook.
        """
        if full_representations:
            return [playbook.read(reader=reader) for playbook in self.playbooks.values()]
        else:
            return [{'name': playbook_name, 'workflows': playbook.get_all_workflows_as_limited_json()}
                    for playbook_name, playbook in self.playbooks.items()]

    def get_all_playbooks(self):
        """Gets a list of all playbooks.

        Returns:
            A list containing all currently loaded playbook names.
        """
        return list(self.playbooks.keys())

    def is_workflow_registered(self, playbook_name, workflow_name):
        """Checks whether or not a workflow is currently registered in the system.

        Args:
            playbook_name (str): Playbook name under which the workflow is located.
            workflow_name (str): The name of the workflow.

        Returns:
            True if the workflow is registered, false otherwise.
        """
        return playbook_name in self.playbooks and self.playbooks[playbook_name].has_workflow_name(workflow_name)

    def is_playbook_registered(self, playbook_name):
        """Checks whether or not a playbook is currently registered in the system.

        Args:
            playbook_name (str): The name of the playbook.

        Returns:
            True if the playbook is registered, false otherwise.
        """
        return playbook_name in self.playbooks

    def update_workflow_name(self, old_playbook, old_workflow, new_playbook, new_workflow):
        """Update the name of a workflow.

        Args:
            old_playbook (str): Name of the current playbook.
            old_workflow (str): Name of the current workflow.
            new_playbook (str): The new name of the playbook.
            new_workflow (str): The new name of the workflow.
        """
        if old_playbook in self.playbooks and self.playbooks[old_playbook].has_workflow_name(old_workflow):
            if new_playbook != old_playbook:
                workflow = self.playbooks[old_playbook].get_workflow_by_name(old_workflow)
                workflow.name = new_workflow
                self.add_workflow(new_playbook, workflow)
                self.playbooks[old_playbook].remove_workflow_by_name(old_workflow)
            else:
                self.playbooks[old_playbook].rename_workflow(old_workflow, new_workflow)
            logger.debug('updated workflow name from '
                         '{0}-{1} to {2}-{3}'.format(old_playbook, old_workflow, new_playbook, new_workflow))

    def update_playbook_name(self, old_playbook, new_playbook):
        """Update the name of a playbook.

        Args:
            old_playbook (str): Name of the current playbook.
            new_playbook (str): The new name of the playbook.
        """
        if old_playbook in self.playbooks:
            self.playbooks[new_playbook] = self.playbooks.pop(old_playbook)
            self.playbooks[new_playbook].name = new_playbook

    def get_workflow(self, playbook_name, workflow_name):
        """Get a workflow object.

        Args:
            playbook_name (str): Playbook name under which the workflow is located.
            workflow_name (str): The name of the workflow.

        Returns:
            The workflow object if found, else None.
        """
        if playbook_name in self.playbooks:
            return self.playbooks[playbook_name].get_workflow_by_name(workflow_name)
        return None

    def get_playbook(self, playbook_name):
        """Gets a playbook

        Args:
            playbook_name (str): The name of the playbook

        Returns:
            The Playbook from the playbook name
        """
        return self.playbooks.get(playbook_name, None)

    def get_all_workflows_by_playbook(self, playbook_name):
        """Get a list of all workflow objects in a playbook.

        Args:
            playbook_name: The name of the playbook.

        Returns:
            A list of all workflow objects in a playbook.
        """
        if playbook_name in self.playbooks:
            return self.playbooks[playbook_name].get_all_workflow_names()
        else:
            return []

    def get_playbook_representation(self, playbook_name, reader=None):
        """Returns the JSON representation of a playbook.

        Args:
            playbook_name: The name of the playbook.
            reader (cls, optional): An optional class to show the playbooks differently. Defaults to None.

        Returns:
            The JSON representation of the playbook if the playbook has any workflows under it, else None.
        """
        if playbook_name in self.playbooks:
            return self.playbooks[playbook_name].read(reader=reader)
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
        if workflow is not None:
            workflow.strip_events()

            workflow_copy = deepcopy(workflow)
            workflow_copy.name = new_workflow_name
            workflow_copy.regenerate_uids()
            workflow_copy.reset_event()

            if new_playbook_name in self.playbooks:
                self.playbooks[new_playbook_name].add_workflow(workflow_copy)
            else:
                self.playbooks[new_playbook_name] = Playbook(new_playbook_name, [workflow_copy])
            logger.info('Workflow copied from {0}-{1} to {2}-{3}'.format(old_playbook_name, old_workflow_name,
                                                                         new_playbook_name, new_workflow_name))

    def copy_playbook(self, old_playbook_name, new_playbook_name):
        """Copies a playbook.

        Args:
            old_playbook_name (str): The name of the playbook to be copied.
            new_playbook_name (str): The new name of the duplicated playbook.
        """
        if old_playbook_name in self.playbooks:
            self.create_playbook(new_playbook_name)
            for workflow in self.playbooks[old_playbook_name].workflows.values():
                self.copy_workflow(old_playbook_name, new_playbook_name, workflow.name, workflow.name)

    def get_workflows_by_uid(self, workflow_uids):
        """Gets a list of workflows from their UIDs

        Args:
            workflow_uids (list[str]): The list of workflow UIDs

        Returns:
            A list of workflows
        """
        playbook_workflows = {}
        for playbook_name, playbook in self.playbooks.items():
            for workflow_uid in workflow_uids:
                workflow = playbook.get_workflow_by_uid(workflow_uid)
                if workflow is not None:
                    if playbook_name in playbook_workflows:
                        playbook_workflows[playbook_name].append(workflow)
                    else:
                        playbook_workflows[playbook_name] = [workflow]
        return playbook_workflows
