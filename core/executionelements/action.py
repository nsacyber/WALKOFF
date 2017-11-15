import json
import logging
import uuid

import gevent
from gevent.event import AsyncResult

import core.config.config
from apps import get_app_action, is_app_action_bound
from core import contextdecorator
from core.case.callbacks import data_sent
from core.decorators import ActionResult
from core.executionelements.executionelement import ExecutionElement
from core.helpers import get_app_action_api, InvalidArgument, format_exception_message
from core.validator import validate_app_action_parameters
from core.argument import Argument

logger = logging.getLogger(__name__)


class Action(ExecutionElement):
    _templatable = True

    def __init__(self, app, action, name='', device_id=None, arguments=None, triggers=None, position=None,
                 risk=0, uid=None, templated=False, raw_representation=None):
        """Initializes a new Action object. A Workflow has many actions that it executes.

        Args:
            app (str): The name of the app associated with the Action
            action (str): The name of the action associated with a Action
            name (str, optional): The name of the Action object. Defaults to an empty string.
            device_id (int, optional): The id of the device associated with the app associated with the Action. Defaults
                to None.
            arguments ([Argument], optional): A list of Argument objects that are arguments to the action.
                Defaults to None.
            triggers (list[Flag], optional): A list of Flag objects for the Action. If a Action should wait for data
                before continuing, then include these Trigger objects in the Action init. Defaults to None.
            position (dict, optional): A dictionary with the x and y coordinates of the Action object. This is used
                for UI display purposes. Defaults to None.
            risk (int, optional): The risk associated with the Action. Defaults to 0.
            uid (str, optional): A universally unique identifier for this object.
                Created from uuid.uuid4().hex in Python
            templated (bool, optional): Whether or not the Action is templated. Used for Jinja templating.
            raw_representation (dict, optional): JSON representation of this object. Used for Jinja templating.
        """
        ExecutionElement.__init__(self, uid)

        self.triggers = triggers if triggers is not None else []
        self._incoming_data = AsyncResult()

        self.name = name
        self.app = app
        self.action = action
        self._run, self._arguments_api = get_app_action_api(self.app, self.action)
        self._action_executable = get_app_action(self.app, self._run)

        # arguments = [Argument(**json_in) for json_in in arguments] if arguments is not None else []
        arguments = {argument.name: argument for argument in arguments} if arguments is not None else {}

        self.templated = templated
        if not self.templated:
            validate_app_action_parameters(self._arguments_api, arguments, self.app, self.action)
        self.arguments = arguments
        self.device_id = device_id
        self.risk = risk
        self.position = position if position is not None else {}

        self._output = None
        self._raw_representation = raw_representation if raw_representation is not None else {}
        self._execution_uid = 'default'

    def get_output(self):
        """Gets the output of a Action (the result)

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
        self._incoming_data.set(data)

    def _update_json(self, updated_json):
        self.action = updated_json['action']
        self.app = updated_json['app']
        self.device_id = updated_json['device'] if 'device' in updated_json else ''
        self.risk = updated_json['risk'] if 'risk' in updated_json else 0
        arguments = {}
        if 'arguments' in updated_json:
            for argument_json in updated_json['arguments']:
                argument = Argument(**argument_json)
                arguments[argument.name] = argument
        if arguments is not None:
            if not self.templated:
                validate_app_action_parameters(self._arguments_api, arguments, self.app, self.action)
        else:
            validate_app_action_parameters(self._arguments_api, [], self.app, self.action)
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
                core.config.config.JINJA_GLOBALS, **kwargs)
            self._update_json(updated_json=json.loads(env))

    def set_arguments(self, new_arguments):
        """Updates the arguments for a Action object.

        Args:
            new_arguments ([Argument]): The new Arguments for the Action object.
        """
        new_arguments = {arg.name: arg for arg in new_arguments}
        validate_app_action_parameters(self._arguments_api, new_arguments, self.app, self.action)
        self.arguments = new_arguments

    def execute(self, instance, accumulator):
        """Executes a Action by calling the associated app function.

        Args:
            instance (App): The instance of an App object to be used to execute the associated function.
            accumulator (dict): Dict containing the results of the previous actions

        Returns:
            The result of the executed function.
        """
        self._execution_uid = str(uuid.uuid4())
        data_sent.send(self, callback_name="Action Started", object_type="Action")

        if self.triggers:
            data_sent.send(self, callback_name="Trigger Action Awaiting Data", object_type="Action")
            logger.debug('Trigger Action {} is awaiting data'.format(self.name))
            self._wait_for_trigger(accumulator)

        try:
            args = validate_app_action_parameters(self._arguments_api, self.arguments, self.app, self.action,
                                                  accumulator=accumulator)
            if is_app_action_bound(self.app, self._run):
                result = self._action_executable(instance, **args)
            else:
                result = self._action_executable(**args)

            data_sent.send(self, callback_name="Function Execution Success", object_type="Action",
                           data=result.as_json())
        except InvalidArgument as e:
            formatted_error = format_exception_message(e)
            logger.error('Error calling action {0}. Error: {1}'.format(self.name, formatted_error))
            data_sent.send(self, callback_name="Action Argument Invalid", object_type="Action")
            self._output = ActionResult('error: {0}'.format(formatted_error), 'InvalidArguments')
            raise
        except Exception as e:
            formatted_error = format_exception_message(e)
            logger.exception('Error calling action {0}. Error: {1}'.format(self.name, formatted_error))
            self._output = ActionResult('error: {0}'.format(formatted_error), 'UnhandledException')
            raise
        else:
            self._output = result
            logger.debug('Action {0}-{1} (uid {2}) executed successfully'.format(self.app, self.action, self.uid))
            return result

    def _wait_for_trigger(self, accumulator):
        while True:
            try:
                data = self._incoming_data.get(timeout=1)
                self._incoming_data = AsyncResult()
            except gevent.Timeout:
                gevent.sleep(0.1)
                continue
            data_in = data['data_in']

            if all(flag.execute(data_in=data_in, accumulator=accumulator) for flag in self.triggers):
                data_sent.send(self, callback_name="Trigger Action Taken", object_type="Action")
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
                data_sent.send(self, callback_name="Trigger Action Not Taken", object_type="Action")

            gevent.sleep(0.1)
