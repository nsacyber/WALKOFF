import asyncio
import logging
import os
from http import HTTPStatus
from pathlib import Path

import pymongo
from fastapi import FastAPI, Depends
from fastapi.openapi.utils import get_openapi
from minio import Minio
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
from starlette.staticfiles import StaticFiles

from api.server.db.mongo import mongo, get_mongo_c
from api.server.endpoints import (appapi, auth, dashboards, global_variables, results, roles, scheduler,
                                  settings, umpire, users, workflowqueue, workflows)
from api.server.scheduler import Scheduler
from api.server.security import (get_raw_jwt, verify_token_in_decoded, verify_token_not_blacklisted,
                                 user_has_correct_roles, get_roles_by_resource_permission)
from api.server.utils.problems import ProblemException
from api.server.utils.socketio import sio, init_sio
from common.minio_helper import push_all_apps_to_minio
from common.config import static, config

logging.basicConfig(level=logging.INFO, format="{asctime} - {name} - {levelname}:{message}", style='{')
logger = logging.getLogger(__name__)

_app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
_walkoff = FastAPI(openapi_prefix="/walkoff/api")
_scheduler = Scheduler()

_app.mount("/walkoff/api", _walkoff)
_app.mount("/walkoff/client", StaticFiles(directory=static.CLIENT_PATH), name="static")


# @_app.on_event("startup")
# async def initialize_mongodb():
#     await mongo.init_db()
#
#
# @_app.on_event("startup")
# async def initialize_users():
#     walkoff_db = mongo.async_client.walkoff_db
#     roles_col = walkoff_db.roles
#     users_col = walkoff_db.users
#
#     for role_name, role in default_roles.items():
#         role_d = await roles_col.find_one({"id_": role.id_})
#         if not role_d:
#             await roles_col.insert_one(dict(role))
#
#     for user_name, user in default_users.items():
#         user_d = await users_col.find_one({"id_": user.id_})
#         if not user_d:
#             await users_col.insert_one(dict(user))


@_app.on_event("startup")
async def start_banner():
    logger.info("API Server started.")


@_app.on_event("startup")
async def connect_to_socketio():
    await init_sio()


@_app.on_event("startup")
async def push_to_minio():
    push_all_apps_to_minio()


@_app.on_event("startup")
async def workflow_results_listener():
    asyncio.create_task(results.update_workflow_status())


@_app.on_event("shutdown")
async def close_connections():
    await sio.disconnect()
    mongo.reg_client.disconnect()
    await mongo.async_client.disconnect()


# Note: The request goes through middleware here in opposite order of instantiation, last to first.
@_walkoff.middleware("http")
async def db_session_middleware(request: Request, call_next):
    try:
        request.state.mongo_c = mongo.collection_from_url(request.url.path)
        request.state.mongo_d = mongo.async_client.walkoff_db
        request.state.scheduler = _scheduler
        response = await call_next(request)
    except pymongo.errors.InvalidName:
        response = await call_next(request)
    # except Exception as e:
    #     response = JSONResponse({"Error": "Internal Server Error", "message": str(e)}, status_code=500)

    return response


@_walkoff.middleware("http")
async def permissions_accepted_for_resource_middleware(request: Request, call_next):
    walkoff_db = mongo.async_client.walkoff_db
    request_path = request.url.path.split("/")

    if len(request_path) >= 4:
        resource_name = request_path[3]
        if len(request_path) == 6:
            if request_path[4] == "personal_data":
                response = await call_next(request)
                return response
        request_method = request.method
        accepted_roles = set()
        resource_permission = ""
        gated_endpoints = ["users", "roles", "apps", "scheduler", "umpire", "dashboards", "settings"]

        # move_on = ["personal_user", "umpire", "globals", "workflows", "console", "auth", "workflowqueue", "appapi",
        #            "streams", "docs", "redoc", "openapi.json", ""]
        if resource_name in gated_endpoints:
            if request_method == "POST":
                resource_permission = "create"

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
                                     "message": "User does not have correct permissions for this endpoint"},
                                    status_code=403)

    response = await call_next(request)
    return response


@_walkoff.middleware("http")
async def permissions_accepted_for_roles_resource_middleware(request: Request, call_next):
    walkoff_db = mongo.async_client.walkoff_db
    request_path = request.url.path.split("/")

    if len(request_path) >= 4:
        resource_name = request_path[3]
        request_method = request.method
        accepted_roles = set()

        current_role_based = ["globals", "workflows", "workflowqueue"]
        if resource_name in current_role_based:
            if resource_name == "globals":
                resource_name = "global_variables"
            elif resource_name == "workflowqueue":
                resource_name = "workflowstatus"

            if request_method == "POST":
                resource_permission = "create"
            else:
                response = await call_next(request)
                return response

            accepted_roles |= await get_roles_by_resource_permission(resource_name, resource_permission, walkoff_db)
            if not await user_has_correct_roles(accepted_roles, request):
                return JSONResponse({"Error": "FORBIDDEN",
                                     "message": "User does not have correct permissions for this resource"},
                                    status_code=403)

    response = await call_next(request)
    return response


@_walkoff.middleware("http")
async def jwt_required_middleware(request: Request, call_next):
    walkoff_db = mongo.async_client.walkoff_db

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
            await verify_token_not_blacklisted(walkoff_db=walkoff_db, decoded_token=decoded_token,
                                               request_type='access')

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

_walkoff.include_router(scheduler.router,
                        prefix="/scheduler",
                        tags=["scheduler"],
                        dependencies=[Depends(get_mongo_c)])

_walkoff.include_router(umpire.router,
                        prefix="/umpire",
                        tags=["umpire"],
                        dependencies=[Depends(get_mongo_c)])

_walkoff.include_router(dashboards.router,
                        prefix="/dashboards",
                        tags=["dashboards"],
                        dependencies=[Depends(get_mongo_c)])

_walkoff.include_router(settings.router,
                        prefix="/settings",
                        tags=["settings"],
                        dependencies=[Depends(get_mongo_c)])

_walkoff.include_router(workflowqueue.router,
                        prefix="/workflowqueue",
                        tags=["workflowqueue"],
                        dependencies=[Depends(get_mongo_c)])

_walkoff.include_router(workflows.router,
                        prefix="/workflows",
                        tags=["workflows"],
                        dependencies=[Depends(get_mongo_c)])


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
            description="A flexible, easy-to-use, automation framework allowing users to integrate their "
                        "capabilities and devices to cut through the repetitive, tedious tasks slowing them down.",
            routes=_walkoff.routes
        )
        openapi_schema["info"]["x-logo"] = {
            "url": "/walkoff/api/client/dist/walkoff/assets/img/walkoffLogo.png"
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
