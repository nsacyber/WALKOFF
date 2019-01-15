import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager

import aioredis

from .result import ActionResult

# get app environment vars
REDIS_URI = os.getenv("REDIS_URI", "redis://localhost")
ACTION_RESULT_CH = os.getenv("ACTION_RESULT_CH", "action-results")
IN_PROCESS_Q = os.getenv("IN_PROCESS_Q", "actions-in-process")


class AppBase:
    def __init__(self, redis=None, logger=None):
        # Creates channels of format "{AppName}-{Priority}"
        self.action_queue_keys = tuple(f"{self.__class__.__name__}-{i}" for i in range(5, 0, -1))
        self.redis: aioredis.Redis = redis
        self.logger = logger if logger is not None else logging.getLogger("AppBaseLoggerShouldBeOverridden")

    @asynccontextmanager
    async def connect_to_redis_pool(self, redis_uri=REDIS_URI) -> aioredis.Redis:
        # Redis client bound to pool of connections (auto-reconnecting).
        self.redis = await aioredis.create_redis_pool(redis_uri)
        try:
            yield self.redis
        finally:
            # gracefully close pool
            self.redis.close()
            await self.redis.wait_closed()
            self.logger.info("Redis connection pool closed.")

    async def get_actions(self):
        """ Continuously monitors the action queues and asynchronously executes actions """
        while True:
            # Currently brpoplpush does not accept a list of keys like brpop does. To achieve the same functionality
            # we iteratively call the non-blocking rpoplpush on each of the app queues in priority order and grab the
            # first result we can
            action = None
            i = 0
            while action is None:
                src_key = self.action_queue_keys[i % len(self.action_queue_keys)]
                action = await self.redis.rpoplpush(src_key, IN_PROCESS_Q)
                i += 1
                await asyncio.sleep(0)

            action = json.loads(action)
            asyncio.create_task(self.execute_action(action))

    async def execute_action(self, action):
        """ Execute an action and ship its result """
        # result = self.func_map[action["action_name"]](**action["params"])
        if hasattr(self, action["action_name"]):
            result = getattr(self, action["action_name"])(**action["params"])
            action_result = ActionResult(action, result)
            self.logger.debug(f"Executed {action['name']}-{action['execution_id']} with result: {result}")
            await self.redis.publish_json(ACTION_RESULT_CH, action_result.to_json())

        else:
            self.logger.error(f"App {self.__class__.__name__} has no method {action['action_name']}")
            action_result = ActionResult(action, error="Action does not exist")
            await self.redis.publish_json(ACTION_RESULT_CH, action_result.to_json())
