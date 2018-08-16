import logging
from uuid import UUID

from sqlalchemy import Column, String, ForeignKey, orm, UniqueConstraint, Boolean, event
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from walkoff.executiondb import Execution_Base
from walkoff.executiondb.action import Action
from walkoff.executiondb.executionelement import ExecutionElement

logger = logging.getLogger(__name__)


class Workflow(ExecutionElement, Execution_Base):
    __tablename__ = 'workflow'
    playbook_id = Column(UUIDType(binary=False), ForeignKey('playbook.id'))
    name = Column(String(80), nullable=False)
    actions = relationship('Action', cascade='all, delete-orphan')
    branches = relationship('Branch', cascade='all, delete-orphan')
    start = Column(UUIDType(binary=False))
    is_valid = Column(Boolean, default=False)
    children = ('actions', 'branches')
    environment_variables = relationship('EnvironmentVariable', cascade='all, delete-orphan')
    __table_args__ = (UniqueConstraint('playbook_id', 'name', name='_playbook_workflow'),)

    def __init__(self, name, start, id=None, actions=None, branches=None, environment_variables=None):
        """Initializes a Workflow object. A Workflow falls under a Playbook, and has many associated Actions
            within it that get executed.

        Args:
            name (str): The name of the Workflow object.
            start (int): ID of the starting Action.
            id (str|UUID, optional): Optional UUID to pass into the Action. Must be UUID object or valid UUID string.
                Defaults to None.
            actions (list[Action]): Optional Action objects. Defaults to None.
            branches (list[Branch], optional): A list of Branch objects for the Workflow object. Defaults to None.
            environment_variables (list[EnvironmentVariable], optional): A list of environment variables for the
                Workflow. Defaults to None.
        """
        ExecutionElement.__init__(self, id)
        self.name = name
        self.actions = actions if actions else []
        self.branches = branches if branches else []
        self.environment_variables = environment_variables if environment_variables else []

        self.start = start

        self.validate()

    @orm.reconstructor
    def init_on_load(self):
        """Loads all necessary fields upon Workflow being loaded from database"""
        if self.environment_variables:
            self._accumulator.update({env_var.id: env_var.value for env_var in self.environment_variables})

    def validate(self):
        """Validates the object"""
        action_ids = [action.id for action in self.actions]
        errors = []
        if not self.start and self.actions:
            errors.append('Workflows with actions require a start parameter')
        elif self.actions and self.start not in action_ids:
            errors.append('Workflow start ID {} not found in actions'.format(self.start))
        for branch in self.branches:
            if branch.source_id not in action_ids:
                errors.append('Branch source ID {} not found in workflow actions'.format(branch.source_id))
            if branch.destination_id not in action_ids:
                errors.append('Branch destination ID {} not found in workflow actions'.format(branch.destination_id))
        self.errors = errors
        self.is_valid = self._is_valid

    def get_action_by_id(self, action_id):
        """Gets an Action by its ID

        Args:
            action_id (UUID): The ID of the Action to find

        Returns:
            (Action): The Action from its ID
        """
        return next((action for action in self.actions if action.id == action_id), None)

    def remove_action(self, action_id):
        """Removes a Action object from the Workflow's list of Actions given the Action ID.

        Args:
            action_id (UUID): The ID of the Action object to be removed.

        Returns:
            (bool): True on success, False otherwise.
        """
        action_to_remove = self.get_action_by_id(action_id)
        self.actions.remove(action_to_remove)
        self.branches[:] = [branch for branch in self.branches if
                            (branch.source_id != action_id and branch.destination_id != action_id)]

        logger.debug('Removed action {0} from workflow {1}'.format(action_id, self.name))
        return True

    def get_executing_action_id(self):
        """Gets the ID of the currently executing Action

        Returns:
            (UUID): The ID of the currently executing Action
        """
        return self._executing_action.id

    def get_executing_action(self):
        """Gets the currently executing Action

        Returns:
            (Action): The currently executing Action
        """
        return self._executing_action

    def get_accumulator(self):
        """Gets the accumulator

        Returns:
            (dict): The accumulator
        """
        return self._accumulator

    def get_instances(self):
        """Gets all instances

        Returns:
            (list[AppInstance]): All instances
        """
        return self._instance_repo.get_all_app_instances()


@event.listens_for(Workflow, 'before_update')
def validate_before_update(mapper, connection, target):
    target.validate()
