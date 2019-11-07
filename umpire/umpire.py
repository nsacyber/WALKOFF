import asyncio
import logging
import signal
import os
from pathlib import Path
from itertools import compress
import uuid

import aiodocker
import aiohttp
import aioredis
from aiodocker.exceptions import DockerError

from common.config import config, static
from common.helpers import send_status_update, UUID_GLOB
from common.redis_helpers import connect_to_aioredis_pool, xlen, xdel
from common.message_types import WorkflowStatusMessage
from common.workflow_types import workflow_loads
from common.docker_helpers import (ServiceKwargs, DockerBuildError, docker_context, stream_docker_log, get_containers,
                                   load_secrets, update_service, connect_to_aiodocker, get_service, get_replicas,
                                   remove_service, get_secret, load_volumes)
from umpire.app_repo import AppRepo

logging.basicConfig(level=logging.INFO, format="{asctime} - {name} - {levelname}:{message}", style='{')
logger = logging.getLogger("UMPIRE")
static.set_local_hostname("local_umpire")


class Umpire:
    def __init__(self, docker_client=None, redis=None, session=None, autoscale_worker=True, autoscale_app=True,
                 autoheal_worker=True, autoheal_apps=True):
        self.redis: aioredis.Redis = redis
        self.docker_client: aiodocker.Docker = docker_client
        self.session = session
        self.app_repo = None
        self.running_apps = {}
        self.worker = {}
        self.max_workers = 1
        self.service_replicas = {}

        self.autoscale_worker = autoscale_worker
        self.autoscale_app = autoscale_app
        self.autoheal_worker = autoheal_worker
        self.autoheal_apps = autoheal_apps

    @classmethod
    async def init(cls, docker_client, redis, session, autoscale_worker, autoscale_app, autoheal_worker, autoheal_apps):
        self = cls(docker_client, redis, session, autoscale_worker, autoscale_app, autoheal_worker, autoheal_apps)
        # await redis.flushall()  # TODO: do a more targeted cleanup of redis
        self.app_repo = await AppRepo.create(config.APPS_PATH, session)
        self.running_apps = await self.get_running_apps()
        self.worker = await get_service(self.docker_client, static.WORKER_SERVICE)
        services = await self.docker_client.services.list()
        self.service_replicas = {s["Spec"]["Name"]: (await get_replicas(self.docker_client, s["ID"])) for s in services}
        self.max_workers = config.get_int("MAX_WORKER_REPLICAS", 10)

        try:
            await self.redis.xgroup_create(static.REDIS_WORKFLOW_QUEUE, static.REDIS_WORKFLOW_GROUP, mkstream=True)
            logger.info(f"Created {static.REDIS_WORKFLOW_QUEUE} stream and {static.REDIS_WORKFLOW_GROUP} group.")

        except aioredis.errors.BusyGroupError:
            logger.info(f"{static.REDIS_WORKFLOW_QUEUE} stream already exists.")

        if len(self.app_repo.apps) < 1:
            logger.error("Walkoff must be loaded with at least one app. Please check that applications dir exists.")
            exit(1)
        return self

    @staticmethod
    async def run(autoscale_worker, autoscale_app, autoheal_worker, autoheal_apps):
        async with connect_to_aioredis_pool(config.REDIS_URI) as redis, aiohttp.ClientSession() as session, \
                connect_to_aiodocker() as docker_client:
            ump = await Umpire.init(docker_client=docker_client, redis=redis, session=session,
                                    autoscale_worker=autoscale_worker, autoscale_app=autoscale_app,
                                    autoheal_worker=autoheal_worker, autoheal_apps=autoheal_apps)

            # Attach our signal handler to cleanly close services we've created
            loop = asyncio.get_running_loop()
            for signame in {'SIGINT', 'SIGTERM'}:
                loop.add_signal_handler(getattr(signal, signame), lambda: asyncio.ensure_future(ump.shutdown()))

            # logger.info("Bringing up Umpire API...")
            # Use --reload when you want to run locally
            # os.system("uvicorn umpire.umpire_api:app --host 0.0.0.0 --port 8000 --lifespan on &")

            logger.info("Umpire is initialized!")
            await asyncio.gather(asyncio.create_task(ump.workflow_control_listener()),
                                 asyncio.create_task(ump.monitor_queues()))
        await ump.shutdown()

    async def shutdown(self):
        logger.info("Shutting down Umpire...")

        # Clean up redis streams
        action_queues = set(await self.redis.keys(pattern="*:*", encoding="utf-8")).union({static.REDIS_WORKFLOW_QUEUE})
        await self.redis.xgroup_destroy(static.REDIS_WORKFLOW_QUEUE, static.REDIS_WORKFLOW_GROUP)
        [await self.redis.xgroup_destroy(q, static.REDIS_ACTION_RESULTS_GROUP) for q in action_queues]
        mask = [await self.redis.delete(q) for q in action_queues]
        removed_qs = list(compress(action_queues, mask))
        logger.debug(f"Removed redis streams: {removed_qs}")

        # # Clean up docker services
        # services = [*(await self.get_running_apps()).keys()]
        # await self.
        # mask = [await self.launch_workers(0)]
        # removed_apps = list(compress(self.running_apps, mask))
        # logger.debug(f"Removed apps: {removed_apps}")

        # Clean up any unfinished tasks (shouldn't really be any though)
        tasks = [t for t in asyncio.all_tasks() if t is not
                 asyncio.current_task()]
        [task.cancel() for task in tasks]
        logger.info("Canceling outstanding tasks")
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("Successfully shutdown Umpire")

    async def get_running_apps(self):
        func = lambda s: s['Spec']['Name'].count(static.APP_PREFIX) > 0
        services = filter(func, (await self.docker_client.services.list()))
        return {s['Spec']['Name']: {'id': s["ID"], 'version': s['Version']['Index']} for s in services}

    async def launch_workers(self, replicas=1):
        try:
            self.worker = await get_service(self.docker_client, static.WORKER_SERVICE)
            if self.worker == {}:
                raise DockerError
            await update_service(self.docker_client, service_id=self.worker["id"], version=self.worker["version"],
                                 image=self.worker["image"], mode={"replicated": {"Replicas": replicas}})
            self.worker = await get_service(self.docker_client, self.worker["id"])
            await asyncio.sleep(3)
        except DockerError:
            logger.exception(f"Service {static.WORKER_SERVICE} failed to update")
            return

    async def launch_app(self, service_name, version, replicas=1):
        try:
            mode = {"replicated": {'Replicas': replicas}}
            self.running_apps[service_name] = await get_service(self.docker_client, service_name)
            await update_service(self.docker_client, service_id=self.running_apps[service_name]["id"],
                                 version=self.running_apps[service_name]["version"],
                                 image=self.running_apps[service_name]["image"], mode=mode)
            self.running_apps[service_name] = await get_service(self.docker_client, service_name)
            await asyncio.sleep(3)
        except DockerError:
            logger.exception(f"Service {service_name} failed to update")

    async def scale_worker(self):
        total_workflows = await xlen(self.redis, static.REDIS_WORKFLOW_QUEUE)
        executing_workflows = (await self.redis.xpending(static.REDIS_WORKFLOW_QUEUE, static.REDIS_WORKFLOW_GROUP))[0]
        queued_workflows = total_workflows - executing_workflows

        logger.debug(f"Queued Workflows: {queued_workflows}")
        logger.debug(f"Executing Workflows: {executing_workflows}")

        current_workers = self.service_replicas.get(static.WORKER_SERVICE, {"running": 0, "desired": 0})["desired"]
        workers_needed = min(total_workflows, self.max_workers)
        logger.debug(f"Running Workers: {current_workers}")
        logger.debug(f"Needed Workers: {workers_needed}")

        if workers_needed > current_workers > 0:
            await self.launch_workers(workers_needed)
        elif workers_needed > current_workers == 0:  # scale to 0 and restart
            await self.launch_workers(0)
            await self.launch_workers(workers_needed)

    async def scale_app(self):
        self.running_apps = await self.get_running_apps()
        logger.debug(
            f"Running apps: {[{s: self.service_replicas.get(s)['running']} for s in self.running_apps.keys()]}")

        streams = [key.split(':') for key in await self.redis.keys(pattern=UUID_GLOB + ":*:*", encoding="utf-8")]

        workloads = {f"{app_name}:{version}": {"total": 0, "queued": 0, "executing": 0}
                     for _, app_name, version in streams}

        if len(streams) > 0:
            for execution_id, app_name, version in streams:
                stream = f"{execution_id}:{app_name}:{version}"
                group = f"{app_name}:{version}"
                try:
                    executing_work = (await self.redis.xpending(stream=stream, group_name=group))[0]
                    total_work = await xlen(self.redis, stream)
                except aioredis.ReplyError:
                    continue  # the group or stream got closed while we were checking other streams

                queued_work = total_work - executing_work

                workloads[group]["executing"] += executing_work
                workloads[group]["queued"] += queued_work
                workloads[group]["total"] += total_work

                service_name = f"{static.APP_PREFIX}_{app_name}"
                curr_replicas = self.service_replicas.get(service_name, {"running": 0, "desired": 0})["desired"]
                max_replicas = config.get_int("MAX_APP_REPLICAS", 10)
                replicas_needed = min(total_work, max_replicas)

                logger.debug(f"Total work: {total_work}")
                logger.debug(f"queued: {total_work}")

                logger.debug(f"Needed replicas: {replicas_needed}")
                logger.debug(f"Current replicas: {curr_replicas}")

                if replicas_needed > curr_replicas:
                    logger.info(f"Launching app {':'.join([service_name, version])}")

                if replicas_needed > curr_replicas > 0:
                    await self.launch_app(service_name, version, replicas_needed)
                elif replicas_needed > curr_replicas == 0:  # scale to 0 and restart
                    await self.launch_app(service_name, version, 0)
                    await self.launch_app(service_name, version, replicas_needed)

            for service_name, workload in workloads.items():
                logger.debug(f"Queued actions for {service_name}: {workload['queued']}")
                logger.debug(f"Executing actions for {service_name}: {workload['executing']}")

    async def check_pending_actions(self):
        self.running_apps = await self.get_running_apps()
        action_queues = set(await self.redis.keys(pattern=UUID_GLOB + ":*:*", encoding="utf-8"))
        if len(action_queues) > 0:
            for key in action_queues:
                execution_id, app_name, version = key.split(':')
                service_name = f"{static.APP_PREFIX}_{app_name}"
                app_group = f"{app_name}:{version}"
                pending = (await self.redis.xpending(key, app_group))
                if pending[0] > 0:
                    containers = await get_containers(self.docker_client, service_name, short_ids=True)
                    consumers = [consumer[0].decode() for consumer in pending[-1]]
                    mask = [consumer in containers for consumer in consumers]

                    if sum(mask) < len(consumers):
                        dead_consumers = compress(consumers, (not _ for _ in mask))
                        for consumer in dead_consumers:
                            logger.warning("Claiming stale messages.")

                            dead_pending = await self.redis.xpending(key, app_group, "-", "+", 1, consumer=consumer)

                            # Umpire claims the message in the name of the UMPIRE!
                            msg = await self.redis.xclaim(key, app_group, "UMPIRE", 1000,
                                                          dead_pending[0][0].decode())

                            # Dereference the stuff we need. This may change as redis solidifies their plan
                            execution_id, action = msg[0][-1].popitem()
                            id_ = msg[0][0]

                            # Put message back in stream
                            await self.redis.xadd(key, {execution_id: action})

                            # Clean up workflow-queue
                            await self.redis.xack(stream=key, group_name=app_group, id=id_)
                            await xdel(self.redis, stream=key, id_=id_)

    async def monitor_queues(self):
        # count = 0
        while True:
            services = await self.docker_client.services.list()
            self.service_replicas = {s["Spec"]["Name"]: (await get_replicas(self.docker_client, s["ID"])) for s in
                                     services}

            if self.autoscale_worker:
                await self.scale_worker()
            if self.autoscale_app:
                await self.scale_app()
            if self.autoheal_apps:
                await self.check_pending_actions()

            # Reload the app projects and apis every once in a while
            # if count * config.get_int("UMPIRE_HEARTBEAT", 1) >= config.get_int("APP_REFRESH", 60):
            #     count = 0
            #     logger.info("Refreshing apps.")
            #     # TODO: maybe do this a bit more intelligently? Presently it throws uniqueness errors for db
            #     await self.app_repo.load_apps_and_apis()
            #     await self.app_repo.delete_unused_apps_and_apis()
            #
            await asyncio.sleep(config.get_int("UMPIRE_HEARTBEAT", 1))
            # count += 1

    async def workflow_control_listener(self):
        """ Continuously monitors the control stream for workflow abort messages """
        while True:
            try:
                with await self.redis as redis:
                    msg = await redis.xread_group(static.REDIS_WORKFLOW_CONTROL_GROUP, static.CONTAINER_ID,
                                                  streams=[static.REDIS_WORKFLOW_CONTROL], count=1, latest_ids=['>'])
            except aioredis.errors.ReplyError:
                logger.debug(f"Stream {static.REDIS_WORKFLOW_CONTROL} doesn't exist. Attempting to create it...")
                await self.redis.xgroup_create(static.REDIS_WORKFLOW_CONTROL, static.REDIS_WORKFLOW_CONTROL_GROUP,
                                               mkstream=True)
                logger.debug(f"Created stream {static.REDIS_WORKFLOW_CONTROL}.")
                continue

            if len(msg) < 1:
                continue

            # Dereference the redis stream message and load the status message
            stream = msg[0][0]
            id_ = msg[0][1]

            execution_id = msg[0][2][b"execution_id"].decode()
            workflow = workflow_loads(msg[0][2][b"workflow"])

            executing_workflows = await self.redis.xpending(static.REDIS_WORKFLOW_QUEUE, static.REDIS_WORKFLOW_GROUP)

            if executing_workflows[0] < 1:
                status = WorkflowStatusMessage.execution_aborted(execution_id, workflow.id_, workflow.name)
                await send_status_update(self.session, execution_id, workflow.id_, status)
            else:
                # Kill worker
                try:
                    worker_to_abort = executing_workflows[3][0][0].decode()
                    container = await self.docker_client.containers.get(worker_to_abort)
                    await container.kill(signal="SIGQUIT")
                except DockerError as e:
                    if not self.autoscale_worker:
                        logger.info("Need to kill worker to abort workflow, but worker is not being scaled by umpire.")
                    else:
                        logger.exception("Failed to kill worker after workflow abort. Unexpected behavior may result.")

                # Kill apps
                action_streams = await self.redis.keys(f"{execution_id}:*:*", encoding="utf-8")

                for stream in action_streams:
                    _, app_name, version = stream.split(':')
                    app_group = f"{app_name}:{version}"
                    executing_apps = (await self.redis.xpending(stream, app_group))[3]
                    await self.redis.delete(stream)

                    status = WorkflowStatusMessage.execution_aborted(execution_id, workflow.id_, workflow.name)
                    await send_status_update(self.session, execution_id, workflow.id_, status)

                    if executing_apps is None:
                        break

                    for app, _ in executing_apps:
                        container = await self.docker_client.containers.get(app.decode())
                        await container.kill(signal="SIGKILL")
                await self.redis.delete(f"{execution_id}:results")
            await self.redis.xack(stream=stream, group_name=static.REDIS_WORKFLOW_CONTROL_GROUP, id=id_)
            await xdel(self.redis, stream=stream, id_=id_)


if __name__ == "__main__":
    import argparse

    LOG_LEVELS = ("debug", "info", "error", "warn", "fatal", "DEBUG", "INFO", "ERROR", "WARN", "FATAL")
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-level", dest="log_level", choices=LOG_LEVELS, default="INFO")
    parser.add_argument("--disable-worker-autoscale", dest="autoscale_worker", action="store_false")
    parser.add_argument("--disable-app-autoscale", dest="autoscale_app", action="store_false")
    parser.add_argument("--disable-worker-autoheal", dest="autoheal_worker", action="store_false")
    parser.add_argument("--disable-app-autoheal", dest="autoheal_app", action="store_false")
    parser.add_argument("--debug", "-d", dest="debug", action="store_true",
                        help="Enables debug level logging for the umpire as well as asyncio debug mode.")
    args = parser.parse_args()

    logger.setLevel(args.log_level.upper())

    try:
        asyncio.run(Umpire.run(autoscale_worker=args.autoscale_worker, autoscale_app=args.autoscale_app,
                               autoheal_worker=args.autoheal_worker, autoheal_apps=args.autoheal_app),
                    debug=args.debug)
    except asyncio.CancelledError:
        pass
