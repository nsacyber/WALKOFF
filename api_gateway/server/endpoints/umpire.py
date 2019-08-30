import json
import requests

from common.config import static
from flask import request, current_app, send_file
from flask_jwt_extended import jwt_required
from http import HTTPStatus


@jwt_required
def list_all_files(app_name, app_version):

    headers = {'content-type': 'application/json'}
    payload = {'app_name': app_name, 'app_version': app_version}
    url = f"http://{static.UMPIRE_SERVICE}:8000/umpire/files"
    r = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)

    if r.status_code == 200:
        return r.json(), HTTPStatus.OK
    else:
        return r.text, HTTPStatus.BAD_REQUEST


@jwt_required
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
        return r.text, HTTPStatus.BAD_REQUEST


@jwt_required
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
        return r.json(), HTTPStatus.OK
    else:
        return r.text, HTTPStatus.BAD_REQUEST


@jwt_required
def get_build_status():
    headers = {'content-type': 'application/json'}
    url = f"http://{static.UMPIRE_SERVICE}:8000/umpire/build"
    r = requests.get(url, headers=headers, verify=False)

    if r.status_code == 200:
        return r.json(), HTTPStatus.OK
    else:
        return r.text, HTTPStatus.BAD_REQUEST


@jwt_required
def build_image(app_name, app_version):
    headers = {'content-type': 'application/json'}
    payload = {'app_name': app_name, 'app_version': app_version}
    url = f"http://{static.UMPIRE_SERVICE}:8000/umpire/build"
    r = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)

    if r.status_code == 200:
        return r.json(), HTTPStatus.OK
    else:
        return r.text, HTTPStatus.BAD_REQUEST


@jwt_required
def build_status_from_id(build_id):
    headers = {'content-type': 'application/json'}
    url = f"http://{static.UMPIRE_SERVICE}:8000/umpire/build/{build_id}"
    r = requests.post(url, headers=headers, verify=False)

    if r.status_code == 200:
        return r.json(), HTTPStatus.OK
    else:
        return r.text, HTTPStatus.BAD_REQUEST


@jwt_required
def save_umpire_file(app_name, app_version):
    headers = {'content-type': 'application/json'}
    payload = {'app_name': app_name, 'app_version': app_version}
    url = f"http://{static.UMPIRE_SERVICE}:8000/umpire/save"
    r = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)

    if r.status_code == 200:
        return r.json(), HTTPStatus.OK
    else:
        return r.json(), HTTPStatus.BAD_REQUEST