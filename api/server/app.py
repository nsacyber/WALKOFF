import logging

from fastapi import FastAPI, Depends
from starlette.requests import Request
from starlette.responses import JSONResponse

from api.server.endpoints import appapi
from api.server.db import DBEngine, get_db
from api.security import get_raw_jwt, verify_token_in_decoded, verify_token_not_blacklisted
from common.config import config, static

logger = logging.getLogger("API")


async def run_before_everything():
    return "use this as a dependency to make it run before every request"

_app = FastAPI()
_db_manager = DBEngine()


@_app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    try:
        request.state.db = _db_manager.session_maker()
        request.state.logger = logger
        response = await call_next(request)
    # except Exception as e:
    #     response = JSONResponse({"Error": "Internal Server Error", "message": str(e)}, status_code=500)
    finally:
        request.state.db.close()

    return response


@_app.middleware("http")
async def jwt_requested(request: Request, call_next):
    try:
        decoded_token = get_raw_jwt(request)
        verify_token_in_decoded(decoded_token, request_type='access')
        verify_token_not_blacklisted(decoded_token, request_type='access')
        #response = await call_next(request)
    finally:
        response = await call_next(request)
    return response


    return response
    # except Exception as e:
    #     response = JSONResponse({"Error": "Internal Server Error", "message": str(e)}, status_code=500)
    # finally:
    #     request.state.db.close()
    #
    # return response


# Include routers here
_app.include_router(appapi.router,
                    prefix="/apps",
                    tags=["apps"],
                    dependencies=[Depends(get_db)])


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
