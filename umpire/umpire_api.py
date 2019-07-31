from sanic import Sanic
from sanic.response import text
from sanic.views import HTTPMethodView
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
    # Returns all files
    async def get(self, request):
        return text("This returns all the files")

    # POST http://localhost:2828/file
    # Body Params: file_path, file_data
    # Returns context of file given a specific file_id
    async def post(self, request):
        file_path = json.loads(request.body.decode('utf-8')).get("file_path")
        file_data = json.loads(request.body.decode('utf-8')).get("file_data")
        return text(f"You have updated {file_path} to include {file_data}")


class UmpireApiFileView2(HTTPMethodView):
    # GET http://localhost:2828/file/file_id
    # Returns context of file given a specific file_id
    # URL Params: file_id
    async def get(self, request, file_path):
        return text(f"You have made a get request for {file_path}'s file context.")


class UmpireApiBuildView1(HTTPMethodView):
    # GET http://localhost:2828/build
    # Returns list of current builds
    async def get(self, request):

        async with connect_to_redis_pool(config.REDIS_URI) as conn:
            ret = []
            build_keys = set(await conn.keys(pattern=BUILD_STATUS_GLOB + "*", encoding="utf-8"))
            for key in build_keys:
                build = await conn.execute('get', key)
                ret.append((key, build))
            return text(f"List of Current Builds: {ret}")

    # POST http://localhost:2828/build
    # Creates a build for a specified WALKOFF app/version number and sets build status in redis keyed by UUID
    # Body Params: app_name, version_number
    async def post(self, request):
        app_name = json.loads(request.body.decode('utf-8')).get("app_name")
        version_number = json.loads(request.body.decode('utf-8')).get("version_number")
        await UmpireApi.build_image(app_name=app_name, version=version_number)

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
            return text(build_status)


app.add_route(UmpireApiBuildView1.as_view(), '/build')
app.add_route(UmpireApiBuildView2.as_view(), '/build/<build_id>')

app.add_route(UmpireApiFileView1.as_view(), '/file')
app.add_route(UmpireApiFileView2.as_view(), '/file/<file_path>')

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=2828, debug=True)
