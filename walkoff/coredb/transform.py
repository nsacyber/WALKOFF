import logging
from copy import deepcopy

from sqlalchemy import Column, Integer, ForeignKey, String, orm
from sqlalchemy.orm import relationship, backref

from walkoff.appgateway import get_transform
from walkoff.coredb.argument import Argument
from walkoff.coredb import Device_Base
from walkoff.events import WalkoffEvent
from walkoff.coredb.executionelement import ExecutionElement
from walkoff.helpers import get_transform_api, InvalidArgument, split_api_params
from walkoff.appgateway.validator import validate_transform_parameters
import walkoff.coredb.devicedb

logger = logging.getLogger(__name__)


class Transform(ExecutionElement, Device_Base):
    __tablename__ = 'transform'
    id = Column(Integer, primary_key=True, autoincrement=True)
    _condition_id = Column(Integer, ForeignKey('condition.id'))
    app_name = Column(String(80), nullable=False)
    action_name = Column(String(80), nullable=False)
    arguments = relationship('Argument', backref=backref('_transform'), cascade='all, delete-orphan')

    def __init__(self, app_name, action_name, arguments=None):
        """Initializes a new Transform object. A Transform is used to transform input into a workflow.
        
        Args:
            app_name (str): The app name associated with this transform
            action_name (str): The action name for the transform.
            arguments (list[Argument], optional): Dictionary of Argument keys to Argument values.
                This dictionary will be converted to a dictionary of str:Argument. Defaults to None.
        """
        ExecutionElement.__init__(self)
        self.app_name = app_name
        self.action_name = action_name

        self._data_param_name, self._run, self._api = get_transform_api(self.app_name, self.action_name)
        self._transform_executable = get_transform(self.app_name, self._run)
        tmp_api = split_api_params(self._api, self._data_param_name)
        validate_transform_parameters(tmp_api, arguments, self.action_name)

        self.arguments = []
        if arguments:
            self.arguments = arguments

    @orm.reconstructor
    def init_on_load(self):
        self._data_param_name, self._run, self._api = get_transform_api(self.app_name, self.action_name)
        self._transform_executable = get_transform(self.app_name, self._run)

    def execute(self, data_in, accumulator):
        """Executes the transform.

        Args:
            data_in: The input to the condition, the last executed action of the workflow or the input to a trigger.
            accumulator (dict): A record of executed actions and their results. Of form {action_name: result}.

        Returns:
            (obj): The transformed data
        """
        original_data_in = deepcopy(data_in)
        try:
            self.__update_arguments(data_in)
            args = validate_transform_parameters(self._api, self.arguments, self.action_name, accumulator=accumulator)
            result = self._transform_executable(**args)
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.TransformSuccess)
            return result
        except InvalidArgument as e:
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.TransformError)
            logger.error('Transform {0} has invalid input {1}. Error: {2}. '
                         'Returning unmodified data'.format(self.action_name, original_data_in, str(e)))
        except Exception as e:
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.TransformError)
            logger.error(
                'Transform {0} encountered an error: {1}. Returning unmodified data'.format(self.action_name, str(e)))
        return original_data_in

    def __update_arguments(self, data):
        arg = None
        for argument in self.arguments:
            if argument.name == self._data_param_name:
                arg = argument
                break
        if arg:
            self.arguments.remove(arg)
        self.arguments.append(Argument(self._data_param_name, value=data))

    def update(self, data):
        if self.app_name != data['app_name']:
            self.app_name = data['app_name']
        if self.action_name != data['action_name']:
            self.action_name = data['action_name']

        if 'arguments' in data:
            arguments_seen = []
            for argument in data['arguments']:
                if 'id' in argument and argument['id']:
                    argument_obj = self.__get_argument_by_id(argument['id'])
                    argument_obj.update(argument)
                    arguments_seen.append(argument_obj.id)
                else:
                    if 'id' in argument:
                        argument.pop('id')
                    argument_obj = Argument(**argument)
                    self.arguments.append(argument_obj)
                    walkoff.coredb.devicedb.device_db.session.add(argument_obj)
                    walkoff.coredb.devicedb.device_db.session.commit()
                    arguments_seen.append(argument_obj.id)

            for argument in self.arguments:
                if argument.id not in arguments_seen:
                    walkoff.coredb.devicedb.device_db.session.delete(argument)
        else:
            self.arguments[:] = []

    def __get_argument_by_id(self, argument_id):
        for argument in self.arguments:
            if argument.id == argument_id:
                return argument
        return None
