from server import forms
from server.context import running_context
import json


def devices():
    return {"apps": running_context.get_apps(),
            "form": forms.AddNewDeviceForm(),
            "editDeviceform": forms.EditDeviceForm()}


def settings():
    user_form = forms.UserForm()
    choices = [(obj.email, str(obj.email)) for obj in running_context.User.query.all()]
    user_form.username.choices = choices
    add_user_form = forms.AddUserForm()
    roles = [(x.name, str(x.name)) for x in running_context.Role.query.all()]
    add_user_form.roles.choices = roles
    return {"systemForm": forms.SettingsForm(), "userForm": user_form, "addUserForm": add_user_form}


def playbook():
    return {"currentWorkflow": "multiactionWorkflow"}


def triggers():
    return {"form": forms.AddNewTriggerForm(), "editForm": forms.EditTriggerForm()}


def cases():
    return {"currentWorkflow": "multiactionWorkflow"}


def dashboard():
    return {"widgets": [{"app": "HelloWorld", "widget": "testWidget"}]}


def controller():
    return {
        "currentController": str(running_context.controller.name),
        "loadedWorkflows": json.dumps(running_context.controller.get_all_workflows()),
        "schedulerStatus": str(running_context.controller.scheduler.state),
        "editSubscriptionForm": forms.EditSubscriptionForm()
    }
