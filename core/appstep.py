import json
from collections import namedtuple
import logging
from core import contextdecorator
import core.config.config
from core.decorators import ActionResult
from core.step import Step
from core.helpers import (get_app_action_api, InvalidElementConstructed, InvalidInput,
                          dereference_step_routing, format_exception_message)
from core.nextstep import NextStep
from core.widgetsignals import get_widget_signal
from apps import get_app_action
from core.validator import validate_app_action_parameters
from core.case.callbacks import data_sent
import uuid
logger = logging.getLogger(__name__)

_Widget = namedtuple('Widget', ['app', 'widget'])


class AppStep(Step):
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
                 raw_json=None):
        """Initializes a new Step Action object. A Workflow has many steps that it executes.
        
        Args:
            name (str, optional): The name of the Step Action object. Defaults to an empty string.
            action (str, optional): The name of the action associated with a Step. Defaults to an empty string.
            app (str, optional): The name of the app associated with the Step. Defaults to an empty string.
            device (str, optional): The name of the device associated with the app associated with the Step. Defaults
                to an empty string.
            inputs (dict, optional): A dictionary of Argument objects that are input to the step execution. Defaults
                to None.
            next_steps (list[NextStep], optional): A list of NextStep Action objects for the Step Action object. 
                Defaults to None.
            position (dict, optional): A dictionary with the x and y coordinates of the Step Action object. This is used
                for UI display purposes. Defaults to None.
            widgets (list[tuple(str, str)], optional): A list of widget tuples, which holds the app and the
                corresponding widget. Defaults to None.
            risk (int, optional): The risk associated with the Step. Defaults to 0.
            uid (str, optional): A universally unique identifier for this object.
                Created from uuid.uuid4().hex in Python
            raw_json (dict, optional): JSON representation of this object. Used for Jinja templating
        """
        Step.__init__(name, device, next_steps, position, widgets, risk, uid, raw_json)

        if action == '' or app == '':
            raise InvalidElementConstructed('Both action and app must be specified in app step constructor')
        self.action = action
        self.app = app
        self.run, self.input_api = get_app_action_api(self.app, self.action)
        get_app_action(self.app, self.run)
        inputs = inputs if inputs is not None else {}
        self.templated = templated
        if not self.templated:
            self.input = validate_app_action_parameters(self.input_api, inputs, self.app, self.action)
        else:
            self.input = inputs

    def _update_json(self, updated_json):
        self.action = updated_json['action']
        self.app = updated_json['app']
        self.device = updated_json['device'] if 'device' in updated_json else ''
        self.risk = updated_json['risk'] if 'risk' in updated_json else 0
        inputs = {arg['name']: arg['value'] for arg in updated_json['inputs']} if 'inputs' in updated_json else {}
        if inputs is not None:
            if not self.templated:
                self.input = validate_app_action_parameters(self.input_api, inputs, self.app, self.action)
            else:
                self.input = inputs
        else:
            self.input = validate_app_action_parameters(self.input_api, {}, self.app, self.action)
        self.conditionals = [NextStep.from_json(cond_json) for cond_json in updated_json['next']]

    @contextdecorator.context
    def render_step(self, **kwargs):
        """Uses JINJA templating to render a Step Action object. 
        
        Args:
            kwargs (dict[str]): Arguments to use in the JINJA templating.
        """
        if self.templated:
            from jinja2 import Environment
            env = Environment().from_string(json.dumps(self.raw_json)).render(core.config.config.JINJA_GLOBALS, **kwargs)
            self._update_json(updated_json=json.loads(env))

    def set_input(self, new_input):
        """Updates the input for a Step Action object.

        Args:
            new_input (dict): The new inputs for the Step Action object.
        """
        self.input = validate_app_action_parameters(self.input_api, new_input, self.app, self.action)

    def execute(self, instance, accumulator):
        """Executes a Step by calling the associated app function.
        
        Args:
            instance (App): The instance of an App object to be used to execute the associated function.
            accumulator (dict): Dict containing the results of the previous steps
            
        Returns:
            The result of the executed function.
        """
        self.execution_uid = uuid.uuid4().hex
        data_sent.send(self, callback_name="Step Started", object_type="Step")
        try:
            args = dereference_step_routing(self.input, accumulator, 'In step {0}'.format(self.name))
            args = validate_app_action_parameters(self.input_api, args, self.app, self.action)
            action = get_app_action(self.app, self.run)
            result = action(instance, **args)
            data_sent.send(self, callback_name="Function Execution Success", object_type="Step",
                           data=json.dumps({"result": result.as_json()}))
        except InvalidInput as e:
            formatted_error = format_exception_message(e)
            logger.error('Error calling step {0}. Error: {1}'.format(self.name, formatted_error))
            data_sent.send(self, callback_name="Step Input Invalid", object_type="Step")
            self.output = ActionResult('error: {0}'.format(formatted_error), 'InvalidInput')
            raise
        except Exception as e:
            formatted_error = format_exception_message(e)
            logger.error('Error calling step {0}. Error: {1}'.format(self.name, formatted_error))
            self.output = ActionResult('error: {0}'.format(formatted_error), 'UnhandledException')
            raise
        else:
            self.output = result
            for widget in self.widgets:
                get_widget_signal(widget.app, widget.widget).send(self, data=json.dumps({"result": result.as_json()}))
            logger.debug('Step {0}-{1} (uid {2}) executed successfully'.format(self.app, self.action, self.uid))
            return result

    def __repr__(self):
        output = {'uid': self.uid,
                  'name': self.name,
                  'action': self.action,
                  'app': self.app,
                  'device': self.device,
                  'risk': str(self.risk),
                  'input': self.input,
                  'next': [next_step for next_step in self.conditionals],
                  'nextUp': self.next_up,
                  'position': self.position,
                  'widget': str([{'app': widget.app, 'name': widget.widget} for widget in self.widgets])}
        if self.output:
            output["output"] = self.output.as_json()
        return str(output)

    def as_json(self):
        """Gets the JSON representation of a Step Action object.
                
        Returns:
            The JSON representation of a Step Action object.
        """
        output = {"uid": self.uid,
                  "name": str(self.name),
                  "action": str(self.action),
                  "app": str(self.app),
                  "device": str(self.device),
                  "risk": self.risk,
                  "inputs": [{'name': arg_name, 'value': arg_value} for arg_name, arg_value in self.input.items()],
                  'widgets': [{'app': widget.app, 'name': widget.widget} for widget in self.widgets],
                  "position": self.position,
                  "next": [next_step.as_json() for next_step in self.conditionals if next_step.name is not None]}
        if self.output:
            output["output"] = self.output.as_json()
        return output

    @staticmethod
    def from_json(json_in, position):
        """Forms a Step Action object from the provided JSON object.
        
        Args:
            json_in (dict): The JSON object to convert from.
            position (dict): position of the step node of the form {'x': <x position>, 'y': <y position>}
            
        Returns:
            The Step Action object parsed from the JSON object.
        """
        device = json_in['device'] if ('device' in json_in
                                       and json_in['device'] is not None
                                       and json_in['device'] != 'None') else ''
        risk = json_in['risk'] if 'risk' in json_in else 0
        widgets = []
        uid = json_in['uid'] if 'uid' in json_in else uuid.uuid4().hex
        if 'widgets' in json_in:
            widgets = [(widget['app'], widget['name'])
                       for widget in json_in['widgets'] if ('app' in widget and 'name' in widget)]
        conditionals = []
        if 'next' in json_in:
            conditionals = [NextStep.from_json(next_step) for next_step in json_in['next'] if next_step]
        return AppStep(name=json_in['name'],
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
                       raw_json=json_in)
