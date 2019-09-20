import logging
from copy import deepcopy
from http import HTTPStatus

from fastapi import FastAPI, Depends
from starlette.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
import pymongo

from api.server.endpoints import appapi, dashboards, workflows, users, console  # auth, roles, users,
from api.server.db import DBEngine, get_db, MongoEngine, get_mongo_c
from api.server.db.user import UserModel
from api.server.db.role import RoleModel

from api.server.db.user_init import default_roles, default_users
from api.server.utils.problems import ProblemException
from api.security import get_raw_jwt, verify_token_in_decoded, verify_token_not_blacklisted, user_has_correct_roles, \
    get_roles_by_resource_permission
from common.config import config, static

logger = logging.getLogger("API")

_app = FastAPI()
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

    for role_key, role_val in default_roles.items():
        role_d = await roles_col.find_one({"id_": role_val["id_"]}, projection={'_id': False})
        if not role_d:
            await roles_col.insert_one(role_val)

    for user_key, user_val in default_users.items():
        user_d = await users_col.find_one({"id_": user_val["id_"]}, projection={'_id': False})
        if not user_d:
            if user_val["password"] is None:
                user_val["password"] = config.get_from_file(config.POSTGRES_KEY_PATH)

            await users_col.insert_one(user_val)

    # # Setup internal user
    # internal_role = await role_col.find_one({"id_": 1}, projection={'_id': False})
    # internal_user = await user_col.find_one({"username": "internal_user"}, projection={'_id': False})
    # if not internal_user:
    #     key = config.get_from_file(config.INTERNAL_KEY_PATH)
    #     user_col.insert_one(UserModel(username="internal_user", password=key, hashed=False, roles=[2]))
    # elif internal_role not in internal_user.roles:
    #     user_copy = deepcopy(internal_user)
    #     user_copy.roles.append(internal_role)
    #     await user_col.replace_one(dict(internal_user), dict(user_copy))
    #
    # # Setup Super Admin user
    # super_admin_role = await role_col.find_one({"id_": 2}, projection={'_id': False})
    # super_admin_user = await user_col.find_one({"username": "super_admin"}, projection={'_id': False})
    # if not super_admin_user:
    #     user_col.insert_one(UserModel(username="super_admin", password="super_admin", hashed=False, roles=[2]))
    # elif super_admin_role not in super_admin_user.roles:
    #     user_copy = deepcopy(super_admin_user)
    #     user_copy.roles.append(super_admin_role)
    #     await user_col.replace_one(dict(super_admin_user), dict(user_copy))
    #
    # # Setup Admin user
    # admin_role = await role_col.find_one({"id_": 3}, projection={'_id': False})
    # admin_user = await user_col.find_one({"username": "admin"}, projection={'_id': False})
    # if not admin_user:
    #     user_col.insert_one(UserModel(username="admin", password="admin", hashed=False, roles=[3]))
    # elif admin_role not in admin_user.roles:
    #     user_copy = deepcopy(admin_user)
    #     user_copy.roles.append(admin_role)
    #     await user_col.replace_one(dict(admin_user), dict(user_copy))





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
    # except Exception as e:
    #     response = JSONResponse({"Error": "Internal Server Error", "message": str(e)}, status_code=500)
    finally:
        request.state.db.close()

    return response


# @_walkoff.middleware("http")
# async def permissions_accepted_for_resource_middleware(request: Request, call_next):
#     db_session = _db_manager.session_maker()
#     request_path = request.url.path.split("/")
#
#     if len(request_path) >= 4:
#         resource_name = request_path[3]
#         request_method = request.method
#         accepted_roles = set()
#         resource_permission = ""
#
#         # TODO: Add check for scheduler "execute" permission when scheduler built out
#         move_on = ["globals", "workflow", "workflowqueue", "auth", "appapi", "docs", "redoc", "openapi.json"]
#         if resource_name not in move_on:
#             if request_method == "POST":
#                 resource_permission = "create"
#
#             if request_method == "GET":
#                 resource_permission = "read"
#
#             if request_method == "PUT":
#                 resource_permission = "put"
#
#             if request_method == "DELETE":
#                 resource_permission = "delete"
#
#             accepted_roles |= get_roles_by_resource_permission(resource_name, resource_permission, db_session)
#             if not user_has_correct_roles(accepted_roles, request):
#                 return JSONResponse({"Error": "FORBIDDEN",
#                                      "message": "User does not have correct permissions for this resource"},
#                                     status_code=403)
#
#     response = await call_next(request)
#     return response


# @_walkoff.middleware("http")
# async def jwt_required_middleware(request: Request, call_next):
#     request_path = request.url.path.split("/")
#     if len(request_path) >= 4:
#         resource_name = request_path[3]
#         if resource_name not in ("auth", "docs", "redoc", "openapi.json"):
#             db_session = _db_manager.session_maker()
#             decoded_token = get_raw_jwt(request)
#
#             if decoded_token is None:
#                 e = ProblemException(HTTPStatus.UNAUTHORIZED, "No authorization provided.",
#                                      "Authorization header is missing.")
#                 return e.as_response()
#
#             verify_token_in_decoded(decoded_token=decoded_token, request_type='access')
#             verify_token_not_blacklisted(db_session=db_session, decoded_token=decoded_token, request_type='access')
#
#     response = await call_next(request)
#     return response


@_walkoff.exception_handler(ProblemException)
async def problem_exception_handler(request: Request, exc: ProblemException):
    r = JSONResponse(
        content=exc.as_dict(),
        headers=exc.headers,
        status_code=exc.status_code
    )
    return r

# Include routers here
# _walkoff.include_router(auth.router,
#                         prefix="/auth",
#                         tags=["auth"],
#                         dependencies=[Depends(get_mongo_c)])

# _walkoff.include_router(global_variables.router,
#                         prefix="/globals",
#                         tags=["globals"],
#                         dependencies=[Depends(get_db)])

_walkoff.include_router(users.router,
                        prefix="/users",
                        tags=["users"],
                        dependencies=[Depends(get_mongo_c)])
#
# _walkoff.include_router(roles.router,
#                         prefix="/roles",
#                         tags=["roles"],
#                         dependencies=[Depends(get_mongo_c)])

_walkoff.include_router(appapi.router,
                        prefix="/apps",
                        tags=["apps"],
                        dependencies=[Depends(get_mongo_c)])

_walkoff.include_router(console.router,
                        prefix="/streams/console",
                        tags=["console"],
                        dependencies=[Depends(get_mongo_c)])

# _walkoff.include_router(dashboards.router,
#                         prefix="/dashboards",
#                         tags=["dashboards"],
#                         dependencies=[Depends(get_mongo_c)])

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

app = _app

#
# # Validate database models before saving them, here.
# # This is here to avoid circular imports.
# with _app.app_context():
#     @event.listens_for(_app.running_context.execution_db.session, "before_flush")
#     def validate_before_flush(session, flush_context, instances):
#         for instance in session.dirty:
#             if isinstance(instance, Workflow):
#                 instance.validate()
#
#
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
