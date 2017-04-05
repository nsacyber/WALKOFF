from xml.etree import cElementTree

from core import arguments
from core.case import callbacks
from core.executionelement import ExecutionElement
from core.filter import Filter
from core.helpers import import_lib
import core.config.config


class Flag(ExecutionElement):
    def __init__(self, xml=None, parent_name='', action='', args=None, filters=None, ancestry=None):
        if xml:
            self._from_xml(xml, parent_name=parent_name, ancestry=ancestry)
        else:
            ExecutionElement.__init__(self, name=action, parent_name=parent_name, ancestry=ancestry)
            self.action = action
            self.args = args if args is not None else {}
            self.filters = filters if filters is not None else []

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
        setattr(self, attribute, value)

    def to_xml(self, *args):
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
        if index is not None:
            self.filters.insert(index, Filter(action=action, args=(args if args is not None else {})))
        else:
            self.filters.append(Filter(action=action, args=(args if args is not None else {})))
        return True

    def remove_filter(self, index=-1):
        try:
            del self.filters[index]
        except IndexError:
            return False
        return True

    def validate_args(self):
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
            else:
                print("ARGS INVALID")
                callbacks.FlagArgsInvalid.send(self)
            return result

    def __repr__(self):
        output = {'action': self.action,
                  'args': {arg: self.args[arg].as_json() for arg in self.args},
                  'filters': [filter_element.as_json() for filter_element in self.filters]}
        return str(output)

    def as_json(self, with_children=True):
        out = {"action": self.action,
               "args": {arg: self.args[arg].as_json() for arg in self.args}}
        if with_children:
            out["filters"] = [filter_element.as_json() for filter_element in self.filters]
        else:
            out["filters"] = [filter_element.name for filter_element in self.filters]
        return out

    @staticmethod
    def from_json(json, parent_name='', ancestry=None):
        args = {arg_name: arguments.Argument.from_json(arg_json) for arg_name, arg_json in json['args'].items()}
        flag = Flag(action=json['action'], args=args, parent_name=parent_name, ancestry=ancestry)
        filters = [Filter.from_json(filter_element, parent_name=flag.name, ancestry=flag.ancestry)
                   for filter_element in json['filters']]
        flag.filters = filters
        return flag

    def get_children(self, ancestry):
        if not ancestry:
            return self.as_json(with_children=False)
        else:
            next_child = ancestry.pop()
            try:
                filter_index = [filter_element.name for filter_element in self.filters].index(next_child)
                return self.filters[filter_index].as_json()
            except ValueError:
                return None
