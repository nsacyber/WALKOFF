from copy import deepcopy
from xml.etree import cElementTree
from core.case import callbacks
from core.executionelement import ExecutionElement
from core.filter import Filter
from core.helpers import get_flag, get_flag_api, InvalidElementConstructed, InvalidInput
from core.validator import validate_flag_parameters, validate_parameter
import logging
logger = logging.getLogger(__name__)


class Flag(ExecutionElement):
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
        if xml is not None:
            self._from_xml(xml, parent_name=parent_name, ancestry=ancestry)
        else:
            if action is None:
                raise InvalidElementConstructed('Action or xml must be specified in flag constructor')
            ExecutionElement.__init__(self, name=action, parent_name=parent_name, ancestry=ancestry)
            self.action = action
            args = args if args is not None else {}
            self.args_api, self.data_in_api = get_flag_api(self.action)
            self.args = validate_flag_parameters(self.args_api, args, self.action)
            self.filters = filters if filters is not None else []

    def _from_xml(self, xml_element, parent_name='', ancestry=None):
        self.action = xml_element.get('action')
        ExecutionElement.__init__(self, name=self.action, parent_name=parent_name, ancestry=ancestry)
        self.args_api, self.data_in_api = get_flag_api(self.action)
        args = {arg.tag: arg.text for arg in xml_element.findall('args/*')}
        self.args = validate_flag_parameters(self.args_api, args, self.action)
        self.filters = [Filter(xml=filter_element,
                               parent_name=self.name,
                               ancestry=self.ancestry)
                        for filter_element in xml_element.findall('filters/*')]

    def __call__(self, data_in=None):
        data = data_in

        for filter_element in self.filters:
            data = filter_element(data_in=data)
        try:
            args = deepcopy(self.args)
            data = validate_parameter(data, self.data_in_api, 'Flag {0}'.format(self.action))
            callbacks.FlagArgsValid.send(self)
            logger.debug('Arguments passed to flag {0} are valid'.format(self.ancestry))
            args.update({self.data_in_api['name']: data})
            return get_flag(self.action)(**args)
        except InvalidInput as e:
            logger.error('Flag {0} has invalid input {1} which was converted to {2}. Error: {3}. '
                         'Returning False'.format(self.action, data_in, data, str(e)))
            callbacks.FlagArgsInvalid.send(self)
            return False
        except Exception as e:
            logger.error('Error encountered executing '
                         'flag {0} with arguments {1} and value {2}: '
                         'Error {3}. Returning False'.format(self.action, self.args, data, str(e)))
            return False

    def as_json(self, with_children=True):
        """Gets the JSON representation of a Flag object.
        
        Args:
            with_children (bool, optional): A boolean to determine whether or not the children elements of the Flag
                object should be included in the output.
                
        Returns:
            The JSON representation of a Flag object.
        """

        out = {"action": self.action,
               "args": self.args}
        if with_children:
            out["filters"] = [filter_element.as_json() for filter_element in self.filters]
        else:
            out["filters"] = [filter_element.name for filter_element in self.filters]
        return out

    @staticmethod
    def from_json(json, parent_name='', ancestry=None):
        """Forms a Flag object from the provided JSON object.
        
        Args:
            json (JSON object): The JSON object to convert from.
            parent_name (str, optional): The name of the parent for ancestry purposes. Defaults to an empty string.
            ancestry (list[str], optional): The ancestry for the new Flag object. Defaults to None.
            
        Returns:
            The Flag object parsed from the JSON object.
        """
        args = {arg_name: arg_json for arg_name, arg_json in json['args'].items()}
        flag = Flag(action=json['action'], args=args, parent_name=parent_name, ancestry=ancestry)
        filters = [Filter.from_json(filter_element, parent_name=flag.name, ancestry=flag.ancestry)
                   for filter_element in json['filters']]
        flag.filters = filters
        return flag

    def to_xml(self, *args):
        """Converts the Flag object to XML format.

        Args:
            args (list[str], optional): A list of arguments to place in the XML.

        Returns:
            The XML representation of the Flag object.
        """
        elem = cElementTree.Element('flag')
        elem.set('action', self.action)
        if self.args:
            args_element = cElementTree.SubElement(elem, 'args')
            for arg_name, arg_value in self.args.items():
                element = cElementTree.Element(arg_name)
                element.text = arg_value
                args_element.append(element)
        if self.filters:
            filters_element = cElementTree.SubElement(elem, 'filters')
            for filter_element in self.filters:
                filters_element.append(filter_element.to_xml())
        return elem

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
