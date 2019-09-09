import json
import logging
from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends

from marshmallow import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, StatementError

from api.server.db import get_db
from api.server.db.appapi import AppApi, AppApiModel, AppApiSchema
from api.server.utils.problem import improper_json_problem, unique_constraint_problem

from common.helpers import validate_uuid

# from api_gateway import helpers
# # ToDo: investigate why these imports are needed (AppApi will not have valid reference to actions if this isn't here
# from api_gateway.executiondb.action import ActionApi
# from api_gateway.executiondb.appapi import AppApi, AppApiSchema
# from api_gateway.security import permissions_accepted_for_resources, ResourcePermissions
# from api_gateway.server.problem import Problem, unique_constraint_problem, improper_json_problem, invalid_input_problem
# from api_gateway.server.decorators import with_resource_factory, is_valid_uid, paginate


router = APIRouter()
logger = logging.getLogger(__name__)


def app_api_getter(db_session: Session, app_api: str):
    if validate_uuid(app_api):
        return db_session.query(AppApi).filter_by(id_=app_api).first()
    else:
        return db_session.query(AppApi).filter_by(name=app_api).first()


app_api_schema = AppApiSchema()
# with_app_api = with_resource_factory('app_api', app_api_getter)


# ToDo: App APIs should be stored in some nosql db instead to avoid this
def add_locations(app_api):
    app_name = app_api.name
    for action in app_api.actions:
        action['location'] = f"{app_name}.{action.name}"
        for param in action.get('parameters', []):
            param['location'] = f"{app_name}.{action.name}:{param.name}"
        if action.get('returns'):
            action.returns.location = f"{app_name}.{action.name}.returns"
    return app_api


def remove_locations(app_api):
    for action in app_api.get('actions', []):
        action.pop('location', None)
        for param in action.get('parameters', []):
            param.pop('location', None)
        if action.get('returns'):
            action['returns'].pop('location', None)
    return app_api


@router.get("/names")
async def read_all_app_names(db_session: Session = Depends(get_db)):
    qr = db_session.query(AppApi).order_by(AppApi.name).all()
    r = [result.name for result in qr]
    return r


@router.get("/apis")
def read_all_app_apis(db_session: Session = Depends(get_db)):
    ret = []
    for app_api in db_session.query(AppApi).order_by(AppApi.name).all():
        ret.append(remove_locations(app_api_schema.dump(app_api)))
    return ret


@router.post("/apis", status_code=HTTPStatus.CREATED)
def create_app_api(*, db_session: Session = Depends(get_db), new_api: AppApiModel):

    # new_api = dict(new_api)

    # if request.files and 'file' in request.files:
    #     data = json.loads(request.files['file'].read().decode('utf-8'))

    # add_locations(new_api)

    try:
        # ToDo: make a proper common type for this when the other components need it
        app_api = app_api_schema.load(dict(new_api), session=db_session)
        db_session.add(app_api)
        db_session.commit()
        logger.info(f"Created App API {app_api.name} ({app_api.id_})")
        return app_api_schema.dump(app_api)
    except ValidationError as e:
        db_session.rollback()
        return improper_json_problem('app_api', 'create', new_api.name, e.messages)
    except IntegrityError:
        db_session.rollback()
        return unique_constraint_problem('app_api', 'create', new_api.name)

#
# @jwt_required
# @permissions_accepted_for_resources(ResourcePermissions('app_apis', ['read']))
# def read_all_app_apis():
#     ret = []
#     for app_api in db_session.query(AppApi).order_by(AppApi.name).all():
#         ret.append(remove_locations(app_api_schema.dump(app_api)))
#     return ret, HTTPStatus.OK
#
#
# @jwt_required
# @permissions_accepted_for_resources(ResourcePermissions('app_apis', ['read']))
# @with_app_api('read', 'app')
# def read_app_api(app):
#     return remove_locations(app_api_schema.dump(app)), HTTPStatus.OK
#
#
# @jwt_required
# @permissions_accepted_for_resources(ResourcePermissions('app_apis', ['update']))
# @with_app_api('update', 'app')
# def update_app_api(app):
#     data = request.get_json()
#     add_locations(data)
#     try:
#         app_api_schema.load(data, instance=app)
#         db_session.commit()
#         current_app.logger.info(f"Updated app_api {app.name} ({app.id_})")
#         return app_api_schema.dump(app), HTTPStatus.OK
#     except IntegrityError:
#         db_session.rollback()
#         return unique_constraint_problem('app_api', 'update', app.id_)
#
#
# @jwt_required
# @permissions_accepted_for_resources(ResourcePermissions('app_apis', ['delete']))
# @with_app_api('delete', 'app')
# def delete_app_api(app):
#     db_session.delete(app)
#     current_app.logger.info(f"Removed app_api {app.name} ({app.id_})")
#     db_session.commit()
#     return None, HTTPStatus.NO_CONTENT
