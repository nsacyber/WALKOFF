from wtforms import Form, BooleanField, StringField, PasswordField, validators, FieldList, DateTimeField, DecimalField, \
    IntegerField, FormField, \
    SelectField, RadioField, SubmitField
from flask_security.forms import Required, EqualTo


class NewUserForm(Form):
    username = StringField('username', [validators.Length(min=4, max=25), validators.data_required()])
    password = PasswordField('password', [validators.data_required()])
    role = FieldList(StringField('role'), [validators.Optional()])


class EditUserForm(Form):
    password = PasswordField('password')
    role = FieldList(StringField('role'), [validators.Optional()])


class NewRoleForm(Form):
    name = StringField('name', [validators.data_required()])
    description = StringField('description')


class EditRoleForm(Form):
    description = StringField('description')
    pages = StringField('pages')


class AddWorkflowForm(Form):
    playbook = StringField('playbook', [validators.Length(min=1, max=50), validators.Optional()])
    template = StringField('template', [validators.Length(min=1, max=50), validators.Optional()])


class AddPlaybookForm(Form):
    playbook_template = StringField('playbook_template', [validators.Length(min=1, max=50), validators.Optional()])


class EditPlaybookForm(Form):
    new_name = StringField('new_name', [validators.Length(min=1, max=50), validators.data_required()])


class EditPlayNameForm(Form):
    new_name = StringField('new_name', [validators.Length(min=1, max=50), validators.Optional()])
    enabled = BooleanField('enabled', [validators.Optional()])
    scheduler_type = StringField('scheduler_type', [validators.Optional()])
    autoRun = BooleanField('autorun', [validators.Optional()])
    scheduler_args = StringField('scheduler_options', [validators.Optional()])


class SavePlayForm(Form):
    filename = StringField('filename', [validators.Length(min=1, max=50), validators.Optional()])
    cytoscape = StringField('cytoscape', [validators.Optional()])


class AddEditStepForm(Form):
    id = StringField('id', [validators.Optional()])
    to = FieldList(StringField('to-id'), [validators.Optional()])
    app = StringField('app', [validators.Optional()])
    device = StringField('device', [validators.Optional()])
    action = StringField('action', [validators.Optional()])
    input = StringField('input', [validators.Optional()])
    error = FieldList(StringField('error'), [validators.Optional()])


class EditConfigForm(Form):
    key = StringField('key', [validators.data_required(), validators.length(min=1, max=25)])
    value = StringField('value')


class EditSingleConfigForm(Form):
    value = StringField('value')


class RemoveConfigForm(Form):
    key = StringField('key', [validators.data_required(), validators.length(min=1, max=25)])


class RenderArgsForm(Form):
    page = StringField("page", [validators.data_required()])
    key = FieldList(StringField("key", [validators.Optional()]))
    value = FieldList(StringField("value", [validators.Optional()]))


class AddNewDeviceForm(Form):
    name = StringField('Name', [validators.Length(min=4, max=25), validators.data_required()])
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


class LoginForm(Form):
    username = StringField('username', [validators.Length(min=4, max=25)])
    password = PasswordField('password')


class addNewTriggerForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=25), validators.Optional()])
    conditional = FieldList(StringField('Conditionals'), [validators.data_required()])
    playbook = StringField('Playbook', [validators.Length(min=1, max=255), validators.data_required()])
    workflow = StringField('Workflow', [validators.Length(min=1, max=255), validators.data_required()])


class editTriggerForm(Form):
    name = StringField('New Name', [validators.Length(min=1, max=25), validators.Optional()])
    conditional = FieldList(StringField('Conditionals'), [validators.Optional()])
    playbook = StringField('Playbook', [validators.Length(min=1, max=255), validators.required()])
    workflow = StringField('Workflow', [validators.Length(min=1, max=255), validators.required()])


class conditionalArgsField(Form):
    key = StringField('key', [validators.Length(min=1, max=25), validators.Optional()])
    value = StringField('value', [validators.Length(min=1, max=25), validators.Optional()])


class conditionalField(Form):
    name = StringField('flag', [validators.Length(min=1, max=25), validators.Optional()])
    args = FieldList(FormField(conditionalArgsField, [validators.Optional()]))
    play = StringField('play', [validators.Length(min=1, max=25), validators.Optional()])


class incomingDataForm(Form):
    data = StringField('data')


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
    caseName = StringField('name', [validators.Optional()])


class EditSubscriptionForm(Form):
    ancestry = FieldList(StringField('ancestry'), [validators.Optional()])
    events = FieldList(StringField('events'), [validators.Optional()])


class AddSubscriptionForm(Form):
    ancestry = FieldList(StringField('ancestry'), [validators.Optional()])
    events = FieldList(StringField('events'), [validators.Optional()])


class DeleteSubscriptionForm(Form):
    ancestry = FieldList(StringField('ancestry'), [validators.Optional()])


class SettingsForm(Form):
    templates_path = StringField('Templates Path', [validators.Optional()])
    workflows_path = StringField('Workflows Path', [validators.Optional()])
    profile_visualizations_path = StringField('Profile Visualizations Path', [validators.Optional()])
    keywords_path = StringField('Keywords Path', [validators.Optional()])
    db_path = StringField('Database Path', [validators.Optional()])
    apps_path = StringField('Apps Path', [validators.Optional()])
    tls_version = StringField('TLS Version', [validators.Optional()])
    certificate_path = StringField('Certificate Path', [validators.Optional()])
    https = StringField('HTTPS Enabled', [validators.Optional()])
    private_key_path = StringField('Private Key Path', [validators.Optional()])

    debug = StringField('Debug', [validators.Optional()])
    default_server = StringField('Default Server', [validators.Optional()])
    host = StringField('Host', [validators.Optional()])
    port = StringField('Port', [validators.Optional()])


class userForm(Form):
    username = SelectField('Username', [validators.Optional()], choices=[])
    email = StringField('Email', [validators.DataRequired("Please enter your email address.")])
    password = PasswordField('Password')
    active = BooleanField()
    confirmed_at = DateTimeField('Confirmed at', [validators.Optional()])
    roles = SelectField('Roles', choices=[])
    last_login_at = DateTimeField("Last login at")
    current_login_at = DateTimeField("Current login at")
    last_login_ip = StringField("Last login ip")
    current_login_ip = StringField("Current login ip")
    login_count = IntegerField("Login count")

class addUserForm(Form):
    username = StringField('Username', [validators.required(message='Enter a user name')])
    password = PasswordField('Password', [Required(), EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Repeat Password')
    roles = SelectField('Roles', choices=[])
    email = StringField('Email', [validators.DataRequired("Please enter your email address.")])
