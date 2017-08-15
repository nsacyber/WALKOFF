from xml.etree import ElementTree
from core.case import callbacks
from core.executionelement import ExecutionElement
from core.helpers import (get_filter, get_filter_api, InvalidInput, InvalidElementConstructed,
                          inputs_xml_to_dict, inputs_to_xml, dereference_step_routing)
from core.validator import validate_filter_parameters, validate_parameter
from copy import deepcopy
import logging
import uuid
logger = logging.getLogger(__name__)


class Filter(ExecutionElement):

    def __init__(self, action=None, xml=None, args=None, uid=None):
        """Initializes a new Filter object. A Filter is used to filter input into a workflow.
        
        Args:
            xml (cElementTree, optional): The XML element tree object. Defaults to None.
            action (str, optional): The action name for the filter. Defaults to an empty string.
            args (dict[str:str], optional): Dictionary of Argument keys to Argument values. This dictionary will be
                converted to a dictionary of str:Argument. Defaults to None.
            uid (str, optional): A universally unique identifier for this object. Created from uuid.uuid4().hex in Python
        """
        if xml is not None:
            self._from_xml(xml)
        else:
            if action is None:
                raise InvalidElementConstructed('Action or xml must be specified in filter constructor')
            ExecutionElement.__init__(self, action, uid)
            self.action = action
            self.args_api, self.data_in_api = get_filter_api(self.action)
            args = args if args is not None else {}
            self.args = validate_filter_parameters(self.args_api, args, self.action)

    def _from_xml(self, xml_element, *args):
        self.action = xml_element.get('action')
        ExecutionElement.__init__(self, name=self.action)
        self.args_api, self.data_in_api = get_filter_api(self.action)
        args_xml = xml_element.find('args')
        args = (inputs_xml_to_dict(args_xml) or {}) if args_xml is not None else {}
        self.args = validate_filter_parameters(self.args_api, args, self.action)

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

    def as_json(self):
        """Gets the JSON representation of a Filter object.
        
        Returns:
            The JSON representation of a Filter object.
        """
        args = [{'name': arg_name, 'value': arg_value} for arg_name, arg_value in self.args.items()]
        return {"uid": self.uid,
                "action": self.action,
                "args": args}

    @staticmethod
    def from_json(json_in):
        """Forms a Filter object from the provided JSON object.
        
        Args:
            json_in (JSON object): The JSON object to convert from.
            
        Returns:
            The Filter object parsed from the JSON object.
        """
        uid = json_in['uid'] if 'uid' in json_in else uuid.uuid4().hex
        out_filter = Filter(action=json_in['action'],
                            args={arg['name']: arg['value'] for arg in json_in['args']},
                            uid=uid)
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

    def __repr__(self):
        output = {'uid': self.uid,
                  'action': self.action,
                  'args': self.args}
        return str(output)
