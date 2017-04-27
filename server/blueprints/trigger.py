import json
from flask import Blueprint, request
from flask_security import auth_token_required, roles_accepted
from server.flaskserver import running_context
from server import forms

triggers_page = Blueprint('triggers_page', __name__)


@triggers_page.route('/execute', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/execution/listener'])
def listener():
    form = forms.IncomingDataForm(request.form)
    returned_json = running_context.Triggers.execute(form.data.data) if form.validate() else {}
    return json.dumps(returned_json)

#TODO: DELETE
@triggers_page.route('/', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/execution/listener'])
def listener_delete():
    form = forms.IncomingDataForm(request.form)
    returned_json = running_context.Triggers.execute(form.data.data) if form.validate() else {}
    return json.dumps(returned_json)


@triggers_page.route('/triggers', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/execution/listener/triggers'])
def display_all_triggers():
    return json.dumps({"status": "success", "triggers": [trigger.as_json()
                                                         for trigger in running_context.Triggers.query.all()]})


@triggers_page.route('/triggers/<string:name>', methods=['PUT'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/execution/listener/triggers'])
def create_trigger(name):
    form = forms.AddNewTriggerForm(request.form)
    if form.validate():
        query = running_context.Triggers.query.filter_by(name=name).first()
        if query is None:
            try:
                json.loads(form.conditional.data)
                running_context.db.session.add(
                    running_context.Triggers(name=name,
                                             condition=form.conditional.data,
                                             playbook=form.playbook.data,
                                             workflow=form.workflow.data))

                running_context.db.session.commit()
                return json.dumps({"status": "success"})
            except ValueError:
                return json.dumps({"status": "error: invalid json in conditional field"})
        else:
            return json.dumps({"status": "warning: trigger with that name already exists"})
    return json.dumps({"status": "error: form not valid"})


@triggers_page.route('/triggers/<string:name>', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/execution/listener/triggers'])
def read_trigger(name):
    query = running_context.Triggers.query.filter_by(name=name).first()
    if query:
        return json.dumps({"status": 'success', "trigger": query.as_json()})
    return json.dumps({"status": "error: trigger not found"})


@triggers_page.route('/triggers/<string:name>', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/execution/listener/triggers'])
def update_trigger(name):
    form = forms.EditTriggerForm(request.form)
    trigger = running_context.Triggers.query.filter_by(name=name).first()
    if form.validate() and trigger is not None:
        # Ensures new name is unique
        if form.name.data:
            if len(running_context.Triggers.query.filter_by(name=form.name.data).all()) > 0:
                return json.dumps({"status": "error: duplicate names found. Trigger could not be edited"})

        result = trigger.edit_trigger(form)

        if result:
            running_context.db.session.commit()
            return json.dumps({"status": "success"})
        else:
            return json.dumps({"status": "error: invalid json in conditional field"})
    return json.dumps({"status": "trigger could not be edited"})


@triggers_page.route('/triggers/<string:name>', methods=['DELETE'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/execution/listener/triggers'])
def delete_trigger(name):
    query = running_context.Triggers.query.filter_by(name=name).first()
    if query:
        running_context.Triggers.query.filter_by(name=name).delete()
        running_context.db.session.commit()
        return json.dumps({"status": "success"})
    elif query is None:
        return json.dumps({"status": "error: trigger does not exist"})
    return json.dumps({"status": "error: could not remove trigger"})


#TODO: DELETE
@triggers_page.route('/triggers/<string:name>/<string:action>', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/execution/listener/triggers'])
def trigger_functions(action, name):
    if action == 'add':
        form = forms.AddNewTriggerForm(request.form)
        if form.validate():
            query = running_context.Triggers.query.filter_by(name=name).first()
            if query is None:
                try:
                    json.loads(form.conditional.data)
                    running_context.db.session.add(
                        running_context.Triggers(name=name,
                                                 condition=form.conditional.data,
                                                 playbook=form.playbook.data,
                                                 workflow=form.workflow.data))

                    running_context.db.session.commit()
                    return json.dumps({"status": "success"})
                except ValueError:
                    return json.dumps({"status": "error: invalid json in conditional field"})
            else:
                return json.dumps({"status": "warning: trigger with that name already exists"})
        return json.dumps({"status": "error: form not valid"})

    if action == 'edit':
        form = forms.EditTriggerForm(request.form)
        trigger = running_context.Triggers.query.filter_by(name=name).first()
        if form.validate() and trigger is not None:
            # Ensures new name is unique
            if form.name.data:
                if len(running_context.Triggers.query.filter_by(name=form.name.data).all()) > 0:
                    return json.dumps({"status": "error: duplicate names found. Trigger could not be edited"})

            result = trigger.edit_trigger(form)

            if result:
                running_context.db.session.commit()
                return json.dumps({"status": "success"})
            else:
                return json.dumps({"status": "error: invalid json in conditional field"})
        return json.dumps({"status": "trigger could not be edited"})

    elif action == 'remove':
        query = running_context.Triggers.query.filter_by(name=name).first()
        if query:
            running_context.Triggers.query.filter_by(name=name).delete()
            running_context.db.session.commit()
            return json.dumps({"status": "success"})
        elif query is None:
            return json.dumps({"status": "error: trigger does not exist"})
        return json.dumps({"status": "error: could not remove trigger"})

    elif action == 'display':
        query = running_context.Triggers.query.filter_by(name=name).first()
        if query:
            return json.dumps({"status": 'success', "trigger": query.as_json()})
        return json.dumps({"status": "error: trigger not found"})
