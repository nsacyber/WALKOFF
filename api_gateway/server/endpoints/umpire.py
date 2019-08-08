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
        return r.text, HTTPStatus.OK
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

# import uuid
# import logging
# import urllib3
#
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
#
# from common.config import config, static
# from common.redis_helpers import connect_to_redis_pool
# from common.minio_helper import MinioApi
# import walkoff_client as walkoff
#
# logger = logging.getLogger("UMPIRE")
# BUILD_STATUS_GLOB = "umpire_api_build"
#
#
# class Request(BaseModel):
#     app_name: str = None
#     app_version: str = None
#     file_path: str = None
#     file_data: str = None
#
#
# app = FastAPI()
#
# def _jwt_authentication(fn):
#     def verify_jwt(fn):
#         # Create a config that represents our Walkoff server
#         config = walkoff.Configuration(host=f"http://localhost:8081/walkoff/api")
#
#         # Create a base API client with which you will interact with Walkoff
#         api_client = walkoff.ApiClient(configuration=config)
#
#         # Create an authentication API client and log in
#         auth_api = walkoff.AuthorizationApi(api_client)
#         ret_code = auth_api.verify()
#
#
#
# # GET http://localhost:2828/file
# # Returns contents of file given a specific app_name, version number, and file path
# # Body Params: app_name, app_version, file_path
# @app.get("/umpire/file")
# async def get_file_contents(request: Request):
#     app_name = request.app_name
#     if app_name is None:
#         raise HTTPException(status_code=400, detail="Unable to process. Parameter app_name not received.")
#     version = request.app_version
#     if version is None:
#         raise HTTPException(status_code=400, detail="Unable to process. Parameter app_version not received.")
#     path = request.file_path
#     if path is None:
#         raise HTTPException(status_code=400, detail="Unable to process. Parameter file-path not received.")
#
#     file_data = await MinioApi.get_file(app_name, version, path)
#     return file_data
#
# # POST http://localhost:2828/file
# # Body Params: app_name, app_version, file_path, file_data, file_size
# # Returns success message letting you know you have updated the file at file_path with the given file_data
# @app.post("/umpire/file")
# async def update_file(request: Request):
#     app_name = request.app_name
#     if app_name is None:
#         raise HTTPException(status_code=400, detail="Unable to process. Parameter app_name not received.")
#
#     version = request.app_version
#     if version is None:
#         raise HTTPException(status_code=400, detail="Unable to process. Parameter app_version not received.")
#
#     path = request.file_path
#     if path is None:
#         raise HTTPException(status_code=400, detail="Unable to process. Parameter file_path not received.")
#
#     file_data = request.file_data
#     if file_data is None:
#         raise HTTPException(status_code=400, detail="Unable to process. Parameter file_data not received.")
#
#     # File data should be bytes right now
#     file_data = file_data.encode('utf-8')
#     file_size = len(file_data)
#
#     success = await MinioApi.update_file(app_name, version, path, file_data, file_size)
#     if success:
#         return f"You have updated {path} to include {file_data}"
#     else:
#         raise HTTPException(status_code=400, detail="FILE NOT FOUND")
#
# # GET http://localhost:2828/files
# # Body Params: app_name, version, path
# # Returns all files that exist under the specified app_name and version number
# @app.get("/umpire/files")
# async def list_all_files(request: Request):
#     app_name = request.app_name
#     if app_name is None:
#         raise HTTPException(status_code=400, detail="Unable to process. Parameter app_name not received.")
#
#     version = request.app_version
#     if version is None:
#         raise HTTPException(status_code=400, detail="Unable to process. Parameter app_version not received.")
#
#     result = await MinioApi.list_files(app_name, version)
#     return result
#
# # GET http://localhost:2828/build
# # Returns list of current builds
# @app.get("/umpire/build")
# async def get_build_statuses():
#     async with connect_to_redis_pool(config.REDIS_URI) as conn:
#         ret = []
#         build_keys = set(await conn.keys(pattern=BUILD_STATUS_GLOB + "*", encoding="utf-8"))
#         for key in build_keys:
#             build = await conn.execute('get', key)
#             build = build.decode('utf-8')
#             ret.append((key, build))
#         return f"List of Current Builds: {ret}"
#
# # POST http://localhost:2828/build
# # Body Params: app_name, app_version
# # Creates a build for a specified WALKOFF app/version number and sets build status in redis keyed by UUID
# @app.post("/umpire/build")
# async def build_image(request: Request):
#     app_name = request.app_name
#     if app_name is None:
#         raise HTTPException(status_code=400, detail="Unable to process. Parameter app_name not received.")
#
#     version = request.app_version
#     if version is None:
#         raise HTTPException(status_code=400, detail="Unable to process. Parameter app_version not received.")
#
#     await MinioApi.build_image(app_name, version)
#
#     build_id = str(uuid.uuid4())
#     redis_key = BUILD_STATUS_GLOB + "." + app_name + "." + build_id
#     build_id = app_name + "." + build_id
#     async with connect_to_redis_pool(config.REDIS_URI) as conn:
#         await conn.execute('set', redis_key, "BUILDING")
#         ret = {"build_id": build_id}
#         return ret
#
# # GET http://localhost:2828/build/build_id
# # URL Param: build_id
# # Returns build status of build specified by build id
# @app.post("/umpire/build/{build_id}")
# async def build_status_from_id(build_id):
#     async with connect_to_redis_pool(config.REDIS_URI) as conn:
#         get = BUILD_STATUS_GLOB + "." + build_id
#         build_status = await conn.execute('get', get)
#         build_status = build_status.decode('utf-8')
#         return build_status
