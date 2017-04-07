from server import forms
import json
from core.context import running_context


def devices():
    return {"apps": running_context.get_apps(),
            "form": forms.AddNewDeviceForm(),
            "editDeviceform": forms.EditDeviceForm()}


def settings():
    user_form = forms.UserForm()
    choices = [(obj.email, str(obj.email)) for obj in running_context.User.query.all()]
    user_form.username.choices = choices
    addUserForm = forms.AddUserForm()
    roles =[(x.name,str(x.name)) for x in running_context.Role.query.all()]
    addUserForm.roles.choices = roles
    return {"systemForm": forms.SettingsForm(), "userForm": user_form, "addUserForm": addUserForm }


def playbook():
    return {"currentWorkflow": "multiactionWorkflow"}


def triggers():
    return {"form": forms.AddNewTriggerForm(), "editForm": forms.EditTriggerForm()}


def cases():
    return {"currentWorkflow": "multiactionWorkflow"}


def dashboard():
    return {"widgets":[{"app":"HelloWorld", "widget":"testWidget"}]}


def controller():
    return {
        "currentController": str(running_context.controller.name),
        "loadedWorkflows": running_context.controller.get_all_workflows(),
        "schedulerStatus": running_context.controller.scheduler.state
    }
