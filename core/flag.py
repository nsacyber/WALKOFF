from xml.etree import cElementTree as et

from core import arguments
from core.case import callbacks
from core.executionelement import ExecutionElement
from core.filter import Filter
from core.helpers import import_lib



class Flag(ExecutionElement):
    def __init__(self, xml=None, parent_name='', action='', args=None, filters=None, ancestry=None):
        if xml:
            self._from_xml(xml, parent_name=parent_name, ancestry=ancestry)
        else:
            ExecutionElement.__init__(self, name=action, parent_name=parent_name, ancestry=ancestry)
            self.action = action
            self.args = args if args is not None else {}
            self.filters = filters if filters is not None else []
        super(Flag, self)._register_event_callbacks({'FlagArgsValid': callbacks.add_flag_entry('Flag args valid'),
                                                     'FlagArgsInvalid': callbacks.add_flag_entry('Flag args invalid')})

    def _from_xml(self, xml_element, parent_name='', ancestry=None):
        self.action = xml_element.get("action")
        ExecutionElement.__init__(self, name=self.action, parent_name=parent_name, ancestry=ancestry)
        self.args = {arg.tag: arguments.Argument(key=arg.tag, value=arg.text, format=arg.get("format"))
                     for arg in xml_element.findall("args/*")}
        self.filters = [Filter(xml=filter_element,
                               parent_name=self.name,
                               ancestry=self.ancestry)
                        for filter_element in xml_element.findall("filters/*")]

    def set(self, attribute=None, value=None):
        setattr(self, attribute, value)

    def to_xml(self, *args):
        elem = et.Element("flag")
        elem.set("action", self.action)
        args_element = et.SubElement(elem, "args")
        for arg in self.args:
            args_element.append(self.args[arg].to_xml())

        filters_element = et.SubElement(elem, "filters")
        for filter in self.filters:
            filters_element.append(filter.to_xml())
        return elem

    def addFilter(self, action="", args=None, index=None):
        if index is not None:
            self.filters.insert(index, Filter(action=action, args=(args if args is not None else {})))
        else:
            self.filters.append(Filter(action=action, args=(args if args is not None else {})))
        return True

    def removeFilter(self, index=-1):
        try:
            del self.filters[index]
        except IndexError:
            return False
        return True

    def validateArgs(self):
        return all(self.args[arg].validate(action=self.action, io="input") for arg in self.args)

    def __call__(self, output=None):
        data = output
        for filter in self.filters:
            data = filter(output=data)

        module = import_lib('flags', self.action)
        if module:
            result = None
            if self.validateArgs():
                result = getattr(module, "main")(args=self.args, value=data)
                self.event_handler.execute_event_code(self, 'FlagArgsValid')
            else:
                print("ARGS INVALID")
                self.event_handler.execute_event_code(self, 'FlagArgsInvalid')
            return result

    def __repr__(self):
        output = {'action': self.action,
                  'args': {arg: self.args[arg].__dict__ for arg in self.args},
                  'filters': [filter.__dict__ for filter in self.filters]}
        return str(output)

    def as_json(self):
        return {"action": self.action,
                "args": {arg: self.args[arg].as_json() for arg in self.args},
                "filters": [filter.as_json() for filter in self.filters]}