import datetime
import logging
import asyncio
import sys

import aioredis
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

from common.message_types import NodeStatusMessage, message_dumps
from common.workflow_types import workflow_loads, Action, ParameterVariant
from common.async_logger import AsyncLogger, AsyncHandler
from common.helpers import UUID_GLOB, fernet_encrypt, fernet_decrypt
from common.redis_helpers import connect_to_aioredis_pool, xlen, xdel, deref_stream_message
from common.socketio_helpers import connect_to_socketio
from common.config import config, static


class SIOStream:
    """ Thin wrapper around an HTTP stream that plugs into the async logger """
    def __init__(self, sio=None):
        super().__init__()
        self.sio = sio
        self.execution_id = None
        self.workflow_id = None

    def flush(self):
        pass

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(min=1, max=10))
    def write(self, message):

        data = {
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "message": message
        }
        self.sio.emit(static.SIO_EVENT_LOG, data, static.SIO_NS_CONSOLE)

    def close(self):
        pass


class AppBase:
    """ The base class for Python-based Walkoff applications, handles Redis and logging configurations. """
    __version__ = None
    app_name = None

    def __init__(self, redis=None, logger=None):
        if self.app_name is None or self.__version__ is None:
            logger.error(("App name or version not set. Please ensure self.app_name is set to match the "
                          "docker-compose service name and self.__version__ is set to match the api.yaml."))
            sys.exit(1)
        #
        # if CONTAINER_ID is None:
        #     logger.error(("CONTAINER_ID not not available. Please ensure 'HOSTNAME' environment variable is set to "
        #                   "match the docker container id. This should be handled automatically by docker but in this "
        #                   "case something must have gone wrong..."))
        #     sys.exit(1)

        # Creates redis keys of format "{AppName}:{Version}:{Priority}"
        self.redis: aioredis.Redis = redis
        self.logger = logger if logger is not None else logging.getLogger("AppBaseLogger")
        self.current_execution_id = None
        self.current_workflow_id = None

    async def get_actions(self):
        """ Continuously monitors the action queue and asynchronously executes actions """
        self.logger.debug("Waiting for actions...")
        app_group = f"{self.app_name}:{self.__version__}"

        while True:
            await asyncio.sleep(1)

            streams = await self.redis.keys(f"{UUID_GLOB}:{app_group}", encoding='utf-8')
            aborted = await self.redis.smembers(static.REDIS_ABORTING_WORKFLOWS, encoding="utf-8")
            streams = [s for s in streams if s.split(':')[0] not in aborted]
            num_streams = len(streams)

            if num_streams < 1:
                sys.exit(-1)  # There's no scheduled work and no reason to live

            try:
                # See if we have any pending messages first
                message = await self.redis.xread_group(app_group, static.CONTAINER_ID, streams=streams, count=1,
                                                       latest_ids=list('0' * num_streams), timeout=None)

                if len(message) < 1:  # We don't have any pending so lets get a new one
                    message = await self.redis.xread_group(app_group, static.CONTAINER_ID, streams=streams, count=1,
                                                           latest_ids=list('>' * num_streams), timeout=None)

                if len(message) < 1:  # We didn't get any messages, start over with new streams
                    continue
            except aioredis.errors.ReplyError:
                continue  # Just keep trying to read messages. This likely gets thrown if a stream doesn't exist

            execution_id_action, stream, id_ = deref_stream_message(message)
            execution_id, action = execution_id_action

            # Actually execute the action
            action = workflow_loads(action)
            await self.execute_action(action)

            # Clean up workflow-queue
            await self.redis.xack(stream=stream, group_name=app_group, id=id_)
            await xdel(self.redis, stream=stream, id_=id_)

    async def execute_action(self, action: Action):
        """ Execute an action, and push its result to Redis. """
        # TODO: Is there a better way to do this?
        self.logger.handlers[0].stream.execution_id = action.execution_id
        self.logger.handlers[0].stream.workflow_id = action.workflow_id

        self.logger.debug(f"Attempting execution of: {action.label}-{action.execution_id}")
        self.current_execution_id = action.execution_id
        self.current_workflow_id = action.workflow_id

        results_stream = f"{action.execution_id}:results"

        if hasattr(self, action.name):
            # Tell everyone we started execution
            action.started_at = datetime.datetime.now()
            start_action_msg = NodeStatusMessage.executing_from_node(action, action.execution_id,
                                                                     started_at=action.started_at)
            await self.redis.xadd(results_stream, {action.execution_id: message_dumps(start_action_msg)})

            try:
                func = getattr(self, action.name, None)
                if callable(func):
                    if len(action.parameters) < 1:
                        result = await func()
                    else:
                        params = {}
                        for p in action.parameters:
                            if p.variant == ParameterVariant.GLOBAL:
                                key = config.get_from_file(config.ENCRYPTION_KEY_PATH, mode='rb')
                                params[p.name] = fernet_decrypt(key, p.value)
                            else:
                                params[p.name] = p.value
                        result = await func(**params)

                    action_result = NodeStatusMessage.success_from_node(action, action.execution_id, result=result,
                                                                        started_at=action.started_at)
                    self.logger.debug(f"Executed {action.label}-{action.execution_id} "
                                      f"with result: {result}")

                else:
                    self.logger.error(f"App {self.__class__.__name__}.{action.name} is not callable")
                    action_result = NodeStatusMessage.failure_from_node(action, action.execution_id,
                                                                        result="Action not callable",
                                                                        started_at=action.started_at)

            except Exception as e:
                self.logger.exception(f"Failed to execute {action.label}-{action.execution_id}")
                action_result = NodeStatusMessage.failure_from_node(action, action.execution_id, result=repr(e),
                                                                    started_at=action.started_at)

        else:
            self.logger.error(f"App {self.__class__.__name__} has no method {action.name}")
            action_result = NodeStatusMessage.failure_from_node(action, action.execution_id,
                                                                result="Action does not exist",
                                                                started_at=action.started_at)

        await self.redis.xadd(results_stream, {action.execution_id: message_dumps(action_result)})

    @classmethod
    async def run(cls):
        """ Connect to Redis and HTTP session, await actions """
        async with connect_to_aioredis_pool(config.REDIS_URI) as redis:
            with connect_to_socketio(config.SOCKETIO_URI, ["/console"]) as sio:
                # TODO: Migrate to the common log config
                logging.basicConfig(format="{asctime} - {name} - {levelname}:{message}", style='{')
                logger = logging.getLogger(f"{cls.__name__}")
                logger.setLevel(logging.DEBUG)

                handler = logging.StreamHandler(stream=SIOStream(sio))
                handler.setFormatter(logging.Formatter(fmt="{asctime} - {name} - {levelname}:{message}", style='{'))
                logger.addHandler(handler)

                app = cls(redis=redis, logger=logger)

                await app.get_actions()
