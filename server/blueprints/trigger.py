import json
from flask import Blueprint, request, current_app
from flask_security import auth_token_required, roles_accepted
from server.flaskserver import running_context
from server import forms

triggers_page = Blueprint('triggers_page', __name__)


@triggers_page.route('/execute', methods=['POST'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/execution/listener'])
def listener():
    form = forms.IncomingDataForm(request.form)
    data_input = None
    if form.validate():
        if form.input.data:
            data_input = json.loads(form.input.data)
        returned_json = running_context.Triggers.execute(form.data.data, data_input)
        current_app.logger.info('Executing triggers with conditional info {0} and input info {1}'.format(form.data.data,
                                                                                                         data_input))
        return json.dumps(returned_json)
    else:
        current_app.logger.error('Received invalid form for trigger execution')
        return json.dumps({})


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
                current_app.logger.info('Added trigger: '
                                        '{0}'.format(json.dumps({"name": name,
                                                                 "condition": form.conditional.data,
                                                                 "workflow": "{0}-{1}".format(form.playbook.data,
                                                                                              form.workflow.data)})))
                return json.dumps({"status": "success"})
            except ValueError:
                current_app.logger.error('Cannot create trigger {0}. Invalid JSON in conditional field'.format(name))
                return json.dumps({"status": "error: invalid json in conditional field"})
        else:
            current_app.logger.warning('Cannot create trigger {0}. Trigger already exists'.format(name))
            return json.dumps({"status": "warning: trigger with that name already exists"})
    current_app.logger.error('Cannot create trigger {0}. Invalid form'.format(name))
    return json.dumps({"status": "error: form not valid"})


@triggers_page.route('/triggers/<string:name>', methods=['GET'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/execution/listener/triggers'])
def read_trigger(name):
    query = running_context.Triggers.query.filter_by(name=name).first()
    if query:
        return json.dumps({"status": 'success', "trigger": query.as_json()})
    current_app.logger.error('Cannot display trigger {0}. Does not exist'.format(name))
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
            current_app.logger.info('Edited trigger {0}'.format(name))
            return json.dumps({"status": "success"})
        else:
            current_app.logger.error('Could not edit trigger {0}. Malformed JSON in conditional'.format(name))
            return json.dumps({"status": "error: invalid json in conditional field"})
    current_app.logger.error('Could not edit trigger {0}. Form is invalid'.format(name))
    return json.dumps({"status": "trigger could not be edited"})


@triggers_page.route('/triggers/<string:name>', methods=['DELETE'])
@auth_token_required
@roles_accepted(*running_context.user_roles['/execution/listener/triggers'])
def delete_trigger(name):
    query = running_context.Triggers.query.filter_by(name=name).first()
    if query:
        running_context.Triggers.query.filter_by(name=name).delete()
        running_context.db.session.commit()
        current_app.logger.info('Deleted trigger {0}'.format(name))
        return json.dumps({"status": "success"})
    elif query is None:
        current_app.logger.warning('Cannot delete trigger {0}. Trigger does not exist'.format(name))
        return json.dumps({"status": "error: trigger does not exist"})
    return json.dumps({"status": "error: could not remove trigger"})

