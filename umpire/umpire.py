import asyncio
import logging
import signal
from pathlib import Path
from itertools import compress
    

import aiodocker
import aiohttp
import aioredis
from aiodocker.exceptions import DockerError
from compose.cli.command import get_project


from common.config import config
from common.helpers import connect_to_redis_pool
from common.docker_helpers import ServiceKwargs, DockerBuildError, docker_context, stream_docker_log, \
    load_secrets, update_service, connect_to_aiodocker, get_service, get_replicas, remove_service
from umpire.app_repo import AppRepo

logging.basicConfig(level=logging.info, format="{asctime} - {name} - {levelname}:{message}", style='{')
logger = logging.getLogger("UMPIRE")
logger.setLevel(logging.DEBUG)


class Umpire:
    def __init__(self, docker_client=None, redis=None):
        self.redis: aioredis.Redis = redis
        self.docker_client: aiodocker.Docker = docker_client
        self.apps = {}
        self.running_apps = {}
        self.worker = {}
        self.max_workers = 1
        self.service_replicas = {}

    @classmethod
    async def init(cls, docker_client, redis, session):
        self = cls(docker_client, redis)
        await redis.flushall()  # TODO: do a more targeted cleanup of redis
        self.apps = await AppRepo.create(config.APPS_PATH, session)
        self.running_apps = await self.get_running_apps()
        self.worker = await get_service(self.docker_client, "worker")
        services = await self.docker_client.services.list()
        self.service_replicas = {s["Spec"]["Name"]: (await get_replicas(self.docker_client, s["ID"])) for s in services}
        await self.build_app_sdk()
        await self.build_worker()

        if len(self.apps) < 1:
            logger.error("Walkoff must be loaded with at least one app. Please check that applications dir exists.")
            exit(1)
        return self

    @staticmethod
    async def run():
        async with connect_to_redis_pool(config.REDIS_URI) as redis, aiohttp.ClientSession() as session, \
                connect_to_aiodocker() as docker_client:
            ump = await Umpire.init(docker_client=docker_client, redis=redis, session=session)

            # Attach our signal handler to cleanly close services we've created
            loop = asyncio.get_running_loop()
            for signame in {'SIGINT', 'SIGTERM'}:
                loop.add_signal_handler(getattr(signal, signame), lambda: asyncio.ensure_future(ump.shutdown()))

            await ump.monitor_queues()
        await ump.shutdown()

    async def shutdown(self):
        logger.info("Shutting down Umpire...")
        services = [*(await self.get_running_apps()).keys(), "worker"]
        mask = [await remove_service(self.docker_client, s) for s in services]
        removed_apps = list(compress(self.running_apps, mask))
        logger.debug(f"Removed apps: {removed_apps}")
        
        # Clean up any unfinished tasks (shouldn't really be any though)
        tasks = [t for t in asyncio.all_tasks() if t is not
                 asyncio.current_task()]
        [task.cancel() for task in tasks]
        logger.info("Canceling outstanding tasks")
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("Successfully shutdown Umpire")

    async def get_running_apps(self):
        func = lambda s: s['Spec']['Name'].count(config.APP_PREFIX) > 0
        services = filter(func, (await self.docker_client.services.list()))
        return {s['Spec']['Name']:  {'id': s["ID"], 'version': s['Version']['Index']} for s in services}

    async def launch_workers(self, replicas=1):
        project = get_project(project_dir=Path(__file__).parent, project_name=config.APP_PREFIX)
        worker = [service for service in project.services if service.name == "worker"][0]

        # see if the image provided by the docker-compose file can be pulled
        try:
            await self.docker_client.images.pull(worker.image_name)
        except DockerError:
            logger.debug(f"Could not pull {worker.image_name}. Trying to build local instead.")
            await self.build_worker()

        try:
            secrets = await load_secrets(self.docker_client, project=project)
            mode = {"replicated": {'Replicas': replicas}}
            service_kwargs = ServiceKwargs.configure(image=worker.image_name, service=worker, secrets=secrets,
                                                     mode=mode)
            await self.docker_client.services.create(name=worker.name, **service_kwargs)
            self.worker = await get_service(self.docker_client, worker.name)

        except DockerError:
            try:
                self.worker = await get_service(self.docker_client, "worker")
                if self.worker == {}:
                    raise DockerError
                await update_service(self.docker_client, service_id=self.worker["id"], version=self.worker["version"],
                                     image=worker.image_name, mode={"replicated": {"Replicas": replicas}})
                self.worker = await get_service(self.docker_client, self.worker["id"])
                return
            except DockerError:
                logger.exception(f"Service {worker.name} failed to update")
                return

    async def build_worker(self):
        try:
            logger.info(f"Building worker")
            repo = f"{config.DOCKER_REGISTRY}/worker"
            project = get_project(project_dir=Path(__file__).parent, project_name=config.APP_PREFIX)
            worker = [service for service in project.services if service.name == "worker"][0]
            build_opts = worker.options.get('build', {})
            self.max_workers = worker.options.get("deploy", {}).get("replicas", 1)

            with docker_context(Path(build_opts["context"]).parent, dirs=["common", "worker"]) as context:
                log_stream = await self.docker_client.images.build(fileobj=context, tag=worker.image_name, rm=True,
                                                                   forcerm=True, pull=True, stream=True,
                                                                   path_dockerfile=build_opts["dockerfile"],
                                                                   encoding="application/x-tar")
            await stream_docker_log(log_stream)
        except DockerBuildError:
            logger.exception(f"Error during worker build")
            return

        try:
            logger.info(f"Pushing worker")
            log_stream = await self.docker_client.images.push(repo, stream=True)
            await stream_docker_log(log_stream)

        except DockerBuildError:
            logger.exception(f"Error during worker push")
            return

    async def build_app_sdk(self):
        try:
            logger.info(f"Building walkoff_app_sdk")
            sdk_name = "walkoff_app_sdk"
            repo = f"{config.DOCKER_REGISTRY}/{sdk_name}"
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
        except DockerBuildError:
            logger.exception(f"Error during walkoff_app_sdk build")
            return

        try:
            logger.info(f"Pushing walkoff_app_sdk")
            log_stream = await self.docker_client.images.push(repo, stream=True)
            await stream_docker_log(log_stream)
        except DockerBuildError:
            logger.exception(f"Error during walkoff_app_sdk push")
            return

    async def launch_app(self, app, version, replicas=1):
        app_name = f"{config.APP_PREFIX}_{app}"
        repo = f"{config.DOCKER_REGISTRY}/{app_name}"
        full_tag = f"{repo}:{version}"
        service = self.apps[app][version].services[0]
        image_name = service.image_name
        image = None

        if app_name in self.running_apps:
            logger.info(f"Service {app} already exists. Trying 'update_app' instead.")
            await self.update_app(app, version, replicas)
            return

        logger.debug(f"Launching {app}...")

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
            secrets = await load_secrets(self.docker_client, project=self.apps[app][version])
            mode = {"replicated": {'Replicas': replicas}}
            service_kwargs = ServiceKwargs.configure(image=image_name, service=service, secrets=secrets, mode=mode)
            await self.docker_client.services.create(name=app_name, **service_kwargs)
            self.running_apps[app_name] = await get_service(self.docker_client, app_name)

        except DockerError:
            logger.exception(f"Service {app_name} failed to launch")
            return

        logger.info(f"Launched {app}")

    async def update_app(self, app, version, replicas=1):
        app_name = f"{config.APP_PREFIX}_{app}"
        repo = f"{config.DOCKER_REGISTRY}/{app_name}"
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
            self.running_apps[app_name] = await get_service(self.docker_client, app_name)
            await update_service(self.docker_client, service_id=self.running_apps[app_name]["id"],
                                 version=self.running_apps[app_name]["version"], image=image_name, mode=mode)
            self.running_apps[app_name] = await get_service(self.docker_client, app_name)

        except DockerError:
            logger.exception(f"Service {app_name} failed to update")
            return

        logger.info(f"Updated {app}")

    async def build_app(self, app, version):
        app_name = f"{config.APP_PREFIX}_{app}"
        repo = f"{config.DOCKER_REGISTRY}/{app_name}"
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
        except DockerBuildError:
            logger.exception(f"Error during {app}:{version} build")
            return

        try:
            logger.info(f"Pushing {app}:{version}")
            log_stream = await self.docker_client.images.push(repo, tag=version, stream=True)
            await stream_docker_log(log_stream)

        except DockerBuildError:
            logger.exception(f"Error during {app}:{version} push")
            return

    async def scale_worker(self):
        queued_workflows = await self.redis.llen(config.REDIS_WORKFLOW_QUEUE)
        logger.info(f"Queued Workflows: {queued_workflows}")

        curr_workers = self.service_replicas.get("worker", {"running": 0, "desired": 0})["desired"]
        workers_needed = min((queued_workflows - curr_workers), self.max_workers)

        if workers_needed > curr_workers > 0:
            await self.launch_workers(workers_needed)
        elif workers_needed > curr_workers == 0:  # scale to 0 and restart
            await self.launch_workers(0)
            await self.launch_workers(workers_needed)

    async def scale_app(self):
        self.running_apps = await self.get_running_apps()
        logger.info(f"Running apps: {[service for service in self.running_apps.keys()]}")

        action_queues = set(await self.redis.keys(pattern="*:*:[1-5]", encoding="utf-8"))
        if len(action_queues) > 0:
            for key in action_queues:
                workload = await self.redis.llen(key)
                app_name, version, _ = key.split(':')  # should yield [app_name, version, priority]
                service_name = f"{config.APP_PREFIX}_{app_name}"
                curr_replicas = self.service_replicas.get(service_name, {"running": 0, "desired": 0})["desired"]
                max_replicas = self.apps[app_name][version].services[0].options["deploy"]["replicas"]
                replicas_needed = min((workload - curr_replicas), max_replicas)

                if replicas_needed > curr_replicas > 0:
                    await self.update_app(app_name, version, replicas_needed)
                elif replicas_needed > curr_replicas == 0:  # scale to 0 and restart
                    await self.update_app(app_name, version, 0)
                    await self.update_app(app_name, version, replicas_needed)

                logger.info(f"Launched copy of {':'.join([app_name, version])}")

    async def monitor_queues(self):
        count = 0
        while True:
            services = await self.docker_client.services.list()
            self.service_replicas = {s["Spec"]["Name"]: (await get_replicas(self.docker_client, s["ID"])) for s in services}

            await self.scale_worker()
            await self.scale_app()

            # Reload the app projects and apis every once in a while
            if count * config.get_int("UMPIRE_HEARTBEAT", 1) >= config.get_int("APP_REFRESH", 60):
                count = 0
                logger.info("Refreshing apps.")
                # TODO: maybe do this a bit more intelligently? Presently it throws uniqueness errors for db
                await self.apps.load_apps_and_apis()

            await asyncio.sleep(config.get_int("UMPIRE_HEARTBEAT", 1))
            count += 1


if __name__ == "__main__":
    try:
        asyncio.run(Umpire.run())
    except asyncio.CancelledError:
        pass
