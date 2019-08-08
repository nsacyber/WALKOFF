import json
from copy import deepcopy
from io import BytesIO
import requests

from common.config import static
from flask import request, current_app, send_file
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError
from sqlalchemy import exists, and_
from sqlalchemy.exc import IntegrityError

from api_gateway import helpers
from api_gateway.executiondb.workflow import Workflow, WorkflowSchema
from api_gateway.helpers import regenerate_workflow_ids
# from api_gateway.helpers import strip_device_ids, strip_argument_ids
from api_gateway.security import permissions_accepted_for_resources, ResourcePermissions
from api_gateway.server.decorators import with_resource_factory, validate_resource_exists_factory, is_valid_uid, \
    paginate
from api_gateway.server.problem import unique_constraint_problem, improper_json_problem, invalid_input_problem
from http import HTTPStatus


# @jwt_required
def list_all_files(app_name, app_version):

    headers = {'content-type': 'application/json'}
    payload = {'app_name': app_name, 'app_version': app_version}
    url = f"http://{static.UMPIRE_SERVICE}:8000/umpire/files"
    r = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)

    if r.status_code == 200:
        return r.json(), HTTPStatus.OK
    else:
        return "Failed", HTTPStatus.BAD_REQUEST


# @jwt_required
def get_file_contents(app_name, app_version, file_path):

    # data = request.get_json()
    # file_path = data.get("file_path")
    headers = {'content-type': 'application/json'}
    payload = {'app_name': app_name, 'app_version': app_version, 'file_path': file_path}
    url = f"http://{static.UMPIRE_SERVICE}:8000/umpire/file"
    r = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)

    if r.status_code == 200:
        return r.json(), HTTPStatus.OK
    else:
        return "Failed", HTTPStatus.BAD_REQUEST


# @jwt_required
def update_file():

    data = request.get_json()
    app_name = data.get("app_name")
    app_version = data.get("app_version")
    file_path = data.get("file_path")
    file_data = data.get("file_data")

    headers = {'content-type': 'application/json'}
    payload = {'app_name': app_name, 'app_version': app_version, 'file_path': file_path, 'file_data': file_data}
    url = f"http://{static.UMPIRE_SERVICE}:8000/umpire/file-upload"
    r = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)

    if r.status_code == 200:
        return r.text, HTTPStatus.OK
    else:
        return "Failed", HTTPStatus.BAD_REQUEST


# @jwt_required
def get_build_status():
    headers = {'content-type': 'application/json'}
    url = f"http://{static.UMPIRE_SERVICE}:8000/umpire/build"
    r = requests.get(url, headers=headers, verify=False)

    if r.status_code == 200:
        return r.text, HTTPStatus.OK
    else:
        return "Failed", HTTPStatus.BAD_REQUEST


# @jwt_required
def build_image(app_name, app_version):
    headers = {'content-type': 'application/json'}
    payload = {'app_name': app_name, 'app_version': app_version}
    url = f"http://{static.UMPIRE_SERVICE}:8000/umpire/build"
    r = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)

    if r.status_code == 200:
        return r.text, HTTPStatus.OK
    else:
        return "Failed", HTTPStatus.BAD_REQUEST


# @jwt_required
def build_status_from_id(build_id):
    headers = {'content-type': 'application/json'}
    url = f"http://{static.UMPIRE_SERVICE}:8000/umpire/build/{build_id}"
    r = requests.post(url, headers=headers, verify=False)

    if r.status_code == 200:
        return r.text, HTTPStatus.OK
    else:
        return "Failed", HTTPStatus.BAD_REQUEST


# # @jwt_required
# def save_file(app_name, app_version):
#     headers = {'content-type': 'application/json'}
#     payload = {'app_name': app_name, 'app_version': app_version}
#     url = f"http://{static.UMPIRE_SERVICE}:8000/umpire/save"
#     r = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)
#
#     if r.status_code == 200:
#         return r.text, HTTPStatus.OK
#     else:
#         return "Failed", HTTPStatus.BAD_REQUEST