import xml.etree.cElementTree as et
from core.ffk import Next
from core import case, arguments
from core.executionelement import ExecutionElement
from core import ffk

class Step(ExecutionElement):
    def __init__(self, xml=None, name="", action="", app="", device="", input=None, next=None, errors=None, parent_name="",
                 ancestry=None):
        ExecutionElement.__init__(self, name=name, parent_name=parent_name, ancestry=ancestry)
        if xml is not None:
            self._from_xml(xml, parent_name=parent_name, ancestry=ancestry)
        else:
            self.action = action
            self.app = app
            self.device = device
            self.input = input if input is not None else {}
            self.conditionals = next if next is not None else []
            self.errors = errors if errors is not None else []
        self.output = None
        self.nextUp = None
        super(Step, self)._register_event_callbacks(
            {'FunctionExecutionSuccess': case.add_step_entry('Function executed successfully'),
             'InputValidated': case.add_step_entry('Input successfully validated'),
             'ConditionalsExecuted': case.add_step_entry('Conditionals executed')})

    def _from_xml(self, step_xml, parent_name='', ancestry=None):
        name = step_xml.get("id")
        ExecutionElement.__init__(self, name=name, parent_name=parent_name, ancestry=ancestry)
        self.action = step_xml.find("action").text
        self.app = step_xml.find("app").text
        self.device = step_xml.find("device").text
        self.input = {arg.tag: arguments.Argument(key=arg.tag, value=arg.text, format=arg.get("format"))
                      for arg in step_xml.findall("input/*")}
        self.conditionals = [ffk.Next(xml=next_step_element, parent_name=id, ancestry=self.ancestry)
                                  for next_step_element in step_xml.findall("next")]
        self.errors = [ffk.Next(xml=error_step_element, parent_name=id, ancestry=self.ancestry)
                            for error_step_element in step_xml.findall("error")]

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
        raise Exception

    def nextStep(self, error=False):
        nextSteps = self.errors if error else self.conditionals

        for n in nextSteps:
            nextStep = n(output=self.output)
            if nextStep:
                self.nextUp = nextStep
                self.event_handler.execute_event_code(self, 'ConditionalsExecuted')
                return nextStep

    def set(self, attribute=None, value=None):
        setattr(self, attribute, value)

    def createNext(self, nextStep="", flags=None):
        flags = flags if flags is not None else []
        newConditional = Next(parent_name=self.name, name=nextStep, flags=flags, ancestry=self.ancestry)
        if any(conditional == newConditional for conditional in self.conditionals):
            return False
        self.conditionals.append(newConditional)
        return True

    def removeNext(self, nextStep=""):
        self.conditionals = [x for x in self.conditionals if x.name != nextStep]
        return True



    def to_xml(self):
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


