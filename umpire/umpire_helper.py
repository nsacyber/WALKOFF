from minio import Minio
from pathlib import Path
from common.config import config, static
import asyncio
import logging


from common.docker_helpers import connect_to_aiodocker, docker_context, stream_docker_log, logger as docker_logger
import pathlib

# tag_name = f"{static.APP_PREFIX}_hello_world"
# app_name = "hello_world"
# version = "1.0.0"
logger = logging.getLogger("Umpire API")


class UmpireApi:

    @staticmethod
    async def build_image(app_name, version):
        tag_name = f"{static.APP_PREFIX}_{app_name}"
        try:
            pathlib.Path(f"./temp_apps/{app_name}/{version}/src").mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(e)

        minio_client = Minio(config.MINIO, access_key='walkoff', secret_key='walkoff123', secure=False)

        objects = minio_client.list_objects("apps-bucket", recursive=True)
        for obj in objects:
            size = obj.size
            p_src = Path(obj.object_name)
            if p_src.parts[1] == app_name:
                hold = str(p_src)
                p_dst = hold[hold.find(app_name):]
                p_dst = f"./temp_apps/{p_dst}"

                data = minio_client.get_object('apps-bucket', hold)
                with open(str(p_dst), 'wb') as file_data:
                    for d in data.stream(size):
                        file_data.write(d)

        logger.setLevel("DEBUG")
        docker_logger.setLevel("DEBUG")
        async with connect_to_aiodocker() as docker_client:
            # async def build_image(docker_client, repo, dockerfile, context_dir, dockerignore):
            # logger.info(f"Building {repo} with {Dockerfile} in {./ data / temp_apps / {app_name} / version /}")
            context_dir = f"./temp_apps/{app_name}/{version}/"
            with docker_context(Path(context_dir)) as context:
                dockerfile = "./Dockerfile"
                log_stream = await docker_client.images.build(fileobj=context, tag=f"{config.DOCKER_REGISTRY}/{tag_name}:{version}", rm=True,
                                                          forcerm=True, pull=True, stream=True,
                                                          path_dockerfile=dockerfile,
                                                          encoding="application/x-tar")
                await stream_docker_log(log_stream)
    @staticmethod
    async def list_files(app_name, version):
        relative_path = []
        minio_client = Minio(config.MINIO, access_key='walkoff', secret_key='walkoff123', secure=False)

        objects = minio_client.list_objects("apps-bucket", recursive=True)
        for obj in objects:
            p_src = Path(obj.object_name)
            if p_src.parts[1] == app_name:
                p_dst = p_src.relative_to(f"{p_src.parts[0]}/{app_name}/{version}")
                relative_path.append(str(p_dst))
        return relative_path

    @staticmethod
    async def get_file(app_name, version, path):
        minio_client = Minio(config.MINIO, access_key='walkoff', secret_key='walkoff123', secure=False)
        abs_path = f"apps/{app_name}/{version}/{path}"
        data = minio_client.get_object('apps-bucket', abs_path)
        return data.read()

    @staticmethod
    async def update_file(app_name, version, path, file_data, file_size):
        minio_client = Minio(config.MINIO, access_key='walkoff', secret_key='walkoff123', secure=False)

        abs_path = f"apps/{app_name}/{version}/{path}"
        found = False
        try:
            minio_client.stat_object("apps-bucket", abs_path)
            found = True
        except Exception as e:
            return str(e)

        if found is True:
            minio_client.remove_object("apps-bucket", abs_path)
            minio_client.put_object("apps-bucket", abs_path, file_data, file_size)
            return True
        else:
            return False

