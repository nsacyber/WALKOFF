import logging

from sqlalchemy import Column, Integer, ForeignKey, String, orm
from sqlalchemy.orm import relationship, backref

from walkoff.appgateway import get_condition
from walkoff.coredb.argument import Argument
from walkoff.coredb import Device_Base
from walkoff.events import WalkoffEvent
from walkoff.coredb.executionelement import ExecutionElement
from walkoff.helpers import get_condition_api, InvalidArgument, format_exception_message, split_api_params, \
    InvalidExecutionElement, UnknownApp, UnknownTransform, UnknownCondition
from walkoff.appgateway.validator import validate_condition_parameters
from walkoff.coredb.transform import Transform
import walkoff.coredb.devicedb

logger = logging.getLogger(__name__)


class Condition(ExecutionElement, Device_Base):
    __tablename__ = 'condition'
    id = Column(Integer, primary_key=True, autoincrement=True)
    _action_id = Column(Integer, ForeignKey('action.id'))
    _branch_id = Column(Integer, ForeignKey('branch.id'))
    app_name = Column(String(80), nullable=False)
    action_name = Column(String(80), nullable=False)
    arguments = relationship('Argument', backref=backref('_condition'), cascade='all, delete-orphan')
    transforms = relationship('Transform', backref=backref('_condition'), cascade='all, delete-orphan')

    def __init__(self, app_name, action_name, arguments=None, transforms=None):
        """Initializes a new Condition object.
        
        Args:
            app_name (str): The name of the app which contains this condition
            action_name (str): The action name for the Condition. Defaults to an empty string.
            arguments (list[Argument], optional): Dictionary of Argument keys to Argument values.
                This dictionary will be converted to a dictionary of str:Argument. Defaults to None.
            transforms(list[Transform], optional): A list of Transform objects for the Condition object.
                Defaults to None.
        """
        ExecutionElement.__init__(self)
        self.app_name = app_name
        self.action_name = action_name

        self._data_param_name, self._run, self._api = get_condition_api(self.app_name, self.action_name)
        tmp_api = split_api_params(self._api, self._data_param_name)
        validate_condition_parameters(tmp_api, arguments, self.action_name)

        self.arguments = []
        if arguments:
            self.arguments = arguments

        self.transforms = []
        if transforms:
            self.transforms = transforms

        self._condition_executable = get_condition(self.app_name, self._run)

    @orm.reconstructor
    def init_on_load(self):
        self._data_param_name, self._run, self._api = get_condition_api(self.app_name, self.action_name)
        self._condition_executable = get_condition(self.app_name, self._run)

    def execute(self, data_in, accumulator):
        """Executes the Condition object, determining if the Condition evaluates to True or False.

        Args:
            data_in (): The input to the Transform objects associated with this Condition.
            accumulator (dict): The accumulated data from previous Actions.

        Returns:
            True if the Condition evaluated to True, False otherwise
        """
        data = data_in

        for transform in self.transforms:
            data = transform.execute(data, accumulator)
        try:
            self.__update_arguments_with_data(data)
            args = validate_condition_parameters(self._api, self.arguments, self.action_name, accumulator=accumulator)
            logger.debug('Arguments passed to condition {} are valid'.format(self.id))
            ret = self._condition_executable(**args)
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.ConditionSuccess)
            return ret
        except InvalidArgument as e:
            logger.error('Condition {0} has invalid input {1} which was converted to {2}. Error: {3}. '
                         'Returning False'.format(self.action_name, data_in, data, format_exception_message(e)))
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.ConditionError)
            return False
        except Exception as e:
            logger.error('Error encountered executing '
                         'condition {0} with arguments {1} and value {2}: '
                         'Error {3}. Returning False'.format(self.action_name, self.arguments, data,
                                                             format_exception_message(e)))
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.ConditionError)
            return False

    def __update_arguments_with_data(self, data):
        arg = None
        for argument in self.arguments:
            if argument.name == self._data_param_name:
                arg = argument
                break
        if arg:
            self.arguments.remove(arg)
        self.arguments.append(Argument(self._data_param_name, value=data))
        walkoff.coredb.devicedb.device_db.session.commit()

    # def update(self, data):
    #     self.app_name = data['app_name']
    #     self.action_name = data['action_name']
    #
    #     if 'arguments' in data and data['arguments']:
    #         self.update_arguments(data['arguments'])
    #     else:
    #         self.arguments[:] = []
    #
    #     try:
    #         self._data_param_name, self._run, self._api = get_condition_api(self.app_name, self.action_name)
    #         tmp_api = split_api_params(self._api, self._data_param_name)
    #         validate_condition_parameters(tmp_api, self.arguments, self.action_name)
    #     except (UnknownApp, UnknownCondition, InvalidArgument):
    #         raise InvalidExecutionElement(self.id, None, "Invalid Condition construction")
    #
    #     if 'transforms' in data and data['transforms']:
    #         self.update_transforms(data['transforms'])
    #     else:
    #         self.transforms[:] = []
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
    # def update_transforms(self, transforms):
    #     transforms_seen = []
    #     for transform in transforms:
    #         if 'id' in transform and transform['id']:
    #             transform_obj = self.__get_transform_by_id(transform['id'])
    #
    #             if transform_obj is None:
    #                 raise InvalidExecutionElement(transform['id'], None, "Invalid Transform ID")
    #
    #             transform_obj.update(transform)
    #             transforms_seen.append(transform_obj.id)
    #         else:
    #             if 'id' in transform:
    #                 transform.pop('id')
    #
    #             try:
    #                 transform_obj = Transform(**transform)
    #             except (ValueError, InvalidArgument, UnknownApp, UnknownTransform):
    #                 raise InvalidExecutionElement(transform['id'], None, "Invalid Transform construction")
    #
    #             self.transforms.append(transform_obj)
    #             walkoff.coredb.devicedb.device_db.session.add(transform_obj)
    #             walkoff.coredb.devicedb.device_db.session.flush()
    #
    #             transforms_seen.append(transform_obj.id)
    #
    #     for transform in self.transforms:
    #         if transform.id not in transforms_seen:
    #             walkoff.coredb.devicedb.device_db.session.delete(transform)

    def __get_argument_by_id(self, argument_id):
        for argument in self.arguments:
            if argument.id == argument_id:
                return argument
        return None

    def __get_transform_by_id(self, transform_id):
        for transform in self.transforms:
            if transform.id == transform_id:
                return transform
        return None
