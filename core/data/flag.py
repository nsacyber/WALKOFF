from xml.etree import ElementTree
import logging
from core.executionelement import ExecutionElement
from core.filter import Filter
from core.validator import validate_flag_parameters
from core.helpers import (get_flag_api, InvalidElementConstructed, inputs_to_xml, inputs_xml_to_dict)
logger = logging.getLogger(__name__)

class FlagData(ExecutionElement):
    def __init__(self, action=None, xml=None, parent_name='', args=None, filters=None, ancestry=None):
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
        args_xml = xml_element.find('args')
        args = (inputs_xml_to_dict(args_xml) or {}) if args_xml is not None else {}
        self.args = validate_flag_parameters(self.args_api, args, self.action)
        self.filters = [Filter(xml=filter_element,
                               parent_name=self.name,
                               ancestry=self.ancestry)
                        for filter_element in xml_element.findall('filters/*')]

    def as_json(self, with_children=True):
        """Gets the JSON representation of a Flag object.

        Args:
            with_children (bool, optional): A boolean to determine whether or not the children elements of the Flag
                object should be included in the output.

        Returns:
            The JSON representation of a Flag object.
        """
        args = {arg_name: {'key': arg_name, 'value': arg_value, 'format': self.__get_arg_type(arg_name)}
                for arg_name, arg_value in self.args.items()}
        out = {"action": self.action,
               "args": args}
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
        args = {arg_name: arg_value['value'] for arg_name, arg_value in json['args'].items()}
        flag = FlagData(action=json['action'], args=args, parent_name=parent_name, ancestry=ancestry)
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
        elem = ElementTree.Element('flag')
        elem.set('action', self.action)
        if self.args:
            args = inputs_to_xml(self.args, root='args')
            elem.append(args)
        if self.filters:
            filters_element = ElementTree.SubElement(elem, 'filters')
            for filter_element in self.filters:
                filters_element.append(filter_element.to_xml())
        return elem

    def __get_arg_type(self, arg_name):
        for arg_api in self.args_api:
            if arg_api['name'] == arg_name:
                if 'type' in arg_api:
                    return arg_api['type']
                elif 'schema' in arg_api:
                    return arg_api['schema']['type']
                else:
                    logger.error('Invalid api schema. This should never happen! Returning string type')
                    return 'string'
        else:
            logger.error('Invalid api schema. This should never happen! Returning string type')
            return 'string'

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