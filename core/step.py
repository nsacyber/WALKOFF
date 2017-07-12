import json
import sys
from xml.etree import ElementTree

import logging
from jinja2 import Template, Markup
from core import contextdecorator
import core.config.config
from core.case import callbacks
from core.decorators import ActionResult
from core.helpers import (InvalidInput, dereference_step_routing, format_exception_message)
from core.widgetsignals import get_widget_signal
from apps import get_app_action
from core.validator import validate_app_action_parameters
from core.data.step import StepData
from core.nextstep import NextStep
from collections import namedtuple
logger = logging.getLogger(__name__)

_Widget = namedtuple('Widget', ['app', 'widget'])

class Step(StepData):
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
                 risk=0):
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
        """
        StepData.__init__(self, xml, name, action, app, device, inputs, next_steps, parent_name, position, ancestry, widgets, risk)

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


    def __repr__(self):
        output = {'name': self.name,
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
            output["output"] = self.output
        return str(output)






