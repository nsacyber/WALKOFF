import logging

from fastapi import FastAPI

from umpire.endpoints import build, files

logger = logging.getLogger("UMPIRE")


_app = FastAPI()

_app.include_router(build.router, prefix="/umpire/build", tags=["build"])
_app.include_router(files.router, prefix="/umpire", tags=["files"])

app = _app
