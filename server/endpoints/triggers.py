import json
from flask import request, current_app
from flask_security import roles_accepted
from server import forms


def get_triggers():
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/execution/listener'])
    def __func():
        return {"status": "success", "triggers": [trigger.as_json()
                                                             for trigger in running_context.Triggers.query.all()]}
    return __func()

def listener():
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/execution/listener'])
    def __func():
        form = forms.IncomingDataForm(request.form)
        data_input = None
        if form.validate():
            if form.input.data:
                data_input = json.loads(form.input.data)
            returned_json = running_context.Triggers.execute(form.data.data, data_input)
            current_app.logger.info(
                'Executing triggers with conditional info {0} and input info {1}'.format(form.data.data,
                                                                                         data_input))
            return returned_json
        else:
            current_app.logger.error('Received invalid form for trigger execution')
            return {}
    return __func()

def create_trigger(trigger_name):
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/execution/listener'])
    def __func():
        form = forms.AddNewTriggerForm(request.form)
        if form.validate():
            query = running_context.Triggers.query.filter_by(name=trigger_name).first()
            if query is None:
                try:
                    json.loads(form.conditional.data)
                    running_context.db.session.add(
                        running_context.Triggers(name=trigger_name,
                                                 condition=form.conditional.data,
                                                 playbook=form.playbook.data,
                                                 workflow=form.workflow.data))

                    running_context.db.session.commit()
                    current_app.logger.info('Added trigger: '
                                            '{0}'.format({"name": trigger_name,
                                                                     "condition": form.conditional.data,
                                                                     "workflow": "{0}-{1}".format(form.playbook.data,
                                                                                                  form.workflow.data)}))
                    return {"status": "success"}
                except ValueError:
                    current_app.logger.error(
                        'Cannot create trigger {0}. Invalid JSON in conditional field'.format(trigger_name))
                    return {"status": "error: invalid json in conditional field"}
            else:
                current_app.logger.warning('Cannot create trigger {0}. Trigger already exists'.format(trigger_name))
                return {"status": "warning: trigger with that name already exists"}
        current_app.logger.error('Cannot create trigger {0}. Invalid form'.format(trigger_name))
        return {"status": "error: form not valid"}
    return __func()

def read_trigger(trigger_name):
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/execution/listener'])
    def __func():
        query = running_context.Triggers.query.filter_by(name=trigger_name).first()
        if query:
            return {"status": 'success', "trigger": query.as_json()}
        current_app.logger.error('Cannot display trigger {0}. Does not exist'.format(trigger_name))
        return {"status": "error: trigger not found"}
    return __func()

def update_trigger(trigger_name):
    from server.context import running_context
    @roles_accepted(*running_context.user_roles['/execution/listener'])
    def __func():
        form = forms.EditTriggerForm(request.form)
        trigger = running_context.Triggers.query.filter_by(name=trigger_name).first()
        if form.validate() and trigger is not None:
            # Ensures new name is unique
            if form.name.data:
                if len(running_context.Triggers.query.filter_by(name=form.name.data).all()) > 0:
                    return {"status": "error: duplicate names found. Trigger could not be edited"}

            result = trigger.edit_trigger(form)

            if result:
                running_context.db.session.commit()
                current_app.logger.info('Edited trigger {0}'.format(trigger))
                return {"status": "success"}
            else:
                current_app.logger.error('Could not edit trigger {0}. Malformed JSON in conditional'.format(trigger))
                return {"status": "error: invalid json in conditional field"}
        current_app.logger.error('Could not edit trigger {0}. Form is invalid'.format(trigger))
        return {"status": "trigger could not be edited"}
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
            return {"status": "success"}
        elif query is None:
            current_app.logger.warning('Cannot delete trigger {0}. Trigger does not exist'.format(trigger_name))
            return {"status": "error: trigger does not exist"}
        return {"status": "error: could not remove trigger"}
    return __func()
