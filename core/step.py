import xml.etree.cElementTree as et

class Step():
    def __init__(self, id="", action="", app="", device="", input={}, next=[], errors=[]):
        self.id = id
        self.action = action
        self.app = app
        self.device = device
        self.input = input
        self.next = next
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
        for n in self.next:
            nextStep = n(output=self.output)
            if nextStep:
                self.nextUp = nextStep
                return nextStep

    def toXML(self):
        step = et.Element("step")

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

        for next in self.next:
            step.append(self.next[next].toXML())

        for error in self.errors:
            step.append(self.errors[error].toXML())

        return step


    def __repr__(self):
        output = {}
        output["id"] = self.id
        output["action"] = self.action
        output["app"] = self.app
        output["device"] = self.device
        output["input"] = self.input
        output["next"] = self.next
        output["errors"] = self.errors
        return str(output)


