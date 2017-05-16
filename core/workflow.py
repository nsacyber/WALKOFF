from xml.etree import cElementTree
from os.path import join, isfile
import json
import logging
from core import arguments
from core.config import paths
from core.instance import Instance
from core import options
from core.case import callbacks
from core.executionelement import ExecutionElement
from core.step import Step
from core.helpers import construct_workflow_name_key, extract_workflow_name

logger = logging.getLogger(__name__)


class Workflow(ExecutionElement):
    def __init__(self, name='', xml=None, children=None, parent_name='', playbook_name=''):
        """Initializes a Workflow object. A Workflow falls under a Playbook, and has many associated Steps
            within it that get executed.
            
        Args:
            name (str, optional): The name of the Workflow object. Defaults to an empty string.
            xml (cElementTree, optional): The XML element tree object. Defaults to None.
            children (dict, optional): A dict of children. Defaults to None.
            parent_name (str, optional): The name of the parent for ancestry purposes. Defaults to an empty string.
            playbook_name (str, optional): The name of the playbook under which the workflow is located. Defaults
                to an empty string.
        """
        ExecutionElement.__init__(self, name=name, parent_name=parent_name, ancestry=[parent_name])
        self.playbook_name = playbook_name
        self.steps = {}
        if xml:
            self._from_xml(xml)
        else:
            self.start_step = 'start'
        self.children = children if (children is not None) else {}
        self.is_completed = False
        self.accumulated_risk = 0.0
        self.total_risk = float(sum([step.risk for step in self.steps.values() if step.risk > 0]))
        self.is_paused = False
        self.executor = None
        self.breakpoint_steps = []

    def reconstruct_ancestry(self, parent_ancestry):
        """Reconstructs the ancestry for a Workflow object. This is needed in case a workflow and/or playbook is renamed.
        
        Args:
            parent_ancestry(list[str]): The parent ancestry list.
        """
        self._construct_ancestry(parent_ancestry)
        for key in self.steps:
            self.steps[key].reconstruct_ancestry(self.ancestry)

    @staticmethod
    def get_workflow(workflow_name):
        """Retrieve a workflow from the name of the workflow.
        
        Args:
            workflow_name: The name of the Workflow objet to be retrieved.
            
        Returns:
            The Workflow object from the provided workflow name.
        """
        if isfile(join(paths.templates_path, workflow_name)):
            tree = cElementTree.ElementTree(file=join(paths.templates_path, workflow_name))
            for workflow in tree.iter(tag='workflow'):
                name = workflow.get('name')
                return Workflow(name=name, xml=workflow)
                # TODO: Make this work with child workflows

    def _from_xml(self, xml_element, *args):
        self.options = options.Options(xml=xml_element.find('.//options'), playbook_name=self.playbook_name)
        start_step = xml_element.find('start')
        self.start_step = start_step.text if start_step is not None else 'start'
        self.steps = {}
        for step_xml in xml_element.findall('.//steps/*'):
            step = Step(xml=step_xml, parent_name=self.name, ancestry=self.ancestry)
            self.steps[step.name] = step

    def assign_child(self, name='', workflow=None):
        self.children[name] = workflow

    def create_step(self, name='', action='', app='', device='', arg_input=None, next_steps=None, errors=None, risk=0):
        """Creates a new Step object and adds it to the Workflow's list of Steps.
        
        Args:
            name (str, optional): The name of the Step object. Defaults to an empty string.
            action (str, optional): The name of the action associated with a Step. Defaults to an empty string.
            app (str, optional): The name of the app associated with the Step. Defaults to an empty string.
            device (str, optional): The name of the device associated with the app associated with the Step. Defaults
            to an empty string.
            arg_input (dict, optional): A dictionary of Argument objects that are input to the step execution. Defaults
            to None.
            next_steps (list[NextStep], optional): A list of NextStep objects for the Step object. Defaults to None.
            errors (list[NextStep], optional): A list of NextStep error objects for the Step object. Defaults to None.
            risk (int, optional): The risk associated with the Step. Defaults to 0.
            
        """
        arg_input = arg_input if arg_input is not None else {}
        next_steps = next_steps if next_steps is not None else []
        errors = errors if errors is not None else []
        # Creates new step object
        arg_input = {arg['tag']: arguments.Argument(key=arg['tag'], value=arg['value'],
                                                    format=arg['format']) for key, arg in arg_input.items()}
        ancestry = list(self.ancestry)
        self.steps[name] = Step(name=name, action=action, app=app, device=device, inputs=arg_input,
                                next_steps=next_steps, errors=errors, ancestry=ancestry, parent_name=self.name,
                                risk=risk)
        self.total_risk += risk
        logger.info('Step added to workflow {0}. Step: {1}'.format(self.ancestry, self.steps[name].as_json()))

    def remove_step(self, name=''):
        """Removes a Step object from the Workflow's list of Steps given the Step name.
        
        Args:
            name (str): The name of the Step object to be removed.
            
        Returns:
            True on success, False otherwise.
        """
        if name in self.steps:
            new_dict = dict(self.steps)
            del new_dict[name]
            self.steps = new_dict
            logger.debug('Removed step {0} from workflow {1}'.format(name, self.ancestry))
            return True
        logger.warning('Could not remove step {0} from workflow {1}. Step does nto exist'.format(name, self.ancestry))
        return False

    def to_xml(self, *args):
        """Converts the Workflow object to XML format.
        
        Returns:
            The XML representation of the Workflow object.
        """
        workflow_element = cElementTree.Element('workflow')
        workflow_element.set('name', extract_workflow_name(self.name))

        workflow_element.append(self.options.to_xml())

        start = cElementTree.SubElement(workflow_element, 'start')
        start.text = self.start_step

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

    def pause(self):
        """Pauses the execution of the Workflow. The Workflow will pause execution before starting the next Step.
        """
        if self.executor is not None:
            logger.info('Pausing workflow {0}'.format(self.ancestry))
            self.is_paused = True

    def resume(self):
        """Resumes a Workflow that has previously been paused.
        """
        try:
            logger.info('Attempting to resume workflow {0}'.format(self.ancestry))
            self.is_paused = False
            self.executor.send(None)
        except (StopIteration, AttributeError) as e:
            logger.warning('Cannot resume workflow {0}. Reason: {1}'.format(self.ancestry, e))
            pass

    def resume_breakpoint_step(self):
        """Resumes a Workflow that has hit a breakpoint at a Step. This is used for debugging purposes.
        """
        try:
            logger.debug('Attempting to resume workflow {0} from breakpoint'.format(self.ancestry))
            self.executor.send(None)
        except (StopIteration, AttributeError) as e:
            logger.warning('Cannot resume workflow {0} from breakpoint. Reason: {1}'.format(self.ancestry, e))
            pass

    def execute(self, start=None, start_input=''):
        """Executes a Workflow by executing all Steps in the Workflow list of Step objects.
        
        Args:
            start (str, optional): The name of the first Step. Defaults to "start".
            start_input (str, optional): Input into the first Step. Defaults to an empty string.
        """
        logger.info('Executing workflow {0}'.format(self.ancestry))
        callbacks.WorkflowExecutionStart.send(self)
        start = start if start is not None else self.start_step
        self.executor = self.__execute(start, start_input)
        next(self.executor)

    def __execute(self, start, start_input):
        instances = {}
        total_steps = []
        steps = self.__steps(start=start)
        first = True
        for step in steps:
            logger.debug('Executing step {0} of workflow {1}'.format(step, self.ancestry))
            while self.is_paused:
                _ = yield
            if step:
                if step.name in self.breakpoint_steps:
                    _ = yield
                callbacks.NextStepFound.send(self)
                if step.device not in instances:
                    instances[step.device] = Instance.create(step.app, step.device)
                    callbacks.AppInstanceCreated.send(self)
                    logger.debug('Created new app instance: App {0}, device {1}'.format(step.app, step.device))
                step.render_step(steps=total_steps)

                if first:
                    if start_input:
                        logger.debug('Swapping input to first step of workflow {0}'.format(self.ancestry))
                        step.input = start_input
                    first = False

                error_flag = self.__execute_step(step, instances[step.device])
                total_steps.append(step)
                steps.send(error_flag)
        self.__shutdown(instances)
        yield

    def __steps(self, start):
        initial_step_name = start
        current_name = initial_step_name
        current = self.steps[current_name]
        while current:
            error_flag = yield current
            next_step = current.get_next_step(error=error_flag)

            # Check for call to child workflow
            if next_step and next_step[0] == '@':
                child_step_generator, child_next_step, child_name = self.__get_child_step_generator(next_step)
                if child_step_generator:
                    for child_step in child_step_generator:
                        if child_step:
                            yield  # needed so outer for-loop is in sync
                            error_flag = yield child_step
                            child_step_generator.send(error_flag)
                        callbacks.WorkflowShutdown.send(self.options.children[child_name])
                    next_step = child_next_step

            current_name = self.__go_to_next_step(current=current_name, next_up=next_step)
            current = self.steps[current_name] if current_name is not None else None
            yield  # needed so that when for-loop calls next() it doesn't advance too far
        yield  # needed so you can avoid catching StopIteration exception

    def __execute_step(self, step, instance):
        error_flag = False
        data = {"step": {"app": step.app,
                         "action": step.action,
                         "name": step.name}}
        json.dumps(data)
        try:
            step.execute(instance=instance())
            callbacks.StepExecutionSuccess.send(self)
        except Exception as e:
            callbacks.StepExecutionError.send(self, data=json.dumps({"step": {"app": step.app,
                                                                              "action": step.action,
                                                                              "name": step.name}}))
            error_flag = True
            step.output = str(e)
            self.accumulated_risk += float(step.risk) / self.total_risk
            logger.debug('Step {0} of workflow {1} executed with error {2}'.format(step, self.ancestry, e))
        finally:
            return error_flag

    def __get_child_step_generator(self, tiered_step_str):
        params = tiered_step_str.split(':')
        if len(params) == 3:
            child_name, child_start, child_next = params[0].lstrip('@'), params[1], params[2]
            child_name = construct_workflow_name_key(self.playbook_name, child_name)
            if (child_name in self.options.children
                    and type(self.options.children[child_name]).__name__ == 'Workflow'):
                logger.debug('Executing child workflow {0} of workflow {1}'.format(child_name, self.ancestry))
                callbacks.WorkflowExecutionStart.send(self.options.children[child_name])
                child_step_generator = self.options.children[child_name].__steps(start=child_start)
                return child_step_generator, child_next, child_name
        return None, None

    def __shutdown(self, instances):
        # Upon finishing shuts down instances
        for instance in instances:
            try:
                logger.debug('Shutting down app instance: Device: {0}'.format(instance))
                instances[instance].shutdown()
            except Exception as e:
                logger.error('Error caught while shutting down app instance. '
                             'Device: {0}. Error {1}'.format(instance, e))
        callbacks.WorkflowShutdown.send(self)

    def get_cytoscape_data(self):
        """Gets the cytoscape data for the Workflow object.
        
        Returns:
            The cytoscape data for the Workflow.
        """
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
        """Reconstruct a Workflow object based on cytoscape data.
        
        Args:
            data (JSON dict): The cytoscape data to be parsed and reconstructed into a Workflow object.
        """
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
        """Gets the children Steps of the Workflow in JSON format.
        
        Args:
            ancestry (list[str]): The ancestry list for the Step to be returned.
            
        Returns:
            The Step in the ancestry (if provided) as a JSON, otherwise None.
        """
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
                  'accumulated_risk': "{0:.2f}".format(self.accumulated_risk * 100.00)}
        return str(output)

    def as_json(self, *args):
        """Gets the JSON representation of a Step object.
        
        Returns:
            The JSON representation of a Step object.
        """
        return {'name': self.name,
                'accumulated_risk': "{0:.2f}".format(self.accumulated_risk * 100.00),
                'options': self.options.as_json(),
                'steps': {name: step.as_json() for name, step in self.steps.items()}}
