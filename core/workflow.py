from xml.etree import cElementTree
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
    def __init__(self, name='', xml=None, children=None, parent_name='', playbook_name=''):
        ExecutionElement.__init__(self, name=name, parent_name=parent_name, ancestry=[parent_name])
        self.playbook_name = playbook_name
        self.steps = {}
        if xml:
            self._from_xml(xml)
        self.children = children if (children is not None) else {}
        self.is_completed = False
        self.accumulated_risk = 0.0
        self.total_risk = sum([step.risk for step in self.steps.values()])

    def reconstruct_ancestry(self, parent_ancestry):
        self._construct_ancestry(parent_ancestry)
        for key in self.steps:
            self.steps[key].reconstruct_ancestry(self.ancestry)

    @staticmethod
    def get_workflow(workflow_name):
        if isfile(join(paths.templates_path, workflow_name)):
            tree = cElementTree.ElementTree(file=join(paths.templates_path, workflow_name))
            for workflow in tree.iter(tag='workflow'):
                name = workflow.get('name')
                return Workflow(name=name, xml=workflow)
                # TODO: Make this work with child workflows

    def _from_xml(self, xml_element, *args):
        self.options = options.Options(xml=xml_element.find('.//options'), playbook_name=self.playbook_name)
        self.steps = {}
        for step_xml in xml_element.findall('.//steps/*'):
            step = Step(xml=step_xml, parent_name=self.name, ancestry=self.ancestry)
            self.steps[step.name] = step

    def assign_child(self, name='', workflow=None):
        self.children[name] = workflow

    def create_step(self, name='', action='', app='', device='', arg_input=None, next_steps=None, errors=None, risk=0):
        arg_input = arg_input if arg_input is not None else {}
        next_steps = next_steps if next_steps is not None else []
        errors = errors if errors is not None else []
        # Creates new step object
        arg_input = {arg['tag']: arguments.Argument(key=arg['tag'], value=arg['value'],
                                                    format=arg['format']) for key, arg in arg_input.items()}
        ancestry = list(self.ancestry)
        self.steps[name] = Step(name=name, action=action, app=app, device=device, inputs=arg_input,
                                next_steps=next_steps, errors=errors, ancestry=ancestry, parent_name=self.name, risk=risk)
        self.total_risk += risk

    def remove_step(self, name=''):
        if name in self.steps:
            new_dict = dict(self.steps)
            del new_dict[name]
            self.steps = new_dict
            return True
        return False

    def to_xml(self, *args):
        workflow_element = cElementTree.Element('workflow')
        workflow_element.set('name', extract_workflow_name(self.name))

        workflow_element.append(self.options.to_xml())

        steps = cElementTree.SubElement(workflow_element, 'steps')
        for step_name, step in self.steps.items():
            steps.append(step.to_xml())
        return workflow_element

    def __go_to_next_step(self, current='', next_up=''):
        if next_up not in self.steps:
            self.steps[current].next_up = None
            current = None
        else:
            current = next_up
        return current

    def execute(self, start='start'):
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

    def __steps(self, start='start'):
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

            current_name = self.__go_to_next_step(current=current_name, next_up=next_step)
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
            self.accumulated_risk += (float(step.risk)/float(self.total_risk))
        finally:
            return error_flag

    def get_child_step_generator(self, tiered_step_str):
        params = tiered_step_str.split(':')
        if len(params) == 3:
            child_name, child_start, child_next = params[0].lstrip('@'), params[1], params[2]
            child_name = construct_workflow_name_key(self.playbook_name, child_name)
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
        except:
            pass

    def get_cytoscape_data(self):
        output = []
        for step in self.steps:
            node_id = self.steps[step].name if self.steps[step].name is not None else 'None'
            step_json = self.steps[step].as_json()
            position = step_json.pop('position')
            node = {"group": "nodes", "data": {"id": node_id, "parameters": step_json},
                    "position": {pos: float(val) for pos, val in position.items()}}
            output.append(node)
            for next_step in self.steps[step].conditionals:
                edge_id = str(node_id) + str(next_step.name)
                if next_step.name in self.steps:
                    node = {"group": "edges",
                            "data": {"id": edge_id, "source": node_id, "target": next_step.name,
                                     "parameters": next_step.as_json()}}
                    output.append(node)
        return output

    def from_cytoscape_data(self, data):
        self.steps = {}
        for node in data:
            if 'source' not in node['data'] and 'target' not in node['data']:
                step_data = node['data']
                step_name = step_data['parameters']['name']
                self.steps[step_name] = Step.from_json(step_data['parameters'],
                                                       node['position'],
                                                       parent_name=self.name,
                                                       ancestry=self.ancestry)

    def get_children(self, ancestry):
        if not ancestry:
            return {'steps': list(self.steps.keys())}
        else:
            ancestry = ancestry[::-1]
            next_child = ancestry.pop()
            if next_child in self.steps:
                return self.steps[next_child].get_children(ancestry)
            else:
                return None

    def __repr__(self):
        output = {'options': self.options,
                  'steps': {step: self.steps[step] for step in self.steps},
                  'accumulated_risk': "{0:.2f}".format(self.accumulated_risk*100.00)}
        return str(output)

    def as_json(self, *args):
        return {'name': self.name,
                'accumulated_risk': "{0:.2f}".format(self.accumulated_risk*100.00),
                'options': self.options.as_json(),
                'steps': {name: step.as_json() for name, step in self.steps.items()}}
