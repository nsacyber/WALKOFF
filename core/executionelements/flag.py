import logging

from core.case.callbacks import data_sent
from core.executionelements.executionelement import ExecutionElement
from core.helpers import get_flag, get_flag_api, InvalidInput, dereference_step_routing, format_exception_message
from core.validator import validate_flag_parameters, validate_parameter

logger = logging.getLogger(__name__)


class Flag(ExecutionElement):
    def __init__(self, action, args=None, filters=None, uid=None):
        """Initializes a new Flag object. 
        
        Args:
            action (str): The action name for the Flag. Defaults to an empty string.
            args (dict[str:str], optional): Dictionary of Argument keys to Argument values. This dictionary will be
                converted to a dictionary of str:Argument. Defaults to None.
            filters(list[Filter], optional): A list of Filter objects for the Flag object. Defaults to None.
            uid (str, optional): A universally unique identifier for this object.
                Created from uuid.uuid4().hex in Python
        """
        ExecutionElement.__init__(self, uid)
        self.action = action
        if isinstance(args, list):
            args = {arg['name']: arg['value'] for arg in args}
        elif isinstance(args, dict):
            args = args
        else:
            args = {}
        self._args_api, self._data_in_api = get_flag_api(self.action)
        self.args = validate_flag_parameters(self._args_api, args, self.action)
        self.filters = filters if filters is not None else []

    def execute(self, data_in, accumulator):
        data = data_in

        for filter_element in self.filters:
            data = filter_element.execute(data, accumulator)
        try:
            data = validate_parameter(data, self._data_in_api, 'Flag {}'.format(self.action))
            args = dereference_step_routing(self.args, accumulator, 'In Flag {}'.format(self.uid))
            data_sent.send(self, callback_name="Flag Success", object_type="Flag")
            logger.debug('Arguments passed to flag {} are valid'.format(self.uid))
            args.update({self._data_in_api['name']: data})
            return get_flag(self.action)(**args)
        except InvalidInput as e:
            logger.error('Flag {0} has invalid input {1} which was converted to {2}. Error: {3}. '
                         'Returning False'.format(self.action, data_in, data, format_exception_message(e)))
            data_sent.send(self, callback_name="Flag Error", object_type="Flag")
            return False
        except Exception as e:
            logger.error('Error encountered executing '
                         'flag {0} with arguments {1} and value {2}: '
                         'Error {3}. Returning False'.format(self.action, self.args, data, format_exception_message(e)))
            data_sent.send(self, callback_name="Flag Error", object_type="Flag")
            return False
