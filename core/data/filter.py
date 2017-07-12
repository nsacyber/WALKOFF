from xml.etree import ElementTree
from core.executionelement import ExecutionElement
from core.helpers import (get_filter_api, InvalidElementConstructed, inputs_xml_to_dict, inputs_to_xml)
from core.validator import validate_filter_parameters
import logging

logger = logging.getLogger(__name__)

class FilterData(ExecutionElement):
    def __init__(self, action=None, xml=None, parent_name='', args=None, ancestry=None):
        if xml is not None:
            self._from_xml(xml, parent_name, ancestry)
        else:
            if action is None:
                raise InvalidElementConstructed('Action or xml must be specified in filter constructor')
            ExecutionElement.__init__(self, name=action, parent_name=parent_name, ancestry=ancestry)
            self.action = action
            self.args_api, self.data_in_api = get_filter_api(self.action)
            args = args if args is not None else {}
            self.args = validate_filter_parameters(self.args_api, args, self.action)

    def _from_xml(self, xml_element, parent_name=None, ancestry=None):
        self.action = xml_element.get('action')
        ExecutionElement.__init__(self, name=self.action, parent_name=parent_name, ancestry=ancestry)
        self.args_api, self.data_in_api = get_filter_api(self.action)
        args_xml = xml_element.find('args')
        args = (inputs_xml_to_dict(args_xml) or {}) if args_xml is not None else {}
        self.args = validate_filter_parameters(self.args_api, args, self.action)

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

    def as_json(self):
        """Gets the JSON representation of a Filter object.

        Returns:
            The JSON representation of a Filter object.
        """
        args = {arg_name: {'key': arg_name, 'value': arg_value, 'format': self.__get_arg_type(arg_name)}
                for arg_name, arg_value in self.args.items()}
        return {"action": self.action,
                "args": args}

    @staticmethod
    def from_json(json, parent_name='', ancestry=None):
        """Forms a Filter object from the provided JSON object.

        Args:
            json (JSON object): The JSON object to convert from.
            parent_name (str, optional): The name of the parent for ancestry purposes. Defaults to an empty string.
            ancestry (list[str], optional): The ancestry for the new Filter object. Defaults to None.

        Returns:
            The Filter object parsed from the JSON object.
        """
        out_filter = FilterData(action=json['action'],
                            args={arg_name: arg_value['value'] for arg_name, arg_value in json['args'].items()},
                            parent_name=parent_name,
                            ancestry=ancestry)
        return out_filter

    def to_xml(self, *args):
        """Converts the Filter object to XML format.

        Args:
            args (list[str], optional): A list of arguments to place in the XML.

        Returns:
            The XML representation of the Filter object.
        """
        elem = ElementTree.Element('filter')
        elem.set('action', self.action)
        if self.args:
            args = inputs_to_xml(self.args, root='args')
            elem.append(args)
        return elem

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