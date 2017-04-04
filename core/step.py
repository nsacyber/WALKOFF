import json
import sys
from xml.etree import cElementTree

from jinja2 import Template, Markup

from core import arguments
from core import contextDecorator
from core import nextstep
import core.config.config
from core.case import callbacks
from core.executionelement import ExecutionElement
from core.helpers import load_app_function
from core.nextstep import NextStep


class InvalidStepInputError(Exception):
    def __init__(self, app, action):
        super(InvalidStepInputError, self).__init__()
        self.message = 'Error: Invalid inputs for action {0} for app {1}'.format(action, app)


class InvalidStepActionError(Exception):
    def __init__(self, app, action):
        super(InvalidStepActionError, self).__init__()
        self.message = 'Error: Step action {0} not found for app {1}'.format(action, app)


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
                 ancestry=None):
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
        self.output = None
        self.next_up = None

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
        xml = t.render(core.config.config.JINJA_GLOBALS, **kwargs)
        self._update_xml(step_xml=cElementTree.fromstring(str(xml)))

    def validate_input(self):
        if (self.app in core.config.config.function_info['apps']
                and self.action in core.config.config.function_info['apps'][self.app]):
            possible_args = core.config.config.function_info['apps'][self.app][self.action]['args']
            if possible_args:
                return (len(list(possible_args)) == len(list(self.input.keys()))
                        and all(self.input[arg].validate(possible_args) for arg in self.input))
            else:
                return True
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
        if self.validate_input():
            callbacks.StepInputValidated.send(self)
            result = load_app_function(instance, self.__lookup_function())(args=self.input)
            callbacks.FunctionExecutionSuccess.send(self, data=json.dumps({"result": result}))
            self.output = result
            return result
        raise InvalidStepInputError(self.app, self.action)

    def get_next_step(self, error=False):
        next_steps = self.errors if error else self.conditionals
        for n in next_steps:
            next_step = n(output=self.output)
            if next_step:
                self.next_up = next_step
                callbacks.ConditionalsExecuted.send(self)
                return next_step

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

    def as_json(self, with_children=True):
        output = {"name": str(self.name),
                  "action": str(self.action),
                  "app": str(self.app),
                  "device": str(self.device),
                  "input": {str(key): self.input[key].as_json() for key in self.input}}
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

    def get_children(self, ancestry):
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
