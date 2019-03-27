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
from common.helpers import connect_to_redis_pool

# get app environment vars
REDIS_URI = os.getenv("REDIS_URI", "redis://localhost")
ACTION_RESULT_CH = os.getenv("ACTION_RESULT_CH", "action-results")
ACTIONS_IN_PROCESS = os.getenv("ACTIONS_IN_PROCESS", "actions-in-process")
API_GATEWAY_URI = os.getenv("API_GATEWAY_URI", "localhost:5000")
APP_NAME = os.getenv("APP_NAME", None)


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
    def __init__(self, redis=None, logger=None, console_logger=None):
        if APP_NAME is None:
            logger.error("APP_NAME not set. Please ensure 'APP_NAME' environment variable is set to match the"
                         + "docker-compose service name.")
            sys.exit(1)

        # Creates redis keys of format "{AppName}_{Version}-{Priority}"
        self.action_queue_keys = tuple(f"{APP_NAME}:{self.__version__}:{i}" for i in range(5, 0, -1))
        self.redis: aioredis.Redis = redis
        self.logger = logger if logger is not None else logging.getLogger("AppBaseLogger")
        self.console_logger = console_logger if console_logger is not None else logging.getLogger("ConsoleBaseLogger")
        self.current_execution_id = None

    async def get_actions(self):
        """ Continuously monitors the action queues and asynchronously executes actions """
        self.logger.debug("Waiting for actions...")
        while True:
            # Currently brpoplpush does not accept a list of keys like brpop does. To achieve the same functionality
            # we iteratively call the non-blocking rpoplpush on each of the app queues in priority order and grab the
            # first result we can
            action = None
            i = 0
            start = time.time()
            while action is None:
                src_key = self.action_queue_keys[i % len(self.action_queue_keys)]
                action = await self.redis.rpoplpush(src_key, ACTIONS_IN_PROCESS)
                i += 1
                await asyncio.sleep(0)

                if time.time() - start > 30:  # We've timed out with no work. Guess we'll die now...
                    sys.exit(1)

            action = workflow_loads(action)
            asyncio.create_task(self.execute_action(action))

    async def execute_action(self, action: Action):
        """ Execute an action and ship its result """
        self.logger.debug(f"Attempting execution of: {action.label}-{action.execution_id}")
        self.console_logger.handlers[0].stream.set_execution_id(f"{action.execution_id}:console")
        if hasattr(self, action.name):
            start_action_msg = NodeStatusMessage.executing_from_node(action, action.execution_id)
            await self.redis.lpush(action.execution_id, message_dumps(start_action_msg))
            try:
                func = getattr(self, action.name, None)
                if callable(func):
                    if len(action.parameters) < 1:
                        result = await func()
                    else:
                        result = await func(**{p.name: p.value for p in action.parameters})
                    action_result = NodeStatusMessage.success_from_node(action, action.execution_id, result)
                    self.logger.debug(f"Executed {action.label}-{action.id_} with result: {result}")

                else:
                    self.logger.error(f"App {self.__class__.__name__}.{action.name} is not callable")
                    action_result = NodeStatusMessage.failure_from_node(action, action.execution_id,
                                                                        error="Action not callable")

            except Exception as e:
                action_result = NodeStatusMessage.failure_from_node(action, action.execution_id, error=repr(e))
                self.logger.exception(f"Failed to execute {action.label}-{action.id_}")

            await self.redis.lpush(action.execution_id, message_dumps(action_result))

        else:
            self.logger.error(f"App {self.__class__.__name__} has no method {action.name}")
            action_result = NodeStatusMessage.failure_from_node(action, action.execution_id, error="Action does not exist")
            await self.redis.lpush(action.execution_id, message_dumps(action_result))

        # Remove the action from the in process queue regardless of success
        await self.redis.lrem(ACTIONS_IN_PROCESS, 0, workflow_dumps(action))

    @classmethod
    async def run(cls):
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


