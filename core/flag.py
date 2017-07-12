
from core.data.flag import FlagData
from core.case import callbacks
from core.helpers import (get_flag, InvalidInput, dereference_step_routing)
from core.validator import validate_parameter
import logging

logger = logging.getLogger(__name__)


class Flag(FlagData):
    def __init__(self, action=None, xml=None, parent_name='', args=None, filters=None, ancestry=None):
        """Initializes a new Flag object. 
        
        Args:
            xml (cElementTree, optional): The XML element tree object. Defaults to None.
            parent_name (str, optional): The name of the parent for ancestry purposes. Defaults to an empty string.
            action (str, optional): The action name for the Flag. Defaults to an empty string.
            args (dict[str:str], optional): Dictionary of Argument keys to Argument values. This dictionary will be
                converted to a dictionary of str:Argument. Defaults to None.
            filters(list[Filter], optional): A list of Filter objects for the Flag object. Defaults to None.
            ancestry (list[str], optional): The ancestry for the Filter object. Defaults to None.
        """
        FlagData.__init__(self, action, xml, parent_name, args, filters, ancestry)



    def __call__(self, data_in, accumulator):
        data = data_in
        for filter_element in self.filters:
            data = filter_element(data, accumulator)
        try:
            data = validate_parameter(data, self.data_in_api, 'Flag {0}'.format(self.action))
            args = dereference_step_routing(self.args, accumulator, 'In Flag {0}'.format(self.name))
            callbacks.FlagSuccess.send(self)
            logger.debug('Arguments passed to flag {0} are valid'.format(self.ancestry))
            args.update({self.data_in_api['name']: data})
            return get_flag(self.action)(**args)
        except InvalidInput as e:
            logger.error('Flag {0} has invalid input {1} which was converted to {2}. Error: {3}. '
                         'Returning False'.format(self.action, data_in, data, str(e)))
            callbacks.FlagError.send(self)
            return False
        except Exception as e:
            logger.error('Error encountered executing '
                         'flag {0} with arguments {1} and value {2}: '
                         'Error {3}. Returning False'.format(self.action, self.args, data, str(e)))
            callbacks.FlagError.send(self)
            return False





    def reconstruct_ancestry(self, parent_ancestry):
        """Reconstructs the ancestry for a Flag object. This is needed in case a workflow and/or playbook is renamed.

        Args:
            parent_ancestry(list[str]): The parent ancestry list.
        """
        self._construct_ancestry(parent_ancestry)
        for filter_element in self.filters:
            filter_element.reconstruct_ancestry(self.ancestry)

    def get_children(self, ancestry):
        """Gets the children Filters of the Flag in JSON format.
        
        Args:
            ancestry (list[str]): The ancestry list for the Filter to be returned.
            
        Returns:
            The Filter in the ancestry (if provided) as a JSON, otherwise None.
        """
        if not ancestry:
            return self.as_json(with_children=False)
        else:
            next_child = ancestry.pop()
            try:
                filter_index = [filter_element.name for filter_element in self.filters].index(next_child)
                return self.filters[filter_index].as_json()
            except ValueError:
                return None

    def __repr__(self):
        output = {'action': self.action,
                  'args': self.args,
                  'filters': [filter_element.as_json() for filter_element in self.filters]}
        return str(output)
