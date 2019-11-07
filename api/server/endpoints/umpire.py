import asyncio
import uuid
from typing import List

from fastapi import APIRouter

from api.server.db.umpire import UploadFile
from api.server.utils.problems import InvalidInputException, DoesNotExistException
from common.config import config
from common.minio_helper import MinioApi
from common.redis_helpers import connect_to_aioredis_pool

BUILD_STATUS_GLOB = "umpire_api_build"

router = APIRouter()


@router.get("/files/{app_name}/{app_version}",
            response_model=List[str], response_description="List of file names in specified app")
async def list_all_files(app_name: str, app_version: str):
    return await MinioApi.list_files(app_name, app_version)


@router.get("/file/{app_name}/{app_version}",
            response_model=str, response_description="Contents of the specified file.")
async def get_file_contents(app_name: str, app_version: str, file_path: str):
    full_path = f"{app_name}/{app_version}/{file_path}"
    success, contents = await MinioApi.get_file(app_name, app_version, file_path)
    if success:
        return contents
    else:
        if contents is None:
            raise DoesNotExistException("read", "file", full_path)
        else:
            raise InvalidInputException("read", "file", full_path, errors={"error": contents})


@router.post("/file_upload")
async def update_file(body: UploadFile):
    full_path = f"{body.app_name}/{body.app_version}/{body.file_path}"
    file_data_bytes = body.file_data.encode('utf-8')
    file_size = len(file_data_bytes)

    success, message = await MinioApi.update_file(body.app_name, body.app_version, body.file_path,
                                                  file_data_bytes, file_size)
    if success:
        return message
    else:
        raise InvalidInputException("upload", "file", full_path, errors={"error": message})


@router.get("/build")
async def get_build_status():
    async with connect_to_aioredis_pool(config.REDIS_URI) as conn:
        ret = []
        build_keys = set(await conn.keys(pattern=BUILD_STATUS_GLOB + "*", encoding="utf-8"))
        for key in build_keys:
            build = await conn.execute('get', key)
            build = build.decode('utf-8')
            ret.append((key, build))
        return ret


@router.post("/build/{app_name}/{app_version}")
async def build_image(app_name: str, app_version: str):
    build_id = str(uuid.uuid4())
    asyncio.create_task(MinioApi.build_image(app_name, app_version, build_id))
    return {"build_id": build_id}


@router.post("/build/{build_id}")
async def build_status_from_id(build_id: str):
    async with connect_to_aioredis_pool(config.REDIS_URI) as conn:
        get = BUILD_STATUS_GLOB + "." + build_id
        build_status = await conn.execute('get', get)
        build_status = build_status.decode('utf-8')
        return build_status


# @router.post("/save/{app_name}/{app_version}")
# async def save_umpire_file(app_name: str, app_version: str):
#
#     result = await MinioApi.save_file(app_name, app_version)
#     if result:
#         return "Successful Update to Local Repo"
#     else:
#         return "Failed"
