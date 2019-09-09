import logging

from fastapi import FastAPI, Depends

from api.server.endpoints import example

from common.config import config, static

logger = logging.getLogger(__name__)


async def run_before_everything():
    return "use this as a dependency to make it run before every request"

_app = FastAPI()

# Include routers here
_app.include_router(example.router,
                    prefix="/example",
                    tags=["example"],
                    dependencies=[Depends(run_before_everything)])


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
