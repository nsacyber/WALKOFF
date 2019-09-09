from flask import request, current_app
from flask_jwt_extended import jwt_required

from api_gateway.extensions import db

from api_gateway.server.problem import Problem
from http import HTTPStatus
from api_gateway.serverdb.buckets import Bucket
from api_gateway.serverdb.buckets import BucketTrigger as Trigger


@jwt_required
def read_all_triggers(bucket_id):
    b = Bucket.query.filter_by(id=bucket_id).first()
    if b:
        return [trigger.as_json() for trigger in b.triggers], HTTPStatus.OK
    else:
        return [], HTTPStatus.NOT_FOUND

@jwt_required
def create_trigger(bucket_id):
    json_data = request.get_json()
    b = Bucket.query.filter_by(id=bucket_id).first()
    if b:
        trigger_params = {'workflow': json_data['workflow'],
            'event_type': json_data['event_type'] if 'event_type' in json_data else 'unspecified',
            'prefix': json_data['prefix'] if 'prefix' in json_data else '',
            'suffix': json_data['suffix'] if 'suffix' in json_data else ''}
        new_trigger = Trigger(**trigger_params)
        b.triggers.append(new_trigger)
        db.session.add(b)
        db.session.commit()
        return new_trigger.as_json(), HTTPStatus.CREATED
    else:
        return [], HTTPStatus.NOT_FOUND

@jwt_required
def read_trigger(bucket_id, trigger_id):
    t = Trigger.query.filter_by(id=trigger_id, bucket_id=bucket_id).first()
    if t:
        return t.as_json(), HTTPStatus.OK
    else:
        return [], HTTPStatus.NOT_FOUND



@jwt_required
def update_trigger(bucket_id, trigger_id):
    json_data = request.get_json()
    t = Trigger.query.filter_by(id=trigger_id, bucket_id=bucket_id).first()
    if t:
        if 'workflow' in json_data:
            t.workflow = json_data['workflow']
        if 'event_type' in json_data:
            t.event_type = json_data['event_type']
        if 'prefix' in json_data:
            t.prefix = json_data['prefix']
        if 'suffix' in json_data:
            t.suffix = json_data['suffix']
        db.session.add(t)
        db.session.commit()
        current_app.logger.info(f"Edited trigger {trigger_id} to {json_data}")
        return t.as_json(), HTTPStatus.OK
    else:
        return [], HTTPStatus.NOT_FOUND

@jwt_required
def delete_trigger(bucket_id, trigger_id):
    t = Trigger.query.filter_by(id=trigger_id, bucket_id=bucket_id).first()
    if t:
        db.session.delete(t)
        db.session.commit()
        return None, HTTPStatus.NO_CONTENT
    else:
        return [], HTTPStatus.NOT_FOUN
