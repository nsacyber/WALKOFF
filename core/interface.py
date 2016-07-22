import sys, importlib, itertools
from config import getApps
from auth import forms

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

def devices():
    return {"apps" : getApps()}, forms.AddNewDeviceForm()