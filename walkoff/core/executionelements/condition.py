import logging

from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship, backref

from walkoff.appgateway import get_condition
from walkoff.core.argument import Argument
from walkoff.devicedb import Device_Base
from walkoff.events import WalkoffEvent
from walkoff.core.executionelements.executionelement import ExecutionElement
from walkoff.helpers import get_condition_api, InvalidArgument, format_exception_message, split_api_params
from walkoff.appgateway.validator import validate_condition_parameters

logger = logging.getLogger(__name__)


class Condition(ExecutionElement, Device_Base):
    __tablename__ = 'condition'
    id = Column(Integer, primary_key=True, autoincrement=True)
    action_id = Column(Integer, ForeignKey('action.id'))
    branch_id = Column(Integer, ForeignKey('branch.id'))
    app_name = Column(String(80), nullable=False)
    action_name = Column(String(80), nullable=False)
    arguments = relationship('Argument', backref=backref('condition'), cascade='all, delete-orphan')
    transforms = relationship('Transform', backref=backref('condition'), cascade='all, delete-orphan')

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

        # TODO: Reset variables
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
            self.__update_arguments(data)
            args = validate_condition_parameters(self._api, self.arguments, self.action_name, accumulator=accumulator)
            logger.debug('Arguments passed to condition {} are valid'.format(self.uid))
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

    def __update_arguments(self, data):
        arg = None
        for argument in self.arguments:
            if argument.name == self._data_param_name:
                arg = None
        self.arguments.remove(arg)
        self.arguments.append(Argument(self._data_param_name, value=data))
