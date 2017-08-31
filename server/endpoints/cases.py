import json
import os
from flask import request, current_app
from server.security import jwt_required, roles_accepted
import core.case.database as case_database
import core.case.subscription as case_subscription
from core.case.subscription import delete_cases, convert_to_event_names
import core.config.config
import core.config.paths
from core.helpers import format_exception_message
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, \
    EVENT_SCHEDULER_START, EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED
from server.returncodes import *
from server.database import db


@jwt_required
def read_all_cases():
    from server.flaskserver import running_context

    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        return [case.as_json() for case in running_context.CaseSubscription.query.all()], SUCCESS

    return __func()


@jwt_required
def create_case(body):
    from server.flaskserver import running_context

    @roles_accepted(*running_context.user_roles['/cases'])
    def __func(body):
        data = request.get_json()
        case_name = data['name']
        case_obj = running_context.CaseSubscription.query.filter_by(name=case_name).first()
        if case_obj is None:
            case = running_context.CaseSubscription(**data)
            db.session.add(case)
            db.session.commit()
            current_app.logger.debug('Case added: {0}'.format(case_name))
            return case.as_json(), OBJECT_CREATED
        else:
            current_app.logger.warning('Cannot create case {0}. Case already exists.'.format(case_name))
            return {"error": "Case already exists."}, OBJECT_EXISTS_ERROR

    return __func(body)


@jwt_required
def read_case(case_id):
    from server.flaskserver import running_context

    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        case_obj = case_database.case_db.session.query(case_database.Case) \
            .filter(case_database.Case.id == case_id).first()
        if case_obj:
            return case_obj.as_json(), SUCCESS
        else:
            current_app.logger.error('Cannot read case {0}. Case does not exist.'.format(case_id))
            return {'error': 'Case does not exist.'}, OBJECT_DNE_ERROR

    return __func()


@jwt_required
def update_case(body):
    from server.flaskserver import running_context

    @roles_accepted(*running_context.user_roles['/cases'])
    def __func(body):
        data = request.get_json()
        case_obj = running_context.CaseSubscription.query.filter_by(id=data['id']).first()
        if case_obj:
            original_name = case_obj.name
            case_name = data['name'] if 'name' in data else original_name

            if 'note' in data and data['note']:
                case_obj.note = data['note']
            if 'name' in data and data['name']:
                case_subscription.rename_case(case_obj.name, data['name'])
                case_obj.name = data['name']
                db.session.commit()
                current_app.logger.debug('Case name changed from {0} to {1}'.format(original_name, data['name']))
            if 'subscriptions' in data:
                case_obj.subscriptions = json.dumps(data['subscriptions'])
                subscriptions = {subscription['uid']: subscription['events'] for subscription in data['subscriptions']}
                if 'controller' in subscriptions:
                    subscriptions['controller'] = convert_to_event_names(subscriptions['controller'])
                for uid, events in subscriptions.items():
                    case_subscription.modify_subscription(case_name, uid, events)
            db.session.commit()
            return case_obj.as_json(), SUCCESS
        else:
            current_app.logger.error('Cannot update case {0}. Case does not exist.'.format(data['id']))
            return {"error": "Case does not exist."}, OBJECT_DNE_ERROR

    return __func(body)


@jwt_required
def delete_case(case_id):
    from server.flaskserver import running_context

    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        case_obj = running_context.CaseSubscription.query.filter_by(id=case_id).first()
        if case_obj:
            delete_cases([case_obj.name])
            db.session.delete(case_obj)
            db.session.commit()
            current_app.logger.debug('Case deleted {0}'.format(case_id))
            return {}, SUCCESS
        else:
            current_app.logger.error('Cannot delete case {0}. Case does not exist.'.format(case_id))
            return {"error": "Case does not exist."}, OBJECT_DNE_ERROR

    return __func()


@jwt_required
def import_cases(body):
    from server.flaskserver import running_context

    @roles_accepted(*running_context.user_roles['/cases'])
    def __func(body):
        data = request.get_json()
        filename = (data['filename'] if (data is not None and 'filename' in data and data['filename'])
                    else core.config.paths.default_case_export_path)
        if os.path.isfile(filename):
            try:
                with open(filename, 'r') as cases_file:
                    cases_file = cases_file.read()
                    cases_file = cases_file.replace('\n', '')
                    cases = json.loads(cases_file)
                case_subscription.add_cases(cases)
                for case in cases:
                    db.session.add(running_context.CaseSubscription(name=case))
                    running_context.CaseSubscription.update(case)
                db.session.commit()
                return {"cases": case_subscription.subscriptions}, SUCCESS
            except (OSError, IOError) as e:
                current_app.logger.error('Error importing cases from file '
                                         '{0}: {1}'.format(filename, format_exception_message(e)))
                return {"error": "Error reading file."}, IO_ERROR
            except ValueError as e:
                current_app.logger.error('Error importing cases from file {0}: '
                                         'Invalid JSON {1}'.format(filename, format_exception_message(e)))
                return {"error": "Invalid JSON file."}, INVALID_INPUT_ERROR
        else:
            current_app.logger.debug('Cases successfully imported from {0}'.format(filename))
            return {"error": "File does not exist."}, IO_ERROR

    return __func(body)


@jwt_required
def export_cases(body):
    from server.flaskserver import running_context

    @roles_accepted(*running_context.user_roles['/cases'])
    def __func(body):
        data = request.get_json()
        filename = (data['filename'] if (data is not None and 'filename' in data and data['filename'])
                    else core.config.paths.default_case_export_path)
        try:
            with open(filename, 'w') as cases_file:
                cases_file.write(json.dumps(case_subscription.subscriptions))
            current_app.logger.debug('Cases successfully exported to {0}'.format(filename))
            return SUCCESS
        except (OSError, IOError) as e:
            current_app.logger.error('Error exporting cases to {0}: {1}'.format(filename, format_exception_message(e)))
            return {"error": "Could not write to file."}, IO_ERROR

    return __func(body)


@jwt_required
def read_all_events(case):
    from server.flaskserver import running_context

    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        try:
            result = case_database.case_db.case_events_as_json(case)
        except:
            current_app.logger.error('Cannot get events for case {0}. Case does not exist.'.format(case))
            return {"error": "Case does not exist."}, OBJECT_DNE_ERROR

        return result, SUCCESS

    return __func()


__scheduler_event_conversion = {'Scheduler Start': EVENT_SCHEDULER_START,
                                'Scheduler Shutdown': EVENT_SCHEDULER_SHUTDOWN,
                                'Scheduler Paused': EVENT_SCHEDULER_PAUSED,
                                'Scheduler Resumed': EVENT_SCHEDULER_RESUMED,
                                'Job Added': EVENT_JOB_ADDED,
                                'Job Removed': EVENT_JOB_REMOVED,
                                'Job Executed': EVENT_JOB_EXECUTED,
                                'Job Error': EVENT_JOB_ERROR}
