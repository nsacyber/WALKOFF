from wtforms import Form, BooleanField, StringField, PasswordField, validators, FieldList, DateTimeField, DecimalField, \
    IntegerField, FormField, \
    SelectField, RadioField, SubmitField


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
    pages = StringField('pages')


class AddPlayForm(Form):
    template = StringField('template', [validators.Length(min=1, max=50), validators.Optional()])


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
    key = StringField('key', [validators.required(), validators.length(min=1, max=25)])
    value = StringField('value')


class EditSingleConfigForm(Form):
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
    ipaddr = StringField('ipaddr', [validators.Optional()])
    apps = FieldList(StringField('apps'), [validators.Optional()])
    port = IntegerField('port', [validators.Optional(), validators.NumberRange(min=0, max=9999)])
    submit = SubmitField('submit')
    extraFields = StringField('extraFields', [validators.Optional()])


class EditDeviceForm(Form):
    name = StringField('name', [validators.Length(min=4, max=25), validators.Optional()])
    username = StringField('username', [validators.Optional()])
    pw = PasswordField('pw', [validators.Optional()])
    ipaddr = StringField('ipaddr', [validators.Optional()])
    port = IntegerField('port', [validators.Optional(), validators.NumberRange(min=0, max=9999)])
    apps = FieldList(StringField('apps'), [validators.Optional()])
    submit = SubmitField('submit')
    extraFields = StringField('extraFields', [validators.Optional()])


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


class EditSubscriptionForm(Form):
    ancestry = FieldList(StringField('ancestry'), [validators.Optional()])
    events = FieldList(StringField('events'), [validators.Optional()])


class AddSubscriptionForm(Form):
    ancestry = FieldList(StringField('ancestry'), [validators.Optional()])
    events = FieldList(StringField('events'), [validators.Optional()])


class DeleteSubscriptionForm(Form):
    ancestry = FieldList(StringField('ancestry'), [validators.Optional()])


class settingsForm(Form):
    templatesPath = StringField('templatesPath', [validators.Optional()])
    workflowsPath = StringField('workflowsPath', [validators.Optional()])
    profileVisualizationsPath = StringField('profileVisualizationsPath', [validators.Optional()])
    keywordsPath = StringField('keywordsPath', [validators.Optional()])
    dbPath = StringField('dbPath', [validators.Optional()])

    TLS_version = StringField('TLS_version', [validators.Optional()])
    certificatePath = StringField('certificatePath', [validators.Optional()])
    https = StringField('https', [validators.Optional()])
    privateKeyPath = StringField('privateKeyPath', [validators.Optional()])

    debug = StringField('debug', [validators.Optional()])
    defaultServer = StringField('defaultServer', [validators.Optional()])
    host = StringField('host', [validators.Optional()])
    port = StringField('port', [validators.Optional()])





class userForm(Form):
    username = SelectField('username', [validators.Optional()], choices=[])
    email = StringField('email', [validators.DataRequired("Please enter your email address."),
                                  validators.Email("Please enter your email address.")])
    password = PasswordField('password')
    active = BooleanField()
    confirmed_at = DateTimeField('confirmed_at', [validators.Optional()])
    roles = SelectField('roles', choices=[])
    last_login_at = DateTimeField("last_login_at")
    current_login_at = DateTimeField("current_login_at")
    last_login_ip = StringField("last_login_ip")
    current_login_ip = StringField("current_login_ip")
    login_count = IntegerField("login_count")
    # active = RadioField('active',choices = [ (h.key.id(),h.homename)for h in User.queryAll()])
