from server import forms
from core.context import running_context

def devices():
    return {"apps": running_context.getApps(), "form":forms.AddNewDeviceForm()}

def settings():
    form = forms.settingsForm()
    choices = [(obj.email, str(obj.email)) for obj in running_context.User.query.all()]
    form.username.choices = choices
    return {"form":form}

def playbook():
    return {"currentWorkflow": "multiactionWorkflow"}

def triggers():
    return {"form": forms.addNewTriggerForm()}

def cases():
    return {"currentWorkflow": "multiactionWorkflow"}

def dashboard():
    return {"widgets":[{"app":"HelloWorld", "widget":"testWidget"}]}

def debug():
    return {}
