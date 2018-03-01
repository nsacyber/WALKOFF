import logging

from sqlalchemy import Column, ForeignKey, String, orm, Boolean
from sqlalchemy.orm import relationship, backref
from sqlalchemy_utils import UUIDType

from walkoff import executiondb
from walkoff.appgateway import get_condition
from walkoff.executiondb.argument import Argument
from walkoff.events import WalkoffEvent
from walkoff.executiondb.executionelement import ExecutionElement
from walkoff.helpers import get_condition_api, InvalidArgument, format_exception_message, split_api_params
from walkoff.appgateway.validator import validate_condition_parameters

logger = logging.getLogger(__name__)


class Condition(ExecutionElement, executiondb.Device_Base):
    __tablename__ = 'condition'
    _conditional_expression_id = Column(UUIDType(binary=False), ForeignKey('conditional_expression.id'))
    app_name = Column(String(80), nullable=False)
    action_name = Column(String(80), nullable=False)
    is_negated = Column(Boolean, default=False)
    arguments = relationship('Argument', backref=backref('_condition'), cascade='all, delete, delete-orphan')
    transforms = relationship('Transform', backref=backref('_condition'), cascade='all, delete-orphan')

    def __init__(self, app_name, action_name, id=None, is_negated=False, arguments=None, transforms=None):
        """Initializes a new Condition object.

        Args:
            app_name (str): The name of the app which contains this condition
            action_name (str): The action name for the Condition. Defaults to an empty string.
            id (str|UUID, optional): Optional UUID to pass into the Condition. Must be UUID object or valid UUID string.
                Defaults to None.
            is_negated (bool, optional): Should the result of the condition be inverted? Defaults to False.
            arguments (list[Argument], optional): Dictionary of Argument keys to Argument values.
                This dictionary will be converted to a dictionary of str:Argument. Defaults to None.
            transforms(list[Transform], optional): A list of Transform objects for the Condition object.
                Defaults to None.
        """
        ExecutionElement.__init__(self, id)
        self.app_name = app_name
        self.action_name = action_name
        self.is_negated = is_negated
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
        """Loads all necessary fields upon Condition being loaded from database"""
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
            print(self._data_param_name)
            print([argument.read() for argument in self.arguments])
            arguments = self.__update_arguments_with_data(data)
            print([argument.read() for argument in arguments])
            args = validate_condition_parameters(self._api, arguments, self.action_name, accumulator=accumulator)
            logger.debug('Arguments passed to condition {} are valid'.format(self.id))
            ret = self._condition_executable(**args)
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.ConditionSuccess)
            if self.is_negated:
                return not ret
            else:
                return ret
        except InvalidArgument as e:
            logger.error('Condition {0} has invalid input {1} which was converted to {2}. Error: {3}. '
                         'Returning False'.format(self.action_name, data_in, data, format_exception_message(e)))
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.ConditionError)
            raise
        except Exception as e:
            logger.error('Error encountered executing '
                         'condition {0} with arguments {1} and value {2}: '
                         'Error {3}. Returning False'.format(self.action_name, arguments, data,
                                                             format_exception_message(e)))
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.ConditionError)
            raise

    def __update_arguments_with_data(self, data):
        arguments = []
        for argument in self.arguments:
            if argument.name != self._data_param_name:
                arguments.append(argument)
        arguments.append(Argument(self._data_param_name, value=data))
        return arguments
