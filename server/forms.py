from wtforms import Form, StringField, validators, FieldList


class RenderArgsForm(Form):
    page = StringField("page", [validators.data_required()])
    key = FieldList(StringField("key", [validators.Optional()]))
    value = FieldList(StringField("value", [validators.Optional()]))
