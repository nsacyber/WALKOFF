import xml.etree.cElementTree as et

from core.ffk import Next

class Step():
    def __init__(self, id="", action="", app="", device="", input={}, next=[], errors=[]):
        self.id = id
        self.action = action
        self.app = app
        self.device = device
        self.input = input
        self.conditionals = next
        self.errors = errors
        self.output = None
        self.nextUp = None

    def validateInput(self):
        if len(self.input) > 0:
            for arg in self.input:
                if not self.input[arg].validate(action=self.action, io="input"):
                    return False
        return True

    def execute(self, instance=None):
        if self.validateInput():
            result = getattr(instance, self.action)(args=self.input)
            self.output = result
            return result

    def nextStep(self):
        for n in self.conditionals:
            nextStep = n(output=self.output)
            if nextStep:
                self.nextUp = nextStep
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
        return str(output)


