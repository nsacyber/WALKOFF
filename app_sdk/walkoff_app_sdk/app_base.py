import asyncio
import logging
import os
import sys
import time
import json

import aioredis
import aiohttp

from common.message_types import NodeStatusMessage, message_dumps
from common.workflow_types import workflow_loads, workflow_dumps, Action
from common.async_logger import AsyncLogger, AsyncHandler
from common.redis_helpers import connect_to_redis_pool, xlen, xdel, deref_stream_message

# get app environment vars
REDIS_URI = os.getenv("REDIS_URI", "redis://localhost")
REDIS_ACTION_RESULTS = os.getenv("REDIS_ACTION_RESULTS", "action-results")
REDIS_ACTION_RESULTS_GROUP = os.getenv("REDIS_ACTION_RESULTS_GROUP", "actions-in-process")
API_GATEWAY_URI = os.getenv("API_GATEWAY_URI", "http://api_gateway:8080")
APP_NAME = os.getenv("APP_NAME")
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
        data = json.dumps({"message": message})
        params = {"workflow_execution_id": self.execution_id}
        url = f"{API_GATEWAY_URI}/api/streams/console/log"

        async with self.session.post(url, data=data, params=params) as resp:
            print(await resp.json())

    async def close(self):
        pass


class AppBase:
    """ The base class for Python-based Walkoff applications, handles Redis and logging configurations. """
    def __init__(self, redis=None, logger=None, console_logger=None):
        if APP_NAME is None:
            logger.error(("APP_NAME not set. Please ensure 'APP_NAME' environment variable is set to match the "
                          "docker-compose service name."))
            sys.exit(1)

        if CONTAINER_ID is None:
            logger.error(("CONTAINER_ID not not available. Please ensure 'HOSTNAME' environment variable is set to "
                          "match the docker container id. This should be handled automatically by docker but in this "
                          "case something must have gone wrong..."))
            sys.exit(1)

        # Creates redis keys of format "{AppName}:{Version}:{Priority}"
        self.action_queue_keys = [f"{APP_NAME}:{self.__version__}:{i}" for i in range(5, 0, -1)]
        self.redis: aioredis.Redis = redis
        self.logger = logger if logger is not None else logging.getLogger("AppBaseLogger")
        self.console_logger = console_logger if console_logger is not None else logging.getLogger("ConsoleBaseLogger")
        self.current_execution_id = None

    async def get_actions(self):
        """ Continuously monitors the action queues and asynchronously executes actions """
        self.logger.debug("Waiting for actions...")

        app_group = f"{APP_NAME}-group"

        while True:
            #TODO: Delete this test code
            redis_keys = [key.decode() for key in await self.redis.keys('*')]
            for key in self.action_queue_keys:
                if key not in redis_keys:
                    await self.redis.xgroup_create(key, app_group, mkstream=True)

            message = await self.redis.xread_group(app_group, CONTAINER_ID, streams=self.action_queue_keys,
                                                   latest_ids=['>' for _ in self.action_queue_keys],
                                                   timeout=APP_TIMEOUT * 1000, count=1)

            if len(message) < 1:  # We've timed out with no work. Guess we'll die now...
                sys.exit(1)

            execution_id_action, stream, id_ = deref_stream_message(message)
            execution_id, action = execution_id_action

            # Remove the workflow from the stream
            await xdel(self.redis, stream=stream, id_=id_)

            # Actually execute the action
            action = workflow_loads(action)
            await self.execute_action(action)

            # Clean up workflow-queue
            await self.redis.xack(stream=stream, group_name=app_group, id=id_)

    async def execute_action(self, action: Action):
        """ Execute an action, and push its result to Redis. """
        self.logger.debug(f"Attempting execution of: {action.label}-{action.execution_id}")
        self.console_logger.handlers[0].stream.set_execution_id(f"{action.execution_id}:console")
        if hasattr(self, action.name):
            start_action_msg = NodeStatusMessage.executing_from_node(action, action.execution_id)
            redis_keys = [key.decode() for key in await self.redis.keys('*')]
            if action.execution_id not in redis_keys:
                await self.redis.xgroup_create(action.execution_id, REDIS_ACTION_RESULTS_GROUP, mkstream=True)

            await self.redis.xadd(action.execution_id, {action.execution_id: message_dumps(start_action_msg)})
            try:
                func = getattr(self, action.name, None)
                if callable(func):
                    if len(action.parameters) < 1:
                        result = await func()
                    else:
                        result = await func(**{p.name: p.value for p in action.parameters})
                    action_result = NodeStatusMessage.success_from_node(action, action.execution_id, result=result)
                    self.logger.debug(f"Executed {action.label}-{action.id_} with result: {result}")

                else:
                    self.logger.error(f"App {self.__class__.__name__}.{action.name} is not callable")
                    action_result = NodeStatusMessage.failure_from_node(action, action.execution_id,
                                                                        result="Action not callable")

            except Exception as e:
                action_result = NodeStatusMessage.failure_from_node(action, action.execution_id, result=repr(e))
                self.logger.exception(f"Failed to execute {action.label}-{action.id_}")

            await self.redis.xadd(action.execution_id, {action.execution_id: message_dumps(action_result)})

        else:
            self.logger.error(f"App {self.__class__.__name__} has no method {action.name}")
            action_result = NodeStatusMessage.failure_from_node(action, action.execution_id,
                                                                result="Action does not exist")
            await self.redis.xadd(action.execution_id, {action.execution_id: message_dumps(action_result)})

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


