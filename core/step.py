import json
import sys
from xml.etree import cElementTree
from collections import namedtuple
import logging
from jinja2 import Template, Markup
from core import contextdecorator
from core import nextstep
import core.config.config
from core.case import callbacks
from core.executionelement import ExecutionElement
from core.helpers import load_app_function, get_api_params, InvalidStepInput
from core.nextstep import NextStep
from core.widgetsignals import get_widget_signal
from apps import get_app_action

import traceback
logger = logging.getLogger(__name__)


class InvalidStepActionError(Exception):
    def __init__(self, app, action):
        super(InvalidStepActionError, self).__init__()
        self.message = 'Error: Step action {0} not found for app {1}'.format(action, app)

_Widget = namedtuple('Widget', ['app', 'widget'])


class Step(ExecutionElement):
    def __init__(self,
                 xml=None,
                 name='',
                 action='',
                 app='',
                 device='',
                 inputs=None,
                 next_steps=None,
                 errors=None,
                 parent_name='',
                 position=None,
                 ancestry=None,
                 widgets=None,
                 risk=0):
        """Initializes a new Step object. A Workflow has many steps that it executes.
        
        Args:
            xml (cElementTree, optional): The XML element tree object. Defaults to None.
            name (str, optional): The name of the Step object. Defaults to an empty string.
            action (str, optional): The name of the action associated with a Step. Defaults to an empty string.
            app (str, optional): The name of the app associated with the Step. Defaults to an empty string.
            device (str, optional): The name of the device associated with the app associated with the Step. Defaults
                to an empty string.
            inputs (dict, optional): A dictionary of Argument objects that are input to the step execution. Defaults
                to None.
            next_steps (list[NextStep], optional): A list of NextStep objects for the Step object. Defaults to None.
            errors (list[NextStep], optional): A list of NextStep error objects for the Step object. Defaults to None.
            parent_name (str, optional): The name of the parent for ancestry purposes. Defaults to an empty string.
            position (dict, optional): A dictionary with the x and y coordinates of the Step object. This is used
                for UI display purposes. Defaults to None.
            ancestry (list[str], optional): The ancestry for the Step object. Defaults to None.
            widgets (list[tuple(str, str)], optional): A list of widget tuples, which holds the app and the 
                corresponding widget. Defaults to None.
            risk (int, optional): The risk associated with the Step. Defaults to 0.
        """
        ExecutionElement.__init__(self, name=name, parent_name=parent_name, ancestry=ancestry)
        self.raw_xml = xml

        if xml is not None:
            self._from_xml(xml, parent_name=parent_name, ancestry=ancestry)
        else:
            self.action = action
            self.app = app
            get_app_action(self.app, self.action)
            self.input = inputs if inputs is not None else {}

            self.device = device
            self.risk = risk
            self.input = inputs if inputs is not None else {}
            self.conditionals = next_steps if next_steps is not None else []
            self.errors = errors if errors is not None else []
            self.position = position if position is not None else {}
            self.widgets = [_Widget(widget_app, widget_name)
                            for (widget_app, widget_name) in widgets] if widgets is not None else []
            self.raw_xml = self.to_xml()
        self.output = None
        self.next_up = None

    def reconstruct_ancestry(self, parent_ancestry):
        """Reconstructs the ancestry for a Step object. This is needed in case a workflow and/or playbook is renamed.
        
        Args:
            parent_ancestry(list[str]): The parent ancestry list.
        """
        self._construct_ancestry(parent_ancestry)
        for next_step in self.conditionals:
            next_step.reconstruct_ancestry(self.ancestry)
        for next_step in self.errors:
            next_step.reconstruct_ancestry(self.ancestry)

    def _from_xml(self, step_xml, parent_name='', ancestry=None):
        name = step_xml.get('id')
        ExecutionElement.__init__(self, name=name, parent_name=parent_name, ancestry=ancestry)

        self.action = step_xml.find('action').text
        self.app = step_xml.find('app').text
        get_app_action(self.app, self.action)
        device_field = step_xml.find('device')
        self.device = device_field.text if device_field is not None else ''
        risk_field = step_xml.find('risk')
        self.risk = int(risk_field.text) if risk_field is not None else 0

        self.input = {arg.get("name"): arg.text for arg in step_xml.findall('inputs/input')}
        self.conditionals = [nextstep.NextStep(xml=next_step_element, parent_name=self.name, ancestry=self.ancestry)
                             for next_step_element in step_xml.findall('next')]
        self.errors = [nextstep.NextStep(xml=error_step_element, parent_name=self.name, ancestry=self.ancestry)
                       for error_step_element in step_xml.findall('error')]
        self.widgets = [_Widget(widget.get('app'), widget.text) for widget in step_xml.findall('widgets/*')]
        position = step_xml.find('position')
        if position is None:
            self.position = {}
        else:
            x_position = position.find('x')
            y_position = position.find('y')
            if x_position is not None and y_position is not None:
                self.position = {'x': x_position.text, 'y': y_position.text}
            else:
                self.position = {}

    def _update_xml(self, step_xml):
        self.action = step_xml.find('action').text
        self.app = step_xml.find('app').text
        device_field = step_xml.find('device')
        self.device = device_field.text if device_field is not None else ''
        risk_field = step_xml.find('risk')
        self.risk = int(risk_field.text) if risk_field is not None else 0
        self.input = {arg.get("name"): arg.text for arg in step_xml.findall('inputs/input')}
        self.conditionals = [nextstep.NextStep(xml=next_step_element, parent_name=self.name, ancestry=self.ancestry)
                             for next_step_element in step_xml.findall('next')]
        self.errors = [nextstep.NextStep(xml=error_step_element, parent_name=self.name, ancestry=self.ancestry)
                       for error_step_element in step_xml.findall('error')]

    @contextdecorator.context
    def render_step(self, **kwargs):
        """Uses JINJA templating to render a Step object. 
        
        Args:
            kwargs (list[str]): Arguments to use in the JINJA templating.
        """
        if sys.version_info[0] > 2:
            content = cElementTree.tostring(self.raw_xml, encoding='unicode', method='xml')
        else:
            content = cElementTree.tostring(self.raw_xml, method='xml')
        t = Template(Markup(content).unescape(), autoescape=True)
        xml = t.render(core.config.config.JINJA_GLOBALS, **kwargs)
        self._update_xml(step_xml=cElementTree.fromstring(str(xml)))

    # def validate_input(self):
    #     """Ensures that the inputs passed in are properly formed.
    #
    #     Returns:
    #          True if inputs are valid, False otherwise.
    #     """
    #     if (self.app in core.config.config.function_info['apps']
    #             and self.action in core.config.config.function_info['apps'][self.app]):
    #         possible_args = core.config.config.function_info['apps'][self.app][self.action]['args']
    #         if possible_args:
    #             return (len(list(possible_args)) == len(list(self.input.keys()))
    #                     and all(self.input[arg].validate(possible_args) for arg in self.input))
    #         else:
    #             return True
    #     logger.warning('app {0} or app action {1} not found in app action metadata'.format(self.app, self.action))
    #     return False


    def validate_input(self, instance=None):
        try:

            args = {}
            for input in self.input:
                args[input] = formatarg(self.input[input])
            return True
        except (ValueError, InvalidStepActionError) as e:
            print(traceback.print_exception(*sys.exc_info()))
            return False

    def __lookup_function(self):
        for action, info in core.config.config.function_info['apps'][self.app].items():
            if action == self.action:
                return self.action
            else:
                if 'aliases' in info and self.action in info['aliases']:
                    return action
        raise InvalidStepActionError(self.app, self.action)

    def execute(self, instance=None):
        """Executes a Step by calling the associated app function.
        
        Args:
            instance (App): The instance of an App object to be used to execute the associated function.
            
        Returns:
            The result of the executed function.
        """

        try:
            fn = self.__lookup_function()
            args = {}
            fn = load_app_function(instance, fn)
            for input in self.input:
                args[input] = formatarg(self.input[input])
        except (ValueError, InvalidStepActionError):
            raise InvalidStepInput(self.app, self.action)
        try:
            response = fn(api=instance.api, action=self.action, args=args)
            result = response.body
            if response.status_code == 400:
                callbacks.StepInputInvalid.send(self)
            if response.status_code == 200:
                callbacks.StepInputValidated.send(self)
                callbacks.FunctionExecutionSuccess.send(self, data=json.dumps({"result": result}))
        except InvalidStepInput:
            raise InvalidStepInput(self.app, self.action)
        except Exception as e:
            import traceback, sys
            print(traceback.print_exc(sys.exc_info()))

        for widget in self.widgets:
            get_widget_signal(widget.app, widget.widget).send(self, data=json.dumps({"result": result}))
        self.output = result
        logger.debug('Step {0} executed successfully'.format(self.ancestry))
        return result


    def get_next_step(self, error=False):
        """Gets the NextStep object to be executed after the current Step.
        
        Args:
            error (bool, optional): Boolean to determine whether or not to use the errors field or the conditionals
                field to find the NextStep object.
                 
        Returns:
            The NextStep object to be executed.
        """
        next_steps = self.errors if error else self.conditionals
        for n in next_steps:
            next_step = n(output=self.output)
            if next_step:
                self.next_up = next_step
                callbacks.ConditionalsExecuted.send(self)
                return next_step

    def to_xml(self, *args):
        """Converts the Step object to XML format.
        
        Returns:
            The XML representation of the Step object.
        """
        step = cElementTree.Element('step')
        step.set("id", self.name)

        element_id = cElementTree.SubElement(step, 'id')
        element_id.text = self.name

        app = cElementTree.SubElement(step, 'app')
        app.text = self.app

        action = cElementTree.SubElement(step, 'action')
        action.text = self.action

        if self.risk:
            risk = cElementTree.SubElement(step, 'risk')
            risk.text = str(self.risk)

        if self.device is not None:
            device = cElementTree.SubElement(step, 'device')
            device.text = self.device

        if self.position and 'x' in self.position and 'y' in self.position:
            position = cElementTree.SubElement(step, 'position')
            x_position = cElementTree.SubElement(position, 'x')
            x_position.text = str(self.position['x'])
            y_position = cElementTree.SubElement(position, 'y')
            y_position.text = str(self.position['y'])

        #TODO: Need to get inputs to xml. only need <name>value</name>
        inputs = cElementTree.SubElement(step, 'inputs')
        for input_name, input_value in self.input.items():
            input_elem = cElementTree.Element('input')
            input_elem.text = str(input_value)
            input_elem.set('name', input_name)
            inputs.append(input_elem)

        if self.widgets:
            widgets = cElementTree.SubElement(step, 'widgets')
            for widget in self.widgets:
                widget_xml = cElementTree.SubElement(widgets, 'widget')
                widget_xml.text = widget.widget
                widget_xml.set('app', widget.app)

        for next_step in self.conditionals:
            next_xml = next_step.to_xml()
            if next_xml is not None:
                step.append(next_step.to_xml())

        for error in self.errors:
            error_xml = error.to_xml()
            if error_xml is not None:
                step.append(error.to_xml(tag='error'))

        return step

    def __repr__(self):
        output = {'name': self.name,
                  'action': self.action,
                  'app': self.app,
                  'device': self.device,
                  'risk': str(self.risk),
                  'input': {key: self.input[key] for key in self.input},
                  'next': [next_step for next_step in self.conditionals],
                  'errors': [error for error in self.errors],
                  'nextUp': self.next_up,
                  'position': self.position,
                  'widget': str([{'app': widget.app, 'name': widget.widget} for widget in self.widgets])}
        if self.output:
            output["output"] = self.output
        return str(output)

    def as_json(self, with_children=True):
        """Gets the JSON representation of a Step object.
        
        Args:
            with_children (bool, optional): A boolean to determine whether or not the children elements of the Step
                object should be included in the output.
                
        Returns:
            The JSON representation of a Step object.
        """
        output = {"name": str(self.name),
                  "action": str(self.action),
                  "app": str(self.app),
                  "device": str(self.device),
                  "risk": str(self.risk),
                  "input": self.input,
                  'widgets': [{'app': widget.app, 'name': widget.widget} for widget in self.widgets],
                  "position": {pos: str(val) for pos, val in self.position.items()}}
        if self.output:
            output["output"] = str(self.output)
        if with_children:
            output["next"] = [next_step.as_json() for next_step in self.conditionals if next_step.name is not None]
            output["errors"] = [error.as_json() for error in self.errors if error.name is not None]
        else:
            output["next"] = [next_step.name for next_step in self.conditionals if next_step.name is not None]
            output["errors"] = [error.name for error in self.errors if error.name is not None]
        return output

    @staticmethod
    def from_json(json_in, position, parent_name='', ancestry=None):
        """Forms a Step object from the provided JSON object.
        
        Args:
            json (JSON object): The JSON object to convert from.
            parent_name (str, optional): The name of the parent for ancestry purposes. Defaults to an empty string.
            ancestry (list[str], optional): The ancestry for the new Step object. Defaults to None.
            
        Returns:
            The Step object parsed from the JSON object.
        """
        device = json_in['device'] if ('device' in json_in
                                       and json_in['device'] is not None
                                       and json_in['device'] != 'None') else ''
        risk = json_in['risk'] if 'risk' in json_in else 0
        widgets = []
        if 'widgets' in json_in:
            widgets = [(widget['app'], widget['name'])
                       for widget in json_in['widgets'] if ('app' in widget and 'name' in widget)]
        step = Step(name=json_in['name'],
                    action=json_in['action'],
                    app=json_in['app'],
                    device=device,
                    risk=risk,
                    inputs={arg_name: {"key": arg_name, "value": arg_element}
                            for arg_name, arg_element in json_in['input'].items()},
                    parent_name=parent_name,
                    position=position,
                    widgets=widgets,
                    ancestry=ancestry)
        if json_in['next']:
            step.conditionals = [NextStep.from_json(next_step, parent_name=step.name, ancestry=step.ancestry)
                                 for next_step in json_in['next'] if next_step]
        if json_in['errors']:
            step.errors = [NextStep.from_json(next_step, parent_name=step.name, ancestry=step.ancestry)
                           for next_step in json_in['errors'] if next_step]
        return step

    def get_children(self, ancestry):
        """Gets the children NextSteps of the Step in JSON format.
        
        Args:
            ancestry (list[str]): The ancestry list for the NextStep to be returned.
            
        Returns:
            The NextStep in the ancestry (if provided) as a JSON, otherwise None.
        """
        if not ancestry:
            return self.as_json(with_children=False)
        else:
            next_child = ancestry.pop()
            if next_child in [conditional.name for conditional in self.conditionals]:
                next_step_index = [conditional.name for conditional in self.conditionals].index(next_child)
                return self.conditionals[next_step_index].get_children(ancestry)
            elif next_child in [error_step.name for error_step in self.errors]:
                next_step_index = [error_step.name for error_step in self.errors].index(next_child)
                return self.errors[next_step_index].get_children(ancestry)
            else:
                return None
