from xml.etree import cElementTree

from core import arguments
from core.case import callbacks
from core.executionelement import ExecutionElement
from core.helpers import import_lib
import core.config.config


class Filter(ExecutionElement):

    def __init__(self, xml=None, parent_name='', action='', args=None, ancestry=None):
        """Initializes a new Filter object. A Filter is used to filter input into a workflow.
        Args:
            xml (cElementTree, optional): The XML element tree object. Defaults to None.
            parent_name (str, optional): The name of the parent for ancestry purposes. Defaults to an empty string.
            action (str, optional): The action name for the filter. Defaults to an empty string.
            args (dict[str:str], optional): Dictionary of Argument keys to Argument values. This dictionary will be
                converted to a dictionary of str:Argument. Defaults to None.
            ancestry (list[str], optional): The ancestry for the Filter object. Defaults to None.
        """
        if xml:
            self._from_xml(xml, parent_name, ancestry)
        else:
            ExecutionElement.__init__(self, name=action, parent_name=parent_name, ancestry=ancestry)
            self.action = action
            args = args if args is not None else {}
            self.args = {arg_name: arguments.Argument(key=arg_name, value=arg_value, format=type(arg_value).__name__)
                         for arg_name, arg_value in args.items()}

    def reconstruct_ancestry(self, parent_ancestry):
        """Reconstructs the ancestry for a Filter object. This is needed in case a workflow and/or playbook is renamed.
        Args:
            parent_ancestry(list[str]): The parent ancestry list.
        """
        self._construct_ancestry(parent_ancestry)

    def _from_xml(self, xml_element, parent_name=None, ancestry=None):
        self.action = xml_element.get('action')
        ExecutionElement.__init__(self, name=self.action, parent_name=parent_name, ancestry=ancestry)
        self.args = {arg.tag: arguments.Argument(key=arg.tag, value=arg.text, format=arg.get('format'))
                     for arg in xml_element.findall('args/*')}

    def to_xml(self, *args):
        """Converts the Filter object to XML format.
        Args:
            args (list[str], optional): A list of arguments to place in the XML.
        Returns:
            The XML representation of the Filter object.
        """
        elem = cElementTree.Element('filter')
        elem.set('action', self.action)
        args_element = cElementTree.SubElement(elem, 'args')
        for arg in self.args:
            args_element.append(self.args[arg].to_xml())
        return elem

    def validate_args(self):
        """Ensures that the arguments passed in are properly formed.
        Returns:
             True if arguments are valid, False otherwise.
        """
        if self.action in core.config.config.function_info['filters']:
            possible_args = core.config.config.function_info['filters'][self.action]['args']
            if possible_args:
                return (len(list(possible_args)) == len(list(self.args.keys()))
                        and all(arg.validate(possible_args) for arg in self.args.values()))
            else:
                return True
        return False

    def __call__(self, output=None):
        module = import_lib('filters', self.action)
        if module and self.validate_args():
            try:
                result = getattr(module, "main")(args=self.args, value=output)
                callbacks.FilterSuccess.send(self)
                return result
            except:
                callbacks.FilterError.send(self)
                print("FILTER ERROR")
        return output

    def __repr__(self):
        output = {'action': self.action,
                  'args': {arg: self.args[arg].__dict__ for arg in self.args}}
        return str(output)

    def as_json(self):
        """Gets the JSON representation of a Filter object.
        Returns:
            The JSON representation of a Filter object.
        """
        return {"action": self.action,
                "args": {arg: self.args[arg].as_json() for arg in self.args}}

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
        args = {arg_name: arguments.Argument.from_json(arg_json) for arg_name, arg_json in json['args'].items()}
        out_filter = Filter(action=json['action'],
                            args=args,
                            parent_name=parent_name,
                            ancestry=ancestry)
        out_filter.args = args
        return out_filter

    def get_children(self, ancestry):
        """Gets the children Filters of the Flag in JSON format.
        Args:
            ancestry (list[str]): The ancestry list for the Filter to be returned.
        Returns:
            Empty dictionary {}
        """
        return {}