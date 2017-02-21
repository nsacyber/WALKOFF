import xml.etree.cElementTree as et
from core.nextstep import Next
from core import arguments
from core.case import callbacks
from core.executionelement import ExecutionElement
from core import nextstep, config
from core import contextDecorator
from jinja2 import Template, Markup
import sys

class InvalidStepArgumentsError(Exception):
    def __init__(self, message=''):
        super(InvalidStepArgumentsError, self).__init__(message)

class Step(ExecutionElement):
    def __init__(self, xml=None, name="", action="", app="", device="", input=None, next=None, errors=None, parent_name="",
                 ancestry=None):
        ExecutionElement.__init__(self, name=name, parent_name=parent_name, ancestry=ancestry)
        self.rawXML = xml

        if xml is not None:
            self._from_xml(xml, parent_name=parent_name, ancestry=ancestry)
        else:
            self.action = action
            self.app = app
            self.device = device
            self.input = input if input is not None else {}
            self.conditionals = next if next is not None else []
            self.errors = errors if errors is not None else []
            self.rawXML = self.to_xml()

        self.output = None
        self.nextUp = None
        super(Step, self)._register_event_callbacks(
            {'FunctionExecutionSuccess': callbacks.add_step_entry('Function executed successfully'),
             'InputValidated': callbacks.add_step_entry('Input successfully validated'),
             'ConditionalsExecuted': callbacks.add_step_entry('Conditionals executed')})

    def _from_xml(self, step_xml, parent_name='', ancestry=None):
        name = step_xml.get("id")
        ExecutionElement.__init__(self, name=name, parent_name=parent_name, ancestry=ancestry)
        self.action = step_xml.find("action").text
        self.app = step_xml.find("app").text
        self.device = step_xml.find("device").text
        self.input = {arg.tag: arguments.Argument(key=arg.tag, value=arg.text, format=arg.get("format"))
                      for arg in step_xml.findall("input/*")}
        self.conditionals = [nextstep.Next(xml=next_step_element, parent_name=id, ancestry=self.ancestry)
                             for next_step_element in step_xml.findall("next")]
        self.errors = [nextstep.Next(xml=error_step_element, parent_name=id, ancestry=self.ancestry)
                       for error_step_element in step_xml.findall("error")]

    def _update_xml(self, step_xml):
        self.action = step_xml.find("action").text
        self.app = step_xml.find("app").text
        self.device = step_xml.find("device").text
        self.input = {arg.tag: arguments.Argument(key=arg.tag, value=arg.text, format=arg.get("format"))
                      for arg in step_xml.findall("input/*")}
        self.conditionals = [nextstep.Next(xml=next_step_element, parent_name=id, ancestry=self.ancestry)
                             for next_step_element in step_xml.findall("next")]
        self.errors = [nextstep.Next(xml=error_step_element, parent_name=id, ancestry=self.ancestry)
                       for error_step_element in step_xml.findall("error")]

    @contextDecorator.context
    def renderStep(self, **kwargs):
        if sys.version_info[0] > 2:
            content = et.tostring(self.rawXML, encoding="unicode", method="xml")
        else:
            content = et.tostring(self.rawXML,  method="xml")

        t = Template(Markup(content).unescape(), autoescape=True)
        xml = t.render(config.JINJA_GLOBALS, **kwargs)
        self._update_xml(step_xml=et.fromstring(str(xml)))

    def validateInput(self):
        return (all(self.input[arg].validate(action=self.action, io="input") for arg in self.input) if self.input
                else True)

    def execute(self, instance=None):
        if self.validateInput():
            self.event_handler.execute_event_code(self, 'InputValidated')
            result = getattr(instance, self.action)(args=self.input)
            self.event_handler.execute_event_code(self, 'FunctionExecutionSuccess')
            self.output = result
            return result
        raise InvalidStepArgumentsError()

    def nextStep(self, error=False):
        next_steps = self.errors if error else self.conditionals

        for n in next_steps:
            next_step = n(output=self.output)
            if next_step:
                self.nextUp = next_step
                self.event_handler.execute_event_code(self, 'ConditionalsExecuted')
                return next_step

    def set(self, attribute=None, value=None):
        setattr(self, attribute, value)

    def createNext(self, nextStep="", flags=None):
        flags = flags if flags is not None else []
        new_conditional = Next(parent_name=self.name, name=nextStep, flags=flags, ancestry=self.ancestry)
        if any(conditional == new_conditional for conditional in self.conditionals):
            return False
        self.conditionals.append(new_conditional)
        return True

    def removeNext(self, nextStep=""):
        self.conditionals = [x for x in self.conditionals if x.name != nextStep]
        return True

    def to_xml(self, *args):
        step = et.Element("step")
        step.set("id", self.name)

        id = et.SubElement(step, "id")
        id.text = self.name

        app = et.SubElement(step, "app")
        app.text = self.app

        action = et.SubElement(step, "action")
        action.text = self.action

        device = et.SubElement(step, "device")
        device.text = self.device

        input = et.SubElement(step, "input")
        for i in self.input:
            input.append(self.input[i].to_xml())

        for next in self.conditionals:
            step.append(next.to_xml())

        for error in self.errors:
            step.append(error.to_xml(tag="error"))

        return step

    def __repr__(self):
        output = {'name': self.name,
                  'action': self.action,
                  'app': self.app,
                  'device': self.device,
                  'input': {key: self.input[key] for key in self.input},
                  'next': [next for next in self.conditionals],
                  'errors': [error for error in self.errors],
                  'nextUp': self.nextUp}
        if self.output:
            output["output"] = self.output
        return str(output)

    def as_json(self):
        output = {"name": str(self.name),
                "action": str(self.name),
                "app": str(self.app),
                "device": str(self.device),
                "input": {str(key): str(self.input[key]) for key in self.input},
                "next": [next.as_json() for next in self.conditionals],
                "errors": [error.as_json() for error in self.errors]}
        if self.output:
            output["output"] = str(self.output)
        return output



