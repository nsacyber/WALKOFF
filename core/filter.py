from core.case import callbacks
from core.data.filter import FilterData
from core.helpers import (get_filter,  InvalidInput, dereference_step_routing)
from core.validator import  validate_parameter
from copy import deepcopy
import logging

logger = logging.getLogger(__name__)


class Filter(FilterData):

    def __init__(self, action=None, xml=None, parent_name='', args=None, ancestry=None):
        """Initializes a new Filter object. A Filter is used to filter input into a workflow.
        
        Args:
            xml (cElementTree, optional): The XML element tree object. Defaults to None.
            parent_name (str, optional): The name of the parent for ancestry purposes. Defaults to an empty string.
            action (str, optional): The action name for the filter. Defaults to an empty string.
            args (dict[str:str], optional): Dictionary of Argument keys to Argument values. This dictionary will be
                converted to a dictionary of str:Argument. Defaults to None.
            ancestry (list[str], optional): The ancestry for the Filter object. Defaults to None.
        """
        FilterData.__init__(self, action, xml, parent_name, args, ancestry)

    def __call__(self, data_in, accumulator):
        """
        Executes the flag

        Args:
            data_in: The input to the flag. Typically from the last step of the workflow or the input to a trigger
            accumulator (dict): A record of executed steps and their results. Of form {step_name: result}
        Returns:
            (bool): Is the flag true for the given data and accumulator
        """
        original_data_in = deepcopy(data_in)
        try:
            data_in = validate_parameter(data_in, self.data_in_api, 'Filter {0}'.format(self.action))
            args = dereference_step_routing(self.args, accumulator, 'In Filter {0}'.format(self.name))
            args.update({self.data_in_api['name']: data_in})
            result = get_filter(self.action)(**args)
            callbacks.FilterSuccess.send(self)
            return result
        except InvalidInput as e:
            callbacks.FilterError.send(self)
            logger.error('Filter {0} has invalid input {1}. Error: {2}. '
                         'Returning unmodified data'.format(self.action, original_data_in, str(e)))
        except Exception as e:
            callbacks.FilterError.send(self)
            logger.error('Filter {0} encountered an error: {1}. Returning unmodified data'.format(self.action, str(e)))
        return original_data_in



    def reconstruct_ancestry(self, parent_ancestry):
        """Reconstructs the ancestry for a Filter object. This is needed in case a workflow and/or playbook is renamed.

        Args:
            parent_ancestry(list[str]): The parent ancestry list.
        """
        self._construct_ancestry(parent_ancestry)

    def get_children(self, ancestry):
        """Gets the children Filters of the Flag in JSON format.
        
        Args:
            ancestry (list[str]): The ancestry list for the Filter to be returned.
            
        Returns:
            Empty dictionary {}
        """
        return {}

    def __repr__(self):
        output = {'action': self.action,
                  'args': self.args}
        return str(output)
