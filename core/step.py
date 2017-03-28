import json
import sys
from xml.etree import cElementTree

from jinja2 import Template, Markup

from core import arguments
from core import contextDecorator
from core import nextstep, config
from core.case import callbacks
from core.executionelement import ExecutionElement
from core.helpers import load_function_aliases, load_app_function
from core.nextstep import NextStep


class InvalidStepArgumentsError(Exception):
    def __init__(self, message=''):
        super(InvalidStepArgumentsError, self).__init__(message)


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
                 ancestry=None,
                 function_aliases=None):
        ExecutionElement.__init__(self, name=name, parent_name=parent_name, ancestry=ancestry)
        self.raw_xml = xml

        if xml is not None:
            self._from_xml(xml, parent_name=parent_name, ancestry=ancestry)
        else:
            self.action = action
            self.app = app
            self.device = device
            self.input = inputs if inputs is not None else {}
            self.conditionals = next_steps if next_steps is not None else []
            self.errors = errors if errors is not None else []
            self.raw_xml = self.to_xml()
        self.function_aliases = function_aliases if function_aliases is not None else load_function_aliases(self.app)
        self.output = None
        self.next_up = None
        super(Step, self)._register_event_callbacks(
            {'FunctionExecutionSuccess': callbacks.add_step_entry('Function executed successfully'),
             'InputValidated': callbacks.add_step_entry('Input successfully validated'),
             'ConditionalsExecuted': callbacks.add_step_entry('Conditionals executed')})

    def _from_xml(self, step_xml, parent_name='', ancestry=None):
        name = step_xml.get('id')
        ExecutionElement.__init__(self, name=name, parent_name=parent_name, ancestry=ancestry)
        self.action = step_xml.find('action').text
        self.app = step_xml.find('app').text
        self.device = step_xml.find('device').text
        self.input = {arg.tag: arguments.Argument(key=arg.tag, value=arg.text, format=arg.get('format'))
                      for arg in step_xml.findall('input/*')}
        self.conditionals = [nextstep.NextStep(xml=next_step_element, parent_name=self.name, ancestry=self.ancestry)
                             for next_step_element in step_xml.findall('next')]
        self.errors = [nextstep.NextStep(xml=error_step_element, parent_name=self.name, ancestry=self.ancestry)
                       for error_step_element in step_xml.findall('error')]

    def _update_xml(self, step_xml):
        self.action = step_xml.find('action').text
        self.app = step_xml.find('app').text
        self.device = step_xml.find('device').text
        self.input = {arg.tag: arguments.Argument(key=arg.tag, value=arg.text, format=arg.get('format'))
                      for arg in step_xml.findall('input/*')}
        self.conditionals = [nextstep.NextStep(xml=next_step_element, parent_name=self.name, ancestry=self.ancestry)
                             for next_step_element in step_xml.findall('next')]
        self.errors = [nextstep.NextStep(xml=error_step_element, parent_name=self.name, ancestry=self.ancestry)
                       for error_step_element in step_xml.findall('error')]

    @contextDecorator.context
    def render_step(self, **kwargs):
        if sys.version_info[0] > 2:
            content = cElementTree.tostring(self.raw_xml, encoding='unicode', method='xml')
        else:
            content = cElementTree.tostring(self.raw_xml, method='xml')

        t = Template(Markup(content).unescape(), autoescape=True)
        xml = t.render(config.JINJA_GLOBALS, **kwargs)
        self._update_xml(step_xml=cElementTree.fromstring(str(xml)))

    def validate_input(self):
        return (all(self.input[arg].validate_function_args(self.app, self.action) for arg in self.input)
                if self.input else True)

    def __lookup_function(self):
        aliases = load_function_aliases(self.app)
        if aliases:
            for function, alias_list in aliases.items():
                if self.action == function or self.action in alias_list:
                    return function
        return self.action

    def execute(self, instance=None):
        if self.validate_input():
            self.event_handler.execute_event_code(self, 'InputValidated')
            result = load_app_function(instance, self.__lookup_function())(args=self.input)
            self.event_handler.execute_event_code(self,
                                                    'FunctionExecutionSuccess',
                                                    data=json.dumps({"result": result}))
            self.output = result
            return result
        raise InvalidStepArgumentsError()

    def get_next_step(self, error=False):
        next_steps = self.errors if error else self.conditionals

        for n in next_steps:
            next_step = n(output=self.output)
            if next_step:
                self.next_up = next_step
                self.event_handler.execute_event_code(self, 'ConditionalsExecuted')
                return next_step

    def set(self, attribute=None, value=None):
        setattr(self, attribute, value)

    def add_next_step(self, next_step_name='', flags=None):
        flags = flags if flags is not None else []
        new_conditional = NextStep(parent_name=self.name,
                                   name=next_step_name,
                                   flags=flags,
                                   ancestry=list(self.ancestry))
        if any(conditional == new_conditional for conditional in self.conditionals):
            return False
        self.conditionals.append(new_conditional)
        return True

    def remove_next_step(self, next_step_name=''):
        self.conditionals = [x for x in self.conditionals if x.name != next_step_name]
        return True

    def to_xml(self, *args):
        step = cElementTree.Element('step')
        step.set("id", self.name)

        element_id = cElementTree.SubElement(step, 'id')
        element_id.text = self.name

        app = cElementTree.SubElement(step, 'app')
        app.text = self.app

        action = cElementTree.SubElement(step, 'action')
        action.text = self.action

        device = cElementTree.SubElement(step, 'device')
        device.text = self.device

        inputs = cElementTree.SubElement(step, 'input')
        for i in self.input:
            inputs.append(self.input[i].to_xml())
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
                  'input': {key: self.input[key] for key in self.input},
                  'next': [next_step for next_step in self.conditionals],
                  'errors': [error for error in self.errors],
                  'nextUp': self.next_up}
        if self.output:
            output["output"] = self.output
        return str(output)

    def as_json(self):
        output = {"name": str(self.name),
                  "action": str(self.action),
                  "app": str(self.app),
                  "device": str(self.device),
                  "input": {str(key): self.input[key].as_json() for key in self.input},
                  "next": [next_step.as_json() for next_step in self.conditionals if next_step.name is not None],
                  "errors": [error.as_json() for error in self.errors if error.name is not None]}
        if self.output:
            output["output"] = str(self.output)
        return output

    @staticmethod
    def from_json(json_in, parent_name='', ancestry=None):
        step = Step(name=json_in['name'],
                    action=json_in['action'],
                    app=json_in['app'],
                    device=json_in['device'],
                    inputs={arg_name: arguments.Argument.from_json(arg_element)
                            for arg_name, arg_element in json_in['input'].items()},
                    parent_name=parent_name,
                    ancestry=ancestry)

        step.conditionals = [NextStep.from_json(next_step, parent_name=step.name, ancestry=step.ancestry)
                             for next_step in json_in['next']]
        step.errors = [NextStep.from_json(next_step, parent_name=step.name, ancestry=step.ancestry)
                       for next_step in json_in['errors']]
        return step
