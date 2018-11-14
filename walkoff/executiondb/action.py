import logging
import uuid

from sqlalchemy import Column, ForeignKey, String, orm, event
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from walkoff.appgateway import get_app_action, is_app_action_bound
from walkoff.appgateway.actionresult import ActionResult
from walkoff.appgateway.apiutil import get_app_action_api, UnknownApp, UnknownAppAction, InvalidArgument
from walkoff.appgateway.validator import validate_app_action_parameters
from walkoff.events import WalkoffEvent
from walkoff.executiondb import Execution_Base
from walkoff.executiondb.argument import Argument
from walkoff.executiondb.executionelement import ExecutionElement

logger = logging.getLogger(__name__)


class Action(ExecutionElement, Execution_Base):
    __tablename__ = 'action'
    workflow_id = Column(UUIDType(binary=False), ForeignKey('workflow.id', ondelete='CASCADE'))
    app_name = Column(String(80), nullable=False)
    action_name = Column(String(80), nullable=False)
    name = Column(String(80), nullable=False)
    device_id = relationship('Argument', uselist=False, cascade='all, delete-orphan',
                             foreign_keys=[Argument.action_device_id], passive_deletes=True)
    arguments = relationship('Argument', cascade='all, delete, delete-orphan', foreign_keys=[Argument.action_id],
                             passive_deletes=True)
    trigger = relationship('ConditionalExpression', cascade='all, delete-orphan', uselist=False, passive_deletes=True)
    position = relationship('Position', uselist=False, cascade='all, delete-orphan', passive_deletes=True)
    children = ('arguments', 'trigger')

    def __init__(self, app_name, action_name, name, device_id=None, id=None, arguments=None, trigger=None,
                 position=None):
        """Initializes a new Action object. A Workflow has one or more actions that it executes.
        Args:
            app_name (str): The name of the app associated with the Action
            action_name (str): The name of the action associated with a Action
            name (str): The name of the Action object.
            device_id (Argument, optional): The device_id for the Action. This device_id is specified in the Argument
                object. If the device_id should be static, then device_id.value should be set to the static device_id.
                If the device_id should be fetched from a previous Action, then the reference and optional selection
                fields of the Argument object should be filled. Defaults to None.
            id (str|UUID, optional): Optional UUID to pass into the Action. Must be UUID object or valid UUID string.
                Defaults to None.
            arguments (list[Argument], optional): A list of Argument objects that are parameters to the action.
                Defaults to None.
            trigger (ConditionalExpression, optional): A ConditionalExpression which causes an Action to wait until the
                data is sent fulfilling the condition. Defaults to None.
            position (Position, optional): Position object for the Action. Defaults to None.
        """
        ExecutionElement.__init__(self, id)

        self.trigger = trigger

        self.name = name
        self.device_id = device_id
        self.app_name = app_name
        self.action_name = action_name

        self.arguments = []
        if arguments:
            self.arguments = arguments

        self.position = position

        self._run = None
        self._arguments_api = None
        self._last_status = None
        self._execution_id = 'default'
        self._resolved_device_id = -1
        self.validate()

    @orm.reconstructor
    def init_on_load(self):
        """Loads all necessary fields upon Action being loaded from database"""
        if not self.errors:
            errors = []
            try:
                self._run, self._arguments_api = get_app_action_api(self.app_name, self.action_name)
                get_app_action(self.app_name, self._run)
            except UnknownApp:
                errors.append('Unknown app {}'.format(self.app_name))
            except UnknownAppAction:
                errors.append('Unknown app action {}'.format(self.action_name))
            self.errors = errors
        self._last_status = None
        self._execution_id = 'default'
        self._resolved_device_id = -1

    def validate(self):
        """Validates the object"""
        errors = []
        try:
            self._run, self._arguments_api = get_app_action_api(self.app_name, self.action_name)
            get_app_action(self.app_name, self._run)
            if is_app_action_bound(self.app_name, self._run) and not self.device_id:
                message = 'App action is bound but no device ID was provided.'.format(self.name)
                errors.append(message)
            validate_app_action_parameters(self._arguments_api, self.arguments, self.app_name, self.action_name)
        except UnknownApp:
            errors.append('Unknown app {}'.format(self.app_name))
        except UnknownAppAction:
            errors.append('Unknown app action {}'.format(self.action_name))
        except InvalidArgument as e:
            errors.extend(e.errors)
        self.errors = errors

    def get_execution_id(self):
        """Gets the execution ID of the Action

        Returns:
            (UUID): The execution ID
        """
        return self._execution_id

    def execute(self, action_execution_strategy, accumulator, instance=None, arguments=None, resume=False):
        """Executes an Action by calling the associated app function.

        Args:
            action_execution_strategy: The strategy used to execute the action (e.g. LocalActionExecutionStrategy)
            accumulator (dict): Dict containing the results of the previous actions
            instance (App, optional): The instance of an App object to be used to execute the associated function.
                This field is required if the Action is a bounded action. Otherwise, it defaults to None.
            arguments (list[Argument], optional): List of Arguments to be used if the Action is the starting step of
                the Workflow. Defaults to None.
            resume (bool, optional): Optional boolean to resume a previously paused workflow. Defaults to False.

        Returns:
            (ActionResult): The result of the executed function.
        """
        logger.info('Executing action {} (id={})'.format(self.name, str(self.name)))
        self._execution_id = str(uuid.uuid4())

        if self.device_id:
            self._resolved_device_id = self.device_id.get_value(accumulator)
            logger.debug('Device resolved to {} for action {}'.format(self._resolved_device_id, str(self.id)))

        if arguments:
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.ActionStarted,
                                                   data={'start_arguments': arguments})
        else:
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.ActionStarted)

        if self.trigger and not resume:
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.TriggerActionAwaitingData)
            logger.debug('Trigger Action {} is awaiting data'.format(self.name))
            return ActionResult("trigger", "trigger")

        arguments = arguments if arguments else self.arguments

        try:
            args = validate_app_action_parameters(self._arguments_api, arguments, self.app_name, self.action_name,
                                                  accumulator=accumulator)
        except InvalidArgument as e:
            result = ActionResult.from_exception(e, 'InvalidArguments')
            accumulator[self.id] = result.result
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.ActionArgumentsInvalid,
                                                   data=result.as_json())
            return result.status

        if is_app_action_bound(self.app_name, self._run):
            result = action_execution_strategy.execute(self, accumulator, args, instance=instance)
        else:
            result = action_execution_strategy.execute(self, accumulator, args)

        if result.status == 'UnhandledException':
            logger.error('Error executing action {} (id={})'.format(self.name, str(self.id)))
        else:
            logger.debug(
                'Action {0}-{1} (id {2}) executed successfully'.format(self.app_name, self.action_name, self.id))

        result.set_default_status(self.app_name, self.action_name)
        if result.is_failure(self.app_name, self.action_name):
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.ActionExecutionError,
                                                   data=result.as_json())
        else:
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.ActionExecutionSuccess,
                                                   data=result.as_json())
        return result.status

    def execute_trigger(self, action_execution_strategy, data_in, accumulator):
        """Executes the trigger for an Action, which will continue execution if the trigger returns True

        Args:
            action_execution_strategy: The strategy used to execute the action (e.g. LocalActionExecutionStrategy)
            data_in (dict): The data to send to the trigger to test against
            accumulator (dict): Dict containing the results of the previous actions

        Returns:
            (bool): True if the trigger returned True, False otherwise
        """
        if self.trigger.execute(action_execution_strategy, data_in=data_in, accumulator=accumulator):
            logger.debug('Trigger is valid for input {0}'.format(data_in))
            return True
        else:
            logger.debug('Trigger is not valid for input {0}'.format(data_in))
            return False

    def get_resolved_device_id(self):
        return self._resolved_device_id


@event.listens_for(Action, 'before_update')
def validate_before_update(mapper, connection, target):
    target.validate()
