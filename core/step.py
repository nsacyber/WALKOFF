import json
import sys
from xml.etree import ElementTree
from collections import namedtuple
import logging
from jinja2 import Template, Markup
from core import contextdecorator
from core import nextstep
import core.config.config
from core.case import callbacks
from core.decorators import ActionResult
from core.executionelement import ExecutionElement
from core.helpers import (get_app_action_api, InvalidElementConstructed, inputs_xml_to_dict, inputs_to_xml,
                          InvalidInput, dereference_step_routing, format_exception_message)
from core.nextstep import NextStep
from core.widgetsignals import get_widget_signal
from apps import get_app_action
from core.validator import validate_app_action_parameters
import uuid
logger = logging.getLogger(__name__)

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
                 parent_name='',
                 position=None,
                 ancestry=None,
                 widgets=None,
                 risk=0,
                 uid=None):
        """Initializes a new Step object. A Workflow has many steps that it executes.
        
        Args:
            xml (ElementTree, optional): The XML element tree object. Defaults to None.
            name (str, optional): The name of the Step object. Defaults to an empty string.
            action (str, optional): The name of the action associated with a Step. Defaults to an empty string.
            app (str, optional): The name of the app associated with the Step. Defaults to an empty string.
            device (str, optional): The name of the device associated with the app associated with the Step. Defaults
                to an empty string.
            inputs (dict, optional): A dictionary of Argument objects that are input to the step execution. Defaults
                to None.
            next_steps (list[NextStep], optional): A list of NextStep objects for the Step object. Defaults to None.
            parent_name (str, optional): The name of the parent for ancestry purposes. Defaults to an empty string.
            position (dict, optional): A dictionary with the x and y coordinates of the Step object. This is used
                for UI display purposes. Defaults to None.
            ancestry (list[str], optional): The ancestry for the Step object. Defaults to None.
            widgets (list[tuple(str, str)], optional): A list of widget tuples, which holds the app and the 
                corresponding widget. Defaults to None.
            risk (int, optional): The risk associated with the Step. Defaults to 0.
            uid (str, optional): A universally unique identifier for this object. Created from uuid.uuid4().hex in Python
        """
        ExecutionElement.__init__(self, name=name, parent_name=parent_name, ancestry=ancestry)
        if xml is not None:
            self._from_xml(xml, parent_name=parent_name, ancestry=ancestry)
            self.uid = uuid.uuid4().hex
        else:
            if action == '' or app == '':
                raise InvalidElementConstructed('Either both action and app or xml must be '
                                                'specified in step constructor')
            self.action = action
            self.app = app
            self.run, self.input_api = get_app_action_api(self.app, self.action)
            get_app_action(self.app, self.run)
            inputs = inputs if inputs is not None else {}
            self.input = validate_app_action_parameters(self.input_api, inputs, self.app, self.action)
            self.device = device
            self.risk = risk
            self.conditionals = next_steps if next_steps is not None else []
            self.position = position if position is not None else {}
            self.widgets = [_Widget(widget_app, widget_name)
                            for (widget_app, widget_name) in widgets] if widgets is not None else []
            self.raw_xml = self.to_xml()
            self.templated = False
            self.uid = uuid.uuid4().hex if uid is None else uid
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

    def _from_xml(self, step_xml, parent_name='', ancestry=None):
        self.raw_xml = step_xml
        name = step_xml.get('id')
        ExecutionElement.__init__(self, name=name, parent_name=parent_name, ancestry=ancestry)

        self.action = step_xml.find('action').text
        self.app = step_xml.find('app').text
        self.run, self.input_api = get_app_action_api(self.app, self.action)
        is_templated_xml = step_xml.find('templated')
        self.templated = is_templated_xml is not None and bool(is_templated_xml.text)
        get_app_action(self.app, self.run)
        input_xml = step_xml.find('inputs')
        if input_xml is not None:
            inputs = inputs_xml_to_dict(input_xml) or {}
            if not self.templated:
                self.input = validate_app_action_parameters(self.input_api, inputs, self.app, self.action)
            else:
                self.input = inputs
        else:
            self.input = validate_app_action_parameters(self.input_api, {}, self.app, self.action)
        device_field = step_xml.find('device')
        self.device = device_field.text if device_field is not None else ''
        risk_field = step_xml.find('risk')
        self.risk = risk_field.text if risk_field is not None else 0
        self.conditionals = [nextstep.NextStep(xml=next_step_element, parent_name=self.name, ancestry=self.ancestry)
                             for next_step_element in step_xml.findall('next')]
        self.widgets = [_Widget(widget.get('app'), widget.text) for widget in step_xml.findall('widgets/*')]
        position = step_xml.find('position')
        if position is None:
            self.position = {}
        else:
            x_position = position.find('x')
            y_position = position.find('y')
            if x_position is not None and y_position is not None:
                self.position = {'x': float(x_position.text), 'y': float(y_position.text)}
            else:
                self.position = {}

    def _update_xml(self, step_xml):
        self.action = step_xml.find('action').text
        self.app = step_xml.find('app').text
        device_field = step_xml.find('device')
        self.device = device_field.text if device_field is not None else ''
        risk_field = step_xml.find('risk')
        self.risk = risk_field.text if risk_field is not None else 0
        input_xml = step_xml.find('inputs')
        if input_xml is not None:
            inputs = inputs_xml_to_dict(input_xml) or {}
            if not self.templated:
                self.input = validate_app_action_parameters(self.input_api, inputs, self.app, self.action)
            else:
                self.input = inputs
        else:
            self.input = validate_app_action_parameters(self.input_api, {}, self.app, self.action)
        self.conditionals = [nextstep.NextStep(xml=next_step_element, parent_name=self.name, ancestry=self.ancestry)
                             for next_step_element in step_xml.findall('next')]

    @contextdecorator.context
    def render_step(self, **kwargs):
        """Uses JINJA templating to render a Step object. 
        
        Args:
            kwargs (dict[str]): Arguments to use in the JINJA templating.
        """
        if self.templated:
            if sys.version_info[0] > 2:
                content = ElementTree.tostring(self.raw_xml, encoding='unicode', method='xml')
            else:
                content = ElementTree.tostring(self.raw_xml, method='xml')
            t = Template(Markup(content).unescape(), autoescape=True)
            xml = t.render(core.config.config.JINJA_GLOBALS, **kwargs)
            self._update_xml(step_xml=ElementTree.fromstring(xml))

    def set_input(self, new_input):
        self.input = validate_app_action_parameters(self.input_api, new_input, self.app, self.action)

    def execute(self, instance, accumulator):
        """Executes a Step by calling the associated app function.
        
        Args:
            instance (App): The instance of an App object to be used to execute the associated function.
            accumulator (dict): Dict containing the results of the previous steps
            
        Returns:
            The result of the executed function.
        """
        callbacks.StepInputValidated.send(self)
        try:
            args = dereference_step_routing(self.input, accumulator, 'In step {0}'.format(self.name))
            args = validate_app_action_parameters(self.input_api, args, self.app, self.action)
            action = get_app_action(self.app, self.run)
            result = action(instance, **args)
            callbacks.FunctionExecutionSuccess.send(self, data=json.dumps({"result": result.as_json()}))
        except InvalidInput as e:
            formatted_error = format_exception_message(e)
            logger.error('Error calling step {0}. Error: {1}'.format(self.name, formatted_error))
            callbacks.StepInputInvalid.send(self)
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
            logger.debug('Step {0} executed successfully'.format(self.ancestry))
            return result

    def get_next_step(self, accumulator):
        """Gets the NextStep object to be executed after the current Step.
        
        Args:
            accumulator (dict): A record of teh previously-executed steps. Of form {step_name: result}
                 
        Returns:
            The NextStep object to be executed.
        """
        for next_step in self.conditionals:
            next_step = next_step(self.output, accumulator)
            if next_step is not None:
                self.next_up = next_step
                callbacks.ConditionalsExecuted.send(self)
                return next_step

    def to_xml(self, *args):
        """Converts the Step object to XML format.
        
        Returns:
            The XML representation of the Step object.
        """
        step = ElementTree.Element('step')
        step.set("id", self.name)

        element_id = ElementTree.SubElement(step, 'name')
        element_id.text = self.name

        app = ElementTree.SubElement(step, 'app')
        app.text = self.app

        action = ElementTree.SubElement(step, 'action')
        action.text = self.action

        if self.risk:
            risk = ElementTree.SubElement(step, 'risk')
            risk.text = self.risk

        if self.device:
            device = ElementTree.SubElement(step, 'device')
            device.text = self.device

        if self.position and 'x' in self.position and 'y' in self.position:
            position = ElementTree.SubElement(step, 'position')
            x_position = ElementTree.SubElement(position, 'x')
            x_position.text = str(self.position['x'])
            y_position = ElementTree.SubElement(position, 'y')
            y_position.text = str(self.position['y'])

        if self.input:
            args = inputs_to_xml(self.input)
            step.append(args)

        if self.widgets:
            widgets = ElementTree.SubElement(step, 'widgets')
            for widget in self.widgets:
                widget_xml = ElementTree.SubElement(widgets, 'widget')
                widget_xml.text = widget.widget
                widget_xml.set('app', widget.app)

        for next_step in self.conditionals:
            next_xml = next_step.to_xml()
            if next_xml is not None:
                step.append(next_step.to_xml())

        return step

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

    def as_json(self, with_children=True):
        """Gets the JSON representation of a Step object.
        
        Args:
            with_children (bool, optional): A boolean to determine whether or not the children elements of the Step
                object should be included in the output.
                
        Returns:
            The JSON representation of a Step object.
        """
        output = {"uid": self.uid,
                  "name": str(self.name),
                  "action": str(self.action),
                  "app": str(self.app),
                  "device": str(self.device),
                  "risk": self.risk,
                  "inputs": [{'name': arg_name, 'value': arg_value} for arg_name, arg_value in self.input.items()],
                  'widgets': [{'app': widget.app, 'name': widget.widget} for widget in self.widgets],
                  "position": self.position}
        if self.output:
            output["output"] = self.output.as_json()
        if with_children:
            output["next"] = [next_step.as_json() for next_step in self.conditionals if next_step.name is not None]
        else:
            output["next"] = [next_step.name for next_step in self.conditionals if next_step.name is not None]
        return output

    @staticmethod
    def from_json(json_in, position, parent_name='', ancestry=None):
        """Forms a Step object from the provided JSON object.
        
        Args:
            json_in (dict): The JSON object to convert from.
            position (dict): position of the step node of the form {'x': <x position>, 'y': <y position>}
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
        uid = json_in['uid'] if 'uid' in json_in else uuid.uuid4().hex
        if 'widgets' in json_in:
            widgets = [(widget['app'], widget['name'])
                       for widget in json_in['widgets'] if ('app' in widget and 'name' in widget)]
        step = Step(name=json_in['name'],
                    action=json_in['action'],
                    app=json_in['app'],
                    device=device,
                    risk=risk,
                    inputs={arg['name']: arg['value'] for arg in json_in['inputs']},
                    parent_name=parent_name,
                    position={key: value for key, value in position.items()},
                    widgets=widgets,
                    ancestry=ancestry,
                    uid=uid)
        if json_in['next']:
            step.conditionals = [NextStep.from_json(next_step, parent_name=step.name, ancestry=step.ancestry)
                                 for next_step in json_in['next'] if next_step]
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
            else:
                return None
