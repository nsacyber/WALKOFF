import sys
import importlib

from core import step as wfstep
from core import ffk
from core import arguments
from core import instance
from core import options

class Workflow(object):
    def __init__(self, name="", workflowConfig=None, children={}):
        self.name = name
        self.workflowXML = workflowConfig
        self.options = self.parseOptions(workflowConfig.find(".//options"))
        self.steps = self.parseSteps(workflowConfig.findall(".//steps/*"))
        self.children = {}

    def parseOptions(self, ops=None):
        # Parses out the options for each item if there are no subelements then pass the text instead
        #options = [{ch.tag: {item.tag: item.text for item in ch} or ch.text} for ch in options]
        scheduler = {"autorun": ops.find(".//scheduler").get("autorun"), "type":ops.find(".//scheduler").get("type"), "args":{option.tag:option.text for option in ops.findall(".//scheduler/*")}}
        enabled = ops.find(".//enabled").text
        children = {child.text:None for child in ops.findall(".//children/child")}

        result = options.Options(scheduler=scheduler, enabled=enabled, children=children)
        return result

    def assignChild(self, name="", workflow=None):
        self.children[name] = workflow

    def parseSteps(self, stepConfig=None):
        steps = {}
        # Parses out the step variables
        for step in stepConfig:
            id = step.get("id")
            action = step.find("action").text
            app = step.find("app").text
            device = step.find("device").text
            input = {arg.tag:arguments.Argument(key=arg.tag, value=arg.text, format=arg.get("format")) for arg in step.findall("input/*")}
            next = [self.parseNext(nextStep) for nextStep in step.findall("next")]
            errors = [self.parseNext(error) for error in step.findall("error")]
            steps[id] = wfstep.Step(id=id, action=action, app=app, device=device, input=input, next=next, errors=errors)
        return steps

    def parseNext(self, next=None):
        flags = [self.parseFlag(flag) for flag in next.findall("flag")]
        nextId = next.get("step")
        nextStep = ffk.Next(nextStep=nextId, flags=flags)
        return nextStep

    def parseFlag(self, flag=None):
        action = flag.get("action")
        filters = [self.parseFilter(filter) for filter in flag.findall("filters/*")]
        args = {arg.tag:arguments.Argument(key=arg.tag, value=arg.text, format=arg.get("format")) for arg in flag.findall("args/*")}
        return ffk.Flag(action=action, filters=filters, args=args)

    def parseFilter(self, filter=None):
        action = filter.get("action")
        args = {arg.tag:arguments.Argument(key=arg.tag, value=arg.text, format=arg.get("format")) for arg in filter.findall("args/*")}
        return ffk.Filter(action=action, args=args)

    def createStep(self, id="", action="", app="", device="", input={}, next=[], errors=[]):
        #Creates new step object
        input = {input[key]["tag"]:arguments.Argument(key=input[key]["tag"], value=input[key]["value"], format=input[key]["format"]) for key in input}
        self.steps[id] = wfstep.Step(id=id, action=action, app=app, device=device, input=input, next=next, errors=errors)
        stepXML = self.steps[id].toXML()
        self.workflowXML.find(".//steps").append(stepXML)

    def removeStep(self, id=""):
        if id in self.steps:
            newDict = dict(self.steps)
            del newDict[id]
            self.steps = newDict
            return True
        return False

    def toXML(self):
        root = self.workflowXML.find(".//steps")
        root.clear()
        for step in self.steps:
            root.append(self.steps[step].toXML())

        return self.workflowXML

    def importApp(self, app=""):
        module = "apps." + app + ".main"
        try:
            return sys.modules[module]
        except KeyError:
            pass
        try:
            return importlib.import_module(module, 'Main')
        except ImportError as e:
            pass

    def createInstance(self, app="", device=""):
        imported = self.importApp(app)
        if imported:
            return instance.Instance(instance=getattr(imported, "Main")(name=app, device=device), state=instance.OK)

    def goToNextStep(self, current="", nextUp=""):
        if nextUp not in self.steps:
            self.steps[current].nextUp = None
            current = None
        else:
            current = nextUp
        return current

    def executeChild(self, name="", start="start", data=None, instances={}):
        if name in self.options.children and type(self.options.children[name]).__name__ == "Workflow":
            steps, instances = self.options.children[name].execute(start=start, data=data, instances=instances)
            return steps

    def execute(self, start="start", data=None, instances={}):
        totalSteps = []
        current = start
        instances = instances
        while current != None:
            step = self.steps[current]
            if step.device not in instances:
                instances[step.device] = self.createInstance(app=step.app, device=step.device)

            [self.steps[current].input[arg].template(self.steps) for arg in step.input]
            step.execute(instance=instances[step.device]())
            totalSteps.append(self.steps[current])
            nextUp = step.nextStep()

            #Check for call to child workflow
            if nextUp and nextUp[0] == '@':
                params = nextUp.split(":")
                params[0] = params[0].lstrip("@")
                if len(params) == 3:
                    childWorkflowOutput = self.executeChild(name=params[0], start=params[1])
                    if childWorkflowOutput:
                        totalSteps.extend(childWorkflowOutput)
                        nextUp = params[2]

            current = self.goToNextStep(current=current, nextUp=nextUp)

        #Upon finishing shuts down instances
        for instance in instances:
            instances[instance].shutdown()

        return totalSteps, str(instances)

    def __repr__(self):
        output = {}
        output["options"] = self.options
        output["steps"] = {step:self.steps[step] for step in self.steps}
        return str(output)









