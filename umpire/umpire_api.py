from sanic import Sanic
from sanic.response import text
from sanic.views import HTTPMethodView
from sanic.exceptions import ServerError
import json
import uuid
import logging

from common.config import config
from common.redis_helpers import connect_to_redis_pool
from umpire.umpire_helper import UmpireApi

logger = logging.getLogger("UMPIRE")
app = Sanic('umpire_api')
BUILD_STATUS_GLOB = "umpire_api_build"


class UmpireApiFileView1(HTTPMethodView):
    # GET http://localhost:2828/file
    # Returns context of file given a specific file_id
    # Body Params: app_name, app_version, file_path
    async def get(self, request):
        app_name = json.loads(request.body.decode('utf-8')).get("app_name")
        if app_name is None:
            raise ServerError("Unable to process. Parameter app_name not received.", status_code=400)

        version = json.loads(request.body.decode('utf-8')).get("app_version")
        if version is None:
            raise ServerError("Unable to process. Parameter app_version not received.", status_code=400)

        path = json.loads(request.body.decode('utf-8')).get("file_path")
        if path is None:
            raise ServerError("Unable to process. Parameter file-path not received.", status_code=400)

        file_data = await UmpireApi.get_file(app_name, version, path)
        return text(file_data)

    # POST http://localhost:2828/file
    # Body Params: app_name, app_version, file_path, file_data, file_size
    # Returns context of file given a specific file_id
    async def post(self, request):
        app_name = json.loads(request.body.decode('utf-8')).get("app_name")
        if app_name is None:
            raise ServerError("Unable to process. Parameter app_name not received.", status_code=400)

        version = json.loads(request.body.decode('utf-8')).get("app_version")
        if version is None:
            raise ServerError("Unable to process. Parameter app_version not received.", status_code=400)

        path = json.loads(request.body.decode('utf-8')).get("file_path")
        if path is None:
            raise ServerError("Unable to process. Parameter file_path not received.", status_code=400)

        file_data = json.loads(request.body.decode('utf-8')).get("file_data")
        if file_data is None:
            raise ServerError("Unable to process. Parameter file_data not received.", status_code=400)

        # File data should be bytes right now
        file_data = file_data.encode('utf-8')
        file_size = len(file_data)

        success = await UmpireApi.update_file(app_name, version, path, file_data, file_size)
        if success:
            return text(f"You have updated {path} to include {file_data}")
        else:
            raise ServerError("FILE NOT FOUND", status_code=400)


class UmpireApiFileView2(HTTPMethodView):
    # GET http://localhost:2828/files
    # Returns all files
    # Body Params: app_name, version, path
    async def get(self, request):
        app_name = json.loads(request.body.decode('utf-8')).get("app_name")
        if app_name is None:
            raise ServerError("Unable to process. Parameter app_name not received.", status_code=400)

        version = json.loads(request.body.decode('utf-8')).get("app_version")
        if version is None:
            raise ServerError("Unable to process. Parameter app_version not received.", status_code=400)

        result = await UmpireApi.list_files(app_name, version)
        return text(result)


class UmpireApiBuildView1(HTTPMethodView):
    # GET http://localhost:2828/build
    # Returns list of current builds
    async def get(self, request):
        async with connect_to_redis_pool(config.REDIS_URI) as conn:
            ret = []
            build_keys = set(await conn.keys(pattern=BUILD_STATUS_GLOB + "*", encoding="utf-8"))
            for key in build_keys:
                build = await conn.execute('get', key)
                build = build.decode('utf-8')
                ret.append((key, build))
            return text(f"List of Current Builds: {ret}")

    # POST http://localhost:2828/build
    # Creates a build for a specified WALKOFF app/version number and sets build status in redis keyed by UUID
    # Body Params: app_name, app_version
    async def post(self, request):
        app_name = json.loads(request.body.decode('utf-8')).get("app_name")
        if app_name is None:
            raise ServerError("Unable to process. Parameter app_name not received.", status_code=400)

        version = json.loads(request.body.decode('utf-8')).get("app_version")
        if version is None:
            raise ServerError("Unable to process. Parameter app_version not received.", status_code=400)

        await UmpireApi.build_image(app_name, version)

        build_id = str(uuid.uuid4())
        redis_key = BUILD_STATUS_GLOB + "." + app_name + "." + build_id
        build_id = app_name + "." + build_id
        async with connect_to_redis_pool(config.REDIS_URI) as conn:
            await conn.execute('set', redis_key, "BUILDING")
            ret = {"build_id": build_id}
            return text(ret)


class UmpireApiBuildView2(HTTPMethodView):
    # GET http://localhost:2828/build/build_id
    # Returns build status of build specified by build id
    # URL Param: build_id
    async def get(self, request, build_id):
        async with connect_to_redis_pool(config.REDIS_URI) as conn:
            get = BUILD_STATUS_GLOB + "." + build_id
            build_status = await conn.execute('get', get)
            build_status = build_status.decode('utf-8')
            return text(build_status)


app.add_route(UmpireApiBuildView1.as_view(), '/build')
app.add_route(UmpireApiBuildView2.as_view(), '/build/<build_id>')

app.add_route(UmpireApiFileView1.as_view(), '/file')
app.add_route(UmpireApiFileView2.as_view(), '/files')

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=2828, debug=True)
