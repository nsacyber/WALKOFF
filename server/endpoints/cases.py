import json
import os
from flask import request, current_app
from flask_security import auth_token_required, roles_accepted
import core.case.database as case_database
import core.case.subscription as case_subscription
from server import forms
from core.case.subscription import CaseSubscriptions, add_cases, delete_cases, \
    rename_case
import core.config.config
import core.config.paths
from core.helpers import construct_workflow_name_key
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_ADDED, EVENT_JOB_REMOVED, \
    EVENT_SCHEDULER_START, EVENT_SCHEDULER_SHUTDOWN, EVENT_SCHEDULER_PAUSED, EVENT_SCHEDULER_RESUMED
from server.return_codes import *


def read_all_cases():
    from server.flaskserver import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        return case_database.case_db.cases_as_json(), SUCCESS
    return __func()


def create_case():
    from server.flaskserver import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        data = request.get_json()
        case = data['case']

        case_obj = CaseSubscriptions()
        add_cases({"{0}".format(str(case)): case_obj})
        case_obj = running_context.CaseSubscription.query.filter_by(name=case).first()
        if case_obj is None:
            running_context.db.session.add(running_context.CaseSubscription(name=case))
            running_context.db.session.commit()
            current_app.logger.debug('Case added: {0}'.format(case))
            return case_subscription.subscriptions_as_json(), OBJECT_CREATED
        else:
            current_app.logger.warning('Cannot create case {0}. Case already exists.'.format(case))
            return {"error": "Case already exists."}, OBJECT_EXISTS_ERROR
    return __func()


def read_case(case_id):
    from server.flaskserver import running_context

    @auth_token_required
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


def update_case():
    from server.flaskserver import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        data = request.get_json()
        case_obj = running_context.CaseSubscription.query.filter_by(id=data['id']).first()
        if case_obj:
            if 'note' in data and data['note']:
                case_database.case_db.edit_case_note(data['id'], data['note'])
            if 'name' in data and data['name']:
                rename_case(case_obj.name, data['name'])
                case_obj.name = data['name']
                running_context.db.session.commit()
                current_app.logger.debug('Case name changed to {0} for Case {1}'.format(data['name'], data['id']))
            return case_database.case_db.cases_as_json(), SUCCESS
        else:
            current_app.logger.error('Cannot update case {0}. Case does not exist.'.format(data['id']))
            return {"error": "Case does not exist."}, OBJECT_DNE_ERROR

    return __func()


def delete_case(case_id):
    from server.flaskserver import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        case_obj = running_context.CaseSubscription.query.filter_by(id=case_id).first()
        delete_cases([case_obj.name])
        if case_obj:
            running_context.db.session.delete(case_obj)
            running_context.db.session.commit()
            current_app.logger.debug('Case deleted {0}'.format(case_id))
            return case_subscription.subscriptions_as_json(), SUCCESS
        else:
            current_app.logger.error('Cannot delete case {0}. Case does not exist.'.format(case_id))
            return {"error": "Case does not exist."}, OBJECT_DNE_ERROR
    return __func()


def import_cases():
    from server.flaskserver import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        data = request.get_json()
        filename = data['filename'] if 'filename' in data and data['filename'] else core.config.paths.default_case_export_path
        if os.path.isfile(filename):
            try:
                with open(filename, 'r') as cases_file:
                    cases_file = cases_file.read()
                    cases_file = cases_file.replace('\n', '')
                    cases = json.loads(cases_file)
                case_subscription.add_cases(cases)
                for case in cases.keys():
                    running_context.db.session.add(running_context.CaseSubscription(name=case))
                    running_context.CaseSubscription.update(case)
                    running_context.db.session.commit()
                return {"cases": case_subscription.subscriptions_as_json()}, SUCCESS
            except (OSError, IOError) as e:
                current_app.logger.error('Error importing cases from file {0}: {1}'.format(filename, e))
                return {"error": "Error reading file."}, IO_ERROR
            except ValueError as e:
                current_app.logger.error('Error importing cases from file {0}: Invalid JSON {1}'.format(filename, e))
                return {"error": "Invalid JSON file."}, INVALID_INPUT_ERROR
        else:
            current_app.logger.debug('Cases successfully imported from {0}'.format(filename))
            return {"error": "File does not exist."}, IO_ERROR
    return __func()


def export_cases():
    from server.flaskserver import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        data = request.get_json()
        filename = data['filename'] if 'filename' in data and data['filename'] else core.config.paths.default_case_export_path
        try:
            with open(filename, 'w') as cases_file:
                cases_file.write(json.dumps(case_subscription.subscriptions_as_json()))
            current_app.logger.debug('Cases successfully exported to {0}'.format(filename))
            return SUCCESS
        except (OSError, IOError) as e:
            current_app.logger.error('Error exporting cases to {0}: {1}'.format(filename, e))
            return {"error": "Could not write to file."}, IO_ERROR
    return __func()


def read_all_subscriptions():
    from server.flaskserver import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        return case_subscription.subscriptions_as_json(), SUCCESS
    return __func()


def read_all_events(case):
    from server.flaskserver import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        try:
            result = case_database.case_db.case_events_as_json(case)
        except:
            current_app.logger.error('Cannot get events for case {0}. Case does not exist.'.format(case))
            return {"error": "Case does not exist."}, OBJECT_DNE_ERROR

        return result, SUCCESS
    return __func()


def create_subscription(case, element):
    from server.flaskserver import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        events = element['events']
        if len(element['ancestry']) == 1 and events:
            events = convert_scheduler_events(events)
        converted_ancestry = convert_ancestry(element['ancestry'])
        result = case_subscription.add_subscription(case, converted_ancestry, events)
        if result:
            running_context.CaseSubscription.update(case)
            running_context.db.session.commit()
            current_app.logger.debug('Subscription added for {0} to {1}'.format(converted_ancestry, events))
            return case_subscription.subscriptions_as_json(), OBJECT_CREATED
        else:
            current_app.logger.error("Cannot create subscription for case {0}. Case does not exist".format(case))
            return {"error": "Case does not exist."}, OBJECT_DNE_ERROR
    return __func()


def read_subscription(case):
    from server.flaskserver import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        if case in core.case.subscription.subscriptions:
            try:
                result = core.case.subscription.subscriptions[case].as_json(names=True)
                return result, SUCCESS
            except KeyError:
                current_app.logger.error("Cannot get subscriptions for case {0}. Case does not exist".format(case))
                return {"error": "case does not exist"}, OBJECT_DNE_ERROR
    return __func()


def convert_ancestry(ancestry):
    if len(ancestry) >= 3:
        ancestry[1] = construct_workflow_name_key(ancestry[1], ancestry[2])
        del ancestry[2]
    return ancestry

__scheduler_event_conversion = {'Scheduler Start': EVENT_SCHEDULER_START,
                                'Scheduler Shutdown': EVENT_SCHEDULER_SHUTDOWN,
                                'Scheduler Paused': EVENT_SCHEDULER_PAUSED,
                                'Scheduler Resumed': EVENT_SCHEDULER_RESUMED,
                                'Job Added': EVENT_JOB_ADDED,
                                'Job Removed': EVENT_JOB_REMOVED,
                                'Job Executed': EVENT_JOB_EXECUTED,
                                'Job Error': EVENT_JOB_ERROR}


def convert_scheduler_events(events):
    return [__scheduler_event_conversion[event] for event in events if event in __scheduler_event_conversion]


def convert_to_event_names(events):
    result = []
    for event in events:
        for key in __scheduler_event_conversion:
            if __scheduler_event_conversion[key] == event:
                result.append(key)
    return result


def update_subscription(case, element):
    from server.flaskserver import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/cases'])
    def __func(element):
        ancestry = convert_ancestry(element['ancestry'])
        if len(ancestry) == 1 and element['events']:
            element['events'] = convert_scheduler_events(element['events'])
        success = case_subscription.edit_subscription(case, ancestry, element['events'])
        running_context.CaseSubscription.update(case)
        running_context.db.session.commit()
        if success:
            current_app.logger.info('Edited subscription {0} to {1}'.format(ancestry, element['events']))
            return case_subscription.subscriptions_as_json(), SUCCESS
        else:
            current_app.logger.error('Error occurred while editing subscription '
                                     '{0} to {1}'.format(ancestry, element['events']))
            return {"error": "Case or element does not exist."}, OBJECT_DNE_ERROR
    return __func(element)


def delete_subscription(case, ancestry):
    from server.flaskserver import running_context

    @auth_token_required
    @roles_accepted(*running_context.user_roles['/cases'])
    def __func():
        converted_ancestry = convert_ancestry(ancestry['ancestry'])
        result = case_subscription.remove_subscription_node(case, converted_ancestry)
        if result:
            running_context.CaseSubscription.update(case)
            running_context.db.session.commit()
            current_app.logger.debug('Deleted subscription {0}'.format(converted_ancestry))
            return case_subscription.subscriptions_as_json()
        else:
            return {'error': 'Case or element does not exist.'}, OBJECT_DNE_ERROR
    return __func()
