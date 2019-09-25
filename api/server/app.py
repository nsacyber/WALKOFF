import logging
from copy import deepcopy
from http import HTTPStatus

from fastapi import FastAPI, Depends
from fastapi.openapi.utils import get_openapi
from starlette.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
import pymongo

from api.server.endpoints import appapi, dashboards, workflows, users, console, results,  auth, roles, global_variables
from api.server.db import DBEngine, get_db, MongoEngine, get_mongo_c
from api.server.db.user import UserModel
from api.server.db.role import RoleModel

from api.server.db.user_init import default_roles, default_users
from api.server.utils.problems import ProblemException
from api.security import get_raw_jwt, verify_token_in_decoded, verify_token_not_blacklisted, user_has_correct_roles, \
    get_roles_by_resource_permission
from common.config import config, static

logger = logging.getLogger(__name__)

_app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
_walkoff = FastAPI(openapi_prefix="/walkoff/api")
_db_manager = DBEngine()
_mongo_manager = MongoEngine()

_app.mount("/walkoff/api", _walkoff)
_app.mount("/walkoff/client", StaticFiles(directory=static.CLIENT_PATH), name="static")


@_app.on_event("startup")
async def initialize_mongodb():
    await _mongo_manager.init_db()


@_app.on_event("startup")
async def initialize_users():
    walkoff_db = _mongo_manager.client.walkoff_db
    roles_col = walkoff_db.roles
    users_col = walkoff_db.users

    for role_name, role in default_roles.items():
        role_d = await roles_col.find_one({"id_": role.id_})
        if not role_d:
            await roles_col.insert_one(dict(role))

    for user_name, user in default_users.items():
        user_d = await users_col.find_one({"id_": user.id_})
        if not user_d:
            await users_col.insert_one(dict(user))


@_app.on_event("startup")
async def start_banner():
    logger.info("API Server started.")


# Note: The request goes through middleware here in opposite order of instantiation, last to first.
@_walkoff.middleware("http")
async def db_session_middleware(request: Request, call_next):
    try:
        request.state.db = _db_manager.session_maker()
        request.state.mongo_c = _mongo_manager.collection_from_url(request.url.path)
        request.state.mongo_d = _mongo_manager.client.walkoff_db
        response = await call_next(request)
    except pymongo.errors.InvalidName:
        response = await call_next(request)
    # except Exception as e:
    #     response = JSONResponse({"Error": "Internal Server Error", "message": str(e)}, status_code=500)
    finally:
        request.state.db.close()

    return response


@_walkoff.middleware("http")
async def permissions_accepted_for_resource_middleware(request: Request, call_next):
    walkoff_db = _mongo_manager.client.walkoff_db

    request_path = request.url.path.split("/")

    if len(request_path) >= 4:
        resource_name = request_path[3]
        request_method = request.method
        accepted_roles = set()
        resource_permission = ""

        role_based = ["globals", "workflows"]
        move_on = ["globals", "workflows", "auth", "workflowqueue", "appapi", "docs", "redoc", "openapi.json"]
        if resource_name not in move_on:
            if request_method == "POST":
                resource_permission = "create"
            # elif resource_name in role_based:
            #     response = await call_next(request)
            #     return response

            if request_method == "GET":
                resource_permission = "read"

            if request_method == "PUT":
                resource_permission = "update"

            if request_method == "DELETE":
                resource_permission = "delete"

            if request_method == "PATCH":
                resource_permission = "execute"

            accepted_roles |= await get_roles_by_resource_permission(resource_name, resource_permission, walkoff_db)
            if not await user_has_correct_roles(accepted_roles, request):
                return JSONResponse({"Error": "FORBIDDEN",
                                     "message": "User does not have correct permissions for this resource"},
                                    status_code=403)

    response = await call_next(request)
    return response


@_walkoff.middleware("http")
async def jwt_required_middleware(request: Request, call_next):
    walkoff_db = _mongo_manager.client.walkoff_db

    request_path = request.url.path.split("/")
    if len(request_path) >= 4:
        resource_name = request_path[3]
        if resource_name not in ("auth", "docs", "redoc", "openapi.json"):
            decoded_token = await get_raw_jwt(request)

            if decoded_token is None:
                e = ProblemException(HTTPStatus.UNAUTHORIZED, "No authorization provided.",
                                     "Authorization header is missing.")
                return e.as_response()

            await verify_token_in_decoded(decoded_token=decoded_token, request_type='access')
            await verify_token_not_blacklisted(walkoff_db=walkoff_db, decoded_token=decoded_token, request_type='access')

    response = await call_next(request)
    return response


@_walkoff.exception_handler(ProblemException)
async def problem_exception_handler(request: Request, exc: ProblemException):
    r = JSONResponse(
        content=exc.as_dict(),
        headers=exc.headers,
        status_code=exc.status_code
    )
    return r

# Include routers here
_walkoff.include_router(auth.router,
                        prefix="/auth",
                        tags=["auth"],
                        dependencies=[Depends(get_mongo_c)])

_walkoff.include_router(global_variables.router,
                        prefix="/globals",
                        tags=["globals"],
                        dependencies=[Depends(get_mongo_c)])

_walkoff.include_router(users.router,
                        prefix="/users",
                        tags=["users"],
                        dependencies=[Depends(get_mongo_c)])

_walkoff.include_router(roles.router,
                        prefix="/roles",
                        tags=["roles"],
                        dependencies=[Depends(get_mongo_c)])

_walkoff.include_router(appapi.router,
                        prefix="/apps",
                        tags=["apps"],
                        dependencies=[Depends(get_mongo_c)])

# _walkoff.include_router(results.router,
#                         prefix="/internal",
#                         tags=["internal"],
#                         dependencies=[Depends(get_mongo_c)])

# _walkoff.include_router(console.router,
#                         prefix="/streams/console",
#                         tags=["console"],
#                         dependencies=[Depends(get_mongo_c)])

_walkoff.include_router(dashboards.router,
                        prefix="/dashboards",
                        tags=["dashboards"],
                        dependencies=[Depends(get_mongo_c)])

# _walkoff.include_router(workflowqueue.router,
#                         prefix="/workflowqueue",
#                         tags=["workflowqueue"],
#                         dependencies=[Depends(get_mongo_c)])
#
# _walkoff.include_router(workflows.router,
#                         prefix="/workflows",
#                         tags=["workflows"],
#                         dependencies=[Depends(get_mongo_c)])


@_app.get("/walkoff/login")
async def login_page():
    with open(static.TEMPLATE_PATH / "login.html") as f:
        login = f.read()

    return HTMLResponse(login)


@_app.get("/")
@_app.get("/walkoff")
@_app.get("/walkoff/")
@_app.get("/walkoff/.*")
async def root_router():
    with open(static.CLIENT_PATH / "dist" / "walkoff" / "index.html") as f:
        index = f.read()

    return HTMLResponse(index)


def custom_openapi():
    if _walkoff.openapi_schema:
        return _walkoff.openapi_schema
    else:
        openapi_schema = get_openapi(
            title="WALKOFF",
            version="1.0.0-rc.2",
            description="A flexible, easy to use, automation framework allowing users to integrate their "
                        "capabilities and devices to cut through the repetitive, tedious tasks slowing them down.",
            routes=_walkoff.routes
        )
        openapi_schema["info"]["x-logo"] = {
            "url": "/walkoff/client/dist/walkoff/assets/img/walkoffLogo.png"
        }
        openapi_schema["tags"] = [
            {"name": "apps", "description": "App API Operations"}
        ]
        _walkoff.openapi_schema = openapi_schema
        return _walkoff.openapi_schema


_walkoff.openapi = custom_openapi

app = _app


# @_app.after_request
# def after_request(response):
#     response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
#     response.headers["Expires"] = 0
#     response.headers["Pragma"] = "no-cache"
#     response.headers["X-Accel-Buffering"] = "no"
#     return response
#
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
