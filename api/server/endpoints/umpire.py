import json
import uuid
import requests
import asyncio
from typing import List

from fastapi import APIRouter, HTTPException
from common.config import static
from api.server.db.umpire import UploadFile
from minio import Minio
from common.minio_helper import MinioApi
from common.config import config
from common.redis_helpers import connect_to_aioredis_pool

BUILD_STATUS_GLOB = "umpire_api_build"

router = APIRouter()


@router.get("/files/{app_name}/{app_version}",
            response_model=List[str], response_description="List of file names")
async def list_all_files(app_name: str, app_version: str):

    result = await MinioApi.list_files(app_name, app_version)
    return result

    # headers = {'content-type': 'application/json'}
    # payload = {'app_name': app_name, 'app_version': app_version}
    # url = f"http://{static.UMPIRE_SERVICE}:8000/umpire/files"
    # r = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)
    #
    # if r.status_code == 200:
    #     return r.json()
    # else:
    #     return r.text


@router.get("/file/{app_name}/{app_version}")
async def get_file_contents(app_name: str, app_version: str, file_path: str):
    file_data = await MinioApi.get_file(app_name, app_version, file_path)
    try:
        return file_data.json()
    except Exception as e:
        return file_data


@router.post("/file_upload/")
async def update_file(body: UploadFile):
    file_data_bytes = body.file_data.encode('utf-8')
    file_size = len(file_data_bytes)

    success, message = await MinioApi.update_file(body.app_name, body.app_version, body.file_path,
                                                  file_data_bytes, file_size)
    if success:
        return f"You have updated {body.file_path}: message"
    else:
        raise HTTPException(status_code=400, detail="FILE NOT FOUND")


@router.get("/build")
async def get_build_status():
    async with connect_to_aioredis_pool(config.REDIS_URI) as conn:
        ret = []
        build_keys = set(await conn.keys(pattern=BUILD_STATUS_GLOB + "*", encoding="utf-8"))
        for key in build_keys:
            build = await conn.execute('get', key)
            build = build.decode('utf-8')
            ret.append((key, build))
        return f"List of Current Builds: {ret}"
    # headers = {'content-type': 'application/json'}
    # url = f"http://{static.UMPIRE_SERVICE}:8000/umpire/build"
    # r = requests.get(url, headers=headers, verify=False)
    #
    # if r.status_code == 200:
    #     return r.json()
    # else:
    #     return r.text


@router.post("/build/{app_name}/{app_version}")
async def build_image(app_name: str, app_version: str):
    build_id = str(uuid.uuid4())
    asyncio.create_task(MinioApi.build_image(app_name, app_version, build_id))
    ret = {"build_id": build_id}
    return ret

    # headers = {'content-type': 'application/json'}
    # payload = {'app_name': app_name, 'app_version': app_version}
    # url = f"http://{static.UMPIRE_SERVICE}:8000/umpire/build"
    # r = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)
    #
    # if r.status_code == 200:
    #     return r.json()
    # else:
    #     return r.text


@router.post("/build/{build_id}")
async def build_status_from_id(build_id: str):

    async with connect_to_aioredis_pool(config.REDIS_URI) as conn:
        get = BUILD_STATUS_GLOB + "." + build_id
        build_status = await conn.execute('get', get)
        build_status = build_status.decode('utf-8')
        return build_status

    # headers = {'content-type': 'application/json'}
    # url = f"http://{static.UMPIRE_SERVICE}:8000/umpire/build/{build_id}"
    # r = requests.post(url, headers=headers, verify=False)
    #
    # if r.status_code == 200:
    #     return r.json()
    # else:
    #     return r.text


@router.post("/save/{app_name}/{app_version}")
async def save_umpire_file(app_name: str, app_version: str):

    result = await MinioApi.save_file(app_name, app_version)
    if result:
        return "Successful Update to Local Repo"
    else:
        return "Failed"
    # headers = {'content-type': 'application/json'}
    # payload = {'app_name': app_name, 'app_version': app_version}
    # url = f"http://{static.UMPIRE_SERVICE}:8000/umpire/save"
    # r = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)
    #
    # if r.status_code == 200:
    #     return r.json()
    # else:
    #     return r.json()