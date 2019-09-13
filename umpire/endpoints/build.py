import uuid
import logging
import asyncio

from fastapi import APIRouter
from pydantic import BaseModel
import aiohttp

from common.config import config
from common.redis_helpers import connect_to_redis_pool
from common.minio_helper import MinioApi

from umpire.app_repo import AppRepo

BUILD_STATUS_GLOB = "umpire_api_build"

router = APIRouter()
logger = logging.getLogger("Umpire")


# GET http://localhost:2828/build
# Returns list of current builds
@router.get("/")
async def get_build_statuses():
    async with connect_to_redis_pool(config.REDIS_URI) as conn:
        ret = []
        build_keys = set(await conn.keys(pattern=BUILD_STATUS_GLOB + "*", encoding="utf-8"))
        for key in build_keys:
            build = await conn.execute('get', key)
            build = build.decode('utf-8')
            ret.append((key, build))
        return f"List of Current Builds: {ret}"


class BuildImage(BaseModel):
    app_name: str
    app_version: str

# POST http://localhost:2828/build
# Body Params: app_name, app_version
# Creates a build for a specified WALKOFF app/version number and sets build status in redis keyed by UUID
@router.post("/")
async def build_image(request: BuildImage):
    build_id = str(uuid.uuid4())
    # build_id = request.app_name + "." + build_id
    #create_task for build_image
    asyncio.create_task(MinioApi.build_image(request.app_name, request.app_version, build_id))
    # async with aiohttp.ClientSession() as session:
    #     app_repo = await AppRepo.create(config.APPS_PATH, session)
    ret = {"build_id": build_id}
    return ret

# GET http://localhost:2828/build/build_id
# URL Param: build_id
# Returns build status of build specified by build id
@router.post("/{build_id}")
async def build_status_from_id(build_id):
    async with connect_to_redis_pool(config.REDIS_URI) as conn:
        get = BUILD_STATUS_GLOB + "." + build_id
        build_status = await conn.execute('get', get)
        build_status = build_status.decode('utf-8')
        return build_status

