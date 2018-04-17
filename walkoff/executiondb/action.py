import logging
import traceback
import uuid

from sqlalchemy import Column, ForeignKey, String, orm, event
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from walkoff.appgateway import get_app_action, is_app_action_bound
from walkoff.appgateway.actionresult import ActionResult
from walkoff.appgateway.validator import validate_app_action_parameters
from walkoff.events import WalkoffEvent
from walkoff.executiondb import Execution_Base
from walkoff.executiondb.argument import Argument
from walkoff.executiondb.executionelement import ExecutionElement
from walkoff.helpers import UnknownApp, UnknownAppAction
from walkoff.helpers import get_app_action_api, InvalidArgument, format_exception_message

logger = logging.getLogger(__name__)


class Action(ExecutionElement, Execution_Base):
    __tablename__ = 'action'
    workflow_id = Column(UUIDType(binary=False), ForeignKey('workflow.id'))
    app_name = Column(String(80), nullable=False)
    action_name = Column(String(80), nullable=False)
    name = Column(String(80), nullable=False)
    device_id = relationship('Argument', uselist=False, cascade='all, delete-orphan',
                             foreign_keys=[Argument.action_device_id])
    arguments = relationship('Argument', cascade='all, delete, delete-orphan', foreign_keys=[Argument.action_id])
    trigger = relationship('ConditionalExpression', cascade='all, delete-orphan', uselist=False)
    position = relationship('Position', uselist=False, cascade='all, delete-orphan')
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
        self._output = None
        self._execution_id = 'default'
        self._action_executable = None
        self._resolved_device_id = -1
        self.validate()

    @orm.reconstructor
    def init_on_load(self):
        """Loads all necessary fields upon Action being loaded from database"""
        if not self.errors:
            self._run, self._arguments_api = get_app_action_api(self.app_name, self.action_name)
            self._action_executable = get_app_action(self.app_name, self._run)
        self._output = None
        self._execution_id = 'default'
        self._resolved_device_id = -1

    def validate(self):
        """Validates the object"""
        errors = []
        try:
            self._run, self._arguments_api = get_app_action_api(self.app_name, self.action_name)
            self._action_executable = get_app_action(self.app_name, self._run)
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

    def get_output(self):
        """Gets the output of an Action (the result)

        Returns:
            (ActionResult): The result of the Action
        """
        return self._output

    def get_execution_id(self):
        """Gets the execution ID of the Action

        Returns:
            (UUID): The execution ID
        """
        return self._execution_id

    def execute(self, accumulator, instance=None, arguments=None, resume=False):
        """Executes an Action by calling the associated app function.

        Args:
            accumulator (dict): Dict containing the results of the previous actions
            instance (App, optional): The instance of an App object to be used to execute the associated function.
                This field is required if the Action is a bounded action. Otherwise, it defaults to None.
            arguments (list[Argument], optional): List of Arguments to be used if the Action is the starting step of
                the Workflow. Defaults to None.
            resume (bool, optional): Optional boolean to resume a previously paused workflow. Defaults to False.

        Returns:
            (ActionResult): The result of the executed function.
        """
        self._execution_id = str(uuid.uuid4())

        if self.device_id:
            self._resolved_device_id = self.device_id.get_value(accumulator)

        WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.ActionStarted)
        if self.trigger and not resume:
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.TriggerActionAwaitingData)
            logger.debug('Trigger Action {} is awaiting data'.format(self.name))
            self._output = None
            return ActionResult("trigger", "trigger")

        arguments = arguments if arguments else self.arguments

        try:
            args = validate_app_action_parameters(self._arguments_api, arguments, self.app_name, self.action_name,
                                                  accumulator=accumulator)
            if is_app_action_bound(self.app_name, self._run):
                result = self._action_executable(instance, **args)
            else:
                result = self._action_executable(**args)
            result.set_default_status(self.app_name, self.action_name)
            if result.is_failure(self.app_name, self.action_name):
                WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.ActionExecutionError,
                                                       data=result.as_json())
            else:
                WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.ActionExecutionSuccess,
                                                       data=result.as_json())
        except Exception as e:
            self.__handle_execution_error(e)
        else:
            self._output = result
            logger.debug(
                'Action {0}-{1} (id {2}) executed successfully'.format(self.app_name, self.action_name, self.id))
            return result

    def __handle_execution_error(self, e):
        formatted_error = format_exception_message(e)
        if isinstance(e, InvalidArgument):
            event = WalkoffEvent.ActionArgumentsInvalid
            return_type = 'InvalidArguments'
        else:
            event = WalkoffEvent.ActionExecutionError
            return_type = 'UnhandledException'
        logger.warning('Exception in {0}: \n{1}'.format(self.name, traceback.format_exc()))
        logger.error('Error calling action {0}. Error: {1}'.format(self.name, formatted_error))
        self._output = ActionResult('error: {0}'.format(formatted_error), return_type)
        WalkoffEvent.CommonWorkflowSignal.send(self, event=event, data=self._output.as_json())

    def execute_trigger(self, data_in, accumulator):
        """Executes the trigger for an Action, which will continue execution if the trigger returns True

        Args:
            data_in (dict): The data to send to the trigger to test against
            accumulator (dict): Dict containing the results of the previous actions

        Returns:
            (bool): True if the trigger returned True, False otherwise
        """
        if self.trigger.execute(data_in=data_in, accumulator=accumulator):
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
