import json
import logging
from copy import deepcopy
from core.case import callbacks
from core.executionelement import ExecutionElement
from core.helpers import UnknownAppAction, UnknownApp, InvalidInput, format_exception_message
from core.instance import Instance
from core.step import Step
import uuid

logger = logging.getLogger(__name__)


class Workflow(ExecutionElement):
    def __init__(self, name='', children=None, playbook_name='', uid=None):
        """Initializes a Workflow object. A Workflow falls under a Playbook, and has many associated Steps
            within it that get executed.
            
        Args:
            name (str, optional): The name of the Workflow object. Defaults to an empty string.
            children (dict, optional): A dict of children. Defaults to None.
            playbook_name (str, optional): The name of the playbook under which the workflow is located. Defaults
                to an empty string.
        """
        ExecutionElement.__init__(self, name=name)
        self.playbook_name = playbook_name
        self.steps = {}
        self.start_step = 'start'
        self.children = children if children is not None else {}
        self.is_completed = False
        self.accumulated_risk = 0.0
        self.total_risk = float(sum([step.risk for step in self.steps.values() if step.risk > 0]))
        self.is_paused = False
        self.executor = None
        self.breakpoint_steps = []
        self.accumulator = {}
        self.uid = uuid.uuid4().hex if uid is None else uid
        self.execution_uid = 'default'

    def assign_child(self, name='', workflow=None):
        self.children[name] = workflow

    def create_step(self, name='', action='', app='', device='', arg_input=None, next_steps=None, risk=0):
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
            risk (int, optional): The risk associated with the Step. Defaults to 0.
            
        """
        arg_input = arg_input if arg_input is not None else {}
        next_steps = next_steps if next_steps is not None else []
        self.steps[name] = Step(name=name, action=action, app=app, device=device, inputs=arg_input,
                                next_steps=next_steps, risk=risk)
        self.total_risk += risk
        logger.info('Step added to workflow {0}. Step: {1}'.format(self.name, self.steps[name].as_json()))

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
            logger.debug('Removed step {0} from workflow {1}'.format(name, self.name))
            return True
        logger.warning('Could not remove step {0} from workflow {1}. Step does not exist'.format(name, self.name))
        return False

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
            logger.info('Pausing workflow {0}'.format(self.name))
            self.is_paused = True

    def resume(self):
        """Resumes a Workflow that has previously been paused.
        """
        try:
            logger.info('Attempting to resume workflow {0}'.format(self.name))
            self.is_paused = False
            self.executor.send(None)
        except (StopIteration, AttributeError) as e:
            logger.warning('Cannot resume workflow {0}. Reason: {1}'.format(self.name, format_exception_message(e)))
            pass

    def resume_breakpoint_step(self):
        """Resumes a Workflow that has hit a breakpoint at a Step. This is used for debugging purposes.
        """
        try:
            logger.debug('Attempting to resume workflow {0} from breakpoint'.format(self.name))
            self.executor.send(None)
        except (StopIteration, AttributeError) as e:
            logger.warning('Cannot resume workflow {0} from breakpoint. '
                           'Reason: {1}'.format(self.name, format_exception_message(e)))
            pass

    def execute(self, execution_uid, start=None, start_input=''):
        """Executes a Workflow by executing all Steps in the Workflow list of Step objects.
        
        Args:
            execution_uid (str): The UUID4 hex string uniquely identifying this workflow instance
            start (str, optional): The name of the first Step. Defaults to "start".
            start_input (str, optional): Input into the first Step. Defaults to an empty string.
        """
        self.execution_uid = execution_uid
        logger.info('Executing workflow {0}'.format(self.name))
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
            logger.debug('Executing step {0} of workflow {1}'.format(step, self.name))
            while self.is_paused:
                _ = yield
            if step is not None:
                if step.name in self.breakpoint_steps:
                    _ = yield
                callbacks.NextStepFound.send(self)
                device_id = (step.app, step.device)
                if device_id not in instances:
                    instances[device_id] = Instance.create(step.app, step.device)
                    callbacks.AppInstanceCreated.send(self)
                    logger.debug('Created new app instance: App {0}, device {1}'.format(step.app, step.device))
                step.render_step(steps=total_steps)
                if first:
                    first = False
                    if start_input:
                        self.__swap_step_input(step, start_input)

                self.__execute_step(step, instances[device_id])
                total_steps.append(step)
                self.accumulator[step.name] = step.output.result
        self.__shutdown(instances)
        yield

    def __steps(self, start):
        initial_step_name = start
        current_name = initial_step_name
        current = self.steps[current_name]
        while current:
            yield current
            next_step = current.get_next_step(self.accumulator)
            # Check for call to child workflow
            if next_step and next_step[0] == '@':
                child_step_generator, child_next_step, child_name = self.__get_child_step_generator(next_step)
                if child_step_generator:
                    for child_step in child_step_generator:
                        if child_step:
                            yield  # needed so outer for-loop is in sync
                            yield child_step
                        callbacks.WorkflowShutdown.send(self.children[child_name])
                    next_step = child_next_step
            current_name = self.__go_to_next_step(current=current_name, next_up=next_step)
            current = self.steps[current_name] if current_name is not None else None
            yield  # needed so that when for-loop calls next() it doesn't advance too far
        yield  # needed so you can avoid catching StopIteration exception

    def __swap_step_input(self, step, start_input):
        logger.debug('Swapping input to first step of workflow {0}'.format(self.name))
        try:
            step.set_input(start_input)
            callbacks.WorkflowInputValidated.send(self)
        except InvalidInput as e:
            logger.error('Cannot change input to workflow {0}. '
                         'Invalid input. Error: {1}'.format(self.name, format_exception_message(e)))
            callbacks.WorkflowInputInvalid.send(self)

    def __execute_step(self, step, instance):
        # TODO: These callbacks should be sent by the step, not the workflow. Func should only execute and handle risk
        data = {"app": step.app,
                "action": step.action,
                "name": step.name,
                "input": step.input}
        try:
            step.execute(instance=instance(), accumulator=self.accumulator)
            data['result'] = step.output.as_json()
            data['execution_uid'] = step.execution_uid
            callbacks.StepExecutionSuccess.send(self, data=json.dumps(data))
        except Exception as e:
            data['result'] = step.output.as_json()
            data['execution_uid'] = step.execution_uid
            callbacks.StepExecutionError.send(self, data=json.dumps(data))
            if self.total_risk > 0:
                self.accumulated_risk += float(step.risk) / self.total_risk
            logger.debug('Step {0} of workflow {1} executed with error {2}'.format(step, self.name,
                                                                                   format_exception_message(e)))

    def __get_child_step_generator(self, tiered_step_str):
        params = tiered_step_str.split(':')
        if len(params) == 3:
            child_name, child_start, child_next = params[0].lstrip('@'), params[1], params[2]
            if (child_name in self.children
                    and type(self.children[child_name]).__name__ == 'Workflow'):
                logger.debug('Executing child workflow {0} of workflow {1}'.format(child_name, self.name))
                self.children[child_name].execution_uid = uuid.uuid4().hex
                callbacks.WorkflowExecutionStart.send(self.children[child_name])
                child_step_generator = self.children[child_name].__steps(start=child_start)
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
                             'Device: {0}. Error {1}'.format(instance, format_exception_message(e)))
        result_str = {}
        for step, step_result in self.accumulator.items():
            try:
                result_str[step] = json.dumps(step_result)
            except TypeError:
                logger.error('Result of workflow is neither string or a JSON-able. Cannot record')
                result_str[step] = 'error: could not convert to JSON'
        callbacks.WorkflowShutdown.send(self, data=self.accumulator)
        logger.info('Workflow {0} completed. Result: {1}'.format(self.name, self.accumulator))

    def __repr__(self):
        return str({'uid': self.uid,
                    'steps': {step: self.steps[step] for step in self.steps},
                    'accumulated_risk': round(self.accumulated_risk, 4)})

    def set_children(self, workflow_pairs):
        for name, workflow in workflow_pairs:
            self.children[name] = workflow

    def as_json(self):
        """Gets the JSON representation of a Step object.
        
        Returns:
            The JSON representation of a Step object.
        """
        out = {'uid': self.uid,
               'name': self.name,
               'steps': [step.as_json() for name, step in self.steps.items()],
               'start': self.start_step,
               'accumulated_risk': round(self.accumulated_risk, 4)}
        if self.children:
            out['children'] = list(self.children.keys())
        return out

    def from_json(self, data):
        """Reconstruct a Workflow object based on JSON data.

       Args:
           data (JSON dict): The JSON data to be parsed and reconstructed into a Workflow object.
       """
        backup_steps = deepcopy(self.steps)
        self.steps = {}
        if 'name' in data:
            self.name = data['name']
        uid = data['uid'] if 'uid' in data else uuid.uuid4().hex
        self.children = {name: None for name in data['children']} if 'children' in data else {}
        try:
            if 'start' in data and data['start']:
                self.start_step = data['start']
            self.steps = {}
            self.uid = uid
            for step_json in data['steps']:
                step = Step.from_json(step_json, position=step_json['position'])
                self.steps[step_json['name']] = step
        except (UnknownApp, UnknownAppAction, InvalidInput):
            self.steps = backup_steps
            raise
