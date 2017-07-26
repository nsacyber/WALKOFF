from wtforms import Form, BooleanField, StringField, PasswordField, validators, FieldList, DateTimeField, \
    IntegerField, FormField, SelectField, SubmitField, TextAreaField
from flask_security.forms import Required, EqualTo


class AddWorkflowForm(Form):
    playbook = StringField('playbook', [validators.Length(min=1, max=50), validators.Optional()])
    template = StringField('template', [validators.Length(min=1, max=50), validators.Optional()])


class CopyWorkflowForm(Form):
    playbook = StringField('playbook', [validators.Length(min=1, max=50), validators.Optional()])
    workflow = StringField('workflow', [validators.Length(min=1, max=50), validators.Optional()])


class CopyPlaybookForm(Form):
    playbook = StringField('playbook', [validators.Length(min=1, max=50), validators.Optional()])


class AddPlaybookForm(Form):
    playbook_template = StringField('playbook_template', [validators.Length(min=1, max=50), validators.Optional()])


class SavePlayForm(Form):
    filename = StringField('filename', [validators.Length(min=1, max=50), validators.Optional()])
    cytoscape = StringField('cytoscape', [validators.Optional()])


class ResumeWorkflowForm(Form):
    uuid = StringField('uuid', [validators.Length(32), validators.DataRequired()])


class AddEditStepForm(Form):
    id = StringField('id', [validators.Optional()])
    to = FieldList(StringField('to-id'), [validators.Optional()])
    app = StringField('app', [validators.Optional()])
    device = StringField('device', [validators.Optional()])
    action = StringField('action', [validators.Optional()])
    input = StringField('input', [validators.Optional()])
    error = FieldList(StringField('error'), [validators.Optional()])


class RenderArgsForm(Form):
    page = StringField("page", [validators.data_required()])
    key = FieldList(StringField("key", [validators.Optional()]))
    value = FieldList(StringField("value", [validators.Optional()]))


class AddNewDeviceForm(Form):
    name = StringField('Name', [validators.Length(min=4, max=25), validators.Optional()])
    username = StringField('Username', [validators.Optional()])
    pw = PasswordField('Password', [validators.Optional()])
    ipaddr = StringField('IP Address', [validators.Optional()])
    apps = FieldList(StringField('Apps'), [validators.Optional()])
    port = IntegerField('Port', [validators.Optional(), validators.NumberRange(min=0, max=9999)])
    submit = SubmitField('Submit')
    extraFields = StringField('Extra Fields', [validators.Optional()])


class EditDeviceForm(Form):
    name = StringField('Name', [validators.Length(min=4, max=25), validators.Optional()])
    username = StringField('Username', [validators.Optional()])
    pw = PasswordField('Password', [validators.Optional()])
    ipaddr = StringField('IP Address', [validators.Optional()])
    port = IntegerField('Port', [validators.Optional(), validators.NumberRange(min=0, max=9999)])
    apps = FieldList(StringField('Apps'), [validators.Optional()])
    submit = SubmitField('Submit')
    extraFields = StringField('Extra Fields', [validators.Optional()])


class ExportImportAppDevices(Form):
    filename = StringField('Filename', [validators.Optional()])


class LoginForm(Form):
    username = StringField('username', [validators.Length(min=4, max=25)])
    password = PasswordField('password')


class AddNewTriggerForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=25), validators.Optional()])
    conditional = TextAreaField('Conditionals', [validators.data_required()])

    playbook = StringField('Playbook', [validators.Length(min=1, max=255), validators.data_required()])
    workflow = StringField('Workflow', [validators.Length(min=1, max=255), validators.data_required()])
    tag = StringField('Tag', [validators.Length(min=1, max=255), validators.Optional()])


class EditTriggerForm(Form):
    name = StringField('New Name', [validators.Length(min=1, max=25), validators.Optional()])
    conditional = TextAreaField('Conditionals', [validators.Optional()])
    playbook = StringField('Playbook', [validators.Length(min=1, max=255), validators.required()])
    workflow = StringField('Workflow', [validators.Length(min=1, max=255), validators.required()])
    tag = StringField('Tag', [validators.Length(min=1, max=255), validators.Optional()])


class ConditionalArgsField(Form):
    key = StringField('key', [validators.Length(min=1, max=25), validators.Optional()])
    value = StringField('value', [validators.Length(min=1, max=25), validators.Optional()])


class ConditionalField(Form):
    name = StringField('flag', [validators.Length(min=1, max=25), validators.Optional()])
    args = FieldList(FormField(ConditionalArgsField, [validators.Optional()]))
    play = StringField('play', [validators.Length(min=1, max=25), validators.Optional()])


class IncomingDataForm(Form):
    data = StringField('data')
    input = StringField('input')


class EditCaseForm(Form):
    name = StringField('name', [validators.Optional()])
    note = StringField('note', [validators.Optional()])


class EditEventForm(Form):
    note = StringField('note', [validators.Optional()])


class EditGlobalSubscriptionForm(Form):
    controller = FieldList(StringField('controller'), [validators.Optional()])
    workflow = FieldList(StringField('workflow'), [validators.Optional()])
    step = FieldList(StringField('step'), [validators.Optional()])
    next_step = FieldList(StringField('next_step'), [validators.Optional()])
    flag = FieldList(StringField('flag'), [validators.Optional()])
    filter = FieldList(StringField('filter'), [validators.Optional()])


class AddCaseForm(Form):
    case_name = StringField('name', [validators.Optional()])


class ExportCaseForm(Form):
    filename = StringField('Filename', [validators.Optional()])


class ImportCaseForm(Form):
    filename = StringField('Filename', [validators.Optional()])


class EditSubscriptionForm(Form):
    ancestry = FieldList(StringField('ancestry'), [validators.Optional()])
    events = FieldList(StringField('events'), [validators.Optional()])


class AddSubscriptionForm(Form):
    ancestry = FieldList(StringField('ancestry'), [validators.Optional()])
    events = FieldList(StringField('events'), [validators.Optional()])


class DeleteSubscriptionForm(Form):
    ancestry = FieldList(StringField('ancestry'), [validators.Optional()])
