from server import forms
from core.context import running_context

def devices():
    return {"apps": running_context.getApps(), "form":forms.AddNewDeviceForm(), "editDeviceform": forms.EditDeviceForm()}

def settings():
    userForm = forms.userForm()
    choices = [(obj.email, str(obj.email)) for obj in running_context.User.query.all()]
    userForm.username.choices = choices
    return {"systemForm":forms.settingsForm(), "userForm": userForm }

def playbook():
    return {"currentWorkflow": "multiactionWorkflow"}

def triggers():
    return {"form": forms.addNewTriggerForm(), "editForm":forms.editTriggerForm()}

def cases():
    return {"currentWorkflow": "multiactionWorkflow"}

def dashboard():
    return {"widgets":[{"app":"HelloWorld", "widget":"testWidget"}]}

def controller():
    return {}
