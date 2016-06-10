import sys, importlib

def loadModule(name):
    module = "apps." + name + ".display"
    try:
        return sys.modules[module]
    except KeyError:
        pass
    try:
        return importlib.import_module(module, '')
    except ImportError as e:
        return None

def loadApp(name, args):
    module = loadModule(name)
    if module:
        return getattr(module, "load")(args)
    return {}