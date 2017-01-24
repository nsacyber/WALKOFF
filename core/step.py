import xml.etree.cElementTree as et
from blinker import Signal
from copy import deepcopy, copy

from core.ffk import Next
from core import case

class Step(object):
    def __init__(self, id="", action="", app="", device="", input={}, next=[], errors=[], parent=""):
        self.id = id
        self.action = action
        self.app = app
        self.device = device
        self.input = input
        self.conditionals = next
        self.errors = errors
        self.parent = parent
        self.output = None
        self.nextUp = None

        #Signals
        self.functionExecutedSuccessfully = Signal()
        self.functionExecutedSuccessfully.connect(case.functionExecutedSuccessfully)

        self.inputValidated = Signal()
        self.inputValidated.connect(case.inputValidated)

        self.conditionalsExecuted = Signal()
        self.conditionalsExecuted.connect(case.conditionalsExecuted)

    def __deepcopy__(self, memo={}):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k in ["functionExecutedSuccessfully", "inputValidated", "conditionalsExecuted"]:
                setattr(result, k, copy(getattr(self, k)))
            else:
                setattr(result, k, deepcopy(getattr(self, k)))
        return result

    def validateInput(self):
        if len(self.input) > 0:
            for arg in self.input:
                if not self.input[arg].validate(action=self.action, io="input"):
                    return False
        return True

    def execute(self, instance=None):
        if self.validateInput():
            self.inputValidated.send(self)
            result = getattr(instance, self.action)(args=self.input)
            self.functionExecutedSuccessfully.send(self)
            self.output = result
            return result
        raise Exception

    def nextStep(self, error=False):
        if error:
            nextSteps = self.errors
        else:
            nextSteps = self.conditionals

        for n in nextSteps:
            nextStep = n(output=self.output)
            if nextStep:
                self.nextUp = nextStep
                self.conditionalsExecuted.send(self)
                return nextStep

    def set(self, attribute=None, value=None):
        setattr(self, attribute, value)

    def createNext(self, nextStep="", flags=[]):
        newConditional = Next(nextStep=nextStep, flags=flags)
        for conditional in self.conditionals:
            if conditional.__eq__(newConditional):
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
        output = {}
        output["id"] = self.id
        output["action"] = self.action
        output["app"] = self.app
        output["device"] = self.device
        output["input"] = {key:self.input[key] for key in self.input}
        output["next"] = [next for next in self.conditionals]
        output["errors"] = [error for error in self.errors]
        output["nextUp"] = self.nextUp
        if self.output:
            output["output"] = self.output
        return str(output)


