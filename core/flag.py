from xml.etree import cElementTree

from core import arguments
from core.case import callbacks
from core.executionelement import ExecutionElement
from core.filter import Filter
from core.helpers import import_lib
import core.config.config
import logging

logger = logging.getLogger(__name__)


class Flag(ExecutionElement):
    def __init__(self, xml=None, parent_name='', action='', args=None, filters=None, ancestry=None):
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
        if xml:
            self._from_xml(xml, parent_name=parent_name, ancestry=ancestry)
        else:
            ExecutionElement.__init__(self, name=action, parent_name=parent_name, ancestry=ancestry)
            self.action = action
            self.args = args if args is not None else {}
            self.filters = filters if filters is not None else []

    def reconstruct_ancestry(self, parent_ancestry):
        """Reconstructs the ancestry for a Flag object. This is needed in case a workflow and/or playbook is renamed.
        
        Args:
            parent_ancestry(list[str]): The parent ancestry list.
        """
        self._construct_ancestry(parent_ancestry)
        for filter in self.filters:
            filter.reconstruct_ancestry(self.ancestry)

    def _from_xml(self, xml_element, parent_name='', ancestry=None):
        self.action = xml_element.get('action')
        ExecutionElement.__init__(self, name=self.action, parent_name=parent_name, ancestry=ancestry)
        self.args = {arg.tag: arguments.Argument(key=arg.tag, value=arg.text, format=arg.get('format'))
                     for arg in xml_element.findall('args/*')}
        self.filters = [Filter(xml=filter_element,
                               parent_name=self.name,
                               ancestry=self.ancestry)
                        for filter_element in xml_element.findall('filters/*')]

    def set(self, attribute=None, value=None):
        """Sets an attribute for the Flag object.
        
        Args:
            attribute (str): The attribute key.
            value (any): The attribute value.
        """
        setattr(self, attribute, value)

    def to_xml(self, *args):
        """Converts the Flag object to XML format.
        
        Args:
            args (list[str], optional): A list of arguments to place in the XML.
            
        Returns:
            The XML representation of the Flag object.
        """
        elem = cElementTree.Element('flag')
        elem.set('action', self.action)
        args_element = cElementTree.SubElement(elem, 'args')
        for arg in self.args:
            args_element.append(self.args[arg].to_xml())

        filters_element = cElementTree.SubElement(elem, 'filters')
        for filter_element in self.filters:
            filters_element.append(filter_element.to_xml())
        return elem

    def add_filter(self, action='', args=None, index=None):
        """Adds a Filter object to the Flag's list of Filters.
        
        Args:
            action (str, optional): The action name for the filter. Defaults to an empty string.
            args (dict[str:str], optional): Dictionary of Argument keys to Argument values. This dictionary will be
                converted to a dictionary of str:Argument. Defaults to None.
            index (any, optional): If index is not None, then the Filter will be inserted at the front of the Filters
                list. Otherwise, it will be appended to the back. Defaults to None.
                
        Returns:
            True upon completion.
        """
        if index is not None:
            self.filters.insert(index, Filter(action=action, args=(args if args is not None else {})))
        else:
            self.filters.append(Filter(action=action, args=(args if args is not None else {})))
        return True

    def remove_filter(self, index=-1):
        """Removes a Filter object from the Flag's list of Filters at a given index.
        
        Args:
            index(int): The index of the Filter object to be removed.
            
        Returns:
            True on success, False otherwise.
        """
        try:
            del self.filters[index]
        except IndexError:
            return False
        return True

    def validate_args(self):
        """Ensures that the arguments passed in are properly formed.
        
        Returns:
             True if arguments are valid, False otherwise.
        """
        if self.action in core.config.config.function_info['flags']:
            possible_args = core.config.config.function_info['flags'][self.action]['args']
            if possible_args:
                return (len(list(possible_args)) == len(list(self.args.keys()))
                        and all(arg.validate(possible_args) for arg in self.args.values()))
            else:
                return True
        return False

    def __call__(self, output=None):
        data = output
        for filter_element in self.filters:
            data = filter_element(output=data)

        module = import_lib('flags', self.action)
        if module:
            result = None
            if self.validate_args():
                result = getattr(module, 'main')(args=self.args, value=data)
                callbacks.FlagArgsValid.send(self)
                logger.debug('Arguments passed to flag {0} are valid'.format(self.ancestry))
            else:
                logger.warning('Arguments passed to flag {0} are invalid. Arguments {1}'.format(self.ancestry,
                                                                                                self.args))
                callbacks.FlagArgsInvalid.send(self)
            return result

    def __repr__(self):
        output = {'action': self.action,
                  'args': {arg: self.args[arg].as_json() for arg in self.args},
                  'filters': [filter_element.as_json() for filter_element in self.filters]}
        return str(output)

    def as_json(self, with_children=True):
        """Gets the JSON representation of a Flag object.
        
        Args:
            with_children (bool, optional): A boolean to determine whether or not the children elements of the Flag
                object should be included in the output.
                
        Returns:
            The JSON representation of a Flag object.
        """
        out = {"action": self.action,
               "args": {arg: self.args[arg].as_json() for arg in self.args}}
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
        args = {arg_name: arguments.Argument.from_json(arg_json) for arg_name, arg_json in json['args'].items()}
        flag = Flag(action=json['action'], args=args, parent_name=parent_name, ancestry=ancestry)
        filters = [Filter.from_json(filter_element, parent_name=flag.name, ancestry=flag.ancestry)
                   for filter_element in json['filters']]
        flag.filters = filters
        return flag

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
