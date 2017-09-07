from flask import request, current_app
from server.security import roles_accepted_for_resources
from flask_jwt_extended import jwt_required
from server.returncodes import *
from server.database import db


def read_all_triggers():
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('trigger')
    def __func():
        return {"triggers": [trigger.as_json() for trigger in running_context.Triggers.query.all()]}, SUCCESS

    return __func()


def listener():
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('trigger')
    def __func():
        trigger_args = request.get_json()
        if 'inputs' not in trigger_args:
            trigger_args['inputs'] = ''
        returned_json = running_context.Triggers.execute(**trigger_args)
        if not (returned_json["executed"] or returned_json["errors"]):
            return returned_json, SUCCESS_WITH_WARNING
        elif returned_json["errors"]:
            return returned_json, INVALID_INPUT_ERROR
        else:
            current_app.logger.info(
                'Executing triggers with conditional info {0} and input info {1}'.format(trigger_args['data'],
                                                                                         trigger_args['inputs']))
            return returned_json, SUCCESS_ASYNC

    return __func()


def create_trigger(trigger_name):
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('trigger')
    def __func():
        data = request.get_json()
        if 'conditions' not in data:
            data['conditions'] = []
        if 'tag' not in data:
            data['tag'] = ''
        data['name'] = trigger_name
        query = running_context.Triggers.query.filter_by(name=trigger_name).first()
        if query is None:
            db.session.add(
                running_context.Triggers(**data))

            db.session.commit()
            current_app.logger.info('Added trigger: '
                                    '{0}'.format(data))
            return {}, OBJECT_CREATED
        else:
            current_app.logger.warning('Cannot create trigger {0}. Trigger already exists'.format(trigger_name))
            return {"error": "Trigger already exists."}, OBJECT_EXISTS_ERROR

    return __func()


def read_trigger(trigger_name):
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('trigger')
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

    @jwt_required
    @roles_accepted_for_resources('trigger')
    def __func():
        data = request.get_json()
        if 'conditions' not in data:
            data['conditions'] = []
        if 'tag' not in data:
            data['tag'] = ''
        trigger = running_context.Triggers.query.filter_by(name=trigger_name).first()
        if trigger is not None:
            # Ensures new name is unique
            if 'name' in data:
                if len(running_context.Triggers.query.filter_by(name=data['name']).all()) > 0:
                    return {"error": "Trigger could not be edited."}, OBJECT_EXISTS_ERROR

            trigger.edit_trigger(data)

            db.session.commit()
            current_app.logger.info('Edited trigger {0}'.format(trigger))
            return trigger.as_json(), SUCCESS

        else:
            current_app.logger.error('Could not edit trigger {0}. Trigger does not exist'.format(trigger))
            return {"error": "Trigger does not exist."}, OBJECT_DNE_ERROR

    return __func()


def delete_trigger(trigger_name):
    from server.context import running_context

    @jwt_required
    @roles_accepted_for_resources('trigger')
    def __func():
        query = running_context.Triggers.query.filter_by(name=trigger_name).first()
        if query:
            running_context.Triggers.query.filter_by(name=trigger_name).delete()
            db.session.commit()
            current_app.logger.info('Deleted trigger {0}'.format(trigger_name))
            return SUCCESS
        else:
            current_app.logger.warning('Cannot delete trigger {0}. Trigger does not exist'.format(trigger_name))
            return {"error": "Trigger does not exist."}, OBJECT_DNE_ERROR

    return __func()
