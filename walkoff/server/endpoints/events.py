from flask import request
from flask_jwt_extended import jwt_required

import walkoff.case.database as case_database
from walkoff.server.returncodes import *
from walkoff.server.security import permissions_accepted_for_resources, ResourcePermissions


def update_event_note():
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('cases', ['update']))
    def __func():
        data = request.get_json()
        valid_event_id = case_database.case_db.session.query(case_database.Event) \
            .filter(case_database.Event.id == data['id']).all()
        if valid_event_id:
            case_database.case_db.edit_event_note(data['id'], data['note'])
            return case_database.case_db.event_as_json(data['id']), SUCCESS
        else:
            return {"error": "Event does not exist."}, OBJECT_DNE_ERROR

    return __func()


def read_event(event_id):
    @jwt_required
    @permissions_accepted_for_resources(ResourcePermissions('cases', ['read']))
    def __func():
        valid_event_id = case_database.case_db.session.query(case_database.Event) \
            .filter(case_database.Event.id == event_id).all()
        if valid_event_id:
            return case_database.case_db.event_as_json(event_id), SUCCESS
        else:
            return {"error": "Event does not exist."}, OBJECT_DNE_ERROR

    return __func()
