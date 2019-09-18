import logging
from http import HTTPStatus

from fastapi import FastAPI, Depends
from starlette.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
import pymongo

from api.server.endpoints import appapi, roles, users, auth
from api.server.db import DBEngine, get_db, MongoEngine, get_mongo_c
from api.server.db.user_init import initialize_default_resources_super_admin, \
    initialize_default_resources_internal_user, initialize_default_resources_admin, \
    initialize_default_resources_app_developer, initialize_default_resources_workflow_developer, \
    initialize_default_resources_workflow_operator, add_user
from api.server.db.user import Role
from api.server.db.user import User
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
async def initialize_users():
    db_session = _db_manager.session_maker()
    initialize_default_resources_internal_user(db_session)
    initialize_default_resources_super_admin(db_session)
    initialize_default_resources_admin(db_session)
    initialize_default_resources_app_developer(db_session)
    initialize_default_resources_workflow_developer(db_session)
    initialize_default_resources_workflow_operator(db_session)

    # Setup internal user
    internal_role = db_session.query(Role).filter_by(id=1).first()
    internal_user = db_session.query(User).filter_by(username="internal_user").first()

    if not internal_user:
        key = config.get_from_file(config.INTERNAL_KEY_PATH)
        add_user(username='internal_user', password=key, roles=[2], db_session=db_session)
    elif internal_role not in internal_user.roles:
        internal_user.roles.append(internal_role)

    # Setup Super Admin user
    super_admin_role = db_session.query(Role).filter_by(id=2).first()
    super_admin_user = db_session.query(User).filter_by(username="super_admin").first()
    if not super_admin_user:
        add_user(username='super_admin', password='super_admin', roles=[2], db_session=db_session)
    elif super_admin_role not in super_admin_user.roles:
        super_admin_user.roles.append(super_admin_role)

    # Setup Admin user
    admin_role = db_session.query(Role).filter_by(id=3).first()
    admin_user = db_session.query(User).filter_by(username="admin").first()
    if not admin_user:
        add_user(username='admin', password='admin', roles=[3], db_session=db_session)
    elif admin_role not in admin_user.roles:
        admin_user.roles.append(admin_role)

    db_session.commit()


# @_app.on_event("startup")
# async def initialize_mongodb():
#     await _mongo_manager.init_db()


@_app.on_event("startup")
async def tester():
    logger.info("API Server started.")


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


@_walkoff.middleware("http")
async def jwt_required_middleware(request: Request, call_next):
    request_path = request.url.path.split("/")
    if len(request_path) >= 4:
        resource_name = request_path[3]
        if resource_name not in ("auth", "docs", "redoc", "openapi.json"):
            db_session = _db_manager.session_maker()
            decoded_token = get_raw_jwt(request)

            if decoded_token is None:
                e = ProblemException(HTTPStatus.UNAUTHORIZED, "No authorization provided.",
                                     "Authorization header is missing.")
                return e.as_response()

            verify_token_in_decoded(decoded_token=decoded_token, request_type='access')
            verify_token_not_blacklisted(db_session=db_session, decoded_token=decoded_token, request_type='access')

    response = await call_next(request)
    return response


@_walkoff.middleware("http")
async def permissions_accepted_for_resource_middleware(request: Request, call_next):
    db_session = _db_manager.session_maker()
    request_path = request.url.path.split("/")

    if len(request_path) >= 4:
        resource_name = request_path[3]
        request_method = request.method
        accepted_roles = set()
        resource_permission = ""

        # TODO: Add check for scheduler "execute" permission when scheduler built out
        move_on = ["globals", "workflow", "workflowqueue", "auth", "appapi", "docs", "redoc", "openapi.json"]
        if resource_name not in move_on:
            if request_method == "POST":
                resource_permission = "create"

            if request_method == "GET":
                resource_permission = "read"

            if request_method == "PUT":
                resource_permission = "put"

            if request_method == "DELETE":
                resource_permission = "delete"

            accepted_roles |= get_roles_by_resource_permission(resource_name, resource_permission, db_session)
            if not user_has_correct_roles(accepted_roles, request):
                return JSONResponse({"Error": "FORBIDDEN",
                                     "message": "User does not have correct permissions for this resource"},
                                    status_code=403)

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
                        dependencies=[Depends(get_db)])

# _walkoff.include_router(global_variables.router,
#                         prefix="/globals",
#                         tags=["globals"],
#                         dependencies=[Depends(get_db)])

_walkoff.include_router(users.router,
                        prefix="/users",
                        tags=["users"],
                        dependencies=[Depends(get_db)])

_walkoff.include_router(roles.router,
                        prefix="/roles",
                        tags=["roles"],
                        dependencies=[Depends(get_db)])

_walkoff.include_router(appapi.router,
                        prefix="/apps",
                        tags=["apps"],
                        dependencies=[Depends(get_mongo_c)])

_walkoff.include_router(appapi.router,
                        prefix="/dashboards",
                        tags=["dashboards"],
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
