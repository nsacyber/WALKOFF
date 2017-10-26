from core.executionelements.executionelement import ExecutionElement


class Playbook(ExecutionElement):
    def __init__(self, name, workflows=None, uid=None):
        """Creates a Playbook object.

        Args:
            name (str): The name of the Playbook
            workflows (list[Workflow], optional): An optional list of Workflows associated with this Playbook
            uid (str, optional): An optional UID to specify for this Playbook
        """
        ExecutionElement.__init__(self, uid)
        self.name = name
        # TODO: When playbook endpoints use UIDs, this should store UIDS
        self.workflows = {workflow.name: workflow for workflow in workflows} if workflows is not None else {}

    def add_workflow(self, workflow):
        """Add a Workflow to the Playbook.

        Args:
            workflow (Workflow): The Workflow object to be added to the Playbook.
        """
        self.workflows[workflow.name] = workflow

    def has_workflow_name(self, workflow_name):
        """Checks if there is a Workflow with the specified name associated with the Playbook

        Args:
            workflow_name (str): The name of the Workflow

        Returns:
            True if there is a Workflow by that name associated with the Playbook, False otherwise
        """
        return workflow_name in self.workflows

    def has_workflow_uid(self, workflow_uid):
        """Checks if there is a Workflow with the specified UID associated with the Playbook

        Args:
            workflow_uid (str): The UID of the Workflow

        Returns:
            True if there is a Workflow with that UID associated with the Playbook, False otherwise
        """
        return any(workflow.uid == workflow_uid for workflow in self.workflows.values())

    def get_workflow_by_name(self, workflow_name):
        """Gets the Workflow by the specified name

        Args:
            workflow_name (str): The name of the Workflow

        Returns:
            The Workflow by that name if found, False otherwise
        """
        try:
            return self.workflows[workflow_name]
        except KeyError:
            return None

    def get_workflow_by_uid(self, workflow_uid):
        """Gets the Workflow by the specified UID

        Args:
            workflow_uid (str): The UID of the Workflow

        Returns:
            The Workflow with that UID if found, False otherwise
        """
        return next((workflow for workflow in self.workflows.values() if workflow.uid == workflow_uid), None)

    def get_all_workflow_names(self):
        """Gets the names of all of the Workflows associated with the Playbook

        Returns:
            A list of the names of all of the Workflows associated with the Playbook
        """
        return list(self.workflows.keys())

    def get_all_workflow_uids(self):
        """Gets the UIDs of all of the Workflows associated with the Playbook

            Returns:
                A list of the UIDs of all of the Workflows associated with the Playbook
        """
        return [workflow.uid for workflow in self.workflows.values()]

    def get_all_workflow_representations(self, reader=None):
        """Gets the representation of all of the Workflows in the Playbook

        Args:
            reader (cls, optional): An optional reader class that specifies the representation of the Workflows

        Returns:
            A list of all of the Workflows associated with the Playbook in the form specified by the reader,
                or the default
        """
        return [workflow.read(reader=reader) for workflow in self.workflows.values()]

    def get_all_workflows_as_limited_json(self):
        """Gets a list of all the Workflows associated with the Playbook, in limited JSON form

        Returns:
            A list of all of the Workflows associated with the Playbook, in limited JSON form

        :return:
        """
        return [{'name': workflow_names, 'uid': workflow.uid} for workflow_names, workflow in self.workflows.items()]

    def rename_workflow(self, old_name, new_name):
        """Renames a Workflow

        Args:
            old_name (str): The current name of the Workflow
            new_name (str): The new name of the Workflow
        """
        if old_name in self.workflows:
            self.workflows[new_name] = self.workflows.pop(old_name)
            self.workflows[new_name].name = new_name

    def remove_workflow_by_name(self, workflow_name):
        """Removes a Workflow with the specified name

        Args:
            workflow_name (str): The name of the Workflow to remove from the Playbook
        """
        if workflow_name in self.workflows:
            self.workflows.pop(workflow_name)

