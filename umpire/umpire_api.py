from sanic import Sanic
from sanic.response import text
from sanic.views import HTTPMethodView
import json
import uuid

app = Sanic('umpire_api')


class UmpireApiView1(HTTPMethodView):
    # Returns list of current builds
    async def get(self, request):
        return text("List of Current Builds")

    # Creates a build for a specified WALKOFF app/version number
    # Body Params: app_name, version_number
    async def post(self, request):
        app_name = json.loads(request.body.decode('utf-8')).get("app_name")
        version_number = json.loads(request.body.decode('utf-8')).get("version_number")
        final = app_name + "/" + version_number
        build_id = str(uuid.uuid4())
        return text(final)


class UmpireApiView2(HTTPMethodView):
    # Returns build status of build specified by build id
    # URL Param: build_id
    async def get(self, request, build_id):
        return text(build_id)


app.add_route(UmpireApiView1.as_view(), '/build')
app.add_route(UmpireApiView2.as_view(), '/build/<build_id>')

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=2828, debug=True)
