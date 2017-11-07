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
from core.argument import Argument
from core.helpers import get_app_action_api, InvalidInput, dereference_step_routing, format_exception_message
from core.validator import validate_app_action_parameters
from core.widgetsignals import get_widget_signal

logger = logging.getLogger(__name__)


class Widget(object):
    def __init__(self, app, name):
        self.app = app
        self.name = name


class Step(ExecutionElement):
    _templatable = True

    def __init__(self, app, action, name='', device='', arguments=None, triggers=None, position=None, widgets=None,
                 risk=0, uid=None, templated=False, raw_representation=None):
        """Initializes a new Step object. A Workflow has many steps that it executes.

        Args:
            app (str): The name of the app associated with the Step
            action (str): The name of the action associated with a Step
            name (str, optional): The name of the Step object. Defaults to an empty string.
            device (str, optional): The name of the device associated with the app associated with the Step. Defaults
                to an empty string.
            arguments ([Argument], optional): A list of Argument objects that are input to the step execution. Defaults
                to None.
            triggers (list[Flag], optional): A list of Flag objects for the Step. If a Step should wait for data
                before continuing, then include these Trigger objects in the Step init. Defaults to None.
            position (dict, optional): A dictionary with the x and y coordinates of the Step object. This is used
                for UI display purposes. Defaults to None.
            widgets (list[tuple(str, str)], optional): A list of widget tuples, which holds the app and the
                corresponding widget. Defaults to None.
            risk (int, optional): The risk associated with the Step. Defaults to 0.
            uid (str, optional): A universally unique identifier for this object.
                Created from uuid.uuid4().hex in Python
            templated (bool, optional): Whether or not the Step is templated. Used for Jinja templating.
            raw_representation (dict, optional): JSON representation of this object. Used for Jinja templating.
        """
        ExecutionElement.__init__(self, uid)

        self.triggers = triggers if triggers is not None else []
        self._incoming_data = AsyncResult()

        self.name = name
        self.app = app
        self.action = action
        self._run, self._input_api = get_app_action_api(self.app, self.action)
        get_app_action(self.app, self._run)

        if isinstance(arguments, list):
            arguments = {arg.name: arg for arg in arguments}
        elif isinstance(arguments, dict):
            arguments = arguments
        else:
            arguments = {}
        self.templated = templated
        if not self.templated:
            self.arguments = validate_app_action_parameters(self._input_api, arguments, self.app, self.action)
        else:
            self.arguments = arguments
        self.device = device if (device is not None and device != 'None') else ''
        self.risk = risk
        self.position = position if position is not None else {}
        self.widgets = [widget if isinstance(widget, Widget) else Widget(**widget)
                        for widget in widgets] if widgets is not None else []

        self._output = None
        self._raw_representation = raw_representation if raw_representation is not None else {}
        self._execution_uid = 'default'

    def get_output(self):
        """Gets the output of a Step (the result)

        Returns:
            The result of the Step
        """
        return self._output

    def get_execution_uid(self):
        """Gets the execution UID of the Step

        Returns:
            The execution UID
        """
        return self._execution_uid

    def send_data_to_trigger(self, data):
        """Sends data to the Step if it has triggers associated with it, and is currently awaiting data

        Args:
            data (dict): The data to send to the triggers. This dict has two keys: 'data_in' which is the data
                to be sent to the triggers, and 'inputs', which is an optional parameter to change the inputs to the
                current Step
        """
        self._incoming_data.set(data)

    def _update_json(self, updated_json):
        self.action = updated_json['action']
        self.app = updated_json['app']
        self.device = updated_json['device'] if 'device' in updated_json else ''
        self.risk = updated_json['risk'] if 'risk' in updated_json else 0
        arguments = {}
        if 'arguments' in updated_json:
            for argument_json in updated_json['arguments'].values():
                argument = Argument(**argument_json)
                arguments[argument.name] = argument
        if arguments is not None:
            if not self.templated:
                self.arguments = validate_app_action_parameters(self._input_api, arguments, self.app, self.action)
            else:
                self.arguments = arguments
        else:
            self.arguments = validate_app_action_parameters(self._input_api, [], self.app, self.action)

    @contextdecorator.context
    def render_step(self, **kwargs):
        """Uses JINJA templating to render a Step object.

        Args:
            kwargs (dict[str]): Arguments to use in the JINJA templating.
        """
        if self.templated:
            from jinja2 import Environment
            env = Environment().from_string(json.dumps(self._raw_representation)).render(
                core.config.config.JINJA_GLOBALS, **kwargs)
            self._update_json(updated_json=json.loads(env))

    def set_input(self, new_arguments):
        """Updates the arguments for a Step object.

        Args:
            new_arguments ([Argument]): The new Arguments for the Step object.
        """
        if isinstance(new_arguments, list):
            new_arguments = {arg.name: arg for arg in new_arguments}
        elif isinstance(new_arguments, dict):
            new_arguments = new_arguments
        self.arguments = validate_app_action_parameters(self._input_api, new_arguments, self.app, self.action)

    def execute(self, instance, accumulator):
        """Executes a Step by calling the associated app function.

        Args:
            instance (App): The instance of an App object to be used to execute the associated function.
            accumulator (dict): Dict containing the results of the previous steps

        Returns:
            The result of the executed function.
        """
        self._execution_uid = str(uuid.uuid4())
        data_sent.send(self, callback_name="Step Started", object_type="Step")

        if self.triggers:
            data_sent.send(self, callback_name="Trigger Step Awaiting Data", object_type="Step")
            logger.debug('Trigger Step {} is awaiting data'.format(self.name))
            self._wait_for_trigger(accumulator)

        try:
            args = {argument.name: argument.get_value(accumulator) for argument in self.arguments}
            args = validate_app_action_parameters(self._input_api, args, self.app, self.action)
            action = get_app_action(self.app, self._run)
            if is_app_action_bound(self.app, self._run):
                result = action(instance, **args)
            else:
                result = action(**args)

            data_sent.send(self, callback_name="Function Execution Success", object_type="Step",
                           data=json.dumps({"result": result.as_json()}))
        except InvalidInput as e:
            formatted_error = format_exception_message(e)
            logger.error('Error calling step {0}. Error: {1}'.format(self.name, formatted_error))
            data_sent.send(self, callback_name="Step Input Invalid", object_type="Step")
            self._output = ActionResult('error: {0}'.format(formatted_error), 'InvalidInput')
            raise
        except Exception as e:
            formatted_error = format_exception_message(e)
            logger.error('Error calling step {0}. Error: {1}'.format(self.name, formatted_error))
            self._output = ActionResult('error: {0}'.format(formatted_error), 'UnhandledException')
            raise
        else:
            self._output = result
            for widget in self.widgets:
                get_widget_signal(widget.app, widget.name).send(self, data=json.dumps({"result": result.as_json()}))
            logger.debug('Step {0}-{1} (uid {2}) executed successfully'.format(self.app, self.action, self.uid))
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
                data_sent.send(self, callback_name="Trigger Step Taken", object_type="Step")
                logger.debug('Trigger is valid for input {0}'.format(data_in))
                accumulator[self.name] = data_in

                arguments = data['arguments'] if 'arguments' in data else []
                if arguments:
                    new_args = {}
                    for argument in arguments:
                        arg = Argument(**argument)
                        new_args[arg.name] = arg
                    self.arguments.update(new_args)
                break
            else:
                logger.debug('Trigger is not valid for input {0}'.format(data_in))
                data_sent.send(self, callback_name="Trigger Step Not Taken", object_type="Step")

            gevent.sleep(0.1)
