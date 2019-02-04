from collections import deque
import asyncio
import logging
import json
import sys
import uuid

import aioredis

from common.config import load_config
from common.helpers import connect_to_redis_pool
from common.workflow_types import Action, Workflow, WorkflowJSONEncoder, WorkflowJSONDecoder

logging.basicConfig(level=logging.INFO, format="{asctime} - {name} - {levelname}:{message}", style='{')
logger = logging.getLogger("WORKER")

config = load_config()


def json_dumps(obj):
    return json.dumps(obj, cls=WorkflowJSONEncoder)


def json_loads(obj):
    return json.dumps(obj, cls=WorkflowJSONDecoder)


class Worker:
    def __init__(self, workflow: Workflow = None, start_action=None, redis=None):
        self.workflow = workflow
        self.start_action = start_action if start_action is not None else self.workflow.start
        self.accumulator = {}
        self.in_process = {}
        self.redis = redis

    @staticmethod
    async def get_workflow(redis: aioredis.Redis):
        """ Continuously monitors the workflow queue for new work """
        while True:
            # # Push test workflow in for now
            # with open("data/workflows/hello.json") as fp:
            #     wf = json.load(fp)
            #     redis.lpush(config["REDIS"]["workflow_q"], json.dumps(wf))

            workflow = await redis.brpoplpush(sourcekey=config["REDIS"]["workflow_q"],
                                              destkey=config["REDIS"]["workflows_in_process"],
                                              timeout=30)

            if workflow is None:  # We've timed out with no work. Guess we'll die now...
                sys.exit(1)

            yield Workflow.from_json(json.loads(workflow))

    @staticmethod
    async def run():
        async with connect_to_redis_pool(config["REDIS"]["redis_uri"]) as redis:
            async for workflow in Worker.get_workflow(redis):

                # Setup worker launch the event loop
                worker = Worker(workflow, redis=redis)
                await worker.execute_workflow()
        await Worker.shutdown()

    @staticmethod
    async def shutdown():
        # Clean up any unfinished tasks (shouldn't really be any though)
        tasks = [t for t in asyncio.all_tasks() if t is not
                 asyncio.current_task()]

        [task.cancel() for task in tasks]

        logger.info('Canceling outstanding tasks')
        await asyncio.gather(*tasks)

    async def execute_workflow(self):
        """ Do a simple BFS to visit and schedule each action in the workflow """
        visited = {self.start_action}
        queue = deque([self.start_action])
        tasks = []

        while queue:
            action = queue.pop()
            parents = set(self.workflow.predecessors(action)) if action is not self.start_action else {}
            children = self.workflow.successors(action)
            action.execution_id = str(uuid.uuid4())
            action.workflow_execution_id = self.workflow.execution_id

            self.in_process[action.id] = action
            tasks.append(asyncio.create_task(self.schedule_action(parents, action)))

            for child in sorted(children, reverse=True):
                if child not in visited:
                    queue.appendleft(child)
                    visited.add(child)

        # Launch the results accumulation task and wait for all the results to come in
        tasks.append(asyncio.create_task(self.get_action_results(config["REDIS"]["action_results_ch"])))
        await asyncio.gather(*tasks)

    async def dereference_params(self, action: Action):
        global_vars = set(await self.redis.hkeys(config["REDIS"]["globals_key"]))

        for param in action.params:
            if param._is_reference:
                if param.reference in self.accumulator:
                    param.value = self.accumulator[param.reference]

                elif param.reference in self.workflow.environment_variables:
                    param.value = self.workflow.environment_variables[param.reference]

                elif param.reference in global_vars:
                    param.value = self.accumulator[param.reference]

                param._is_reference = False
                param.reference = None

    async def schedule_action(self, parents: {Action}, action: Action):
        """ Waits until all dependencies of an action are met and then schedules the action """
        while not all(parent.id in self.accumulator for parent in parents):
            await asyncio.sleep(0)

        await self.dereference_params(action)

        await self.redis.lpush(f"{action.app_name}-{action.priority}", json_dumps(action))
        logger.info(f"Scheduled {action}")

    async def get_action_results(self, results_channel_key):
        """ Continuously monitors the results queue until all scheduled actions have been completed """
        channel: [aioredis.Channel] = (await self.redis.subscribe(results_channel_key))[0]
        while len(self.in_process) > 0:
            msg = await channel.get_json()
            if msg is None:
                break  # channel was unsubbed

            # Ensure that the recieved ActionResult is for an action we launched
            if msg["workflow"]["execution_id"] == self.workflow.execution_id and msg["action_id"] in self.in_process:
                # if msg["error"] is None and msg["result"] is not None:

                if msg["status"] == "ActionStarted":
                    logger.info(f"App started exectuion of: {msg['name']}-{msg['execution_id']}")

                elif msg["status"] == "ActionExecutionSuccess":
                    self.accumulator[msg["action_id"]] = msg["result"]
                    logger.info(f"Worker recieved result for: {msg['name']}-{msg['execution_id']}")

                    # Remove the action from our local in_process queue as well as the one in redis
                    action = self.in_process.pop(msg["action_id"])
                    await self.redis.lrem(config["REDIS"]["actions_in_process"], 0, json_dumps(action))

                else:
                    self.accumulator[msg["action_id"]] = msg["error"]
                    logger.info(f"Worker recieved error \"{msg['error']}\" for: {msg['name']}-{msg['execution_id']}")

        logger.info("Action-Results channel closed")


if __name__ == "__main__":
    # Launch the worker event loop
    asyncio.run(Worker.run())
