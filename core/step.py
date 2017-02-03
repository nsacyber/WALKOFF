import xml.etree.cElementTree as et
from core.ffk import Next
from core import case
from core.events import EventHandler


class StepEventHandler(EventHandler):
    def __init__(self, shared_log=None):
        EventHandler.__init__(self, 'StepEventHandler', shared_log,
                              events={'FunctionExecutionSuccess': case.add_step_entry('Function executed successfully'),
                                      'InputValidated': case.add_step_entry('Input successfully validated'),
                                      'ConditionalsExecuted': case.add_step_entry('Conditionals executed')})


class Step(object):
    def __init__(self, id="", action="", app="", device="", input=None, next=None, errors=None, parent="",
                 ancestry=None, ):
        self.id = id
        self.action = action
        self.app = app
        self.device = device
        self.input = input if input is not None else {}
        self.conditionals = next if next is not None else []
        self.errors = errors if errors is not None else []
        self.parent_workflow = parent
        self.output = None
        self.nextUp = None
        self.eventlog = []
        self.stepEventHandler = StepEventHandler(self.eventlog)
        self.ancestry = list(ancestry) if ancestry is not None else []
        self.ancestry.append(self.id)

    def validateInput(self):
        return (all(self.input[arg].validate(action=self.action, io="input") for arg in self.input) if self.input
                else True)

    def execute(self, instance=None):
        if self.validateInput():
            self.stepEventHandler.execute_event_code(self, 'InputValidated')
            result = getattr(instance, self.action)(args=self.input)
            self.stepEventHandler.execute_event_code(self, 'FunctionExecutionSuccess')
            self.output = result
            return result
        raise Exception

    def nextStep(self, error=False):
        nextSteps = self.errors if error else self.conditionals

        for n in nextSteps:
            nextStep = n(output=self.output)
            if nextStep:
                self.nextUp = nextStep
                self.stepEventHandler.execute_event_code(self, 'ConditionalsExecuted')
                return nextStep

    def set(self, attribute=None, value=None):
        setattr(self, attribute, value)

    def createNext(self, nextStep="", flags=None):
        flags = flags if flags is not None else []
        newConditional = Next(self.id, nextStep=nextStep, flags=flags, ancestry=self.ancestry)
        if any(conditional == newConditional for conditional in self.conditionals):
            return False
        self.conditionals.append(newConditional)
        return True

    def removeNext(self, nextStep=""):
        self.conditionals = [x for x in self.conditionals if x.nextStep != nextStep]
        return True



    def toXML(self):
        step = et.Element("step")
        step.set("id", self.id)

        id = et.SubElement(step, "id")
        id.text = self.id

        app = et.SubElement(step, "app")
        app.text = self.app

        action = et.SubElement(step, "action")
        action.text = self.action

        device = et.SubElement(step, "device")
        device.text = self.device

        input = et.SubElement(step, "input")
        for i in self.input:
            input.append(self.input[i].toXML())

        for next in self.conditionals:
            step.append(next.toXML())

        for error in self.errors:
            step.append(error.toXML(tag="error"))

        return step

    def __repr__(self):
        output = {'id': self.id,
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


