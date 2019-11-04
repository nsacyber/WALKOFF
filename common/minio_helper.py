from minio import Minio
from pathlib import Path
from common.config import config, static
import logging
import io
import aiodocker
import os
from os import stat
from urllib3.exceptions import ResponseError
from minio.error import NoSuchKey

import asyncio

from common.docker_helpers import connect_to_aiodocker, docker_context, stream_umpire_build_log, logger as docker_logger
import pathlib

logger = logging.getLogger("Umpire")


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
                logger.info("Sending image to be built")
                dockerfile = "./Dockerfile"
                try:
                    log_stream = await docker_client.images.build(fileobj=context, tag=repo, rm=True,
                                                                  forcerm=True, pull=True, stream=True,
                                                                  path_dockerfile=dockerfile,
                                                                  encoding="application/x-tar")
                    logger.info("Docker image building")
                    await stream_umpire_build_log(log_stream, build_id)
                    logger.info("Docker image Built")
                    # if await push_image(docker_client, repo):
                    #     return "Docker image built and pushed successfully."
                    success = await push_image(docker_client, repo)
                    if success:
                        saved = await MinioApi.save_file(app_name, version)
                        if saved is True:
                            return True
                            # return True, "Successfully built and pushed image"
                        else:
                            return False
                    else:
                        return False
                        # return False, "Failed to push image"
                except Exception as e:
                    return False
                    # return False, str(e)

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
            return data.read()
        except NoSuchKey as n:
            return "No Such Key"
        except ResponseError as e:
            return "Response Error"

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
            return True, str(r)
        except Exception as e:
            return False, str(e)

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
                #TODO: Make this more secure, don't just base it off of requirements.txt
                owner_id = stat(f"apps/{app_name}/{version}/requirements.txt").st_uid
                group_id = stat(f"apps/{app_name}/{version}/requirements.txt").st_gid
                os.chown(p_dst, owner_id, group_id)
        if editing is False:
            return False
        else:
            return True
