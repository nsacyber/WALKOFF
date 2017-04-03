import xml.etree.cElementTree as et
from os.path import join, isfile

from core import arguments
from core.config import paths
from core.instance import Instance
from core import options
from core.case import callbacks
from core.executionelement import ExecutionElement
from core.step import Step
from core.helpers import construct_workflow_name_key, extract_workflow_name

class Workflow(ExecutionElement):
    def __init__(self, name="", workflowConfig=None, children=None, parent_name="", filename=''):
        ExecutionElement.__init__(self, name=name, parent_name=parent_name, ancestry=[parent_name])
        self.workflowXML = workflowConfig
        self.filename = filename
        self._from_xml(self.workflowXML)
        self.children = children if (children is not None) else {}
        self.is_completed = False

    @staticmethod
    def get_workflow(workflow_name):
        if isfile(join(paths.templates_path, workflow_name)):
            tree = et.ElementTree(file=join(paths.templates_path, workflow_name))
            for workflow in tree.iter(tag="workflow"):
                name = workflow.get("name")
                return Workflow(name=name, workflowConfig=workflow)
                # TODO: Make this work with child workflows

    def _from_xml(self, xml_element, *args):
        self.options = options.Options(xml=xml_element.find(".//options"), workflow_name=self.name, filename=self.filename)
        self.steps = {}
        for step_xml in xml_element.findall(".//steps/*"):
            step = Step(xml=step_xml, parent_name=self.name, ancestry=self.ancestry)
            self.steps[step.name] = step

    def assignChild(self, name="", workflow=None):
        self.children[name] = workflow

    def createStep(self, id="", action="", app="", device="", input=None, next=None, errors=None):
        input = input if input is not None else {}
        next = next if next is not None else []
        errors = errors if errors is not None else []
        # Creates new step object
        input = {input[key]["tag"]: arguments.Argument(key=input[key]["tag"], value=input[key]["value"],
                                                       format=input[key]["format"]) for key in input}
        ancestry = list(self.ancestry)
        self.steps[id] = Step(name=id, action=action, app=app, device=device, inputs=input, next_steps=next,
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

    def to_xml(self, *args):
        self.workflowXML.set('name', extract_workflow_name(self.name))
        root = self.workflowXML.find(".//steps")
        if list(iter(root)):
            root.clear()
        for step in self.steps:
            root.append(self.steps[step].to_xml())
        return self.workflowXML

    def goToNextStep(self, current="", nextUp=""):
        if nextUp not in self.steps:
            self.steps[current].nextUp = None
            current = None
        else:
            current = nextUp
        return current

    def execute(self, start="start", data=None):
        instances = {}
        total_steps = []
        steps = self.__steps(start=start)
        for step in steps:
            if step:
                callbacks.NextStepFound.send(self)
                if step.device not in instances:
                    instances[step.device] = Instance.create(step.app, step.device)
                    callbacks.AppInstanceCreated.send(self)

                step.render_step(steps=total_steps)

                error_flag = self.__execute_step(step, instances[step.device])
                total_steps.append(step)
                steps.send(error_flag)
        self.__shutdown(instances)

    def __steps(self, start="start"):
        initial_step_name = start
        current_name = initial_step_name
        current = self.steps[current_name]
        while current:
            error_flag = yield current
            next_step = current.get_next_step(error=error_flag)

            # Check for call to child workflow
            if next_step and next_step[0] == '@':
                child_step_generator, child_next_step = self.get_child_step_generator(next_step)
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
            callbacks.StepExecutionSuccess.send(self)
        except Exception as e:
            error_flag = True
            step.output = str(e)
        finally:
            return error_flag

    def get_child_step_generator(self, tiered_step_str):
        params = tiered_step_str.split(':')
        if len(params) == 3:
            child_name, child_start, child_next = params[0].lstrip('@'), params[1], params[2]
            child_name = construct_workflow_name_key(self.filename, child_name)
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
            callbacks.WorkflowShutdown.send(self)
        except Exception:
            pass

    def get_cytoscape_data(self):
        output = []
        for step in self.steps:
            node_id = self.steps[step].name if self.steps[step].name is not None else 'None'
            node = {"group": "nodes", "data": {"id": self.steps[step].name, "parameters": self.steps[step].as_json()}}
            output.append(node)
            for next_step in self.steps[step].conditionals:
                edge_id = str(self.steps[step].name) + str(next_step.name)
                if next_step.name in self.steps:
                    node = {"group": "edges",
                            "data": {"id": edge_id, "source": self.steps[step].name, "target": next_step.name,
                                     "parameters": next_step.as_json()}}
                    output.append(node)
        return output

    def from_cytoscape_data(self, data):
        steps = {}
        for node in data:
            if 'source' not in node['data'] and 'target' not in node['data']:
                step_data = node['data']
                step_name = step_data['parameters']['name']
                steps[step_name] = Step.from_json(step_data['parameters'], parent_name=self.name, ancestry=self.ancestry)
        self.steps = steps

    def __repr__(self):
        output = {'options': self.options,
                  'steps': {step: self.steps[step] for step in self.steps}}
        return str(output)
