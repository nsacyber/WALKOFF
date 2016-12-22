import importlib
import xml.etree.cElementTree as et

class Next():
    def __init__(self, nextStep="", flags=[]):
        self.nextStep = nextStep
        self.flags = flags

    def toXML(self):
        elem = et.Element("next")
        elem.set("next", self.nextStep)
        for flag in self.flags:
            elem.append(flag.toXML())

        return elem

    def createFlag(self, action="", args={}, filters=[]):
        newFlag = Flag(action=action, args=args, filters=filters)
        self.flags.append(newFlag)

    def removeFlag(self, index=-1):
        try:
            self.flags.remove(self.flags[index])

            #Reflect change in XML
            #selected = self.xml.find(".//flag[" + str(index) + "]")
            #self.xml.find(".").remove(selected)
            return True
        except IndexError:
            return False

    def __call__(self, output=None):
        for flag in self.flags:
            if not flag(output=output):
                return None
        return self.nextStep

    def __repr__(self):
        output = {}
        output["nextStep"] = self.nextStep
        output["flags"] = [flag.__dict__ for flag in self.flags]
        return str(output)


class Flag():
    def __init__(self, action="", args={}, filters=[]):
        self.action = action
        self.args = args
        self.filters = filters

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


    def validateArgs(self):
        for arg in self.args:
            if not self.args[arg].validate(action=self.action, io="input"):
                return False
        return True

    def __call__(self, output=None):
        data = output
        for filter in self.filters:
            data = filter(output=data)

        module = self.checkImport()
        if module:
            if self.validateArgs():
                result = getattr(module, "main")(args=self.args, value=output)
            return result

    def checkImport(self):
        try:
            flagModule = importlib.import_module("core.flags." + self.action)
        except ImportError as e:
            flagModule = None
        finally:
            return flagModule

    def __repr__(self):
        output = {}
        output["action"] = self.action
        output["args"] = {arg:self.args[arg].__dict__ for arg in self.args}
        output["filters"] = [filter.__dict__ for filter in self.filters]
        return str(output)

class Filter():
    def __init__(self, action="", args={}):
        self.action = action
        self.args = args

    def toXML(self):
        elem = et.Element("filter")
        elem.set("action", self.action)
        argsElement = et.Element("args")
        for arg in self.args:
            argsElement.append(self.args[arg].toXML())

        return elem

    def __call__(self, output=None):
        module = self.checkImport()
        if module:
            result = getattr(module, "main")(args=self.args, value=output)
            return result
        return output

    def checkImport(self):
        try:
            filterModule = importlib.import_module("core.filters." + self.action)
        except ImportError as e:
            filterModule = None
        finally:
            return filterModule

    def __repr__(self):
        output = {}
        output["action"] = self.action
        output["args"] = {arg:self.args[arg].__dict__ for arg in self.args}
        return str(output)
