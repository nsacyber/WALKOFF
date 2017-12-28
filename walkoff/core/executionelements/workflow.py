import json
import logging
import threading
from copy import deepcopy

from walkoff.appgateway.appinstance import AppInstance
from walkoff.events import WalkoffEvent
from walkoff.core.executionelements.action import Action
from walkoff.core.executionelements.branch import Branch
from walkoff.core.executionelements.executionelement import ExecutionElement
from walkoff.core.helpers import UnknownAppAction, UnknownApp, InvalidArgument, format_exception_message

logger = logging.getLogger(__name__)


class Workflow(ExecutionElement):
    def __init__(self, name='', uid=None, actions=None, branches=None, start=None):
        """Initializes a Workflow object. A Workflow falls under a Playbook, and has many associated Actions
            within it that get executed.
            
        Args:
            name (str, optional): The name of the Workflow object. Defaults to an empty string.
            uid (str, optional): Optional UID to pass in for the workflow. Defaults to uuid.uuid4().
            actions (dict, optional): Optional Action objects. Defaults to None.
            branches (list[Branch], optional): A list of Branch objects for the Action object. Defaults to None.
            start (str, optional): Optional UID of the starting Action. Defaults to None.
        """
        ExecutionElement.__init__(self, uid)
        self.name = name
        self.actions = {action.uid: action for action in actions} if actions is not None else {}

        self.branches = {}
        if actions:
            for action in actions:
                self.branches[action.uid] = []

        if branches:
            for branch in branches:
                if branch.source_uid in self.branches:
                    self.branches[branch.source_uid].append(branch)

        self.start = start if start is not None else 'start'

        self._is_paused = False
        self._resume = threading.Event()
        self._accumulator = {}
        self._execution_uid = 'default'

    def create_action(self, name='', action='', app='', device='', arguments=None, risk=0):
        """Creates a new Action object and adds it to the Workflow's list of Actions.
        
        Args:
            name (str, optional): The name of the Action object. Defaults to an empty string.
            action (str, optional): The name of the action associated with a Action. Defaults to an empty string.
            app (str, optional): The name of the app associated with the Action. Defaults to an empty string.
            device (str, optional): The name of the device associated with the app associated with the Action. Defaults
                to an empty string.
            arguments (list[Argument]): A list of Argument objects that are parameters to the action execution. Defaults
                to None.
            risk (int, optional): The risk associated with the Action. Defaults to 0.
            
        """
        arguments = arguments if arguments is not None else []
        action = Action(name=name, action_name=action, app_name=app, device_id=device, arguments=arguments, risk=risk)
        self.actions[action.uid] = action
        self.branches[action.uid] = []
        self._total_risk += risk
        logger.info('Action added to workflow {0}. Action: {1}'.format(self.name, self.actions[action.uid].read()))

    def remove_action(self, uid):
        """Removes a Action object from the Workflow's list of Actions given the Action UID.
        
        Args:
            uid (str): The UID of the Action object to be removed.
            
        Returns:
            True on success, False otherwise.
        """
        if uid in self.actions:
            self.actions.pop(uid)

            self.branches.pop(uid)
            for action in self.branches.keys():
                for branch in list(self.branches[action]):
                    if branch.destination_uid == uid:
                        self.branches[action].remove(branch)

            logger.debug('Removed action {0} from workflow {1}'.format(uid, self.name))
            return True
        logger.warning('Could not remove action {0} from workflow {1}. Action does not exist'.format(uid, self.name))
        return False

    def pause(self):
        """Pauses the execution of the Workflow. The Workflow will pause execution before starting the next Action.
        """
        self._is_paused = True
        logger.info('Pausing workflow {0}'.format(self.name))

    def resume(self):
        """Resumes a Workflow that has previously been paused.
        """
        try:
            logger.info('Attempting to resume workflow {0}'.format(self.name))
            self._is_paused = False
            self._resume.set()
        except (StopIteration, AttributeError) as e:
            logger.warning('Cannot resume workflow {0}. Reason: {1}'.format(self.name, format_exception_message(e)))
            pass

    def execute(self, execution_uid, start=None, start_arguments=None):
        """Executes a Workflow by executing all Actions in the Workflow list of Action objects.

        Args:
            execution_uid (str): The UUID4 hex string uniquely identifying this workflow instance
            start (str, optional): The name of the first Action. Defaults to None.
            start_arguments (list[Argument]): Argument parameters into the first Action. Defaults to None.
        """
        self._execution_uid = execution_uid
        logger.info('Executing workflow {0}'.format(self.name))
        WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.WorkflowExecutionStart)
        start = start if start is not None else self.start
        executor = self.__execute(start, start_arguments)
        next(executor)

    def __execute(self, start, start_arguments):
        instances = {}
        total_actions = []
        actions = self.__actions(start=start)
        first = True
        for action in (action_ for action_ in actions if action_ is not None):
            self._executing_action = action
            logger.debug('Executing action {0} of workflow {1}'.format(action, self.name))
            if self._is_paused:
                WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.WorkflowPaused)
                self._resume.wait()
                self._resume.clear()
                WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.WorkflowResumed)

            device_id = self.__setup_app_instance(instances, action)
            action.render_action(actions=total_actions)

            if first:
                first = False
                if start_arguments:
                    self.__swap_action_arguments(action, start_arguments)
            action.execute(instance=instances[device_id](), accumulator=self._accumulator)
            self._accumulator[action.uid] = action.get_output().result
            total_actions.append(action)
        self.__shutdown(instances)
        yield

    def __setup_app_instance(self, instances, action):
        device_id = (action.app_name, action.device_id)
        if device_id not in instances:
            instances[device_id] = AppInstance.create(action.app_name, action.device_id)
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.AppInstanceCreated)
            logger.debug('Created new app instance: App {0}, device {1}'.format(action.app_name, action.device_id))
        return device_id

    def send_data_to_action(self, data):
        """Sends data to an Action if it has triggers associated with it, and is currently awaiting data

        Args:
            data (dict): The data to send to the triggers. This dict has two keys: 'data_in' which is the data
                to be sent to the triggers, and 'arguments', which is an optional parameter to change the arguments to
                the current Action
        """
        self._executing_action.send_data_to_trigger(data)

    def __actions(self, start):
        initial_action_uid = start
        current_uid = initial_action_uid
        current_action = self.actions[current_uid] if self.actions else None
        while current_action:
            yield current_action
            branch_uid = self.get_branch(current_action, self._accumulator)
            current_uid = self.__go_to_branch(branch_uid)
            current_action = self.actions[current_uid] if current_uid is not None else None
            yield  # needed so that when for-loop calls next() it doesn't advance too far
        yield  # needed so you can avoid catching StopIteration exception

    def get_branch(self, current_action, accumulator):
        """Executes the Branch objects associated with this Workflow to determine which Action should be
            executed next.

        Args:
            current_action(Action): The current action that has just finished executing.
            accumulator (dict): The accumulated results of previous Actions.

        Returns:
            The UID of the next Action to be executed if successful, else None.
        """
        if self.branches:
            for branch in sorted(self.branches[current_action.uid]):
                # TODO: This here is the only hold up from getting rid of action._output.
                # Keep whole result in accumulator
                branch = branch.execute(current_action.get_output(), accumulator)
                if branch is not None:
                    return branch
        else:
            return None

    def __go_to_branch(self, branch_uid):
        if branch_uid not in self.actions:
            current = None
        else:
            current = branch_uid
        return current

    def __swap_action_arguments(self, action, start_arguments):
        logger.debug('Swapping arguments to first action of workflow {0}'.format(self.name))
        try:
            action.set_arguments(start_arguments)
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.WorkflowArgumentsValidated)
        except InvalidArgument as e:
            logger.error('Cannot change arguments to workflow {0}. '
                         'Invalid arguments. Error: {1}'.format(self.name, format_exception_message(e)))
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.WorkflowArgumentsInvalid)

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
        for action, action_result in self._accumulator.items():
            try:
                result_str[action] = json.dumps(action_result)
            except TypeError:
                logger.error('Result of workflow is neither string or a JSON-able. Cannot record')
                result_str[action] = 'error: could not convert to JSON'
        data = dict(self._accumulator)
        try:
            data_json = json.dumps(data)
        except TypeError:
            data_json = str(data)
        WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.WorkflowShutdown, data=data_json)
        logger.info('Workflow {0} completed. Result: {1}'.format(self.name, self._accumulator))

    def update_from_json(self, json_in):
        """Reconstruct a Workflow object based on JSON data.

           Args:
               json_in (JSON dict): The JSON data to be parsed and reconstructed into a Workflow object.
        """

        backup_actions = self.deepcopy_actions_with_events()
        backup_branches = deepcopy(self.branches)
        self.actions = {}
        if 'name' in json_in:
            self.name = json_in['name']
        uid = json_in['uid'] if 'uid' in json_in else self.uid
        try:
            if 'start' in json_in and json_in['start']:
                self.start = json_in['start']
            self.actions = {}
            self.uid = uid
            for action_json in json_in['actions']:
                action = Action.create(action_json)
                self.actions[action_json['uid']] = action
            if "branches" in json_in:
                branches = [Branch.create(cond_json) for cond_json in json_in['branches']]
                self.branches = {}
                for branch in branches:
                    if branch.source_uid not in self.branches:
                        self.branches[branch.source_uid] = []
                    self.branches[branch.source_uid].append(branch)
        except (UnknownApp, UnknownAppAction, InvalidArgument):
            self.restore_actions_and_events(backup_actions)
            self.branches = backup_branches
            raise

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
        start_action = deepcopy(self.actions.pop(self.start, None))
        if start_action is not None:
            start_action = deepcopy(start_action)
            super(Workflow, self).regenerate_uids()
            self.actions = {action.uid: action for action in self.actions.values()}
            start_action.regenerate_uids()
            self.start = start_action.uid
            self.actions[self.start] = start_action
        else:
            super(Workflow, self).regenerate_uids()

    def deepcopy_actions_with_events(self):
        """Makes a deepcopy of all actions, including their event objects

        Returns:
            A dict of action_uid: (action, event)
        """
        actions = {}
        for action in self.actions.values():
            event = action._event
            action._event = None
            actions[action.uid] = (deepcopy(action), event)
        return actions

    def restore_actions_and_events(self, backup_actions):
        """Restores all actions that were previously deepcopied

        Args:
            backup_actions (dict): The actions to be restored
        """
        self.actions = {}
        for action, event in backup_actions.values():
            action.event = event
            self.actions[action.uid] = action

    def strip_events(self):
        """Removes the Event object from all of the Actions and the Workflow, necessary to do a deepcopy
        """
        for action in self.actions.values():
            action._event = None
        self._resume = None

    def reset_event(self):
        """Reinitialize an Event object for all of the Actions and the Workflow when a Workflow is copied
        """
        from threading import Event
        for action in self.actions.values():
            action._event = Event()
        self._resume = Event()
