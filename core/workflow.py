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
        self.ancestry = [parentController, self.name]
        self.parentController = parentController
        self.workflowXML = workflowConfig
        self.options = self.parseOptions(workflowConfig.find(".//options"))
        self.steps = self.parseSteps(workflowConfig.findall(".//steps/*"))
        self.children = children if (children is not None) else {}
        self.eventlog = []
        self.workflowEventHandler = WorkflowEventHandler(self.eventlog)
        self.__instances = {}

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
            steps[id] = wfstep.Step(id=id, action=action, app=app, device=device, input=input,
                                    parent=self.name, ancestry=self.ancestry)
            steps[id].conditionals = [self.parseNext(id, steps[id].ancestry, next=nextStep) for nextStep in step.findall("next")]
            steps[id].errors = [self.parseNext(id, steps[id].ancestry, next=error) for error in step.findall("error")]
        return steps

    def parseNext(self, previous_id, ancestry, next=None):
        nextId = next.get("step")
        nextStep = ffk.Next(previous_id, nextStep=nextId, ancestry=ancestry)
        nextStep.flags = [self.parseFlag(previous_id, nextStep.ancestry, flag) for flag in next.findall("flag")]
        return nextStep

    def parseFlag(self, previous_id, ancestry, flag=None):
        action = flag.get("action")
        args = {arg.tag: arguments.Argument(key=arg.tag, value=arg.text, format=arg.get("format")) for arg in
                flag.findall("args/*")}
        parsed_flag = ffk.Flag(previous_step_id=previous_id, action=action, args=args, ancestry=ancestry)
        parsed_flag.filters = [self.parseFilter(previous_id, parsed_flag.ancestry, filter) for filter in flag.findall("filters/*")]
        return parsed_flag

    def parseFilter(self, previous_id, ancestry, filter=None):
        action = filter.get("action")
        args = {arg.tag: arguments.Argument(key=arg.tag, value=arg.text, format=arg.get("format")) for arg in
                filter.findall("args/*")}
        return ffk.Filter(previous_step_id=previous_id, action=action, args=args, ancestry=ancestry)

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

    def execute(self, start="start"):
        total_steps = []
        instances = {}
        steps = self.__steps(start=start)

        for step in steps:
            if step:
                self.workflowEventHandler.execute_event_code(self, 'NextStepFound')
                if step.device not in instances:
                    instances[step.device] = self.createInstance(app=step.app, device=step.device)
                    self.workflowEventHandler.execute_event_code(self, 'InstanceCreated')

                for arg in step.input:
                    step.input[arg].template(steps=total_steps)

                error_flag = self.__execute_step(step, instances[step.device])
                total_steps.append(step)
                steps.send(error_flag)
        self.__shutdown(instances)
        return total_steps, str(instances)

    def __steps(self, start="start"):
        initial_step_name = start
        current_name = initial_step_name
        current = self.steps[current_name]
        while current:
            error_flag = yield current
            next_step = current.nextStep(error=error_flag)

            # Check for call to child workflow
            if next_step and next_step[0] == '@':
                child_step_generator, child_next_step = self.__get_child_step_generator(next_step)
                if child_step_generator:
                    for child_step in child_step_generator:
                        if child_step:
                            yield  # needed so outer for-loop is in sync
                            error_flag = yield child_step
                            child_step_generator.send(error_flag)
                    next_step = child_next_step

            current_name = self.goToNextStep(current=current_name, nextUp=next_step)
            current = self.steps[current_name] if current_name is not None else None
            yield  # needed so that when for-loop calls next() it doesn't advance too far
        yield  # needed so you can avoid catching StopIteration exception

    def __execute_step(self, step, instance):
        try:
            step.execute(instance=instance())
            self.workflowEventHandler.execute_event_code(self, 'StepExecutionSuccess')
            error_flag = False
        except Exception as e:
            error_flag = True
            step.output = str(e)
        finally:
            return error_flag

    def __get_child_step_generator(self, tiered_step_str):
            params = tiered_step_str.split(':')
            if len(params) == 3:
                child_name, child_start, child_next = params[0].lstrip('@'), params[1], params[2]
                if (child_name in self.options.children
                    and type(self.options.children[child_name]).__name__ == 'Workflow'):
                    child_step_generator = self.options.children[child_name].__steps(start=child_start)
            return child_step_generator, child_next

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
