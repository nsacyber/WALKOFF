import logging
import os
from pathlib import Path

from fastapi import FastAPI
from minio import Minio

from common.config import config

from umpire.endpoints import build, files

logger = logging.getLogger("UMPIRE")
p = Path('./apps').glob('**/*')

_app = FastAPI()

_app.include_router(build.router, prefix="/umpire/build", tags=["build"])
_app.include_router(files.router, prefix="/umpire", tags=["files"])


@_app.on_event("startup")
async def push_to_minio():
    minio_client = Minio(config.MINIO, access_key=config.get_from_file(config.MINIO_ACCESS_KEY_PATH),
                         secret_key=config.get_from_file(config.MINIO_SECRET_KEY_PATH), secure=False)
    bucket_exists = False
    try:
        buckets = minio_client.list_buckets()
        for bucket in buckets:
            if bucket.name == "apps-bucket":
                bucket_exists = True
    except Exception as e:
        logger.info("Bucket doesn't exist.")

    if not bucket_exists:
        minio_client.make_bucket("apps-bucket", location="us-east-1")

    files_to_upload = [x for x in p if x.is_file()]
    for file in files_to_upload:
        path_to_file = str(file)
        with open(path_to_file, "rb") as file_data:
            file_stat = os.stat(path_to_file)
            minio_client.put_object("apps-bucket", path_to_file, file_data, file_stat.st_size)


app = _app
