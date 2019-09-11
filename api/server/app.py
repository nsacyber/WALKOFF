import logging
from http import HTTPStatus

from fastapi import FastAPI, Depends
from starlette.requests import Request
from starlette.responses import JSONResponse
import pymongo

from api.server.endpoints import appapi
from api.server.db import get_roles_by_resource_permission, DBEngine, get_db, MongoEngine, get_mongo_c, \
    initialize_default_resources_super_admin, initialize_default_resources_internal_user, \
    initialize_default_resources_admin, initialize_default_resources_app_developer, \
    initialize_default_resources_workflow_developer, initialize_default_resources_workflow_operator, add_user, Role, User

from api.security import get_raw_jwt, verify_token_in_decoded, verify_token_not_blacklisted, user_has_correct_roles
from common.config import config, static

logger = logging.getLogger("API")


async def run_before_everything():
    return "use this as a dependency to make it run before every request"

_app = FastAPI()
_db_manager = DBEngine()
_mongo_manager = MongoEngine()


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
    internal_role = db_session(Role).query.filter_by(id=1).first()
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


@_app.on_event("startup")
async def initialize_mongodb():
    await _mongo_manager.init_db()


@_app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    try:
        request.state.db = _db_manager.session_maker()
        request.state.mongo_c = _mongo_manager.collection_from_url(request.url.path)
        response = await call_next(request)
    # except Exception as e:
    #     response = JSONResponse({"Error": "Internal Server Error", "message": str(e)}, status_code=500)
    finally:
        request.state.db.close()

    return response

@_app.middleware("http")
async def jwt_required_middleware(request: Request, call_next):
    db_session = _db_manager.session_maker()
    decoded_token = get_raw_jwt(request)
    verify_token_in_decoded(decoded_token=decoded_token, request_type='access')
    verify_token_not_blacklisted(db_session=db_session, decoded_token=decoded_token, request_type='access')

    response = await call_next(request)
    return response

@_app.middleware("http")
async def permissions_accepted_for_resource_middleware(request: Request, call_next):
    db_session = _db_manager.session_maker()
    request_path = (request.url.path).split("/")
    resource_name = request_path[1]
    request_method = request.method
    accepted_roles = set()
    resource_permission = ""

    # TODO: Add check for scheduler "execute" permission
    if resource_name != ("globals" and "workflows" and "workflowqueue"):
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
            return "Unauthorized View", HTTPStatus.FORBIDDEN

    response = await call_next(request)
    return response


# Include routers here
# _app.include_router(appapi.router,
#                     prefix="/walkoff/globals",
#                     tags=["globals"],
#                     dependencies=[Depends(get_db)])
#
# _app.include_router(appapi.router,
#                     prefix="/walkoff/users",
#                     tags=["users"],
#                     dependencies=[Depends(get_db)])
#
# _app.include_router(appapi.router,
#                     prefix="/walkoff/roles",
#                     tags=["users"],
#                     dependencies=[Depends(get_db)])

_app.include_router(appapi.router,
                    prefix="/walkoff/apps",
                    tags=["apps"],
                    dependencies=[Depends(get_mongo_c)])


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
