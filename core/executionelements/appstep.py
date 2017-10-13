import json
import logging
from core.decorators import ActionResult
from core.executionelements.step_2 import Step
from core.helpers import (get_app_action_api, InvalidInput,
                          dereference_step_routing, format_exception_message)
from core.executionelements.nextstep import NextStep
from core.widgetsignals import get_widget_signal
from apps import get_app_action
from core.validator import validate_app_action_parameters
from core.case.callbacks import data_sent
logger = logging.getLogger(__name__)


class Widget(object):
    def __init__(self, app, name):
        self.app = app
        self.name = name


class AppStep(Step):
    def __init__(self,
                 app,
                 action,
                 name='',
                 uid=None,
                 device='',
                 inputs=None,
                 next_steps=None,
                 position=None,
                 widgets=None,
                 risk=0,
                 templated=False,
                 raw_representation=None):
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
            raw_representation (dict, optional): JSON representation of this object. Used for Jinja templating
        """
        Step.__init__(self, name, uid, next_steps, position, risk, templated, raw_representation)
        self.device = device
        self.action = action
        self.app = app
        self._run, self._input_api = get_app_action_api(self.app, self.action)
        get_app_action(self.app, self._run)
        inputs = inputs if inputs is not None else {}
        if not self.templated:
            self.inputs = validate_app_action_parameters(self._input_api, inputs, self.app, self.action)
        else:
            self.inputs = inputs
        self.widgets = [widget if isinstance(widget, Widget) else Widget(**widget)
                        for widget in widgets] if widgets is not None else []

    def _update_json_from_template(self, updated_json):
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
        self.conditionals = [NextStep.create(cond_json) for cond_json in updated_json['next']]

    def set_input(self, new_input):
        """Updates the input for a Step Action object.

        Args:
            new_input (dict): The new inputs for the Step Action object.
        """
        self.inputs = validate_app_action_parameters(self._input_api, new_input, self.app, self.action)

    def execute(self, instance, accumulator):
        """Executes a Step by calling the associated app function.
        
        Args:
            instance (App): The instance of an App object to be used to execute the associated function.
            accumulator (dict): Dict containing the results of the previous steps
            
        Returns:
            The result of the executed function.
        """
        self.generate_execution_uid()
        data_sent.send(self, callback_name="Step Started", object_type="Step")
        try:
            args = dereference_step_routing(self.inputs, accumulator, 'In step {0}'.format(self.name))
            args = validate_app_action_parameters(self._input_api, args, self.app, self.action)
            action = get_app_action(self.app, self._run)
            result = action(instance, **args)
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
