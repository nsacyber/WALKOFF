import importlib
import xml.etree.cElementTree as et

from core import arguments, case
from core.events import EventHandler, Event
from core.executionelement import ExecutionElement


class Next(ExecutionElement):
    def __init__(self, parent_name="", name="", nextWorkflow="", flags=None, ancestry=None):
        ExecutionElement.__init__(self, name=name, parent_name=parent_name, ancestry=ancestry)
        self.flags = flags if flags is not None else []
        self.__construct_ancestry(ancestry)
        super(Next, self)._register_event_callbacks({'NextStepTaken': case.add_next_step_entry('Step taken'),
                                                     'NextStepNotTaken': case.add_next_step_entry('Step not taken')})
    '''
    def from_xml(self, next_xml, ancestry):
        self.nextStep = next_xml.get("step")
        self.__construct_ancestry(ancestry)
        self.flags = [self.parseFlag(self.id, self.ancestry, flag) for flag in next_xml.findall("flag")]
    '''
    def __construct_ancestry(self, ancestry=None):
        self.ancestry = list(ancestry) if ancestry is not None else []
        self.ancestry.append(self.name)

    def toXML(self, tag="next"):
        elem = et.Element(tag)
        elem.set("next", self.name)
        for flag in self.flags:
            elem.append(flag.toXML())
        return elem

    def createFlag(self, action="", args=None, filters=None):
        newFlag = Flag(action=action,
                       args=(args if args is not None else {}),
                       filters=(filters if filters is not None else []))
        self.flags.append(newFlag)

    def removeFlag(self, index=-1):
        try:
            self.flags.remove(self.flags[index])

            # Reflect change in XML
            # selected = self.xml.find(".//flag[" + str(index) + "]")
            # self.xml.find(".").remove(selected)
            return True
        except IndexError:
            return False

    def __eq__(self, other):
        return self.name == other.name and set(self.flags) == set(other.flags)

    def __call__(self, output=None):
        if all(flag(output=output) for flag in self.flags):
            self.event_handler.execute_event_code(self, 'NextStepTaken')
            return self.name
        else:
            self.event_handler.execute_event_code(self, 'NextStepNotTaken')
            return None

    def __repr__(self):
        output = {'nextStep': self.name,
                  'flags': [flag.__dict__ for flag in self.flags]}
        return str(output)


class Flag(ExecutionElement):
    def __init__(self, parent_name="", action="", args=None, filters=None, ancestry=None):
        ExecutionElement.__init__(self, name=action, parent_name=parent_name, ancestry=ancestry)
        self.action = action
        self.args = args if args is not None else {}
        self.filters = filters if filters is not None else []
        super(Flag, self)._register_event_callbacks({'FlagArgsValid': case.add_flag_entry('Flag args valid'),
                                                     'FlagArgsInvalid': case.add_flag_entry('Flag args invalid')})

    def set(self, attribute=None, value=None):
        setattr(self, attribute, value)

    def toXML(self):
        elem = et.Element("flag")
        elem.set("action", self.action)
        argsElement = et.SubElement(elem, "args")
        for arg in self.args:
            argsElement.append(self.args[arg].toXML())

        filtersElement = et.SubElement(elem, "filters")
        for filter in self.filters:
            filtersElement.append(filter.toXML())
        return elem

    def addFilter(self, action="", args=None, index=None):
        if index is not None:
            self.filters.insert(index, Filter(action=action, args=(args if args is not None else {})))
        else:
            self.filters.append(Filter(action=action, args=(args if args is not None else {})))
        return True

    def removeFilter(self, index=None):
        del self.filters[index]
        return True

    def validateArgs(self):
        return all(self.args[arg].validate(action=self.action, io="input") for arg in self.args)

    def __call__(self, output=None):
        data = output
        for filter in self.filters:
            data = filter(output=data)

        module = self.checkImport()
        if module:
            result = None
            if self.validateArgs():
                result = getattr(module, "main")(args=self.args, value=data)
                self.event_handler.execute_event_code(self, 'FlagArgsValid')
            else:
                self.event_handler.execute_event_code(self, 'FlagArgsInvalid')
            return result

    def checkImport(self):
        try:
            flagModule = importlib.import_module("core.flags." + self.action)
        except ImportError as e:
            flagModule = None
        finally:
            return flagModule

    def __repr__(self):
        output = {'action': self.action,
                  'args': {arg: self.args[arg].__dict__ for arg in self.args},
                  'filters': [filter.__dict__ for filter in self.filters]}
        return str(output)


class Filter(ExecutionElement):
    def __init__(self, parent_name="", action="", args=None, ancestry=None):
        ExecutionElement.__init__(self, name=action, parent_name=parent_name, ancestry=ancestry)
        self.action = action
        safeargs = args if args is not None else {}
        self.args = {arg: arguments.Argument(key=arg, value=args[arg], format=type(args[arg]).__name__)
                     for arg in safeargs}
        super(Filter, self)._register_event_callbacks({'FilterSuccess': case.add_flag_entry('Filter success'),
                                                       'FilterError': case.add_flag_entry('Filter error')})

    def toXML(self):
        elem = et.Element("filter")
        elem.set("action", self.action)
        argsElement = et.SubElement(elem, "args")
        for arg in self.args:
            argsElement.append(self.args[arg].toXML())

        return elem

    def __call__(self, output=None):
        module = self.checkImport()
        if module:
            try:
                result = getattr(module, "main")(args=self.args, value=output)
                self.event_handler.execute_event_code(self, 'FilterSuccess')
                return result
            except Exception:
                self.event_handler.execute_event_code(self, 'FilterError')
        return output

    def checkImport(self):
        try:
            filterModule = importlib.import_module("core.filters." + self.action)
        except ImportError as e:
            filterModule = None
        finally:
            return filterModule

    def __repr__(self):
        output = {'action': self.action,
                  'args': {arg: self.args[arg].__dict__ for arg in self.args}}
        return str(output)
