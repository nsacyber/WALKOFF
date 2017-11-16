import logging
from copy import deepcopy

from core.case.callbacks import data_sent
from core.executionelements.executionelement import ExecutionElement
from core.argument import Argument
from core.helpers import get_transform_api, InvalidArgument, split_api_params
from core.validator import validate_transform_parameters, validate_parameter
from apps import get_transform

logger = logging.getLogger(__name__)


class Transform(ExecutionElement):

    def __init__(self, app_name, action_name, arguments=None, uid=None):
        """Initializes a new Transform object. A Transform is used to transform input into a workflow.
        
        Args:
            app_name (str): The app name associated with this transform
            action_name (str): The action name for the transform.
            arguments (list[Argument], optional): Dictionary of Argument keys to Argument values. This dictionary will be
                converted to a dictionary of str:Argument. Defaults to None.
            uid (str, optional): A universally unique identifier for this object.
                Created from uuid.uuid4() in Python
        """
        ExecutionElement.__init__(self, uid)
        self.app_name = app_name
        self.action_name = action_name
        self._data_param_name, self._run, self._api = get_transform_api(self.app_name, self.action_name)
        self._transform_executable = get_transform(self.app_name, self._run)
        arguments = {arg.name: arg for arg in arguments} if arguments is not None else {}
        tmp_api = split_api_params(self._api, self._data_param_name)
        validate_transform_parameters(tmp_api, arguments, self.action_name)
        self.arguments = arguments

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
            self.arguments.update({self._data_param_name: Argument(self._data_param_name, value=data_in)})
            args = validate_transform_parameters(self._api, self.arguments, self.action_name, accumulator=accumulator)
            result = self._transform_executable(**args)
            data_sent.send(self, callback_name="Transform Success", object_type="Transform")
            return result
        except InvalidArgument as e:
            data_sent.send(self, callback_name="Transform Error", object_type="Transform")
            logger.error('Transform {0} has invalid input {1}. Error: {2}. '
                         'Returning unmodified data'.format(self.action_name, original_data_in, str(e)))
        except Exception as e:
            data_sent.send(self, callback_name="Transform Error", object_type="Transform")
            logger.error('Transform {0} encountered an error: {1}. Returning unmodified data'.format(self.action_name, str(e)))
        return original_data_in
