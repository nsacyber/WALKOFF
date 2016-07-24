from wtforms import Form, BooleanField, StringField, PasswordField, validators, FieldList, DateTimeField, DecimalField, IntegerField
import formChecks


class NewUserForm(Form):
    username = StringField('username', [validators.Length(min=4, max=25), validators.required()])
    password = PasswordField('password', [validators.required()])
    role = FieldList(StringField('role', [validators.Length(min=4, max=25)]))

class EditUserForm(Form):
    password = PasswordField('password')
    role = FieldList(StringField('role', [validators.Length(min=4, max=25)]))

class NewRoleForm(Form):
    name = StringField('name', [validators.required()])
    description = StringField('description')

class EditRoleForm(Form):
    description = StringField('description')

class AddNewPlayForm(Form):
    name = StringField('name', [validators.Length(min=1, max=25), validators.required()])

class EditPlayOptionsForm(Form):
    autoRun = BooleanField("autorun")
    s_sDT = DateTimeField("sDT")
    s_eDT = DateTimeField("eDT")
    s_interval = DecimalField("interval", places=2)

class EditStepForm(Form):
    id = StringField('id', [validators.Optional()])
    to = FieldList(StringField('to-id'), [validators.Optional()])
    app = StringField('app', [validators.Optional()])
    device = StringField('device', [validators.Optional()])
    action = StringField('action', [validators.Optional()])
    input = StringField('input', [validators.Optional(), formChecks.inValidator])
    error = FieldList(StringField('error'), [validators.Optional()])

class EditConfigForm(Form):
    key = StringField('key', [validators.required(), validators.length(min=1, max=25)])
    value = StringField('value')

class RemoveConfigForm(Form):
    key = StringField('key', [validators.required(), validators.length(min=1, max=25)])

class RenderArgsForm(Form):
    page = StringField("page", [validators.required()])
    key = FieldList(StringField("key", [validators.Optional()]))
    value = FieldList(StringField("value", [validators.Optional()]))

class AddNewDeviceForm(Form):
    name = StringField('name', [validators.Length(min=4, max=25), validators.required()])
    username = StringField('username', [validators.Optional()])
    pw = PasswordField('pw', [validators.Optional()])
    app = StringField('app', [validators.required()])
    ipaddr = StringField('ipaddr', [validators.Optional()])
    port = IntegerField('port', [validators.Optional(), validators.NumberRange(min=0, max=9999)])

class LoginForm(Form):
    username = StringField('username', [validators.Length(min=4, max=25)])
    password = PasswordField('password')

class addNewTriggerForm(Form):
    name = StringField('name', [validators.Length(min=1, max=25), validators.required()])
    conditional = FieldList(StringField('conditional'), [validators.required()])
    play = StringField('play', [validators.Length(min=1, max=25), validators.required()])

class editTriggerForm(Form):
    name = StringField('name', [validators.Length(min=1, max=25), validators.Optional()])
    conditional = FieldList(StringField('conditional'), [validators.Optional()])
    play = StringField('play', [validators.Length(min=1, max=25), validators.Optional()])

class incomingDataForm(Form):
    data = StringField('data')