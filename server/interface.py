from server import forms
from .database import User
from core.context import running_context

def devices():
    return {"apps": running_context.getApps()}, forms.AddNewDeviceForm()

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

def debug():
    return {}, None
