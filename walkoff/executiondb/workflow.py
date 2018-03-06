import json
import logging
from uuid import UUID

from sqlalchemy import Column, String, ForeignKey, orm, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from walkoff.appgateway.appinstancerepo import AppInstanceRepo
from walkoff.events import WalkoffEvent
from walkoff.executiondb import Device_Base
from walkoff.executiondb.action import Action
from walkoff.executiondb.executionelement import ExecutionElement
from walkoff.helpers import InvalidExecutionElement

logger = logging.getLogger(__name__)


class Workflow(ExecutionElement, Device_Base):
    __tablename__ = 'workflow'
    playbook_id = Column(UUIDType(binary=False), ForeignKey('playbook.id'))
    name = Column(String(80), nullable=False)
    actions = relationship('Action', cascade='all, delete-orphan')
    branches = relationship('Branch', cascade='all, delete-orphan')
    start = Column(UUIDType(binary=False))
    __table_args__ = (UniqueConstraint('playbook_id', 'name', name='_playbook_workflow'),)

    def __init__(self, name, start, id=None, actions=None, branches=None):
        """Initializes a Workflow object. A Workflow falls under a Playbook, and has many associated Actions
            within it that get executed.
        Args:
            name (str): The name of the Workflow object.
            start (int): ID of the starting Action.
            id (str|UUID, optional): Optional UUID to pass into the Action. Must be UUID object or valid UUID string.
                Defaults to None.
            actions (list[Action]): Optional Action objects. Defaults to None.
            branches (list[Branch], optional): A list of Branch objects for the Workflow object. Defaults to None.
        """
        ExecutionElement.__init__(self, id)
        self.name = name
        self.actions = actions if actions else []
        self.branches = branches if branches else []

        self.start = start

        self._is_paused = False
        self._abort = False
        self._accumulator = {}
        self._execution_id = 'default'
        self._instance_repo = None

        self.validate()

    @orm.reconstructor
    def init_on_load(self):
        """Loads all necessary fields upon Workflow being loaded from database"""
        self._is_paused = False
        self._abort = False
        self._accumulator = {}
        self._instance_repo = AppInstanceRepo()
        self._execution_id = 'default'

    def validate(self):
        action_ids = [action.id for action in self.actions]
        errors = {}
        if not self.start and self.actions:
            errors['start'] = 'Workflows with actions require a start parameter'
        elif self.actions and self.start not in action_ids:
            errors['start'] = 'Workflow start ID {} not found in actions'.format(self.start)

        branch_errors = []
        for branch in self.branches:
            if branch.source_id not in action_ids:
                branch_errors.append('Branch source ID {} not found in workflow actions'.format(branch.source_id))
            if branch.destination_id not in action_ids:
                branch_errors.append(
                    'Branch destination ID {} not found in workflow actions'.format(branch.destination_id))
        if branch_errors:
            errors['branches'] = branch_errors
        if errors:
            raise InvalidExecutionElement(self.id, self.name, 'Invalid workflow', errors=errors)

    def get_action_by_id(self, action_id):
        return next((action for action in self.actions if action.id == action_id), None)

    def remove_action(self, action_id):
        """Removes a Action object from the Workflow's list of Actions given the Action ID.
        Args:
            action_id (str): The ID of the Action object to be removed.
        Returns:
            True on success, False otherwise.
        """
        action_to_remove = self.get_action_by_id(action_id)
        self.actions.remove(action_to_remove)
        self.branches[:] = [branch for branch in self.branches if
                            (branch.source_id != action_id and branch.destination_id != action_id)]

        logger.debug('Removed action {0} from workflow {1}'.format(action_id, self.name))
        return True

    def pause(self):
        """Pauses the execution of the Workflow. The Workflow will pause execution before starting the next Action.
        """
        self._is_paused = True
        logger.info('Pausing workflow {0}'.format(self.name))

    def abort(self):
        """Aborts the execution of the Workflow. The Workflow will abort execution before starting the next Action.
        """
        self._abort = True
        logger.info('Aborting workflow {0}'.format(self.name))

    def execute(self, execution_id, start=None, start_arguments=None, resume=False):
        """Executes a Workflow by executing all Actions in the Workflow list of Action objects.
        Args:
            execution_id (str): The UUID4 hex string uniquely identifying this workflow instance
            start (int, optional): The ID of the first Action. Defaults to None.
            start_arguments (list[Argument]): Argument parameters into the first Action. Defaults to None.
            resume (bool, optional): Optional boolean to resume a previously paused workflow. Defaults to False.
        """
        self._execution_id = execution_id
        logger.info('Executing workflow {0}'.format(self.name))
        WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.WorkflowExecutionStart)
        start = start if start is not None else self.start
        if not isinstance(start, UUID):
            start = UUID(start)
        executor = self.__execute(start, start_arguments, resume)
        next(executor)

    def __execute(self, start, start_arguments=None, resume=False):
        actions = self.__actions(start=start)
        first = True
        for action in (action_ for action_ in actions if action_ is not None):
            self._executing_action = action
            logger.debug('Executing action {0} of workflow {1}'.format(action, self.name))

            if self._is_paused:
                self._is_paused = False
                WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.WorkflowPaused)
                yield
            if self._abort:
                self._abort = False
                WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.WorkflowAborted)
                yield

            device_id = self._instance_repo.setup_app_instance(action)

            if first:
                first = False
                result = action.execute(instance=self._instance_repo.get_app_instance(device_id)(),
                                        accumulator=self._accumulator, arguments=start_arguments, resume=resume)
            else:
                result = action.execute(instance=self._instance_repo.get_app_instance(device_id)(),
                                        accumulator=self._accumulator, resume=resume)
            if result and result.status == "trigger":
                yield
            self._accumulator[action.id] = action.get_output().result
        self.__shutdown()
        yield

    def __actions(self, start):
        current_id = start
        current_action = self.get_action_by_id(current_id)

        while current_action:
            yield current_action
            current_id = self.get_branch(current_action, self._accumulator)
            current_action = self.get_action_by_id(current_id) if current_id is not None else None
            yield  # needed so that when for-loop calls next() it doesn't advance too far
        yield  # needed so you can avoid catching StopIteration exception

    def get_branch(self, current_action, accumulator):
        """Executes the Branch objects associated with this Workflow to determine which Action should be
            executed next.
        Args:
            current_action(Action): The current action that has just finished executing.
            accumulator (dict): The accumulated results of previous Actions.
        Returns:
            The ID of the next Action to be executed if successful, else None.
        """
        if self.branches:
            branches = sorted(
                self.__get_branches_by_action_id(current_action.id), key=lambda branch_: branch_.priority)
            for branch in branches:
                # TODO: This here is the only hold up from getting rid of action._output.
                # Keep whole result in accumulator
                destination_id = branch.execute(current_action.get_output(), accumulator)
                return destination_id
            return None
        else:
            return None

    def __get_branches_by_action_id(self, id_):
        branches = []
        if self.branches:
            for branch in self.branches:
                if branch.source_id == id_:
                    branches.append(branch)
        return branches

    def __shutdown(self):
        # Upon finishing shut down instances
        self._instance_repo.shutdown_instances()
        result_str = {}
        for action, action_result in self._accumulator.items():
            try:
                result_str[action] = json.dumps(action_result)
            except TypeError:
                logger.error('Result of workflow is neither string or a JSON-able. Cannot record')
                result_str[action] = 'error: could not convert to JSON'
        data = dict(self._accumulator)
        try:
            data_json = json.dumps(data)
        except TypeError:
            data_json = str(data)
        WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.WorkflowShutdown, data=data_json)
        logger.info('Workflow {0} completed. Result: {1}'.format(self.name, self._accumulator))

    def set_execution_id(self, execution_id):
        """Sets the execution UD for the Workflow
        Args:
            execution_id (str): The execution ID
        """
        self._execution_id = execution_id

    def get_execution_id(self):
        """Gets the execution ID for the Workflow
        Returns:
            The execution ID of the Workflow
        """
        return self._execution_id

    def get_executing_action_id(self):
        """Gets the ID of the currently executing Action
        Returns:
            The ID of the currently executing Action
        """
        return self._executing_action.id

    def get_accumulator(self):
        """Gets the accumulator
        Returns:
            The accumulator
        """
        return self._accumulator

    def get_instances(self):
        """Gets all instances
        Returns:
            All instances
        """
        return self._instance_repo.get_all_app_instances()
