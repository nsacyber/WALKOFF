import json
import logging
from copy import deepcopy

import gevent

from core.appinstance import AppInstance
from core.case.callbacks import data_sent
from core.executionelements.executionelement import ExecutionElement
from core.executionelements.step import Step
from core.executionelements.nextstep import NextStep
from core.helpers import UnknownAppAction, UnknownApp, InvalidArgument, format_exception_message
from core.jsonelementreader import JsonElementReader

logger = logging.getLogger(__name__)


class Workflow(ExecutionElement):
    def __init__(self, name='', uid=None, steps=None, next_steps=None, start=None, accumulated_risk=0.0):
        """Initializes a Workflow object. A Workflow falls under a Playbook, and has many associated Steps
            within it that get executed.
            
        Args:
            name (str, optional): The name of the Workflow object. Defaults to an empty string.
            uid (str, optional): Optional UID to pass in for the workflow. Defaults to uuid.uuid4().
            steps (dict, optional): Optional Step objects. Defaults to None.
            next_steps (list[NextStep], optional): A list of NextStep objects for the Step object. Defaults to None.
            start (str, optional): Optional UID of the starting Step. Defaults to None.
            accumulated_risk (float, optional): The amount of risk that the execution of this Workflow has
                accrued. Defaults to 0.0.
        """
        ExecutionElement.__init__(self, uid)
        self.name = name
        self.steps = {step.uid: step for step in steps} if steps is not None else {}

        self.next_steps = {}
        if steps:
            for step in steps:
                self.next_steps[step.uid] = []

        if next_steps:
            for next_step in next_steps:
                if next_step.source_uid in self.next_steps:
                    self.next_steps[next_step.source_uid].append(next_step)

        self.start = start if start is not None else 'start'
        self.accumulated_risk = accumulated_risk

        self._total_risk = float(sum([step.risk for step in self.steps.values() if step.risk > 0]))
        self._is_paused = False
        self._accumulator = {}
        self._execution_uid = 'default'

    def create_step(self, name='', action='', app='', device='', arguments=None, risk=0):
        """Creates a new Step object and adds it to the Workflow's list of Steps.
        
        Args:
            name (str, optional): The name of the Step object. Defaults to an empty string.
            action (str, optional): The name of the action associated with a Step. Defaults to an empty string.
            app (str, optional): The name of the app associated with the Step. Defaults to an empty string.
            device (str, optional): The name of the device associated with the app associated with the Step. Defaults
                to an empty string.
            arguments (list[Argument]): A list of Argument objects that are parameters to the step execution. Defaults
                to None.
            risk (int, optional): The risk associated with the Step. Defaults to 0.
            
        """
        arguments = arguments if arguments is not None else []
        step = Step(name=name, action=action, app=app, device_id=device, arguments=arguments, risk=risk)
        self.steps[step.uid] = step
        self.next_steps[step.uid] = []
        self._total_risk += risk
        logger.info('Step added to workflow {0}. Step: {1}'.format(self.name, self.steps[step.uid].read()))

    def remove_step(self, uid):
        """Removes a Step object from the Workflow's list of Steps given the Step name.
        
        Args:
            uid (str): The UID of the Step object to be removed.
            
        Returns:
            True on success, False otherwise.
        """
        if uid in self.steps:
            self.steps.pop(uid)

            self.next_steps.pop(uid)
            for step in self.next_steps.keys():
                for next_step in list(self.next_steps[step]):
                    if next_step.destination_uid == uid:
                        self.next_steps[step].remove(next_step)

            logger.debug('Removed step {0} from workflow {1}'.format(uid, self.name))
            return True
        logger.warning('Could not remove step {0} from workflow {1}. Step does not exist'.format(uid, self.name))
        return False

    def pause(self):
        """Pauses the execution of the Workflow. The Workflow will pause execution before starting the next Step.
        """
        self._is_paused = True
        logger.info('Pausing workflow {0}'.format(self.name))

    def resume(self):
        """Resumes a Workflow that has previously been paused.
        """
        try:
            logger.info('Attempting to resume workflow {0}'.format(self.name))
            self._is_paused = False
        except (StopIteration, AttributeError) as e:
            logger.warning('Cannot resume workflow {0}. Reason: {1}'.format(self.name, format_exception_message(e)))
            pass

    def execute(self, execution_uid, start=None, start_arguments=''):
        """Executes a Workflow by executing all Steps in the Workflow list of Step objects.

        Args:
            execution_uid (str): The UUID4 hex string uniquely identifying this workflow instance
            start (str, optional): The name of the first Step. Defaults to None.
            start_arguments (list[Argument]): Argument paramaters into the first Step. Defaults to None.
        """
        self._execution_uid = execution_uid
        logger.info('Executing workflow {0}'.format(self.name))
        data_sent.send(self, callback_name="Workflow Execution Start", object_type="Workflow")
        start = start if start is not None else self.start
        executor = self.__execute(start, start_arguments)
        next(executor)

    def __execute(self, start, start_arguments):
        instances = {}
        total_steps = []
        steps = self.__steps(start=start)
        first = True
        for step in (step_ for step_ in steps if step_ is not None):
            self._executing_step = step
            logger.debug('Executing step {0} of workflow {1}'.format(step, self.name))
            data_sent.send(self, callback_name="Next Step Found", object_type="Workflow")

            if self._is_paused:
                data_sent.send(self, callback_name="Workflow Paused", object_type="Workflow")
                while self._is_paused:
                    gevent.sleep(1)
                    continue
                data_sent.send(self, callback_name="Workflow Resumed", object_type="Workflow")

            device_id = self.__setup_app_instance(instances, step)
            step.render_step(steps=total_steps)

            if first:
                first = False
                if start_arguments:
                    self.__swap_step_arguments(step, start_arguments)
            self.__execute_step(step, instances[device_id])
            total_steps.append(step)
            self._accumulator[step.uid] = step.get_output().result
        self.__shutdown(instances)
        yield

    def __setup_app_instance(self, instances, step):
        device_id = (step.app, step.device_id)
        if device_id not in instances:
            instances[device_id] = AppInstance.create(step.app, step.device_id)
            data_sent.send(self, callback_name="App Instance Created", object_type="Workflow")
            logger.debug('Created new app instance: App {0}, device {1}'.format(step.app, step.device_id))
        return device_id

    def send_data_to_step(self, data):
        """Sends data to a Step if it has triggers associated with it, and is currently awaiting data

        Args:
            data (dict): The data to send to the triggers. This dict has two keys: 'data_in' which is the data
                to be sent to the triggers, and 'arguments', which is an optional parameter to change the arguments to
                the current Step
        """
        self._executing_step.send_data_to_trigger(data)

    def __steps(self, start):
        initial_step_uid = start
        current_uid = initial_step_uid
        current_step = self.steps[current_uid] if self.steps else None
        while current_step:
            yield current_step
            next_step_uid = self.get_next_step(current_step, self._accumulator)
            current_uid = self.__go_to_next_step(next_step_uid)
            current_step = self.steps[current_uid] if current_uid is not None else None
            yield  # needed so that when for-loop calls next() it doesn't advance too far
        yield  # needed so you can avoid catching StopIteration exception

    def get_next_step(self, current_step, accumulator):
        if self.next_steps:
            for next_step in sorted(self.next_steps[current_step.uid]):
                next_step = next_step.execute(current_step.get_output(), accumulator)
                if next_step is not None:
                    return next_step
        else:
            return None

    def __go_to_next_step(self, next_step_uid):
        if next_step_uid not in self.steps:
            current = None
        else:
            current = next_step_uid
        return current

    def __swap_step_arguments(self, step, start_arguments):
        logger.debug('Swapping arguments to first step of workflow {0}'.format(self.name))
        try:
            step.set_arguments(start_arguments)
            data_sent.send(self, callback_name="Workflow Arguments Validated", object_type="Workflow")
        except InvalidArgument as e:
            logger.error('Cannot change arguments to workflow {0}. '
                         'Invalid arguments. Error: {1}'.format(self.name, format_exception_message(e)))
            data_sent.send(self, callback_name="Workflow Arguments Invalid", object_type="Workflow")

    def __execute_step(self, step, instance):
        data = {"app": step.app,
                "action": step.action,
                "name": step.name,
                "arguments": JsonElementReader.read(step.arguments)}
        try:
            step.execute(instance=instance(), accumulator=self._accumulator)
            data['result'] = step.get_output().as_json() if step.get_output() is not None else None
            data['execution_uid'] = step.get_execution_uid()
            data_sent.send(self, callback_name="Step Execution Success", object_type="Workflow", data=data)
        except Exception as e:
            data['result'] = step.get_output().as_json() if step.get_output() is not None else None
            data['execution_uid'] = step.get_execution_uid()
            data_sent.send(self, callback_name="Step Execution Error", object_type="Workflow", data=data)
            if self._total_risk > 0:
                self.accumulated_risk += float(step.risk) / self._total_risk
            logger.debug('Step {0} of workflow {1} executed with error {2}'.format(step, self.name,
                                                                                   format_exception_message(e)))

    def __shutdown(self, instances):
        # Upon finishing shuts down instances
        for instance_name, instance in instances.items():
            try:
                if instance() is not None:
                    logger.debug('Shutting down app instance: Device: {0}'.format(instance_name))
                    instance.shutdown()
            except Exception as e:
                logger.error('Error caught while shutting down app instance. '
                             'Device: {0}. Error {1}'.format(instance_name, format_exception_message(e)))
        result_str = {}
        for step, step_result in self._accumulator.items():
            try:
                result_str[step] = json.dumps(step_result)
            except TypeError:
                logger.error('Result of workflow is neither string or a JSON-able. Cannot record')
                result_str[step] = 'error: could not convert to JSON'
        data = dict(self._accumulator)
        try:
            data_json = json.dumps(data)
        except TypeError:
            data_json = str(data)
        data_sent.send(self, callback_name="Workflow Shutdown", object_type="Workflow", data=data_json)
        logger.info('Workflow {0} completed. Result: {1}'.format(self.name, self._accumulator))

    def update_from_json(self, json_in):
        """Reconstruct a Workflow object based on JSON data.

           Args:
               json_in (JSON dict): The JSON data to be parsed and reconstructed into a Workflow object.
        """

        # backup_steps = deepcopy(self.steps)
        backup_steps = self.strip_async_result(with_deepcopy=True)
        self.steps = {}
        if 'name' in json_in:
            self.name = json_in['name']
        uid = json_in['uid'] if 'uid' in json_in else self.uid
        try:
            if 'start' in json_in and json_in['start']:
                self.start = json_in['start']
            self.steps = {}
            self.uid = uid
            for step_json in json_in['steps']:
                step = Step.create(step_json)
                self.steps[step_json['uid']] = step
            if "next_steps" in json_in:
                next_steps = [NextStep.create(cond_json) for cond_json in json_in['next_steps']]
                self.next_steps = {}
                for next_step in next_steps:
                    if next_step.source_uid not in self.next_steps:
                        self.next_steps[next_step.source_uid] = []
                    self.next_steps[next_step.source_uid].append(next_step)
        except (UnknownApp, UnknownAppAction, InvalidArgument):
            self.reload_async_result(backup_steps, with_deepcopy=True)
            raise

    def regenerate_uids(self):
        start_step = deepcopy(self.steps.pop(self.start, None))
        if start_step is not None:
            start_step = deepcopy(start_step)
            super(Workflow, self).regenerate_uids()
            self.steps = {step.uid: step for step in self.steps.values()}
            start_step.regenerate_uids()
            self.start = start_step.uid
            self.steps[self.start] = start_step
        else:
            super(Workflow, self).regenerate_uids()

    def set_execution_uid(self, execution_uid):
        """Sets the execution UID for the Workflow

        Args:
            execution_uid (str): The execution UID
        """
        self._execution_uid = execution_uid

    def get_execution_uid(self):
        """Gets the execution UID for the Workflow

        Returns:
            The execution UID of the Workflow
        """
        return self._execution_uid

    def regenerate_uids(self):
        start_step = deepcopy(self.steps.pop(self.start, None))
        if start_step is not None:
            start_step = deepcopy(start_step)
            super(Workflow, self).regenerate_uids()
            self.steps = {step.uid: step for step in self.steps.values()}
            start_step.regenerate_uids()
            self.start = start_step.uid
            self.steps[self.start] = start_step
        else:
            super(Workflow, self).regenerate_uids()


    def strip_async_result(self, with_deepcopy=False):
        """Removes the AsyncResult object from all of the Steps, necessary to deepcopy a Workflow

        Args:
            with_deepcopy (bool, optional): Whether or not to deepcopy the Step, or just return the AsyncResult.
                Defaults to False.

        Returns:
            A dict of step_uid: async_result, or step_uid to (step, async_result)
        """
        steps = {}
        for step in self.steps.values():
            async_result = step._incoming_data
            step._incoming_data = None
            if with_deepcopy:
                steps[step.uid] = (deepcopy(step), async_result)
            else:
                steps[step.uid] = async_result
        return steps

    def reload_async_result(self, steps, with_deepcopy=False):
        """Reloads the AsyncResult object for all of the Steps, necessary to restore a Workflow

        Args:
            steps (dict): A dict of step_uid: async_result, or step_uid to (step, async_result)
            with_deepcopy (bool, optional): Whether or not the Step was deepcopied (i.e. what format the steps dict
                is in). Defaults to False
        """
        if with_deepcopy:
            for step in steps.values():
                step_obj = step[0]
                step_obj._incoming_data = step[1]
                self.steps[step_obj.name] = step_obj
        else:
            for step in self.steps.values():
                step._incoming_data = steps[step.uid]

    def reset_async_result(self):
        """Reinitialize an AsyncResult object for all of the Steps when a Workflow is copied
        """
        from gevent.event import AsyncResult
        for step in self.steps.values():
            step._incoming_data = AsyncResult()
