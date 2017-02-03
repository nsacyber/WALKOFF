import importlib
import xml.etree.cElementTree as et

from core import arguments, case
from core.events import EventHandler, Event


class NextStepEventHandler(EventHandler):
    def __init__(self, shared_log=None):
        EventHandler.__init__(self, "nextStepHandler", shared_log,
                              events={'NextStepTaken': case.add_next_step_entry('Step taken'),
                                      'NextStepNotTaken': case.add_next_step_entry('Step not taken')})


class FlagEventHandler(EventHandler):
    def __init__(self, shared_log=None):
        EventHandler.__init__(self, "flagHandler", shared_log,
                              events={'FlagArgsValid': case.add_flag_entry('Flag args valid'),
                                      'FlagArgsInvalid': case.add_flag_entry('Flag args invalid')})


class FilterEventHandler(EventHandler):
    def __init__(self, shared_log=None):
        EventHandler.__init__(self, "filterHandler", shared_log,
                              events={'FilterSuccess': case.add_flag_entry('Filter success'),
                                      'FilterError': case.add_flag_entry('Filter error')})


class Next(object):
    def __init__(self, previous_step_id="", nextStep="", nextWorkflow="", flags=None, ancestry=None):
        self.nextStep = nextStep
        self.id = previous_step_id
        self.flags = flags if flags is not None else []
        self.event_handler = NextStepEventHandler()
        self.ancestry = list(ancestry) if ancestry is not None else []
        self.ancestry.append(self.nextStep)

    def toXML(self, tag="next"):
        elem = et.Element(tag)
        elem.set("next", self.nextStep)
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
        return self.nextStep == other.nextStep and set(self.flags) == set(other.flags)

    def __call__(self, output=None):
        if all(flag(output=output) for flag in self.flags):
            self.event_handler.execute_event_code(self, 'NextStepTaken')
            return self.nextStep
        else:
            self.event_handler.execute_event_code(self, 'NextStepNotTaken')
            return None

    def __repr__(self):
        output = {'nextStep': self.nextStep,
                  'flags': [flag.__dict__ for flag in self.flags]}
        return str(output)


class Flag(object):
    def __init__(self, previous_step_id="", action="", args=None, filters=None, ancestry=None):
        self.action = action
        self.args = args if args is not None else {}
        self.filters = filters if filters is not None else []
        self.event_handler = FlagEventHandler()
        self.id = previous_step_id
        self.ancestry = list(ancestry) if ancestry is not None else []
        self.ancestry.append(self.action)

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


class Filter(object):
    def __init__(self, previous_step_id="", action="", args=None, ancestry=None):
        self.action = action
        safeargs = args if args is not None else {}
        self.args = {arg: arguments.Argument(key=arg, value=args[arg], format=type(args[arg]).__name__)
                     for arg in safeargs}
        self.event_handler = FilterEventHandler()
        self.id = previous_step_id
        self.ancestry = list(ancestry) if ancestry is not None else []
        self.ancestry.append(self.action)

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
