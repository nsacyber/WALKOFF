import json
from collections import namedtuple
import logging
from core import contextdecorator
import core.config.config
from core.decorators import ActionResult
from core.executionelement import ExecutionElement
from core.helpers import (get_app_action_api, InvalidElementConstructed, InvalidInput,
                          dereference_step_routing, format_exception_message)
from core.nextstep import NextStep
from core.widgetsignals import get_widget_signal
from apps import get_app_action
from core.validator import validate_app_action_parameters
from core.case.callbacks import data_sent
import uuid
logger = logging.getLogger(__name__)


class Widget(object):
    def __init__(self, app, name):
        self.app = app
        self.name = name


class Step(ExecutionElement):
    def __init__(self,
                 name='',
                 action='',
                 app='',
                 device='',
                 inputs=None,
                 next_steps=None,
                 position=None,
                 widgets=None,
                 risk=0,
                 uid=None,
                 templated=False,
                 raw_representation=None):
        """Initializes a new Step object. A Workflow has many steps that it executes.
        
        Args:
            name (str, optional): The name of the Step object. Defaults to an empty string.
            action (str, optional): The name of the action associated with a Step. Defaults to an empty string.
            app (str, optional): The name of the app associated with the Step. Defaults to an empty string.
            device (str, optional): The name of the device associated with the app associated with the Step. Defaults
                to an empty string.
            inputs (dict, optional): A dictionary of Argument objects that are input to the step execution. Defaults
                to None.
            next_steps (list[NextStep], optional): A list of NextStep objects for the Step object. Defaults to None.
            position (dict, optional): A dictionary with the x and y coordinates of the Step object. This is used
                for UI display purposes. Defaults to None.
            widgets (list[tuple(str, str)], optional): A list of widget tuples, which holds the app and the
                corresponding widget. Defaults to None.
            risk (int, optional): The risk associated with the Step. Defaults to 0.
            uid (str, optional): A universally unique identifier for this object.
                Created from uuid.uuid4().hex in Python
            raw_representation (dict, optional): JSON representation of this object. Used for Jinja templating
        """
        ExecutionElement.__init__(self, uid)
        if action == '' or app == '':
            raise InvalidElementConstructed('Either both action and app or xml must be '
                                            'specified in step constructor')
        self.name = name
        self.action = action
        self.app = app
        self._run, self._input_api = get_app_action_api(self.app, self.action)
        get_app_action(self.app, self._run)
        inputs = inputs if inputs is not None else {}
        self.templated = templated
        if not self.templated:
            self.inputs = validate_app_action_parameters(self._input_api, inputs, self.app, self.action)
        else:
            self.inputs = inputs
        self.device = device
        self.risk = risk
        self.next_steps = next_steps if next_steps is not None else []
        self.position = position if position is not None else {}
        self.widgets = [Widget(widget_app, widget_name)
                        for (widget_app, widget_name) in widgets] if widgets is not None else []

        self._output = None
        self._next_up = None
        self._raw_representation = raw_representation if raw_representation is not None else {}
        self._execution_uid = 'default'

    def get_output(self):
        return self._output

    def get_next_up(self):
        return self._next_up

    def set_next_up(self, next_up):
        self._next_up = next_up

    def get_execution_uid(self):
        return self._execution_uid

    def _update_json(self, updated_json):
        self.action = updated_json['action']
        self.app = updated_json['app']
        self.device = updated_json['device'] if 'device' in updated_json else ''
        self.risk = updated_json['risk'] if 'risk' in updated_json else 0
        inputs = {arg['name']: arg['value'] for arg in updated_json['inputs']} if 'inputs' in updated_json else {}
        if inputs is not None:
            if not self.templated:
                self.inputs = validate_app_action_parameters(self._input_api, inputs, self.app, self.action)
            else:
                self.inputs = inputs
        else:
            self.inputs = validate_app_action_parameters(self._input_api, {}, self.app, self.action)
        self.next_steps = [NextStep.from_json(cond_json) for cond_json in updated_json['next_steps']]

    @contextdecorator.context
    def render_step(self, **kwargs):
        """Uses JINJA templating to render a Step object. 
        
        Args:
            kwargs (dict[str]): Arguments to use in the JINJA templating.
        """
        if self.templated:
            from jinja2 import Environment
            env = Environment().from_string(json.dumps(self._raw_representation)).render(core.config.config.JINJA_GLOBALS, **kwargs)
            self._update_json(updated_json=json.loads(env))

    def set_input(self, new_input):
        """Updates the input for a Step object.

        Args:
            new_input (dict): The new inputs for the Step object.
        """
        self.inputs = validate_app_action_parameters(self._input_api, new_input, self.app, self.action)

    def __send_callback(self, callback_name, data={}):
        data['sender'] = {}
        data['sender']['name'] = self.name
        data['sender']['app'] = self.app
        data['sender']['action'] = self.action
        data['sender']['inputs'] = self.inputs
        data['callback_name'] = callback_name
        data['sender']['id'] = self.name
        data['sender']['execution_uid'] = self._execution_uid
        data['sender']['uid'] = self.uid
        data_sent.send(None, data=data)
        # if self.results_sock:
        #     self.results_sock.send_json(data)

    def execute(self, instance, accumulator):
        """Executes a Step by calling the associated app function.
        
        Args:
            instance (App): The instance of an App object to be used to execute the associated function.
            accumulator (dict): Dict containing the results of the previous steps
            
        Returns:
            The result of the executed function.
        """
        self._execution_uid = uuid.uuid4().hex
        self.__send_callback('Step Started')
        try:
            args = dereference_step_routing(self.inputs, accumulator, 'In step {0}'.format(self.name))
            args = validate_app_action_parameters(self._input_api, args, self.app, self.action)
            action = get_app_action(self.app, self._run)
            result = action(instance, **args)
            self.__send_callback('Function Execution Success',
                                 {'name': self.name, 'data': {'result': result.as_json()}})
        except InvalidInput as e:
            formatted_error = format_exception_message(e)
            logger.error('Error calling step {0}. Error: {1}'.format(self.name, formatted_error))
            self.__send_callback('Step Input Invalid')
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
                get_widget_signal(widget.app, widget.widget).send(self, data=json.dumps({"result": result.as_json()}))
            logger.debug('Step {0}-{1} (uid {2}) executed successfully'.format(self.app, self.action, self.uid))
            return result

    def get_next_step(self, accumulator):
        """Gets the NextStep object to be executed after the current Step.
        
        Args:
            accumulator (dict): A record of teh previously-executed steps. Of form {step_name: result}
                 
        Returns:
            The NextStep object to be executed.
        """

        for next_step in self.next_steps:
            next_step = next_step(self._output, accumulator)
            if next_step is not None:
                self._next_up = next_step
                self.__send_callback('Conditionals Executed')
                return next_step

    def __repr__(self):
        output = {'uid': self.uid,
                  'name': self.name,
                  'action': self.action,
                  'app': self.app,
                  'device': self.device,
                  'risk': str(self.risk),
                  'input': self.inputs,
                  'next_steps': [next_step for next_step in self.next_steps],
                  'nextUp': self._next_up,
                  'position': self.position,
                  'widget': str([{'app': widget.app, 'name': widget.widget} for widget in self.widgets])}
        if self._output:
            output["output"] = self._output.as_json()
        return str(output)

    @staticmethod
    def from_json(json_in, position):
        """Forms a Step object from the provided JSON object.
        
        Args:
            json_in (dict): The JSON object to convert from.
            position (dict): position of the step node of the form {'x': <x position>, 'y': <y position>}
            
        Returns:
            The Step object parsed from the JSON object.
        """
        device = json_in['device'] if ('device' in json_in
                                       and json_in['device'] is not None
                                       and json_in['device'] != 'None') else ''
        risk = json_in['risk'] if 'risk' in json_in else 0
        widgets = []
        uid = json_in['uid'] if 'uid' in json_in else None
        if 'widgets' in json_in:
            widgets = [(widget['app'], widget['name'])
                       for widget in json_in['widgets'] if ('app' in widget and 'name' in widget)]
        conditionals = []
        if 'next_steps' in json_in:
            conditionals = [NextStep.from_json(next_step) for next_step in json_in['next_steps'] if next_step]
        if isinstance(position, list):
            print('incorrect!')
            position = {}
        return Step(name=json_in['name'],
                    action=json_in['action'],
                    app=json_in['app'],
                    device=device,
                    risk=risk,
                    inputs={arg['name']: arg['value'] for arg in json_in['inputs']},
                    next_steps=conditionals,
                    position={key: value for key, value in position.items()},
                    widgets=widgets,
                    uid=uid,
                    templated=json_in['templated'] if 'templated' in json_in else False,
                    raw_representation=json_in)
