import uuid
import logging

from common.config import config
from common.redis_helpers import connect_to_redis_pool
from common.minio_helper import MinioApi
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("UMPIRE")
BUILD_STATUS_GLOB = "umpire_api_build"


class Request(BaseModel):
    app_name: str = None
    app_version: str = None
    file_path: str = None
    file_data: str = None


app = FastAPI()

# GET http://localhost:2828/file
# Returns contents of file given a specific app_name, version number, and file path
# Body Params: app_name, app_version, file_path
@app.post("/umpire/file")
async def get_file_contents(request: Request):
    app_name = request.app_name
    if app_name is None:
        raise HTTPException(status_code=400, detail="Unable to process. Parameter app_name not received.")
    version = request.app_version
    if version is None:
        raise HTTPException(status_code=400, detail="Unable to process. Parameter app_version not received.")
    path = request.file_path
    if path is None:
        raise HTTPException(status_code=400, detail="Unable to process. Parameter file-path not received.")

    file_data = await MinioApi.get_file(app_name, version, path)
    return file_data

# POST http://localhost:2828/file
# Body Params: app_name, app_version, file_path, file_data, file_size
# Returns success message letting you know you have updated the file at file_path with the given file_data
@app.post("/umpire/file-upload")
async def update_file(request: Request):
    app_name = request.app_name
    if app_name is None:
        raise HTTPException(status_code=400, detail="Unable to process. Parameter app_name not received.")

    version = request.app_version
    if version is None:
        raise HTTPException(status_code=400, detail="Unable to process. Parameter app_version not received.")

    path = request.file_path
    if path is None:
        raise HTTPException(status_code=400, detail="Unable to process. Parameter file_path not received.")

    file_data = request.file_data
    if file_data is None:
        raise HTTPException(status_code=400, detail="Unable to process. Parameter file_data not received.")

    # File data should be bytes right now
    file_data = file_data.encode('utf-8')
    file_size = len(file_data)

    success = await MinioApi.update_file(app_name, version, path, file_data, file_size)
    if success:
        return f"You have updated {path} to include {file_data}"
    else:
        raise HTTPException(status_code=400, detail="FILE NOT FOUND")

# GET http://localhost:2828/files
# Body Params: app_name, version, path
# Returns all files that exist under the specified app_name and version number
@app.post("/umpire/files")
async def list_all_files(request: Request):
    app_name = request.app_name
    if app_name is None:
        raise HTTPException(status_code=400, detail="Unable to process. Parameter app_name not received.")

    version = request.app_version
    if version is None:
        raise HTTPException(status_code=400, detail="Unable to process. Parameter app_version not received.")

    result = await MinioApi.list_files(app_name, version)
    return result

# GET http://localhost:2828/build
# Returns list of current builds
@app.get("/umpire/build")
async def get_build_statuses():
    async with connect_to_redis_pool(config.REDIS_URI) as conn:
        ret = []
        build_keys = set(await conn.keys(pattern=BUILD_STATUS_GLOB + "*", encoding="utf-8"))
        for key in build_keys:
            build = await conn.execute('get', key)
            build = build.decode('utf-8')
            ret.append((key, build))
        return f"List of Current Builds: {ret}"

# POST http://localhost:2828/build
# Body Params: app_name, app_version
# Creates a build for a specified WALKOFF app/version number and sets build status in redis keyed by UUID
@app.post("/umpire/build")
async def build_image(request: Request):
    app_name = request.app_name
    if app_name is None:
        raise HTTPException(status_code=400, detail="Unable to process. Parameter app_name not received.")

    version = request.app_version
    if version is None:
        raise HTTPException(status_code=400, detail="Unable to process. Parameter app_version not received.")

    await MinioApi.build_image(app_name, version)

    build_id = str(uuid.uuid4())
    redis_key = BUILD_STATUS_GLOB + "." + app_name + "." + build_id
    build_id = app_name + "." + build_id
    async with connect_to_redis_pool(config.REDIS_URI) as conn:
        await conn.execute('set', redis_key, "BUILDING")
        ret = {"build_id": build_id}
        return ret

# GET http://localhost:2828/build/build_id
# URL Param: build_id
# Returns build status of build specified by build id
@app.post("/umpire/build/{build_id}")
async def build_status_from_id(build_id):
    async with connect_to_redis_pool(config.REDIS_URI) as conn:
        get = BUILD_STATUS_GLOB + "." + build_id
        build_status = await conn.execute('get', get)
        build_status = build_status.decode('utf-8')
        return build_status
