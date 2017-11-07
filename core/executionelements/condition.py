import logging

from core.case.callbacks import data_sent
from core.executionelements.executionelement import ExecutionElement
from core.helpers import (get_condition, get_condition_api, InvalidInput,
                          dereference_step_routing, format_exception_message)
from core.validator import validate_condition_parameters, validate_parameter

logger = logging.getLogger(__name__)


class Condition(ExecutionElement):
    def __init__(self, action, arguments=None, transforms=None, uid=None, app=''):
        """Initializes a new Condition object.
        
        Args:
            action (str, optional): The action name for the Condition. Defaults to an empty string.
            arguments (dict[str:str], optional): Dictionary of Argument keys to Argument values. This dictionary will be
                converted to a dictionary of str:Argument. Defaults to None.
            transforms(list[Transform], optional): A list of Transform objects for the Condition object. Defaults to None.
            uid (str, optional): A universally unique identifier for this object.
                Created from uuid.uuid4() in Python
        """
        ExecutionElement.__init__(self, uid)
        self.app = app
        self.action = action
        if isinstance(arguments, list):
            arguments = {arg['name']: arg['value'] for arg in arguments}
        elif isinstance(arguments, dict):
            arguments = arguments
        else:
            arguments = {}
        self._args_api, self._data_in_api = get_condition_api(self.action)
        self.arguments = validate_condition_parameters(self._args_api, arguments, self.action)
        self.transforms = transforms if transforms is not None else []

    def execute(self, data_in, accumulator):
        data = data_in

        for transform in self.transforms:
            data = transform.execute(data, accumulator)
        try:
            data = validate_parameter(data, self._data_in_api, 'Condition {}'.format(self.action))
            args = {argument.name: argument.get_value(accumulator) for argument in self.arguments}
            data_sent.send(self, callback_name="Condition Success", object_type="Condition")
            logger.debug('Arguments passed to condition {} are valid'.format(self.uid))
            args.update({self._data_in_api['name']: data})
            return get_condition(self.action)(**args)
        except InvalidInput as e:
            logger.error('Condition {0} has invalid input {1} which was converted to {2}. Error: {3}. '
                         'Returning False'.format(self.action, data_in, data, format_exception_message(e)))
            data_sent.send(self, callback_name="Condition Error", object_type="Condition")
            return False
        except Exception as e:
            logger.error('Error encountered executing '
                         'condition {0} with arguments {1} and value {2}: '
                         'Error {3}. Returning False'.format(self.action, self.arguments, data, format_exception_message(e)))
            data_sent.send(self, callback_name="Condition Error", object_type="Condition")
            return False
