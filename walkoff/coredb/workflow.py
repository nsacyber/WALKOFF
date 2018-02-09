import json
import logging
from uuid import UUID
import threading

from sqlalchemy import Column, String, ForeignKey, orm, UniqueConstraint
from sqlalchemy.orm import relationship, backref

from walkoff.appgateway.appinstance import AppInstance
from walkoff.coredb import Device_Base
from walkoff.events import WalkoffEvent
from walkoff.coredb.action import Action
from walkoff.coredb.executionelement import ExecutionElement
from walkoff.helpers import InvalidArgument, format_exception_message
from walkoff.dbtypes import Guid
from uuid import uuid4

logger = logging.getLogger(__name__)


class Workflow(ExecutionElement, Device_Base):
    __tablename__ = 'workflow'
    _playbook_id = Column(Guid(), ForeignKey('playbook.id'))
    name = Column(String(80), nullable=False)
    actions = relationship('Action', backref=backref('_workflow'), cascade='all, delete-orphan')
    branches = relationship('Branch', backref=backref('_workflow'), cascade='all, delete-orphan')
    start = Column(Guid(), nullable=False)
    __table_args__ = (UniqueConstraint('_playbook_id', 'name', name='_playbook_workflow'),)

    def __init__(self, name, start, id=None, actions=None, branches=None):
        """Initializes a Workflow object. A Workflow falls under a Playbook, and has many associated Actions
            within it that get executed.

        Args:
            name (str): The name of the Workflow object.
            start (int): ID of the starting Action.
            actions (list[Action]): Optional Action objects. Defaults to None.
            branches (list[Branch], optional): A list of Branch objects for the Workflow object. Defaults to None.
        """
        ExecutionElement.__init__(self, id)
        self.name = name

        self.actions = []
        if actions:
            self.actions = actions

        self.branches = []
        if branches:
            self.branches = branches

        self.start = start

        self._is_paused = False
        self._resume = threading.Event()
        self._accumulator = {}
        self._execution_id = 'default'
        self._instances = {}

    @orm.reconstructor
    def init_on_load(self):
        self._is_paused = False
        self._resume = threading.Event()
        self._accumulator = {}
        self._instances = {}
        self._execution_id = 'default'

    def remove_action(self, id_):
        """Removes a Action object from the Workflow's list of Actions given the Action ID.

        Args:
            id_ (str): The ID of the Action object to be removed.

        Returns:
            True on success, False otherwise.
        """
        self.actions[:] = [action for action in self.actions if action.id != id_]
        self.branches[:] = [branch for branch in self.branches if
                            (branch.source_id != id_ and branch.destination_id != id_)]

        logger.debug('Removed action {0} from workflow {1}'.format(id_, self.name))
        return True

    def pause(self):
        """Pauses the execution of the Workflow. The Workflow will pause execution before starting the next Action.
        """
        self._is_paused = True
        logger.info('Pausing workflow {0}'.format(self.name))

    def resume(self):
        """Resumes a Workflow that has previously been paused.
        """
        try:
            logger.info('Attempting to resume workflow {0}'.format(self.name))
            self._is_paused = False
            self._resume.set()
        except (StopIteration, AttributeError) as e:
            logger.warning('Cannot resume workflow {0}. Reason: {1}'.format(self.name, format_exception_message(e)))
            pass

    def execute(self, execution_id, start=None, start_arguments=None, resume=False):
        """Executes a Workflow by executing all Actions in the Workflow list of Action objects.

        Args:
            execution_id (str): The UUID4 hex string uniquely identifying this workflow instance
            start (int, optional): The ID of the first Action. Defaults to None.
            start_arguments (list[Argument]): Argument parameters into the first Action. Defaults to None.
            resume (bool, optional): Optional boolean to resume a previously paused workflow. Defaults to False.
        """
        print("Workflow execute top")
        self._execution_id = execution_id
        logger.info('Executing workflow {0}'.format(self.name))
        WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.WorkflowExecutionStart)
        start = start if start is not None else self.start
        if not isinstance(start, UUID):
            start = UUID(start)
        executor = self.__execute(start, start_arguments, resume)
        next(executor)

    def __execute(self, start, start_arguments=None, resume=False):
        print("in execute")
        actions = self.__actions(start=start)
        first = True
        for action in (action_ for action_ in actions if action_ is not None):
            print("Workflow starting to execute")
            self._executing_action = action
            logger.debug('Executing action {0} of workflow {1}'.format(action, self.name))
            if self._is_paused:
                print("WORKFLOW PAUSED")
                self._is_paused = False
                WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.WorkflowPaused)
                return

            device_id = self.__setup_app_instance(self._instances, action)

            if first:
                first = False
                result = action.execute(instance=self._instances[device_id](), accumulator=self._accumulator,
                                        arguments=start_arguments, resume=resume)
            else:
                result = action.execute(instance=self._instances[device_id](), accumulator=self._accumulator,
                                        resume=resume)
            if result and result.status == "trigger":
                return
            print("after here")
            self._accumulator[action.id] = action.get_output().result
        print("Workflow shutting down")
        self.__shutdown(self._instances)
        yield

    def __setup_app_instance(self, instances, action):
        device_id = (action.app_name, action.device_id)
        if device_id not in instances:
            instances[device_id] = AppInstance.create(action.app_name, action.device_id)
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.AppInstanceCreated)
            logger.debug('Created new app instance: App {0}, device {1}'.format(action.app_name, action.device_id))
        return device_id

    def __actions(self, start):
        current_id = start
        current_action = self.__get_action_by_id(current_id)
        print(self.actions)
        print(current_id)
        print(current_action)

        while current_action:
            print("yielding action")
            yield current_action
            current_id = self.get_branch(current_action, self._accumulator)
            current_action = self.__get_action_by_id(current_id) if current_id is not None else None
            yield  # needed so that when for-loop calls next() it doesn't advance too far
        yield  # needed so you can avoid catching StopIteration exception

    def __get_action_by_id(self, action_id):
        for action in self.actions:
            if action.id == action_id:
                return action
        return None

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
            branches = sorted(self.__get_branches_by_action_id(current_action.id))
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

    def __swap_action_arguments(self, action, start_arguments):
        logger.debug('Swapping arguments to first action of workflow {0}'.format(self.name))
        try:
            action.set_arguments(start_arguments)
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.WorkflowArgumentsValidated)
        except InvalidArgument as e:
            logger.error('Cannot change arguments to workflow {0}. '
                         'Invalid arguments. Error: {1}'.format(self.name, format_exception_message(e)))
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.WorkflowArgumentsInvalid)

    def __shutdown(self, instances):
        # Upon finishing shuts down instances
        for instance_name, instance in instances.items():
            try:
                if instance() is not None:
                    logger.debug('Shutting down app instance: Device: {0}'.format(instance_name))
                    instance.shutdown()
            except Exception as e:
                logger.error('Error caught while shutting down app instance. '
                             'Device: {0}. Error {1}'.format(instance_name, format_exception_message(e)))
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
        return self._executing_action.id

    def get_accumulator(self):
        return self._accumulator

    def get_instances(self):
        return self._instances

    def regenerate_ids(self, with_children=True, action_mapping=None):
        """
        Regenerates the IDs of the workflow and its children
        Args:
            with_children (bool optional): Regenerate the childrens' IDs of this object? Defaults to True
            action_mapping (dict, optional): The dictionary of prev action IDs to new action IDs. Defaults to None.
        """
        self.id = str(uuid4())
        action_mapping = {}

        for action in self.actions:
            prev_id = action.id
            action_mapping[prev_id] = action.id

        for action in self.actions:
            action.regenerate_ids(action_mapping)

        for branch in self.branches:
            branch.source_id = action_mapping[branch.source_id]
            branch.destination_id = action_mapping[branch.destination_id]
            branch.regenerate_ids(action_mapping)

        self.start = action_mapping[self.start]
