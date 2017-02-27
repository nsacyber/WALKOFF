import importlib
import sys

from core import forms
from core.config import getApps
from server.database import User

def loadModule(name):
    module = "apps." + name + ".display"
    try:
        return sys.modules[module]
    except KeyError:
        pass
    try:
        return importlib.import_module(module, '')
    except ImportError:
        return None


def loadApp(name, keys, values):
    module = loadModule(name)
    args = dict(zip(keys, values))
    return getattr(module, "load")(args) if module else {}


def data_stream(app_name, stream_name):
    module = loadModule(app_name)
    if module:
        return getattr(module, 'stream_generator')(stream_name)


def devices():
    return {"apps": getApps()}, forms.AddNewDeviceForm()


def settings():
    form = forms.settingsForm()
    choices = [(obj.email, str(obj.email)) for obj in User.query.all()]
    form.username.choices = choices
    return {}, form


def playbook():
    return {"currentWorkflow": "multiactionWorkflow"}, None


def triggers():
    return {}, forms.addNewTriggerForm()


def cases():
    return {"currentWorkflow": "multiactionWorkflow"}, None

def dashboard():
    return {}, None
