import asyncio
import logging
import re
import os
import sys

import aioredis
import docker
import docker.tls
import docker.errors
import docker.types
import docker.models.services
from docker.types.services import SecretReference
from compose.service import Service


from common.config import load_config
from common.helpers import connect_to_redis_pool, connect_to_docker, ServiceKwargs
from umpire.app_repo import AppRepo

logging.basicConfig(level=logging.info, format="{asctime} - {name} - {levelname}:{message}", style='{')
logger = logging.getLogger("UMPIRE")
logger.setLevel(logging.DEBUG)

config = load_config()
USING_DOCKER = config["UMPIRE"]["backend"].casefold() == "docker".casefold()
USING_KUBERNETES = config["UMPIRE"]["backend"].casefold() == "kubernetes".casefold() \
                or config["UMPIRE"]["backend"].casefold() == "k8s".casefold()

if not (USING_DOCKER or USING_KUBERNETES):
    logger.error("No valid orchestration selected. Please select either 'docker' or 'kubernetes'")
    sys.exit(1)


# TODO: Add verification that AppRepo got initialized before use
class Umpire:
    def __init__(self, docker_client=None, k8s_client=None, redis_client=None):
        self.redis_client: aioredis.Redis = redis_client
        self.docker_client: docker.DockerClient = docker_client
        self.k8s_client = k8s_client
        self.apps = dict()

    @classmethod
    async def init(cls, docker_client=None, k8s_client=None, redis_client=None):
        inst = cls(docker_client, k8s_client, redis_client)
        inst.apps = await AppRepo.create(config["UMPIRE"]["apps_path"], redis_client)

        if len(inst.apps) < 1:
            logger.error("Walkoff must be loaded with at least one app. Please check that applications dir exists.")
            exit(1)
        return inst

    def launch_app(self, app, version):
        logger.debug(f"Launching {app}-{version}")

        repo = f"{config['UMPIRE']['DOCKER_REGISTRY']}/{config['UMPIRE']['DOCKER_REPOSITORY']}"
        tag = f"{repo}:{app}-{version}"
        secrets = self.load_secrets(app, version)

        # see if we have an image and build one if not
        try:
            self.docker_client.images.get(tag)

        except docker.errors.ImageNotFound:
            self.build_app(app, version)

        except docker.errors.APIError:
            logger.exception(f"Docker API error during launch of {app}-{version}")
            return

        service_kwargs = ServiceKwargs().configure(service=self.apps[app][version].services[0], secrets=secrets)
        service: docker.models.services.Service = self.docker_client.services.create(tag, **service_kwargs)

        logger.info(f"Launched {app}")

    def load_secrets(self, app, version) -> [SecretReference]:
        project = self.apps[app][version]
        service: Service = project.services[0]
        secret_references = []
        for service_secret in service.secrets:
            secret = service_secret["secret"]
            filename = service_secret.get("file", secret.source)

            # Compose doesn't parse external secrets so we'll assume there is one and build if it doesn't exist
            try:
                secret_id = self.docker_client.secrets.get(secret.source)

            except docker.errors.NotFound:
                with open(filename, 'rb') as fp:
                    data = fp.read()

                secret_id = self.docker_client.secrets.create(name=secret.source, data=data).id

            except docker.errors.APIError:
                logger.exception(f"Docker API error during retrival of secret: {secret.source}")
                return

            secret_references.append(SecretReference(secret_id=secret_id, secret_name=secret.source,
                                                     filename=filename, uid=secret.uid, gid=secret.gid,
                                                     mode=secret.mode))
        return secret_references

    def build_app(self, app, version):
        repo = f"{config['UMPIRE']['DOCKER_REGISTRY']}/{config['UMPIRE']['DOCKER_REPOSITORY']}"
        tag = f"{app}-{version}"
        full_tag = f"{repo}:{tag}"

        service: Service = self.apps[app][version].services[0]
        build_opts = service.options.get('build', {})

        try:
            logger.info(f"Building {app}-{version}")
            path = build_opts.get("context", None)
            image, logs = self.docker_client.images.build(path=path, tag=full_tag, rm=True, forcerm=True, pull=True)
            for line in logs:
                if "stream" in line and line["stream"].strip():
                    logger.debug(line["stream"].strip())
                elif "status" in line:
                    logger.info(line["status"].strip())
            logger.info(f"Pushing {app}-{version}")
            for line in self.docker_client.images.push(repo, tag=tag, stream=True, decode=True):
                if line.get("status", False):
                    logger.debug(line["status"])

            return image

        except TypeError:
            logger.exception(f"No build path specified for {app}-{version} build")
            return

        except docker.errors.BuildError:
            logger.exception(f"Error during {app}-{version} build")
            return

        except docker.errors.APIError:
            logger.exception(f"Docker API error during {app}-{version} build")
            return

    async def monitor_queues(self):

        while True:
            # TODO: Come up with a more robust system of naming queues
            # Find all redis keys matching our "{AppName}-{Priority}" pattern
            keys = await self.redis_client.keys(pattern="[A-Z]*-[1-5]", encoding="utf-8")
            services = self.docker_client.services.list()
            logger.info(f"Redis keys: {keys}")
            logger.info(f"Running apps: {services}")
            await asyncio.sleep(10)
            for key in keys:
                workload = self.redis_client.llen(key)
                # if workload > 0 and self.docker_client.services.get(key.split())


if __name__ == "__main__":
    async def run_umpire():
        async with connect_to_redis_pool(config["REDIS"]["redis_uri"]) as redis:
            ump = await Umpire.init(docker_client=connect_to_docker(), redis_client=redis)
            # ump.build_app("TestApp", "v0.1.1")
            # ump.launch_app("TestApp", "v0.1.1")
            await ump.monitor_queues()

        # Clean up any unfinished tasks (shouldn't really be any though)
        tasks = [t for t in asyncio.all_tasks() if t is not
                 asyncio.current_task()]

        [task.cancel() for task in tasks]

        logger.info('Canceling outstanding tasks')
        await asyncio.gather(*tasks)

    asyncio.run(run_umpire())
