import logging
from copy import deepcopy

from core.case.callbacks import data_sent
from core.executionelements.executionelement import ExecutionElement
from core.helpers import get_transform_api, InvalidInput, dereference_step_routing
from core.validator import validate_transform_parameters, validate_parameter
from apps import get_transform

logger = logging.getLogger(__name__)


class Transform(ExecutionElement):

    def __init__(self, app, action, args=None, uid=None):
        """Initializes a new Transform object. A Transform is used to transform input into a workflow.
        
        Args:
            app (str): The app name associated with this transform
            action (str): The action name for the transform.
            args (dict[str:str], optional): Dictionary of Argument keys to Argument values. This dictionary will be
                converted to a dictionary of str:Argument. Defaults to None.
            uid (str, optional): A universally unique identifier for this object.
                Created from uuid.uuid4() in Python
        """
        ExecutionElement.__init__(self, uid)
        self.app = app
        self.action = action
        self._run, self._args_api, self._data_in_api = get_transform_api(self.app, self.action)
        self._transform_executable = get_transform(self.app, self._run)
        if isinstance(args, list):
            args = {arg['name']: arg['value'] for arg in args}
        elif isinstance(args, dict):
            args = args
        else:
            args = {}

        self.args = validate_transform_parameters(self._args_api, args, self.action)

    def execute(self, data_in, accumulator):
        """Executes the transform.

        Args:
            data_in: The input to the condition. Typically from the last step of the workflow or the input to a trigger.
            accumulator (dict): A record of executed steps and their results. Of form {step_name: result}.

        Returns:
            (obj): The transformed data
        """
        original_data_in = deepcopy(data_in)
        try:
            data_in = validate_parameter(data_in, self._data_in_api, 'Transform {0}'.format(self.action))
            args = dereference_step_routing(self.args, accumulator, 'In Transform {0}'.format(self.uid))
            args.update({self._data_in_api['name']: data_in})
            result = self._transform_executable(**args)
            data_sent.send(self, callback_name="Transform Success", object_type="Transform")
            return result
        except InvalidInput as e:
            data_sent.send(self, callback_name="Transform Error", object_type="Transform")
            logger.error('Transform {0} has invalid input {1}. Error: {2}. '
                         'Returning unmodified data'.format(self.action, original_data_in, str(e)))
        except Exception as e:
            data_sent.send(self, callback_name="Transform Error", object_type="Transform")
            logger.error('Transform {0} encountered an error: {1}. Returning unmodified data'.format(self.action, str(e)))
        return original_data_in

