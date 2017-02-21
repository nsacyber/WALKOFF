from xml.etree import cElementTree as et

from core import arguments
from core.case import callbacks
from core.executionelement import ExecutionElement
from core.helpers import import_lib


class Filter(ExecutionElement):
    def __init__(self, xml=None, parent_name="", action="", args=None, ancestry=None):
        if xml:
            self._from_xml(xml, parent_name, ancestry)
        else:
            ExecutionElement.__init__(self, name=action, parent_name=parent_name, ancestry=ancestry)
            self.action = action
            args = args if args is not None else {}
            self.args = {arg: arguments.Argument(key=arg, value=args[arg], format=type(args[arg]).__name__)
                         for arg in args}
        super(Filter, self)._register_event_callbacks({'FilterSuccess': callbacks.add_flag_entry('Filter success'),
                                                       'FilterError': callbacks.add_flag_entry('Filter error')})

    def _from_xml(self, xml_element, parent_name=None, ancestry=None):
        self.action = xml_element.get('action')
        ExecutionElement.__init__(self, name=self.action, parent_name=parent_name, ancestry=ancestry)
        args = {arg.tag: arguments.Argument(key=arg.tag, value=arg.text, format=arg.get("format")) for arg in
                xml_element.findall("args/*")}
        self.args = {arg: arguments.Argument(key=arg, value=args[arg], format=type(args[arg]).__name__)
                     for arg in args}

    def to_xml(self, *args):
        elem = et.Element("filter")
        elem.set("action", self.action)
        args_element = et.SubElement(elem, "args")
        for arg in self.args:
            args_element.append(self.args[arg].to_xml())

        return elem

    def __call__(self, output=None):
        module = import_lib('filters', self.action)
        if module:
            try:
                result = getattr(module, "main")(args=self.args, value=output)
                self.event_handler.execute_event_code(self, 'FilterSuccess')
                return result
            except Exception:
                self.event_handler.execute_event_code(self, 'FilterError')
                print("FILTER ERROR")
        return output

    def __repr__(self):
        output = {'action': self.action,
                  'args': {arg: self.args[arg].__dict__ for arg in self.args}}
        return str(output)

    def as_json(self):
        return {"action": self.action,
                "args": {arg: self.args[arg].as_json() for arg in self.args}}