import json

from flask import request, current_app, send_file
from flask_jwt_extended import jwt_required

import walkoff.case.database as case_database
from walkoff.case.subscription import Subscription
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
    return current_app.running_context.case_db.session.query(case_database.Case) \
        .filter(case_database.Case.id == case_id).first()


with_case = with_resource_factory('case', case_getter)
with_subscription = with_resource_factory(
    'subscription',
    lambda case_id: CaseSubscription.query.filter_by(id=case_id).first())


def convert_subscriptions(subscriptions):
    return [Subscription(subscription['id'], subscription['events']) for subscription in subscriptions]


def split_subscriptions(subscriptions):
    controller_subscriptions = None
    for i, subscription in enumerate(subscriptions):
        if subscription.id == 'controller':
            controller_subscriptions = subscriptions.pop(i)
    return subscriptions, controller_subscriptions


def read_all_cases():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('cases', ['read']))
    def __func():
        page = request.args.get('page', 1, type=int)
        return [case.as_json() for case in
                CaseSubscription.query.paginate(page, current_app.config['ITEMS_PER_PAGE'], False).items], SUCCESS

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
            case_subscription = CaseSubscription(**data)
            db.session.add(case_subscription)
            db.session.commit()
            case = case_database.Case(name=case_name)
            current_app.running_context.case_db.session.add(case)
            current_app.running_context.case_db.commit()
            if 'subscriptions' in data:
                subscriptions = convert_subscriptions(data['subscriptions'])
                subscriptions, controller_subscriptions = split_subscriptions(subscriptions)
                current_app.running_context.executor.create_case(case.id, subscriptions)
                if controller_subscriptions:
                    current_app.running_context.case_logger.add_subscriptions(case.id, subscriptions)
            current_app.logger.debug('Case added: {0}'.format(case_name))
            return case_subscription.as_json(), OBJECT_CREATED
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
            case = current_app.running_context.case_db.session.query(case_database.Case).filter(
                case_database.Case.name == original_name).first()
            if 'note' in data and data['note']:
                case_obj.note = data['note']
            if 'name' in data and data['name']:
                case_obj.name = data['name']
                if case:
                    case.name = data['name']
                current_app.running_context.case_db.session.commit()
                current_app.logger.debug('Case name changed from {0} to {1}'.format(original_name, data['name']))
            if 'subscriptions' in data:
                case_obj.subscriptions = data['subscriptions']
                subscriptions = convert_subscriptions(data['subscriptions'])
                subscriptions, controller_subscriptions = split_subscriptions(subscriptions)
                current_app.running_context.executor.update_case(case.id, subscriptions)
                if controller_subscriptions:
                    current_app.running_context.case_logger.update_subscriptions(case.id, subscriptions)
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
            case_name = case_obj.name
            db.session.delete(case_obj)
            db.session.commit()
            case = current_app.running_context.case_db.session.query(case_database.Case).filter(
                case_database.Case.name == case_name).first()
            if case:
                current_app.running_context.executor.delete_case(case_id)
                current_app.running_context.case_logger.delete_case(case_id)
                current_app.running_context.case_db.session.delete(case)
            current_app.running_context.case_db.commit()
            current_app.logger.debug('Case deleted {0}'.format(case_id))
            return None, NO_CONTENT
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
            page = request.args.get('page', 1, type=int)
            result = current_app.running_context.case_db.case_events_as_json(case_id)
        except Exception:
            current_app.logger.error('Cannot get events for case {0}. Case does not exist.'.format(case_id))
            return Problem(
                OBJECT_DNE_ERROR,
                'Could not read events for case.',
                'Case {} does not exist.'.format(case_id))

        return result, SUCCESS

    return __func()
