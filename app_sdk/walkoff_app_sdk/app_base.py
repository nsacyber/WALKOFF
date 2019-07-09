import logging
import os
import sys

import aioredis
import aiohttp

from walkoff_app_sdk.common.message_types import NodeStatusMessage, message_dumps
from walkoff_app_sdk.common.workflow_types import workflow_loads, Action, ParameterVariant
from walkoff_app_sdk.common.async_logger import AsyncLogger, AsyncHandler
from walkoff_app_sdk.common.helpers import UUID_GLOB
from walkoff_app_sdk.common.redis_helpers import connect_to_redis_pool, xlen, xdel, deref_stream_message
from walkoff_app_sdk.common.config import config

# get app environment vars
REDIS_URI = os.getenv("REDIS_URI", "redis://localhost")
REDIS_ACTION_RESULTS_GROUP = os.getenv("REDIS_ACTION_RESULTS_GROUP", "actions-in-process")
REDIS_ABORTING_WORKFLOWS = os.getenv("REDIS_ABORTING_WORKFLOWS", "aborting-workflows")
API_GATEWAY_URI = os.getenv("API_GATEWAY_URI", "http://api_gateway:8080")
APP_TIMEOUT = os.getenv("APP_TIMEOUT", 30)
CONTAINER_ID = os.getenv("HOSTNAME")


class HTTPStream:
    """ Thin wrapper around an HTTP stream that plugs into the async logger """
    def __init__(self, session=None):
        super().__init__()
        self.session = session
        self.execution_id = None

    def set_execution_id(self, channel):
        self.execution_id = channel

    async def flush(self):
        pass

    async def write(self, message):
        data = {"message": message}
        params = {"workflow_execution_id": self.execution_id}
        url = f"{API_GATEWAY_URI}/api/streams/console/logger"

        await self.session.post(url, json=data, params=params)

    async def close(self):
        pass


class AppBase:
    """ The base class for Python-based Walkoff applications, handles Redis and logging configurations. """
    __version__ = None
    app_name = None

    def __init__(self, redis=None, logger=None, console_logger=None):#, docker_client=None):
        if self.app_name is None or self.__version__ is None:
            logger.error(("App name or version not set. Please ensure self.app_name is set to match the "
                          "docker-compose service name and self.__version__ is set to match the api.yaml."))
            sys.exit(1)

        if CONTAINER_ID is None:
            logger.error(("CONTAINER_ID not not available. Please ensure 'HOSTNAME' environment variable is set to "
                          "match the docker container id. This should be handled automatically by docker but in this "
                          "case something must have gone wrong..."))
            sys.exit(1)

        # Creates redis keys of format "{AppName}:{Version}:{Priority}"
        self.redis: aioredis.Redis = redis
        self.logger = logger if logger is not None else logging.getLogger("AppBaseLogger")
        self.console_logger = console_logger if console_logger is not None else logging.getLogger("ConsoleBaseLogger")
        self.current_execution_id = None

    async def get_actions(self):
        """ Continuously monitors the action queue and asynchronously executes actions """
        self.logger.debug("Waiting for actions...")
        app_group = f"{self.app_name}:{self.__version__}"

        while True:
            streams = await self.redis.keys(f"{UUID_GLOB}:{app_group}", encoding='utf-8')
            aborted = await self.redis.smembers(REDIS_ABORTING_WORKFLOWS, encoding="utf-8")
            streams = [s for s in streams if s.split(':')[0] not in aborted]
            num_streams = len(streams)

            if num_streams < 1:
                sys.exit(-1)  # There's no scheduled work and no reason to live

            try:
                # See if we have any pending messages first
                message = await self.redis.xread_group(app_group, CONTAINER_ID, streams=streams, count=1,
                                                       latest_ids=list('0' * num_streams), timeout=None)

                if len(message) < 1:  # We don't have any pending so lets get a new one
                    message = await self.redis.xread_group(app_group, CONTAINER_ID, streams=streams, count=1,
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
        self.logger.debug(f"Attempting execution of: {action.label}-{action.execution_id}")
        self.console_logger.handlers[0].stream.set_execution_id(action.execution_id)
        self.current_execution_id = action.execution_id

        results_stream = f"{action.execution_id}:results"

        if hasattr(self, action.name):
            # Tell everyone we started execution
            start_action_msg = NodeStatusMessage.executing_from_node(action, action.execution_id)
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
                                f = open('/run/secrets/walkoff_encryption_key')
                                key = f.read()
                                my_cipher = GlobalCipher(key)
                                temp = my_cipher.decrypt(p.value)
                                params[p.name] = temp
                            else:
                                params[p.name] = p.value
                        result = await func(**params)

                    action_result = NodeStatusMessage.success_from_node(action, action.execution_id, result=result)
                    self.logger.debug(f"Executed {action.label}-{action.id_} with result: {result}")

                else:
                    self.logger.error(f"App {self.__class__.__name__}.{action.name} is not callable")
                    action_result = NodeStatusMessage.failure_from_node(action, action.execution_id,
                                                                        result="Action not callable")

            except Exception as e:
                self.logger.exception(f"Failed to execute {action.label}-{action.id_}")
                action_result = NodeStatusMessage.failure_from_node(action, action.execution_id, result=repr(e))

        else:
            self.logger.error(f"App {self.__class__.__name__} has no method {action.name}")
            action_result = NodeStatusMessage.failure_from_node(action, action.execution_id,
                                                                result="Action does not exist")
        await self.redis.xadd(results_stream, {action.execution_id: message_dumps(action_result)})

    @classmethod
    async def run(cls):
        """ Connect to Redis and HTTP session, await actions """
        async with connect_to_redis_pool(REDIS_URI) as redis, aiohttp.ClientSession() as session:
            # TODO: Migrate to the common log config
            logging.basicConfig(format="{asctime} - {name} - {levelname}:{message}", style='{')
            logger = logging.getLogger(f"{cls.__name__}")
            logger.setLevel(logging.DEBUG)

            console_logger = AsyncLogger(f"{cls.__name__}", level=logging.DEBUG)
            handler = AsyncHandler(stream=HTTPStream(session))
            handler.setFormatter(logging.Formatter(fmt="{asctime} - {name} - {levelname}:{message}", style='{'))
            console_logger.addHandler(handler)

            app = cls(redis=redis, logger=logger, console_logger=console_logger)

            await app.get_actions()
