import logging
from copy import deepcopy

from core.case.callbacks import data_sent
from core.executionelements.executionelement import ExecutionElement
from core.helpers import get_filter, get_filter_api, InvalidInput, dereference_step_routing
from core.validator import validate_filter_parameters, validate_parameter

logger = logging.getLogger(__name__)


class Filter(ExecutionElement):

    def __init__(self, action, args=None, uid=None):
        """Initializes a new Filter object. A Filter is used to filter input into a workflow.
        
        Args:
            action (str, optional): The action name for the filter. Defaults to an empty string.
            args (dict[str:str], optional): Dictionary of Argument keys to Argument values. This dictionary will be
                converted to a dictionary of str:Argument. Defaults to None.
            uid (str, optional): A universally unique identifier for this object.
                Created from uuid.uuid4().hex in Python
        """
        ExecutionElement.__init__(self, uid)
        self.action = action
        self._args_api, self._data_in_api = get_filter_api(self.action)
        if isinstance(args, list):
            args = {arg['name']: arg['value'] for arg in args}
        elif isinstance(args, dict):
            args = args
        else:
            args = {}

        self.args = validate_filter_parameters(self._args_api, args, self.action)

    def execute(self, data_in, accumulator):
        """Executes the flag.

        Args:
            data_in: The input to the flag. Typically from the last step of the workflow or the input to a trigger.
            accumulator (dict): A record of executed steps and their results. Of form {step_name: result}.

        Returns:
            (bool): Is the flag true for the given data and accumulator
        """
        original_data_in = deepcopy(data_in)
        try:
            data_in = validate_parameter(data_in, self._data_in_api, 'Filter {0}'.format(self.action))
            args = dereference_step_routing(self.args, accumulator, 'In Filter {0}'.format(self.uid))
            args.update({self._data_in_api['name']: data_in})
            result = get_filter(self.action)(**args)
            data_sent.send(self, callback_name="Filter Success", object_type="Filter")
            return result
        except InvalidInput as e:
            data_sent.send(self, callback_name="Filter Error", object_type="Filter")
            logger.error('Filter {0} has invalid input {1}. Error: {2}. '
                         'Returning unmodified data'.format(self.action, original_data_in, str(e)))
        except Exception as e:
            data_sent.send(self, callback_name="Filter Error", object_type="Filter")
            logger.error('Filter {0} encountered an error: {1}. Returning unmodified data'.format(self.action, str(e)))
        return original_data_in
