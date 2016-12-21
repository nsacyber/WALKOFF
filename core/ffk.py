import importlib

class Next():
    def __init__(self, nextStep=None, flags=[]):
        self.nextStep = nextStep
        self.flags = flags

    def __call__(self, output=None):
        for flag in self.flags:
            if not flag(output=output):
                return None
        return self.nextStep

    def __repr__(self):
        output = {}
        output["nextStep"] = self.nextStep
        output["flags"] = self.flags
        return str(output)


class Flag():
    def __init__(self, action="", args={}, filters=[]):
        self.action = action
        self.args = args
        self.filters = filters

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
        output["args"] = self.args
        output["filters"] = self.filters
        return str(output)

class Filter():
    def __init__(self, action="", args={}):
        self.action = action
        self.args = args

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
        output["args"] = self.args
        return str(output)
