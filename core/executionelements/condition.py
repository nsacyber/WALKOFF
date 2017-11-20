import logging

from core.case.callbacks import data_sent
from core.executionelements.executionelement import ExecutionElement
from core.helpers import get_condition_api, InvalidArgument, format_exception_message, split_api_params
from core.argument import Argument
from core.validator import validate_condition_parameters
from apps import get_condition

logger = logging.getLogger(__name__)


class Condition(ExecutionElement):
    def __init__(self, app_name, action_name, arguments=None, transforms=None, uid=None):
        """Initializes a new Condition object.
        
        Args:
            app_name (str): The name of the app which contains this condition
            action_name (str): The action name for the Condition. Defaults to an empty string.
            arguments (list[Argument], optional): Dictionary of Argument keys to Argument values. This dictionary will be
                converted to a dictionary of str:Argument. Defaults to None.
            transforms(list[Transform], optional): A list of Transform objects for the Condition object. Defaults to None.
            uid (str, optional): A universally unique identifier for this object.
                Created from uuid.uuid4() in Python
        """
        ExecutionElement.__init__(self, uid)
        self.app_name = app_name
        self.action_name = action_name
        self._data_param_name, self._run, self._api = get_condition_api(self.app_name, self.action_name)
        self._condition_executable = get_condition(self.app_name, self._run)
        arguments = {arg.name: arg for arg in arguments} if arguments is not None else {}
        tmp_api = split_api_params(self._api, self._data_param_name)
        validate_condition_parameters(tmp_api, arguments, self.action_name)
        self.arguments = arguments
        self.transforms = transforms if transforms is not None else []

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
            self.arguments.update({self._data_param_name: Argument(self._data_param_name, value=data)})
            args = validate_condition_parameters(self._api, self.arguments, self.action_name, accumulator=accumulator)
            logger.debug('Arguments passed to condition {} are valid'.format(self.uid))
            ret = self._condition_executable(**args)
            data_sent.send(self, callback_name="Condition Success", object_type="Condition")
            return ret
        except InvalidArgument as e:
            logger.error('Condition {0} has invalid input {1} which was converted to {2}. Error: {3}. '
                         'Returning False'.format(self.action_name, data_in, data, format_exception_message(e)))
            data_sent.send(self, callback_name="Condition Error", object_type="Condition")
            return False
        except Exception as e:
            logger.error('Error encountered executing '
                         'condition {0} with arguments {1} and value {2}: '
                         'Error {3}. Returning False'.format(self.action_name, self.arguments, data,
                                                             format_exception_message(e)))
            data_sent.send(self, callback_name="Condition Error", object_type="Condition")
            return False
