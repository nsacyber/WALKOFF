from flask import request, current_app
from flask_jwt_extended import jwt_required

from api_gateway.extensions import db
from api_gateway.security import admin_required

from api_gateway.server.problem import Problem
from http import HTTPStatus
from api_gateway.serverdb.buckets import Bucket


@jwt_required
def read_all_buckets():
    page = request.args.get('page', 1, type=int)

    return [bucket.as_json() for bucket in Bucket.query.paginate(page, current_app.config['ITEMS_PER_PAGE'], False).items], HTTPStatus.OK


@jwt_required
def create_bucket():
    json_data = request.get_json()
    if not Bucket.query.filter_by(name=json_data['name']).first():
        bucket_params = {'name': json_data['name'],
                        'description': json_data['description'] if 'description' in json_data else '',
                        'triggers' : [_create_trigger(x) for x in json_data["triggers"]] if 'triggers' in json_data else []
                        }
        new_bucket = Bucket(**bucket_params)
        added = new_bucket.create_bucket_in_minio(new_bucket.name)
        if added:
            db.session.add(new_bucket)
            db.session.commit()
        else:
            db.session.expire(new_bucket)

        current_app.logger.info(f"Bucket added: {bucket_params}")
        return new_bucket.as_json(), HTTPStatus.CREATED
    else:
        current_app.logger.warning(f"Bucket with name {json_data['name']} already exists")
        return Problem.from_crud_resource(
            HTTPStatus.BAD_REQUEST,
            'bucket',
            'create',
            f"Bucket with name {json_data['name']} already exists")

def _create_trigger(json_data):
    out = {'workflow': json_data['workflow'],
            'event_type': json_data['event_type'] if 'event_type' in json_data else 'unspecified',
            'prefix': json_data['prefix'] if 'prefix' in json_data else '',
            'suffix': json_data['suffix'] if 'suffix' in json_data else ''}
    return out


@jwt_required
def read_bucket(bucket_id):
    q = Bucket.query.filter_by(id=bucket_id).first()
    if q:
        return q.as_json(), HTTPStatus.OK
    else:
        return [], HTTPStatus.NOT_FOUND


@jwt_required
def update_bucket(bucket_id):
    json_data = request.get_json()
    b = Bucket.query.filter_by(id=bucket_id).first()
    if b:
        if 'name' in json_data:
            added = b.create_bucket_in_minio(json_data["name"])
            removed = b.remove_bucket_in_minio(b.name)

            b.name = json_data["name"]
            db.session.commit()

        if 'description' in json_data:
            b.description = json_data['description']

        db.session.commit()
        current_app.logger.info(f"Edited bucket {bucket_id} to {json_data}")
        return b.as_json(), HTTPStatus.OK
    else:
        return [], HTTPStatus.NOT_FOUND

@jwt_required
def delete_bucket(bucket_id):
    b = Bucket.query.filter_by(id=bucket_id).first()
    if b:
        status = b.remove_bucket_in_minio(b.name)
        if status:
            db.session.delete(b)
            db.session.commit()
            return None, HTTPStatus.NO_CONTENT
    return None, HTTPStatus.NOT_FOUND
