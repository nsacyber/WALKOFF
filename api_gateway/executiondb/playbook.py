from sqlalchemy import Column, String
from sqlalchemy.orm import relationship, backref

from api_gateway.executiondb import Execution_Base
from api_gateway.executiondb.executionelement import ExecutionElement


class Playbook(ExecutionElement, Execution_Base):
    __tablename__ = 'playbook'
    name = Column(String(255), nullable=False, unique=True)
    workflows = relationship('Workflow', backref=backref('playbook'), cascade='all, delete-orphan',
                             passive_deletes=True)

    def __init__(self, name, workflows=None, _id=None, errors=None):
        """Creates a Playbook object.

        Args:
            name (str): The name of the Playbook
            workflows (list[Workflow], optional): An optional list of Workflows associated with this Playbook.
                Defaults to None.
            _id (str|UUID, optional): Optional UUID to pass into the Playbook. Must be UUID object or valid UUID string.
                Defaults to None.
        """
        ExecutionElement.__init__(self, _id, errors)
        self.name = name
        if workflows:
            self.workflows = workflows

        self.validate()

    def validate(self):
        pass

    def add_workflow(self, workflow):
        """Add a Workflow to the Playbook.

        Args:
            workflow (Workflow): The Workflow object to be added to the Playbook.
        """
        self.workflows.append(workflow)

    def has_workflow_name(self, workflow_name):
        """Checks if there is a Workflow with the specified name associated with the Playbook

        Args:
            workflow_name (str): The name of the Workflow

        Returns:
            (bool): True if there is a Workflow by that name associated with the Playbook, False otherwise
        """
        for workflow in self.workflows:
            if workflow.name == workflow_name:
                return True
        return False

    def has_workflow_id(self, workflow_id):
        """Checks if there is a Workflow with the specified ID associated with the Playbook

        Args:
            workflow_id (UUID): The ID of the Workflow

        Returns:
            (bool): True if there is a Workflow with that ID associated with the Playbook, False otherwise
        """
        for workflow in self.workflows:
            if workflow._id == workflow_id:
                return True
        return False

    def get_workflow_by_name(self, workflow_name):
        """Gets the Workflow by the specified name

        Args:
            workflow_name (str): The name of the Workflow

        Returns:
            (Workflow): The Workflow by that name if found, None otherwise
        """
        for workflow in self.workflows:
            if workflow.name == workflow_name:
                return workflow
        return None

    def get_workflow_by_id(self, workflow_id):
        """Gets the Workflow by the specified ID

        Args:
            workflow_id (UUID): The ID of the Workflow

        Returns:
            (Workflow): The Workflow with that ID if found, None otherwise
        """
        for workflow in self.workflows:
            if workflow._id == workflow_id:
                return workflow
        return None

    def get_all_workflow_names(self):
        """Gets the names of all of the Workflows associated with the Playbook

        Returns:
            (list[str]): A list of the names of all of the Workflows associated with the Playbook
        """
        return [workflow.name for workflow in self.workflows]

    def get_all_workflow_ids(self):
        """Gets the IDs of all of the Workflows associated with the Playbook

        Returns:
            (list[UUID]): A list of the IDs of all of the Workflows associated with the Playbook
        """
        return [workflow._id for workflow in self.workflows]

    def get_all_workflow_representations(self, reader=None):
        """Gets the representation of all of the Workflows in the Playbook

        Args:
            reader (cls, optional): An optional reader class that specifies the representation of the Workflows

        Returns:
            (list[representation]): A list of all of the Workflows associated with the Playbook in the form specified
                by the reader, or the default
        """
        return [workflow.read(reader=reader) for workflow in self.workflows]

    def get_all_workflows_as_limited_json(self):
        """Gets a list of all the Workflows associated with the Playbook, in limited JSON form

        Returns:
            (list[dict]): A list of all of the Workflows associated with the Playbook, in limited JSON form
        """
        return [{'name': workflow.name, 'id': workflow._id} for workflow in self.workflows]

    def rename_workflow(self, old_name, new_name):
        """Renames a Workflow

        Args:
            old_name (str): The current name of the Workflow
            new_name (str): The new name of the Workflow
        """
        for workflow in self.workflows:
            if workflow.name == old_name:
                workflow.name = new_name

    def remove_workflow_by_name(self, workflow_name):
        """Removes a Workflow with the specified name

        Args:
            workflow_name (str): The name of the Workflow to remove from the Playbook
        """
        wf = None
        for workflow in self.workflows:
            if workflow.name == workflow_name:
                wf = workflow
        if wf:
            self.workflows.remove(wf)
