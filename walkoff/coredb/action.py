import json
import logging
import threading
import uuid

from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, orm
from sqlalchemy.orm import relationship, backref

import walkoff.config.config
from walkoff.appgateway import get_app_action, is_app_action_bound
from walkoff.core import contextdecorator
from walkoff.coredb.argument import Argument
from walkoff.core.actionresult import ActionResult
from walkoff.coredb import Device_Base
from walkoff.coredb.type_decorators import Json
from walkoff.events import WalkoffEvent
from walkoff.coredb.executionelement import ExecutionElement
from walkoff.helpers import get_app_action_api, InvalidArgument, format_exception_message, InvalidExecutionElement, \
    UnknownApp, UnknownCondition, UnknownTransform
from walkoff.appgateway.validator import validate_app_action_parameters
import walkoff.coredb.devicedb
from walkoff.coredb.condition import Condition

logger = logging.getLogger(__name__)


class Action(ExecutionElement, Device_Base):
    _templatable = True

    __tablename__ = 'action'
    id = Column(Integer, primary_key=True, autoincrement=True)
    _workflow_id = Column(Integer, ForeignKey('workflow.id'))
    app_name = Column(String(80), nullable=False)
    action_name = Column(String(80), nullable=False)
    name = Column(String(80))
    device_id = Column(Integer)
    arguments = relationship('Argument', backref=backref('_action'), cascade='all, delete-orphan')
    triggers = relationship('Condition', backref=backref('_action'), cascade='all, delete-orphan')
    x_coordinate = Column(Integer)
    y_coordinate = Column(Integer)
    templated = Column(Boolean)
    raw_representation = Column(Json)

    def __init__(self, app_name, action_name, name, device_id=None, arguments=None, triggers=None,
                 x_coordinate=None, y_coordinate=None, templated=False, raw_representation=None):
        """Initializes a new Action object. A Workflow has many actions that it executes.

        Args:
            app_name (str): The name of the app associated with the Action
            action_name (str): The name of the action associated with a Action
            name (str): The name of the Action object.
            device_id (int, optional): The id of the device associated with the app associated with the Action. Defaults
                to None.
            arguments (list[Argument], optional): A list of Argument objects that are parameters to the action.
                Defaults to None.
            triggers (list[Condition], optional): A list of Condition objects for the Action. If a Action should wait
                for data before continuing, then include these Trigger objects in the Action init. Defaults to None.
            x_coordinate(int, optional): X coordinate of the Action object, used for UI display purposes. Defaults
                to None.
            y_coordinate(int, optional): Y coordinate of the Action object, used for UI display purposes. Defaults
                to None.
            templated (bool, optional): Whether or not the Action is templated. Used for Jinja templating.
            raw_representation (dict, optional): JSON representation of this object. Used for Jinja templating.
        """
        ExecutionElement.__init__(self)

        self.triggers = []
        if triggers:
            for trigger in triggers:
                self.triggers.append(trigger)

        self.name = name
        self.device_id = device_id
        self.app_name = app_name
        self.action_name = action_name

        self._run, self._arguments_api = get_app_action_api(self.app_name, self.action_name)
        if is_app_action_bound(self.app_name, self._run) and not self.device_id:
            raise InvalidArgument(
                "Cannot initialize Action {}. App action is bound but no device ID was provided.".format(self.name))

        self.templated = templated
        if not self.templated:
            validate_app_action_parameters(self._arguments_api, arguments, self.app_name, self.action_name)

        self.arguments = []
        if arguments:
            self.arguments = arguments

        self.x_coordinate = x_coordinate
        self.y_coordinate = y_coordinate

        self.raw_representation = raw_representation if raw_representation is not None else {}

        self._incoming_data = None
        self._event = threading.Event()
        self._output = None
        self._execution_uid = 'default'
        self._action_executable = get_app_action(self.app_name, self._run)

    @orm.reconstructor
    def init_on_load(self):
        self._run, self._arguments_api = get_app_action_api(self.app_name, self.action_name)
        self._incoming_data = None
        self._event = threading.Event()
        self._output = None
        self._action_executable = get_app_action(self.app_name, self._run)
        self._execution_uid = 'default'

    def get_output(self):
        """Gets the output of an Action (the result)

        Returns:
            The result of the Action
        """
        return self._output

    def get_execution_uid(self):
        """Gets the execution UID of the Action

        Returns:
            The execution UID
        """
        return self._execution_uid

    def send_data_to_trigger(self, data):
        """Sends data to the Action if it has triggers associated with it, and is currently awaiting data

        Args:
            data (dict): The data to send to the triggers. This dict has two keys: 'data_in' which is the data
                to be sent to the triggers, and 'arguments', which is an optional parameter to change the arguments
                to the current Action
        """
        self._incoming_data = data
        self._event.set()

    def _update_json(self, updated_json):
        self.app_name = updated_json['app_name']
        self.action_name = updated_json['action_name']
        self.device_id = updated_json['device_id'] if 'device_id' in updated_json else None
        arguments = []
        if 'arguments' in updated_json:
            for argument_json in updated_json['arguments']:
                argument = Argument(**argument_json)
                arguments.append(argument)
        if arguments is not None:
            if not self.templated:
                validate_app_action_parameters(self._arguments_api, arguments, self.app_name, self.action_name)
        else:
            validate_app_action_parameters(self._arguments_api, [], self.app_name, self.action_name)
        self.arguments = arguments

    @contextdecorator.context
    def render_action(self, **kwargs):
        """Uses JINJA templating to render a Action object.

        Args:
            kwargs (dict[str]): Arguments to use in the JINJA templating.
        """
        if self.templated:
            from jinja2 import Environment
            env = Environment().from_string(json.dumps(self.raw_representation)).render(
                walkoff.config.config.JINJA_GLOBALS, **kwargs)
            self._update_json(updated_json=json.loads(env))

    def set_arguments(self, new_arguments):
        """Updates the arguments for an Action object.

        Args:
            new_arguments ([Argument]): The new Arguments for the Action object.
        """
        validate_app_action_parameters(self._arguments_api, new_arguments, self.app_name, self.action_name)
        self.arguments = new_arguments

    def execute(self, instance, accumulator):
        """Executes an Action by calling the associated app function.

        Args:
            instance (App): The instance of an App object to be used to execute the associated function.
            accumulator (dict): Dict containing the results of the previous actions

        Returns:
            The result of the executed function.
        """
        self._execution_uid = str(uuid.uuid4())

        WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.ActionStarted)

        if self.triggers:
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.TriggerActionAwaitingData)
            logger.debug('Trigger Action {} is awaiting data'.format(self.name))
            self._wait_for_trigger(accumulator)

        try:
            args = validate_app_action_parameters(self._arguments_api, self.arguments, self.app_name, self.action_name,
                                                  accumulator=accumulator)
            if is_app_action_bound(self.app_name, self._run):
                result = self._action_executable(instance, **args)
            else:
                result = self._action_executable(**args)
            result.set_default_status(self.app_name, self.action_name)
            if result.is_failure(self.app_name, self.action_name):
                WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.ActionExecutionError,
                                                       data=result.as_json())
            else:
                WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.ActionExecutionSuccess,
                                                       data=result.as_json())
        except Exception as e:
            self.__handle_execution_error(e)
        else:
            self._output = result
            logger.debug(
                'Action {0}-{1} (id {2}) executed successfully'.format(self.app_name, self.action_name, self.id))
            return result

    def __handle_execution_error(self, e):
        formatted_error = format_exception_message(e)
        if isinstance(e, InvalidArgument):
            event = WalkoffEvent.ActionArgumentsInvalid
            return_type = 'InvalidArguments'
        else:
            event = WalkoffEvent.ActionExecutionError
            return_type = 'UnhandledException'
        logger.error('Error calling action {0}. Error: {1}'.format(self.name, formatted_error))
        self._output = ActionResult('error: {0}'.format(formatted_error), return_type)
        WalkoffEvent.CommonWorkflowSignal.send(self, event=event, data=self._output.as_json())

    def _wait_for_trigger(self, accumulator):
        while True:
            self._event.wait()
            if self._incoming_data is None:
                continue
            data = self._incoming_data
            data_in = data['data_in']
            self._incoming_data = None
            self._event.clear()

            if all(trigger.execute(data_in=data_in, accumulator=accumulator) for trigger in self.triggers):
                self.__accept_trigger(accumulator, data, data_in)
                break
            else:
                logger.debug('Trigger is not valid for input {0}'.format(data_in))
                WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.TriggerActionNotTaken)

    def __accept_trigger(self, accumulator, data, data_in):
        WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.TriggerActionTaken)
        logger.debug('Trigger is valid for input {0}'.format(data_in))
        accumulator[self.name] = data_in
        arguments = data['arguments'] if 'arguments' in data else []
        if arguments:
            for argument in arguments:
                check_arg = self.__get_argument_by_name(argument.name)
                if check_arg:
                    self.arguments.remove(check_arg)
                self.arguments.append(argument)

    def __get_argument_by_name(self, name):
        for argument in self.arguments:
            if argument.name == name:
                return argument
        return None

    def __get_argument_by_id(self, argument_id):
        for argument in self.arguments:
            if argument.id == argument_id:
                return argument
        return None

    def __get_trigger_by_id(self, trigger_id):
        for trigger in self.triggers:
            if trigger.id == trigger_id:
                return trigger
        return None

    # def update(self, data):
    #     self.app_name = data['app_name']
    #     self.action_name = data['action_name']
    #     self.name = data['name']
    #     self.device_id = data['device_id'] if 'device_id' in data else self.device_id
    #     self.x_coordinate = data['x_coordinate'] if 'x_coordinate' in data else self.x_coordinate
    #     self.y_coordinate = data['y_coordinate'] if 'y_coordinate' in data else self.y_coordinate
    #
    #     self._run, self._arguments_api = get_app_action_api(self.app_name, self.action_name)
    #     if is_app_action_bound(self.app_name, self._run) and not self.device_id:
    #         raise InvalidExecutionElement(self.id, self.name, "App action is bound but no device ID was provided.")
    #
    #     if 'arguments' in data and data['arguments']:
    #         self.update_arguments(data['arguments'])
    #     else:
    #         self.arguments[:] = []
    #
    #     if not self.templated:
    #         try:
    #             validate_app_action_parameters(self._arguments_api, self.arguments, self.app_name, self.action_name)
    #         except InvalidArgument:
    #             raise InvalidExecutionElement(self.id, self.name, "Invalid Action Arguments")
    #
    #     if 'triggers' in data and data['triggers']:
    #         self.update_triggers(data['triggers'])
    #     else:
    #         self.triggers[:] = []
    #
    # def update_arguments(self, arguments):
    #     arguments_seen = []
    #     for argument in arguments:
    #         if 'id' in argument and argument['id']:
    #             argument_obj = self.__get_argument_by_id(argument['id'])
    #
    #             if argument_obj is None:
    #                 raise InvalidExecutionElement(argument['id'], argument['name'], "Invalid Argument ID")
    #
    #             argument_obj.update(argument)
    #             arguments_seen.append(argument_obj.id)
    #         else:
    #             if 'id' in argument:
    #                 argument.pop('id')
    #
    #             try:
    #                 argument_obj = Argument(**argument)
    #             except (ValueError, InvalidArgument):
    #                 raise InvalidExecutionElement(argument['id'], argument['name'], "Invalid Argument construction")
    #
    #             self.arguments.append(argument_obj)
    #             walkoff.coredb.devicedb.device_db.session.add(argument_obj)
    #             walkoff.coredb.devicedb.device_db.session.flush()
    #
    #             arguments_seen.append(argument_obj.id)
    #
    #     for argument in self.arguments:
    #         if argument.id not in arguments_seen:
    #             walkoff.coredb.devicedb.device_db.session.delete(argument)
    #
    # def update_triggers(self, triggers):
    #     triggers_seen = []
    #     for trigger in triggers:
    #         if 'id' in trigger and trigger['id']:
    #             trigger_obj = self.__get_trigger_by_id(trigger['id'])
    #
    #             if trigger_obj is None:
    #                 raise InvalidExecutionElement(trigger['id'], None, "Invalid Trigger ID")
    #
    #             trigger_obj.update(trigger)
    #             triggers_seen.append(trigger_obj.id)
    #         else:
    #             if 'id' in trigger:
    #                 trigger.pop('id')
    #
    #             try:
    #                 trigger_obj = Condition(**trigger)
    #             except (ValueError, InvalidArgument, UnknownApp, UnknownCondition, UnknownTransform):
    #                 raise InvalidExecutionElement(trigger['id'], None, "Invalid Trigger construction")
    #
    #             self.arguments.append(trigger_obj)
    #             walkoff.coredb.devicedb.device_db.session.add(trigger_obj)
    #             walkoff.coredb.devicedb.device_db.session.flush()
    #
    #             triggers_seen.append(trigger_obj.id)
    #
    #     for trigger in self.triggers:
    #         if trigger.id not in triggers_seen:
    #             walkoff.coredb.devicedb.device_db.session.delete(trigger)
