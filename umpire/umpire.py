import asyncio
import logging
import json
from pathlib import Path
from functools import reduce
from itertools import compress

import aiodocker
import aiohttp
import aioredis
from aiodocker.exceptions import DockerError
from docker.types.services import SecretReference
from compose.cli.command import get_project


from common.config import config
from common.helpers import connect_to_redis_pool
from common.docker_helpers import ServiceKwargs, DockerBuildError, docker_context, stream_docker_log, get_secret, \
    create_secret, update_service, connect_to_aiodocker
from umpire.app_repo import AppRepo

logging.basicConfig(level=logging.info, format="{asctime} - {name} - {levelname}:{message}", style='{')
logger = logging.getLogger("UMPIRE")
logger.setLevel(logging.DEBUG)


# TODO: Add verification that AppRepo got initialized before use
class Umpire:
    def __init__(self, docker_client=None, redis=None):
        self.redis: aioredis.Redis = redis
        self.docker_client: aiodocker.Docker = docker_client
        self.apps = {}
        self.running_apps = {}
        self.worker = None

    @classmethod
    async def init(cls, docker_client, redis, session):
        self = cls(docker_client, redis)
        self.apps = await AppRepo.create(config["UMPIRE"]["apps_path"], session)
        self.running_apps = await self.get_running_apps()
        self.worker = await self.get_service("worker")
        await self.build_app_sdk()

        if len(self.apps) < 1:
            logger.error("Walkoff must be loaded with at least one app. Please check that applications dir exists.")
            exit(1)
        return self

    @staticmethod
    async def run():
        async with connect_to_redis_pool(config["REDIS"]["redis_uri"]) as redis, aiohttp.ClientSession() as session, \
                connect_to_aiodocker() as docker_client:
            ump = await Umpire.init(docker_client=docker_client, redis=redis, session=session)
            await ump.monitor_queues()
        await Umpire.shutdown()

    @staticmethod
    async def shutdown():
        # Clean up any unfinished tasks (shouldn't really be any though)
        tasks = [t for t in asyncio.all_tasks() if t is not
                 asyncio.current_task()]

        [task.cancel() for task in tasks]

        logger.info('Canceling outstanding tasks')
        await asyncio.gather(*tasks)

    async def get_running_apps(self):
        func = lambda s: s['Spec']['Name'].count(config["UMPIRE"]["app_prefix"]) > 0
        services = filter(func, (await self.docker_client.services.list()))
        return {s['Spec']['Name']:  {'id': s["ID"], 'version': s['Version']['Index']} for s in services}

    async def get_service(self, service_id):
        try:
            s = await self.docker_client.services.inspect(service_id)
            return {'id': s["ID"], 'version': s['Version']['Index']}
        except DockerError:
            return {}

    async def launch_workers(self, replicas=1):
        project = get_project(project_dir=Path(__file__).parent, project_name=config["UMPIRE"]["app_prefix"])
        worker = [service for service in project.services if service.name == "worker"][0]

        # see if the image provided by the docker-compose file can be pulled
        try:
            await self.docker_client.images.pull(worker.image_name)
        except DockerError:
            logger.debug(f"Could not pull {worker.image_name}. Trying to build local instead.")

        try:
            secrets = await self.load_secrets(project=project)
            mode = {"replicated": {'Replicas': replicas}}
            service_kwargs = ServiceKwargs.configure(image=worker.image_name, service=worker, secrets=secrets,
                                                     mode=mode)
            await self.docker_client.services.create(name=worker.name, **service_kwargs)
            self.worker = await self.get_service(worker.name)

        except DockerError:
            try:
                self.worker = await self.get_service(self.worker["id"])
                await update_service(self.docker_client, service_id=self.worker["id"], version=self.worker["version"],
                                     image=worker.image_name, mode={"replicated": {"Replicas": replicas}})
                self.worker = await self.get_service(self.worker["id"])
                return
            except DockerError:
                logger.exception(f"Service {worker.name} failed to update")
                return

    async def build_worker(self):
        try:
            logger.info(f"Building worker")
            repo = f"{config['UMPIRE']['DOCKER_REGISTRY']}/worker"
            project = get_project(project_dir=Path(__file__).parent, project_name=config["UMPIRE"]["app_prefix"])
            worker = [service for service in project.services if service.name == "worker"][0]
            build_opts = worker.options.get('build', {})

            with docker_context(Path(build_opts["context"]).parent) as context:
                log_stream = await self.docker_client.images.build(fileobj=context, tag=worker.image_name, rm=True,
                                                                   forcerm=True, pull=True, stream=True,
                                                                   path_dockerfile=build_opts["dockerfile"],
                                                                   encoding="application/x-tar")
            await stream_docker_log(log_stream)

            logger.info(f"Pushing worker")
            log_stream = await self.docker_client.images.push(repo, stream=True)
            await stream_docker_log(log_stream)

        except DockerBuildError:
            logger.exception(f"Error during worker build")
            return

    async def build_app_sdk(self):
        try:
            logger.info(f"Building walkoff_app_sdk")
            sdk_name = "walkoff_app_sdk"
            repo = f"{config['UMPIRE']['DOCKER_REGISTRY']}/{sdk_name}"
            project = get_project(project_dir=Path(__file__).parent, project_name=sdk_name)
            sdk = [service for service in project.services if service.name == sdk_name][0]
            build_opts = sdk.options.get('build', {})

            with docker_context(Path(build_opts["context"])) as context:
                log_stream = await self.docker_client.images.build(fileobj=context, tag=sdk.image_name, rm=True,
                                                                   forcerm=True, pull=True, stream=True,
                                                                   path_dockerfile=build_opts["dockerfile"],
                                                                   encoding="application/x-tar")
            await stream_docker_log(log_stream)

            # Give image a locally accessible tag as well for docker-compose up runs
            await self.docker_client.images.tag(repo, sdk_name)

            logger.info(f"Pushing walkoff_app_sdk")
            log_stream = await self.docker_client.images.push(repo, stream=True)
            await stream_docker_log(log_stream)

        except DockerBuildError:
            logger.exception(f"Error during walkoff_app_sdk build")
            return

    async def launch_app(self, app, version, replicas=1):
        app_name = f"{config['UMPIRE']['app_prefix']}_{app}"
        repo = f"{config['UMPIRE']['DOCKER_REGISTRY']}/{app_name}"
        full_tag = f"{repo}:{version}"
        service = self.apps[app][version].services[0]
        image_name = service.image_name
        image = None

        if app_name in self.running_apps:
            logger.info(f"Service {app} already exists. Trying 'update_app' instead.")
            await self.update_app(app, version, replicas)
            return

        logger.debug(f"Launching {app}...")

        # # see if the image provided by the docker-compose file can be pulled
        # try:
        #     image = await self.docker_client.images.pull(image_name)
        # except DockerError:
        #     logger.debug(f"Could not pull {image_name}. Trying to see build local instead.")

        # if we didn't find the image, try to build it
        if image is None:
            await self.build_app(app, version)
            image_name = full_tag

        try:
            secrets = await self.load_secrets(project=self.apps[app][version])
            mode = {"replicated": {'Replicas': replicas}}
            service_kwargs = ServiceKwargs.configure(image=image_name, service=service, secrets=secrets, mode=mode)
            await self.docker_client.services.create(name=app_name, **service_kwargs)
            self.running_apps[app_name] = await self.get_service(app_name)

        except DockerError:
            logger.exception(f"Service {app_name} failed to launch")
            return

        logger.info(f"Launched {app}")

    async def update_app(self, app, version, replicas=1):
        app_name = f"{config['UMPIRE']['app_prefix']}_{app}"
        repo = f"{config['UMPIRE']['DOCKER_REGISTRY']}/{app_name}"
        full_tag = f"{repo}:{version}"
        service = self.apps[app][version].services[0]
        image_name = service.image_name
        image = None

        if app_name not in self.running_apps:
            logger.info(f"Service {app} does not exists. Trying 'launch_app' instead.")
            await self.launch_app(app, version, replicas)
            return

        logger.debug(f"Updating {app}...")

        # see if the image provided by the docker-compose file can be pulled
        try:
            image = await self.docker_client.images.pull(image_name)
        except DockerError:
            logger.debug(f"Could not pull {image_name}. Trying to see build local instead.")

        # if we didn't find the image, try to build it
        if image is None:
            await self.build_app(app, version)
            image_name = full_tag

        try:
            mode = {"replicated": {'Replicas': replicas}}
            self.running_apps[app_name] = await self.get_service(app_name)
            await update_service(self.docker_client, service_id=self.running_apps[app_name]["id"],
                                 version=self.running_apps[app_name]["version"], image=image_name, mode=mode)
            self.running_apps[app_name] = await self.get_service(app_name)

        except DockerError:
            logger.exception(f"Service {app_name} failed to update")
            return

        logger.info(f"Updated {app}")

    async def load_secrets(self, project):
        service = project.services[0]
        secret_references = []
        for service_secret in service.secrets:
            secret = service_secret["secret"]
            filename = service_secret.get("file", secret.source)

            # Compose doesn't parse external secrets so we'll assume there is one and build if it doesn't exist
            try:
                secret_id = await get_secret(self.docker_client, secret.source)

            except (AttributeError, DockerError):
                with open(filename, 'rb') as fp:
                    data = fp.read()
                secret_id = await create_secret(self.docker_client, name=secret.source, data=data)

            secret_references.append(SecretReference(secret_id=secret_id["ID"], secret_name=secret.source,
                                                     uid=secret.uid, gid=secret.gid, mode=secret.mode))
        return secret_references

    async def build_app(self, app, version):
        app_name = f"{config['UMPIRE']['app_prefix']}_{app}"
        repo = f"{config['UMPIRE']['DOCKER_REGISTRY']}/{app_name}"
        full_tag = f"{repo}:{version}"
        service = self.apps[app][version].services[0]
        build_opts = service.options.get('build', {})

        if build_opts.get("context", None) is None:
            logger.error(f"App {app}:{version} must specify docker build context in docker-compose.yaml.")
            return

        try:
            logger.info(f"Building {app}:{version}")
            with docker_context(build_opts["context"]) as context:
                log_stream = await self.docker_client.images.build(fileobj=context, tag=full_tag, rm=True, forcerm=True,
                                                                   path_dockerfile="Dockerfile", stream=True,
                                                                   encoding="application/x-tar")
            await stream_docker_log(log_stream)

            # Give image a locally accessible tag as well for docker-compose up runs
            await self.docker_client.images.tag(full_tag, app_name, tag=version)

            # TODO: don't push failed builds
            logger.info(f"Pushing {app}:{version}")
            log_stream = await self.docker_client.images.push(repo, tag=version, stream=True)
            await stream_docker_log(log_stream)

        except DockerBuildError:
            logger.exception(f"Error during {app}:{version} build")
            return

    async def remove_service(self, service):
        try:
            return await self.docker_client.services.delete(service)
        except DockerError:
            logger.exception(f"Could not delete {service}.")
            return False

    async def monitor_queues(self):
        def replicas_getter(d, service):
            if "ID" in d:
                d = {d["Spec"]["Name"]: d["Spec"]["Mode"]["Replicated"]["Replicas"]}
            d[service["Spec"]["Name"]] = service["Spec"]["Mode"]["Replicated"]["Replicas"]
            return d

        count = 0
        while True:
            # TODO: Come up with a more robust system of naming queues
            # Find all redis keys matching our "{AppName}-{Priority}" pattern
            keys = set(await self.redis.keys(pattern="*:*:[1-5]", encoding="utf-8"))
            logger.info(f"Redis keys: {keys}")

            self.running_apps = await self.get_running_apps()
            logger.info(f"Running apps: {[service for service in self.running_apps.keys()]}")

            num_workflows = await self.redis.llen(config["REDIS"]["workflow_q"])
            logger.info(f"Number of Workflows: {num_workflows}")

            services = await self.docker_client.services.list()
            service_replicas = reduce(replicas_getter, services) if len(services) > 0 else {}

            workers_needed = min((num_workflows - service_replicas.get("worker", 0)),
                                 config.getint("UMPIRE", "max_workers"))
            if workers_needed > 0:
                await self.launch_workers(workers_needed)

            else:
                if self.worker:
                    await self.remove_service("worker")
                    self.worker = {}

            if len(keys) > 0:  # we have some work for the apps, let's spin some up
                for key in keys:
                    workload = await self.redis.llen(key)
                    app_name, version, _ = key.split(':')  # should yield [app_name, version, priority]
                    curr_replicas = service_replicas.get(app_name, 0)
                    max_replicas = self.apps[app_name][version].services[0].options["deploy"]["replicas"]
                    replicas_needed = min((workload - curr_replicas), max_replicas)
                    if curr_replicas == 0:
                        await self.launch_app(app_name, version, replicas=replicas_needed)
                    logger.info(f"Launched copy of {':'.join([app_name, version])}")

            else:  # There isn't any work so lets kill any running apps and workers
                mask = [await self.remove_service(app) for app in self.running_apps]
                removed_apps = list(compress(self.running_apps, mask))
                logger.debug(f"Removed apps: {removed_apps}")

            # Check to see if any apps are running that we don't have work for and kill them
            for key in filter(lambda s: any([app.lstrip(config["UMPIRE"]["app_prefix"]) not in s
                                             for app in self.running_apps]), keys):
                app, _, __ = key.split(':')
                await self.remove_service(app)
                logger.debug(f"Removed app: {app}")

            # Reload the app projects and apis every once in a while
            if count * 5 >= config.getint("UMPIRE", "app_refresh"):
                count = 0
                logger.info("Refreshing apps.")
                # TODO: maybe do this a bit more intelligently? Presently it throws uniqueness errors for db
                await self.apps.load_apps_and_apis()

            await asyncio.sleep(5)
            count += 1


if __name__ == "__main__":
    asyncio.run(Umpire.run())
