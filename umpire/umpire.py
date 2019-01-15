import asyncio
import logging
import re
import json
import os
from contextlib import asynccontextmanager

import aioredis
import docker
import docker.tls
import docker.errors
from docker.models.images import Image
from compose.cli.main import TopLevelCommand
from compose.project import Project
from compose.cli.command import set_parallel_limit, get_project
from compose.config.environment import Environment

from common import config

logging.basicConfig(level=logging.DEBUG, format="{asctime} - {name} - {levelname}:{message}", style='{')
logger = logging.getLogger("UMPIRE")


def load_env():
    environment = os.environ
    environment.update({key: val for key, val in config["umpire"]["docker_compose_env"].items() if val is not None})
    return Environment(environment)


def load_app_repo(path):
    apps = {}
    for app in os.listdir(path):
        #  grabs only directories and ignores all __* directories i.e. __pycache__
        if os.path.isdir(os.path.join(path, app)) and not re.fullmatch("(__.*)", app):
            apps[app] = {}
            app_path = os.path.join(path, app)
            for version in os.listdir(app_path):
                if re.fullmatch(r"(v(\d\.?)+)", version):  # grabs all valid version directories of form "v0.12.3.45..."
                    version_path = os.path.join(app_path, version)
                    if ORCHESTRATOR is Orchistrator.LOCAL:
                        pass
                    elif ORCHESTRATOR is Orchistrator.DOCKER_COMPOSE:
                        pass
                    elif ORCHESTRATOR is Orchistrator.DOCKER_SWARM:
                        get_project(project_dir=version_path, environment=load_env())
                        apps[app][version] = project_from_options(os.path.join(path, app, version), DOCKER_COMPOSE_OPTS)
                        # apps[app] = {v for v in os.listdir(os.path.join(path, app)) if re.fullmatch(r"(v(\d\.?)+)", v)}
                    elif ORCHESTRATOR is Orchistrator.KUBERNETES:
                        pass



                logger.debug(f"Loaded {app} versions: {apps[app].keys()}")
    return apps


class Umpire:
    def __init__(self, redis=None):
        self.redis: aioredis.Redis = redis
        self.docker: docker.DockerClient = None
        self.kubernetes = None
        self.app_repo = load_app_repo(config["umpire"]["app_repo_path"])

    @asynccontextmanager
    async def connect_to_redis_pool(self, redis_uri) -> aioredis.Redis:
        # Redis client bound to pool of connections (auto-reconnecting).
        self.redis = await aioredis.create_redis_pool(redis_uri)
        try:
            yield self.redis
        finally:
            # gracefully close pool
            self.redis.close()
            await self.redis.wait_closed()
            logger.info("Redis connection pool closed.")

    # def connect_to_docker(self, docker_url):
    #     tls_config = docker.tls.TLSConfig(ca_cert=os.path.join(DOCKER_CERT_DIR, "ca.pem"),
    #                                       client_cert=(os.path.join(DOCKER_CERT_DIR, "cert.pem"),
    #                                                    os.path.join(DOCKER_CERT_DIR, "key.pem")))
    #     self.docker = docker.DockerClient(base_url=docker_url, tls=tls_config)
    #     try:
    #         if self.docker.ping():
    #             logger.debug(f"Connected to Docker Engine: v{self.docker.version()['Version']}")
    #             return
    #     except docker.errors.APIError as e:
    #         logger.error(f"Docker API error during connect: {e}")
    #         return

    async def get_messages(self, umpire_channel_key):
        """ Continuously monitors the message queue """
        channel: [aioredis.Channel] = (await self.redis.subscribe(umpire_channel_key))[0]
        while True:
            print(await self.redis.keys('*'))
            msg = await channel.get_json()
            if msg is None:
                break  # channel was unsubbed

            if msg["command"] == "query":
                pass
            elif msg["command"] == "build":
                self.docker.images.build()
        logger.info("Channel closed")

    def launch_app(self, image: Image):
        app = image.tags[-1]
        logger.debug(f"Launching {app}")
        env = None
        if os.path.exists(os.path.join(*app.split(':'), "env.txt")):
            with open(os.path.join(*app.split(':'), "env.txt")) as fp:
                env = [line for line in fp if re.fullmatch("(\w+=\w+)", line)]
        self.docker.containers.run(image, environment=env, detach=True, remove=True, auto_remove=True)
        logger.info(f"Launched {app}")

    def build_app(self, app, version):
        dockerfile_path = os.path.join(config["umpire"]["app_repo_path"], app, version)
        try:
            image, logs = self.docker.images.build(path=dockerfile_path, tag=f"walkoff:{app}-{version}", rm=True,
                                                   forcerm=True, pull=True)
            for line in logs:
                logger.debug(line)

            self.launch_app(image)

        except docker.errors.BuildError as e:
            logger.error(f"Docker build error during {app}-{version} build: {e.build_log}")
            return

        except docker.errors.APIError as e:
            logger.error(f"Docker API error during {app}-{version} build: {e}")
            return


if __name__ == "__main__":

    async def run_umpire():
        ump = Umpire()
        # ump.connect_to_docker()
        async with ump.connect_to_redis_pool() as redis:
            await ump.get_messages(config["umpire"]["apigateway2umpire_ch"])

        # Clean up any unfinished tasks (shouldn't really be any though)
        tasks = [t for t in asyncio.all_tasks() if t is not
                 asyncio.current_task()]

        [task.cancel() for task in tasks]

        logger.info('Canceling outstanding tasks')
        await asyncio.gather(*tasks)

    asyncio.run(run_umpire())