import json
from flask import request, current_app
from flask_security import roles_accepted
from server import forms
from server.return_codes import *


def read_all_triggers():
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/execution/listener'])
    def __func():
        return {"triggers": [trigger.as_json() for trigger in running_context.Triggers.query.all()]}, SUCCESS

    return __func()


def listener():
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/execution/listener'])
    def __func():
        form = forms.IncomingDataForm(request.form)
        data_input = None
        if form.input.data:
            data_input = json.loads(form.input.data)

        name=''
        tags=[]
        if request.args:
            if 'name' in request.args:
                name = request.args['name']
            if 'tags' in request.args:
                tags = request.args.getlist('tags')
            returned_json = running_context.Triggers.execute(form.data.data, data_input, trigger_name=name, tags=tags)
        else:
            returned_json = running_context.Triggers.execute(form.data.data, data_input)

        if not (returned_json["executed"] or returned_json["errors"]):
            return returned_json, SUCCESS_WITH_WARNING
        elif returned_json["errors"]:
            return returned_json, INVALID_INPUT_ERROR
        else:
            current_app.logger.info(
                'Executing triggers with conditional info {0} and input info {1}'.format(form.data.data,
                                                                                         data_input))
            return returned_json, SUCCESS

    return __func()


def create_trigger(trigger_name):
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/execution/listener'])
    def __func():
        form = forms.AddNewTriggerForm(request.form)
        query = running_context.Triggers.query.filter_by(name=trigger_name).first()
        if query is None:
            try:
                json.loads(form.conditional.data)
                running_context.db.session.add(
                    running_context.Triggers(name=trigger_name,
                                             condition=form.conditional.data,
                                             playbook=form.playbook.data,
                                             workflow=form.workflow.data,
                                             tag=form.tag.data))

                running_context.db.session.commit()
                current_app.logger.info('Added trigger: '
                                        '{0}'.format({"name": trigger_name,
                                                      "condition": form.conditional.data,
                                                      "workflow": "{0}-{1}".format(form.playbook.data,
                                                                                   form.workflow.data),
                                                      "tag": form.tag.data}))
                return {},OBJECT_CREATED
            except ValueError:
                current_app.logger.error(
                    'Cannot create trigger {0}. Invalid JSON in conditional field'.format(trigger_name))
                return {"error": 'Invalid JSON in conditional field.'}, INVALID_INPUT_ERROR
        else:
            current_app.logger.warning('Cannot create trigger {0}. Trigger already exists'.format(trigger_name))
            return {"error": "Trigger already exists."}, OBJECT_EXISTS_ERROR

    return __func()


def read_trigger(trigger_name):
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/execution/listener'])
    def __func():
        query = running_context.Triggers.query.filter_by(name=trigger_name).first()
        if query:
            return {"trigger": query.as_json()}, SUCCESS
        else:
            current_app.logger.error('Cannot display trigger {0}. Does not exist'.format(trigger_name))
            return {"error": "Trigger does not exist."}, OBJECT_DNE_ERROR

    return __func()


def update_trigger(trigger_name):
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/execution/listener'])
    def __func():
        form = forms.EditTriggerForm(request.form)
        trigger = running_context.Triggers.query.filter_by(name=trigger_name).first()
        if trigger is not None:
            # Ensures new name is unique
            if form.name.data:
                if len(running_context.Triggers.query.filter_by(name=form.name.data).all()) > 0:
                    return {"error": "Trigger could not be edited."}, OBJECT_EXISTS_ERROR

            result = trigger.edit_trigger(form)

            if result:
                running_context.db.session.commit()
                current_app.logger.info('Edited trigger {0}'.format(trigger))
                return SUCCESS
            else:
                current_app.logger.error('Could not edit trigger {0}. Malformed JSON in conditional'.format(trigger))
                return {"error": "Invalid json in conditional field"}, INVALID_INPUT_ERROR
        else:
            current_app.logger.error('Could not edit trigger {0}. Trigger does not exist'.format(trigger))
            return {"error": "Trigger does not exist."}, OBJECT_DNE_ERROR

    return __func()


def delete_trigger(trigger_name):
    from server.context import running_context

    @roles_accepted(*running_context.user_roles['/execution/listener'])
    def __func():
        query = running_context.Triggers.query.filter_by(name=trigger_name).first()
        if query:
            running_context.Triggers.query.filter_by(name=trigger_name).delete()
            running_context.db.session.commit()
            current_app.logger.info('Deleted trigger {0}'.format(trigger_name))
            return SUCCESS
        else:
            current_app.logger.warning('Cannot delete trigger {0}. Trigger does not exist'.format(trigger_name))
            return {"error": "Trigger does not exist."}, OBJECT_DNE_ERROR

    return __func()
