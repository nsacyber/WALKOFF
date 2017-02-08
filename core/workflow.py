import sys
import importlib

from core.step import Step
from core import arguments
from core import instance
from core import options
from core import case
from core.executionelement import ExecutionElement


class Workflow(ExecutionElement):
    def __init__(self, name="", workflowConfig=None, children=None, parent_name=""):
        ExecutionElement.__init__(self, name=name, parent_name=parent_name, ancestry=[parent_name])
        self.workflowXML = workflowConfig
        self._from_xml(self.workflowXML)
        self.children = children if (children is not None) else {}
        super(Workflow, self)._register_event_callbacks(
            {'InstanceCreated': case.add_workflow_entry("New workflow instance Created"),
             'StepExecutionSuccess': case.add_workflow_entry('Step executed successfully'),
             'NextStepFound': case.add_workflow_entry('Next step found'),
             'WorkflowShutdown': case.add_workflow_entry("Workflow shut down")})

    def _from_xml(self, xml_element):
        self.options = options.Options(xml=xml_element.find(".//options"), workflow_name=self.name)
        self.steps = {}
        for step_xml in xml_element.findall(".//steps/*"):
            step = Step(xml=step_xml, parent_name=self.name, ancestry=self.ancestry)
            self.steps[step.name] = step

    def assignChild(self, name="", workflow=None):
        self.children[name] = workflow

    def createStep(self, id="", action="", app="", device="", input={}, next=[], errors=[]):
        # Creates new step object
        input = {input[key]["tag"]: arguments.Argument(key=input[key]["tag"], value=input[key]["value"],
                                                       format=input[key]["format"]) for key in input}
        ancestry = list(self.ancestry)
        ancestry.append(id)
        self.steps[id] = Step(name=id, action=action, app=app, device=device, input=input, next=next,
                              errors=errors, ancestry=ancestry, parent_name=self.name)
        stepXML = self.steps[id].to_xml()
        self.workflowXML.find(".//steps").append(stepXML)

    def removeStep(self, id=""):
        if id in self.steps:
            newDict = dict(self.steps)
            del newDict[id]
            self.steps = newDict
            return True
        return False

    def to_xml(self):
        root = self.workflowXML.find(".//steps")
        root.clear()
        for step in self.steps:
            root.append(self.steps[step].to_xml())

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
                self.event_handler.execute_event_code(self, 'NextStepFound')
                if step.device not in instances:
                    instances[step.device] = self.createInstance(app=step.app, device=step.device)
                    self.event_handler.execute_event_code(self, 'InstanceCreated')

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
        error_flag = False
        try:
            step.execute(instance=instance())
            self.event_handler.execute_event_code(self, 'StepExecutionSuccess')
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
        return None, None

    def __shutdown(self, instances):
        try:
            # Upon finishing shuts down instances
            for instance in instances:
                instances[instance].shutdown()
            self.event_handler.execute_event_code(self, 'WorkflowShutdown')
        except Exception:
            pass

    def __repr__(self):
        output = {'options': self.options,
                  'steps': {step: self.steps[step] for step in self.steps}}
        return str(output)
