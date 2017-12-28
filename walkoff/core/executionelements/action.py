import json
import logging
import threading
import uuid

import walkoff.config.config
from walkoff.appgateway import get_app_action, is_app_action_bound
from walkoff.core import contextdecorator
from walkoff.core.argument import Argument
from walkoff.core.actionresult import ActionResult
from walkoff.core.events import WalkoffEvent
from walkoff.core.executionelements.executionelement import ExecutionElement
from walkoff.core.helpers import get_app_action_api, InvalidArgument, format_exception_message
from walkoff.appgateway.validator import validate_app_action_parameters

logger = logging.getLogger(__name__)


class Action(ExecutionElement):
    _templatable = True

    def __init__(self, app_name, action_name, name='', device_id=None, arguments=None, triggers=None, position=None,
                 uid=None, templated=False, raw_representation=None):
        """Initializes a new Action object. A Workflow has many actions that it executes.

        Args:
            app_name (str): The name of the app associated with the Action
            action_name (str): The name of the action associated with a Action
            name (str, optional): The name of the Action object. Defaults to an empty string.
            device_id (int, optional): The id of the device associated with the app associated with the Action. Defaults
                to None.
            arguments ([Argument], optional): A list of Argument objects that are parameters to the action.
                Defaults to None.
            triggers (list[Flag], optional): A list of Flag objects for the Action. If a Action should wait for data
                before continuing, then include these Trigger objects in the Action init. Defaults to None.
            position (dict, optional): A dictionary with the x and y coordinates of the Action object. This is used
                for UI display purposes. Defaults to None.
            uid (str, optional): A universally unique identifier for this object.
                Created from uuid.uuid4().hex in Python
            templated (bool, optional): Whether or not the Action is templated. Used for Jinja templating.
            raw_representation (dict, optional): JSON representation of this object. Used for Jinja templating.
        """
        ExecutionElement.__init__(self, uid)

        self.triggers = triggers if triggers is not None else []
        self._incoming_data = None
        self._event = threading.Event()

        self.name = name
        self.device_id = device_id
        self.app_name = app_name
        self.action_name = action_name
        self._run, self._arguments_api = get_app_action_api(self.app_name, self.action_name)

        if is_app_action_bound(self.app_name, self._run) and not self.device_id:
            raise InvalidArgument(
                "Cannot initialize Action {}. App action is bound but no device ID was provided.".format(self.name))

        self._action_executable = get_app_action(self.app_name, self._run)

        arguments = {argument.name: argument for argument in arguments} if arguments is not None else {}

        self.templated = templated
        if not self.templated:
            validate_app_action_parameters(self._arguments_api, arguments, self.app_name, self.action_name)
        self.arguments = arguments
        self.position = position if position is not None else {}

        self._output = None
        self._raw_representation = raw_representation if raw_representation is not None else {}
        self._execution_uid = 'default'

    def get_output(self):
        """Gets the output of an Action (the result)

        Returns:
            The result of the Action
        """
        return self._output

    def get_execution_uid(self):
        """Gets the execution UID of the Action

        Returns:
            The execution UID
        """
        return self._execution_uid

    def send_data_to_trigger(self, data):
        """Sends data to the Action if it has triggers associated with it, and is currently awaiting data

        Args:
            data (dict): The data to send to the triggers. This dict has two keys: 'data_in' which is the data
                to be sent to the triggers, and 'arguments', which is an optional parameter to change the arguments
                to the current Action
        """
        self._incoming_data = data
        self._event.set()

    def _update_json(self, updated_json):
        self.action_name = updated_json['action_name']
        self.app_name = updated_json['app_name']
        self.device_id = updated_json['device_id'] if 'device_id' in updated_json else None
        arguments = {}
        if 'arguments' in updated_json:
            for argument_json in updated_json['arguments']:
                argument = Argument(**argument_json)
                arguments[argument.name] = argument
        if arguments is not None:
            if not self.templated:
                validate_app_action_parameters(self._arguments_api, arguments, self.app_name, self.action_name)
        else:
            validate_app_action_parameters(self._arguments_api, [], self.app_name, self.action_name)
        self.arguments = arguments

    @contextdecorator.context
    def render_action(self, **kwargs):
        """Uses JINJA templating to render a Action object.

        Args:
            kwargs (dict[str]): Arguments to use in the JINJA templating.
        """
        if self.templated:
            from jinja2 import Environment
            env = Environment().from_string(json.dumps(self._raw_representation)).render(
                walkoff.config.config.JINJA_GLOBALS, **kwargs)
            self._update_json(updated_json=json.loads(env))

    def set_arguments(self, new_arguments):
        """Updates the arguments for an Action object.

        Args:
            new_arguments ([Argument]): The new Arguments for the Action object.
        """
        new_arguments = {arg.name: arg for arg in new_arguments}
        validate_app_action_parameters(self._arguments_api, new_arguments, self.app_name, self.action_name)
        self.arguments = new_arguments

    def execute(self, instance, accumulator):
        """Executes an Action by calling the associated app function.

        Args:
            instance (App): The instance of an App object to be used to execute the associated function.
            accumulator (dict): Dict containing the results of the previous actions

        Returns:
            The result of the executed function.
        """
        self._execution_uid = str(uuid.uuid4())

        WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.ActionStarted)

        if self.triggers:
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.TriggerActionAwaitingData)
            logger.debug('Trigger Action {} is awaiting data'.format(self.name))
            self._wait_for_trigger(accumulator)

        try:
            args = validate_app_action_parameters(self._arguments_api, self.arguments, self.app_name, self.action_name,
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
        except InvalidArgument as e:
            formatted_error = format_exception_message(e)
            logger.error('Error calling action {0}. Error: {1}'.format(self.name, formatted_error))
            # TODO: Should this event return the error?
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.ActionArgumentsInvalid)
            self._output = ActionResult('error: {0}'.format(formatted_error), 'InvalidArguments')
        except Exception as e:
            formatted_error = format_exception_message(e)
            logger.exception('Error calling action {0}. Error: {1}'.format(self.name, formatted_error))
            self._output = ActionResult('error: {0}'.format(formatted_error), 'UnhandledException')
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.ActionExecutionError,
                                                   data=self._output.as_json())
        else:
            self._output = result
            logger.debug(
                'Action {0}-{1} (uid {2}) executed successfully'.format(self.app_name, self.action_name, self.uid))
            return result

    def _wait_for_trigger(self, accumulator):
        while True:
            self._event.wait()
            if self._incoming_data is None:
                continue
            data = self._incoming_data
            data_in = data['data_in']
            self._incoming_data = None
            self._event.clear()

            if all(condition.execute(data_in=data_in, accumulator=accumulator) for condition in self.triggers):
                WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.TriggerActionTaken)
                logger.debug('Trigger is valid for input {0}'.format(data_in))
                accumulator[self.name] = data_in

                arguments = data['arguments'] if 'arguments' in data else []
                if arguments:
                    new_args = {}
                    for argument in arguments:
                        new_args[argument.name] = argument
                    self.arguments.update(new_args)
                break
            else:
                logger.debug('Trigger is not valid for input {0}'.format(data_in))
                WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.TriggerActionNotTaken)
