import sys, importlib, itertools

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

def loadApp(name, keys, values):
    module = loadModule(name)

    args = {k.data: v.data for k, v in itertools.izip(keys,values)}

    if module:
        return getattr(module, "load")(args)
    return {}