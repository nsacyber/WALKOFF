import pathlib
from pathlib import Path
import logging
import io
import asyncio
import os
from os import stat
from urllib3.exceptions import ResponseError

import aiodocker
from minio import Minio
from minio.error import NoSuchKey, InvalidArgumentError

from common.config import config, static
from common.docker_helpers import connect_to_aiodocker, docker_context, logger as docker_logger
from common.socketio_helpers import connect_to_socketio_async

logger = logging.getLogger("Umpire")


async def stream_umpire_build_log(log_stream, build_id):
    async with connect_to_socketio_async(config.SOCKETIO_URI, namespaces=["/buildStatus"]) as sio:
        async for line in log_stream:
            if "stream" in line and line.get("stream", "").strip():
                key = "stream"
                build_status = "building"
            elif "status" in line:
                key = "status"
                build_status = "building"
            elif "error" in line:
                key = "error"
                build_status = "failure"
            elif "aux" in line:
                continue

            data = line[key].strip()
            logger.info(data)
            body = {"stream": data, "build_status": build_status, "build_id": build_id}
            await sio.emit(static.SIO_EVENT_LOG, body, namespace=static.SIO_NS_BUILD)
            if key == "error":
                raise aiodocker.exceptions.DockerBuildError(line)

        body = {"stream": "\n", "build_status": "success", "build_id": build_id}
        await sio.emit(static.SIO_EVENT_LOG, body, namespace=static.SIO_NS_BUILD)
        await asyncio.sleep(1)


async def push_image(docker_client, repo):
    logger.info(f"Pushing image {repo}.")
    try:
        await docker_client.images.push(repo)
        # await stream_docker_log(log_stream)
        logger.info(f"Pushed image {repo}.")
        return True
    except aiodocker.exceptions.DockerError as e:
        logger.exception(f"Failed to push image: {e}")
        return False


class MinioApi:
    @staticmethod
    async def build_image(app_name, version, build_id):
        tag_name = f"{static.APP_PREFIX}_{app_name}"
        repo = f"{config.DOCKER_REGISTRY}/{tag_name}:{version}"
        try:
            pathlib.Path(f"./rebuilt_apps/{app_name}/{version}/src").mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(e)

        minio_client = Minio(config.MINIO, access_key=config.get_from_file(config.MINIO_ACCESS_KEY_PATH),
                             secret_key=config.get_from_file(config.MINIO_SECRET_KEY_PATH), secure=False)
        objects = minio_client.list_objects("apps-bucket", recursive=True)
        for obj in objects:
            size = obj.size
            p_src = Path(obj.object_name)
            if p_src.parts[1] == app_name:
                hold = str(p_src)
                p_dst = hold[hold.find(app_name):]
                p_dst = Path("rebuilt_apps") / p_dst
                os.makedirs(p_dst.parent, exist_ok=True)

                data = minio_client.get_object('apps-bucket', hold)
                with open(p_dst, 'wb+') as file_data:
                    for d in data.stream(size):
                        file_data.write(d)

        logger.setLevel("DEBUG")
        docker_logger.setLevel("DEBUG")
        async with connect_to_aiodocker() as docker_client:
            context_dir = f"./rebuilt_apps/{app_name}/{version}/"
            with docker_context(Path(context_dir)) as context:
                logger.info("Sending build job to Docker.")
                log_stream = await docker_client.images.build(fileobj=context, tag=repo, rm=True,
                                                              forcerm=True, pull=True, stream=True,
                                                              path_dockerfile="./Dockerfile",
                                                              encoding="application/x-tar")
                logger.info("Image building.")
                await stream_umpire_build_log(log_stream, build_id)
                logger.info("Image build completed.")
                success = await push_image(docker_client, repo)
                if success:
                    saved = await MinioApi.save_file(app_name, version)
                    if saved is True:
                        return True
                    else:
                        return False
                else:
                    return False

    @staticmethod
    async def list_files(app_name, version):
        relative_path = []
        minio_client = Minio(config.MINIO, access_key=config.get_from_file(config.MINIO_ACCESS_KEY_PATH),
                             secret_key=config.get_from_file(config.MINIO_SECRET_KEY_PATH), secure=False)
        objects = minio_client.list_objects("apps-bucket", recursive=True)
        for obj in objects:
            p_src = Path(obj.object_name)
            if p_src.parts[1] == app_name:
                p_dst = p_src.relative_to(f"{p_src.parts[0]}/{app_name}/{version}")
                relative_path.append(str(p_dst))
        return relative_path

    @staticmethod
    async def get_file(app_name, version, path):
        minio_client = Minio(config.MINIO, access_key=config.get_from_file(config.MINIO_ACCESS_KEY_PATH),
                             secret_key=config.get_from_file(config.MINIO_SECRET_KEY_PATH), secure=False)
        abs_path = f"apps/{app_name}/{version}/{path}"
        try:
            data = minio_client.get_object('apps-bucket', abs_path)
            return True, data.read()
        except NoSuchKey:
            return False, None
        except ResponseError as e:
            return False, e

    @staticmethod
    async def update_file(app_name, version, path, file_data, file_size):
        minio_client = Minio(config.MINIO, access_key=config.get_from_file(config.MINIO_ACCESS_KEY_PATH),
                             secret_key=config.get_from_file(config.MINIO_SECRET_KEY_PATH), secure=False)
        abs_path = f"apps/{app_name}/{version}/{path}"
        found = False
        try:
            minio_client.stat_object("apps-bucket", abs_path)
            found = True
        except Exception as e:
            logger.info("File does not exist, creating a new one.")

        if found is True:
            minio_client.remove_object("apps-bucket", abs_path)
            logger.info("File exists, removing it before creating a new one.")

        file_data = io.BytesIO(file_data)
        try:
            minio_client.put_object("apps-bucket", abs_path, file_data, file_size)
            r = minio_client.stat_object("apps-bucket", abs_path)
            return True, vars(r)
        except (TypeError, ValueError, InvalidArgumentError) as e:
            return False, f"Failed to update file: {e}"

    @staticmethod
    async def save_file(app_name, version):
        temp = []
        editing = False
        minio_client = Minio(config.MINIO, access_key=config.get_from_file(config.MINIO_ACCESS_KEY_PATH),
                             secret_key=config.get_from_file(config.MINIO_SECRET_KEY_PATH), secure=False)
        objects = minio_client.list_objects("apps-bucket", recursive=True)
        if objects is []:
            return False
        for obj in objects:
            size = obj.size
            p_src = Path(obj.object_name)
            if p_src.parts[1] == app_name:
                hold = str(p_src)
                p_dst = hold[hold.find(app_name):]
                p_dst = Path("apps") / p_dst
                os.makedirs(p_dst.parent, exist_ok=True)
                editing = True
                try:
                    data = minio_client.get_object('apps-bucket', hold)
                except NoSuchKey as n:
                    return False
                except ResponseError as r:
                    return False
                with open(str(p_dst), 'wb+') as file_data:
                    for d in data.stream(size):
                        file_data.write(d)
                # TODO: Make this more secure, don't just base it off of requirements.txt
                owner_id = stat(f"apps/{app_name}/{version}/requirements.txt").st_uid
                group_id = stat(f"apps/{app_name}/{version}/requirements.txt").st_gid
                os.chown(p_dst, owner_id, group_id)
        if editing is False:
            return False
        else:
            return True


def push_all_apps_to_minio():
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

    files_to_upload = [x for x in Path('./apps').glob('**/*') if x.is_file()]
    for file in files_to_upload:
        path_to_file = str(file).replace("\\", "/")
        with open(path_to_file, "rb") as file_data:
            file_stat = os.stat(path_to_file)
            minio_client.put_object("apps-bucket", path_to_file, file_data, file_stat.st_size)

    logger.info("Apps Pushed to Minio")


def remove_all_apps_from_minio():
    minio_client = Minio(config.MINIO, access_key=config.get_from_file(config.MINIO_ACCESS_KEY_PATH),
                         secret_key=config.get_from_file(config.MINIO_SECRET_KEY_PATH), secure=False)

    try:
        minio_client.remove_bucket("apps-bucket")
    except Exception as e:
        logger.info("Bucket doesn't exist.")
