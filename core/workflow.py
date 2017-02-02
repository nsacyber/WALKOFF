import sys
import importlib

from core import step as wfstep
from core import ffk
from core import arguments
from core import instance
from core import options
from core import case
from core.events import EventHandler, Event


class WorkflowEventHandler(EventHandler):
    def __init__(self, shared_log=None):
        EventHandler.__init__(self, "WorkflowEventHandler", shared_log,
                              events={'InstanceCreated': case.add_workflow_entry("New workflow instance Created"),
                                      'StepExecutionSuccess': case.add_workflow_entry('Step executed successfully'),
                                      'NextStepFound': case.add_workflow_entry('Next step found'),
                                      'WorkflowShutdown': case.add_workflow_entry("Workflow shut down")})


class Workflow(object):
    def __init__(self, name="", workflowConfig=None, children=None, parentController=""):
        self.name = name
        self.parentController = parentController
        self.workflowXML = workflowConfig
        self.options = self.parseOptions(workflowConfig.find(".//options"))
        self.steps = self.parseSteps(workflowConfig.findall(".//steps/*"))
        self.children = children if (children is not None) else {}
        self.eventlog = []
        self.workflowEventHandler = WorkflowEventHandler(self.eventlog)

    def parseOptions(self, ops=None):
        # Parses out the options for each item if there are no subelements then pass the text instead
        scheduler = {"autorun": ops.find(".//scheduler").get("autorun"), "type": ops.find(".//scheduler").get("type"),
                     "args": {option.tag: option.text for option in ops.findall(".//scheduler/*")}}
        enabled = ops.find(".//enabled").text
        children = {child.text: None for child in ops.findall(".//children/child")}

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
            input = {arg.tag: arguments.Argument(key=arg.tag, value=arg.text, format=arg.get("format")) for arg in
                     step.findall("input/*")}
            next = [self.parseNext(id, nextStep) for nextStep in step.findall("next")]
            errors = [self.parseNext(id, error) for error in step.findall("error")]
            steps[id] = wfstep.Step(id=id, action=action, app=app, device=device, input=input, next=next, errors=errors,
                                    parent=self.name)
        return steps

    def parseNext(self, previous_id, next=None):
        flags = [self.parseFlag(previous_id, flag) for flag in next.findall("flag")]
        nextId = next.get("step")
        nextStep = ffk.Next(previous_id, nextStep=nextId, flags=flags)
        return nextStep

    def parseFlag(self, previous_id, flag=None):
        action = flag.get("action")
        filters = [self.parseFilter(previous_id, filter) for filter in flag.findall("filters/*")]
        args = {arg.tag: arguments.Argument(key=arg.tag, value=arg.text, format=arg.get("format")) for arg in
                flag.findall("args/*")}
        return ffk.Flag(previous_step_id=previous_id, action=action, filters=filters, args=args)

    def parseFilter(self, previous_id, filter=None):
        action = filter.get("action")
        args = {arg.tag: arguments.Argument(key=arg.tag, value=arg.text, format=arg.get("format")) for arg in
                filter.findall("args/*")}
        return ffk.Filter(previous_step_id=previous_id, action=action, args=args)

    def createStep(self, id="", action="", app="", device="", input={}, next=[], errors=[]):
        # Creates new step object
        input = {input[key]["tag"]: arguments.Argument(key=input[key]["tag"], value=input[key]["value"],
                                                       format=input[key]["format"]) for key in input}
        self.steps[id] = wfstep.Step(id=id, action=action, app=app, device=device, input=input, next=next,
                                     errors=errors)
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
        except ImportError:
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

    def executeChild(self, name="", start="start", data=None, instances=None):
        instances = instances if instances is not None else {}
        if name in self.options.children and type(self.options.children[name]).__name__ == "Workflow":
            steps, instances = self.options.children[name].execute(start=start, data=data, instances=instances)
            return steps

    def execute(self, start="start", data=None, instances=None):
        total_steps = []
        instances = instances if instances is not None else {}
        for __ in self.__step_generator(start, instances, total_steps):
            self.workflowEventHandler.execute_event_code(self, 'NextStepFound')

        self.__shutdown(instances)

        return total_steps, str(instances)

    def __step_generator(self, start, instances, total_steps):
        current = start
        while current:
            next_step = self.__execute_step(self.steps[current], instances, total_steps)
            yield next_step
            current = self.goToNextStep(current=current, nextUp=next_step)

    def __execute_step(self, step, instances, total_steps):
        if step.device not in instances:
            instances[step.device] = self.createInstance(app=step.app, device=step.device)
            self.workflowEventHandler.execute_event_code(self, 'InstanceCreated')

        for arg in step.input:
            step.input[arg].template(steps=total_steps)

        try:
            step.execute(instance=instances[step.device]())
            self.workflowEventHandler.execute_event_code(self, 'StepExecutionSuccess')
            error_flag = False
        except Exception as e:
            error_flag = True
            step.output = str(e)
        finally:
            total_steps.append(step)
            return self.__next_step(step, error_flag, total_steps)

    def __next_step(self, step, error_flag, total_steps):
        next_step = step.nextStep(error=error_flag)

        # Check for call to child workflow
        if next_step and next_step[0] == '@':
            params = next_step.split(":")
            params[0] = params[0].lstrip("@")
            if len(params) == 3:
                childWorkflowOutput = self.executeChild(name=params[0], start=params[1])
                if childWorkflowOutput:
                    total_steps.extend(childWorkflowOutput)
                    next_step = params[2]
        return next_step

    def __shutdown(self, instances):
        try:
            # Upon finishing shuts down instances
            for instance in instances:
                instances[instance].shutdown()
            self.workflowEventHandler.execute_event_code(self, 'WorkflowShutdown')
        except Exception:
            pass

    def __repr__(self):
        output = {'options': self.options,
                  'steps': {step: self.steps[step] for step in self.steps}}
        return str(output)
