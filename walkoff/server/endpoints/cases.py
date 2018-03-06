import json

from flask import request, current_app, send_file
from flask_jwt_extended import jwt_required

import walkoff.case.database as case_database
import walkoff.case.subscription as case_subscription
from walkoff.case.subscription import delete_cases
from walkoff.security import permissions_accepted_for_resources, ResourcePermissions
from walkoff.server.decorators import with_resource_factory
from walkoff.server.problem import Problem
from walkoff.server.returncodes import *
from walkoff.serverdb import db
from walkoff.serverdb.casesubscription import CaseSubscription

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


def case_getter(case_id):
    return case_database.case_db.session.query(case_database.Case) \
        .filter(case_database.Case.id == case_id).first()


with_case = with_resource_factory('case', case_getter)
with_subscription = with_resource_factory(
    'subscription',
    lambda case_id: CaseSubscription.query.filter_by(id=case_id).first())


def read_all_cases():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('cases', ['read']))
    def __func():
        return [case.as_json() for case in CaseSubscription.query.all()], SUCCESS

    return __func()


def create_case():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('cases', ['create']))
    def __func():
        if request.files and 'file' in request.files:
            f = request.files['file']
            data = json.loads(f.read().decode('utf-8'))
        else:
            data = request.get_json()
        case_name = data['name']
        case_obj = CaseSubscription.query.filter_by(name=case_name).first()
        if case_obj is None:
            case = CaseSubscription(**data)
            db.session.add(case)
            db.session.commit()
            current_app.logger.debug('Case added: {0}'.format(case_name))
            return case.as_json(), OBJECT_CREATED
        else:
            current_app.logger.warning('Cannot create case {0}. Case already exists.'.format(case_name))
            return Problem.from_crud_resource(
                OBJECT_EXISTS_ERROR,
                'case',
                'create',
                'Case with name {} already exists.'.format(case_name))

    return __func()


def read_case(case_id, mode=None):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('cases', ['read']))
    @with_case('read', case_id)
    def __func(case_obj):
        if mode == "export":
            f = StringIO()
            f.write(json.dumps(case_obj.as_json(), sort_keys=True, indent=4, separators=(',', ': ')))
            f.seek(0)
            return send_file(f, attachment_filename=case_obj.name + '.json', as_attachment=True), SUCCESS
        else:
            return case_obj.as_json(), SUCCESS

    return __func()


def update_case():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('cases', ['update']))
    def __func():
        data = request.get_json()
        case_obj = CaseSubscription.query.filter_by(id=data['id']).first()
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
                case_obj.subscriptions = data['subscriptions']
                subscriptions = {subscription['id']: subscription['events'] for subscription in data['subscriptions']}
                for uid, events in subscriptions.items():
                    case_subscription.modify_subscription(case_name, uid, events)
            db.session.commit()
            return case_obj.as_json(), SUCCESS
        else:
            current_app.logger.error('Cannot update case {0}. Case does not exist.'.format(data['id']))
            return Problem.from_crud_resource(
                OBJECT_DNE_ERROR,
                'case.',
                'update',
                'Case {} does not exist.'.format(data['id']))

    return __func()


def patch_case():
    return update_case()


def delete_case(case_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('cases', ['delete']))
    def __func():
        case_obj = CaseSubscription.query.filter_by(id=case_id).first()
        if case_obj:
            delete_cases([case_obj.name])
            db.session.delete(case_obj)
            db.session.commit()
            current_app.logger.debug('Case deleted {0}'.format(case_id))
            return {}, NO_CONTENT
        else:
            current_app.logger.error('Cannot delete case {0}. Case does not exist.'.format(case_id))
            return Problem.from_crud_resource(
                OBJECT_DNE_ERROR,
                'case',
                'delete',
                'Case {} does not exist.'.format(case_id))

    return __func()


def read_all_events(case_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('cases', ['read']))
    def __func():
        try:
            result = case_database.case_db.case_events_as_json(case_id)
        except Exception:
            current_app.logger.error('Cannot get events for case {0}. Case does not exist.'.format(case_id))
            return Problem(
                OBJECT_DNE_ERROR,
                'Could not read events for case.',
                'Case {} does not exist.'.format(case_id))

        return result, SUCCESS

    return __func()
