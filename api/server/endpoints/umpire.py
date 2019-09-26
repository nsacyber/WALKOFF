import json
import requests

from fastapi import APIRouter
from common.config import static
from api.server.db.umpire import UploadFile

router = APIRouter()


@router.get("/files/{app_name}/{app_version}")
def list_all_files(app_name: str, app_version: str):

    headers = {'content-type': 'application/json'}
    payload = {'app_name': app_name, 'app_version': app_version}
    url = f"http://{static.UMPIRE_SERVICE}:8000/umpire/files"
    r = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)

    if r.status_code == 200:
        return r.json()
    else:
        return r.text


@router.get("/file/{app_name}/{app_version}")
def get_file_contents(app_name: str, app_version: str, file_path: str):
    # data = request.get_json()
    # file_path = data.get("file_path")
    headers = {'content-type': 'application/json'}
    payload = {'app_name': app_name, 'app_version': app_version, 'file_path': file_path}
    url = f"http://{static.UMPIRE_SERVICE}:8000/umpire/file"
    r = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)

    if r.status_code == 200:
        return r.json()
    else:
        return r.text


@router.post("/file_upload/")
def update_file(body: UploadFile):

    app_name = body.app_name
    app_version = body.app_version
    file_path = body.file_data
    file_data = body.file_path

    headers = {'content-type': 'application/json'}
    payload = {'app_name': app_name, 'app_version': app_version, 'file_path': file_path, 'file_data': file_data}
    url = f"http://{static.UMPIRE_SERVICE}:8000/umpire/file-upload"
    r = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)

    if r.status_code == 200:
        return r.json()
    else:
        return r.text


@router.get("/build")
def get_build_status():
    headers = {'content-type': 'application/json'}
    url = f"http://{static.UMPIRE_SERVICE}:8000/umpire/build"
    r = requests.get(url, headers=headers, verify=False)

    if r.status_code == 200:
        return r.json()
    else:
        return r.text


@router.post("/build/{app_name}/{app_version}")
def build_image(app_name: str, app_version: str):
    headers = {'content-type': 'application/json'}
    payload = {'app_name': app_name, 'app_version': app_version}
    url = f"http://{static.UMPIRE_SERVICE}:8000/umpire/build"
    r = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)

    if r.status_code == 200:
        return r.json()
    else:
        return r.text


@router.post("/build/{build_id}")
def build_status_from_id(build_id: str):
    headers = {'content-type': 'application/json'}
    url = f"http://{static.UMPIRE_SERVICE}:8000/umpire/build/{build_id}"
    r = requests.post(url, headers=headers, verify=False)

    if r.status_code == 200:
        return r.json()
    else:
        return r.text


@router.post("/save/{app_name}/{app_version}")
def save_umpire_file(app_name: str, app_version: str):
    headers = {'content-type': 'application/json'}
    payload = {'app_name': app_name, 'app_version': app_version}
    url = f"http://{static.UMPIRE_SERVICE}:8000/umpire/save"
    r = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)

    if r.status_code == 200:
        return r.json()
    else:
        return r.json()