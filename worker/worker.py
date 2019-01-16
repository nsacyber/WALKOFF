import uuid
from collections import deque
import asyncio
import logging
from contextlib import asynccontextmanager
import json

import aioredis

from common import config
from common.workflow_types import Action, Branch, Workflow, Point

logging.basicConfig(level=logging.INFO, format="{asctime} - {name} - {levelname}:{message}", style='{')
logger = logging.getLogger("WORKER")


class Worker:
    def __init__(self, workflow: Workflow, start_action=None):
        self.workflow = workflow
        self.start_action = start_action if start_action is not None else self.workflow.start
        self.accumulator = {}
        self.in_process = {}

    @asynccontextmanager
    async def connect_to_redis_pool(self, redis_uri) -> aioredis.Redis:
        # Redis client bound to pool of connections (auto-reconnecting).
        self.redis = await aioredis.create_redis_pool(redis_uri)
        try:
            yield self.redis
        finally:
            # gracefully close pool
            self.redis.close()
            await self.redis.wait_closed()
            logger.info("Redis connection pool closed.")

    async def execute_workflow(self):
        """ Do a simple BFS to visit and schedule each action in the workflow """
        visited = {self.start_action}
        queue = deque([self.start_action])
        tasks = []

        while queue:
            action = queue.pop()
            parents = set(self.workflow.predecessors(action))
            children = self.workflow.successors(action)
            action.execution_id = str(uuid.uuid4())

            self.in_process[action.execution_id] = action
            tasks.append(asyncio.create_task(self.schedule_action(parents, action)))

            for child in sorted(children, reverse=True):
                if child not in visited:
                    queue.appendleft(child)
                    visited.add(child)

        # Launch the results accumulation task and wait for all the results to come in
        tasks.append(asyncio.create_task(self.get_action_results(config["redis"]["action_results_ch"])))
        await asyncio.gather(*tasks)

    async def schedule_action(self, parents: {Action}, action: Action):
        """ Waits until all dependencies of an action are met and then schedules the action """
        while not all(parent.execution_id in self.accumulator for parent in parents):
            await asyncio.sleep(0)
        await self.redis.lpush(f"{action.app_name}-{action.priority}", json.dumps(action.to_json()))
        logger.info(f"Scheduled {action}-{action.execution_id}")

    async def get_action_results(self, results_channel_key):
        """ Continuously monitors the results queue until all scheduled actions have been completed """
        channel: [aioredis.Channel] = (await self.redis.subscribe(results_channel_key))[0]
        while len(self.in_process) > 0:
            msg = await channel.get_json()
            if msg is None:
                break  # channel was unsubbed

            # Ensure that the recieved ActionResult is for an action we launched
            if msg["execution_id"] in self.in_process:
                if msg["error"] is None:
                    self.accumulator[msg["execution_id"]] = msg["result"]
                    logger.info(f"Worker recieved result for: {msg['name']}-{msg['execution_id']}")
                else:
                    self.accumulator[msg["execution_id"]] = msg["error"]
                    logger.info(f"Worker recieved error \"{msg['error']}\" for: {msg['name']}-{msg['execution_id']}")

                # Remove the action from our local in_process queue as well as the one in redis
                action = self.in_process.pop(msg["execution_id"])
                await self.redis.lrem(config["redis"]["in_process_q"], 0, json.dumps(action.to_json()))
        
        logger.info("Channel closed")


if __name__ == "__main__":
    import sys
    from common import config


    async def run_worker(workflow):
        # Setup worker launch the event loop
        worker = Worker(workflow)
        async with worker.connect_to_redis_pool(config["redis"]["redis_uri"]) as redis:
            await worker.execute_workflow()

        # Clean up any unfinished tasks (shouldn't really be any though)
        tasks = [t for t in asyncio.all_tasks() if t is not
                 asyncio.current_task()]

        [task.cancel() for task in tasks]

        logger.info('Canceling outstanding tasks')
        await asyncio.gather(*tasks)



    # Design our workflow
    a = Action("sleep_a", "sleep", "TestApp", {"sleep_time": 1}, 5, Point(5, 5))
    b = Action("sleep_b", "sleep", "TestApp", {"sleep_time": 10}, 4, Point(4, 4))
    c = Action("sleep_c", "sleep", "TestApp", {"sleep_time": 1}, 3, Point(6, 4))
    d = Action("sleep_d", "sleep", "TestApp", {"sleep_time": 1}, 2, Point(5, 3))
    e = Action("sleep_e", "sleep", "TestApp", {"sleep_time": 1}, 1, Point(6, 3))
    f = Action("foo_f", "foo", "TestApp", {"bar": "spam"}, 5, Point(6, 2))
    branches = {Branch(a, b), Branch(a, c), Branch(b, d), Branch(c, d), Branch(c, e), Branch(e, f)}
    actions = {a, b, c, d, e, f}

    # Flow network to test concurrent execution of n actions of varying priorities.
    # n = 200
    # a = Action("sleep_a", "sleep", "TestApp", {"sleep_time": 1}, 5, Point(5, 5))
    # z = Action("sleep_z", "sleep", "TestApp", {"sleep_time": 1}, 5, Point(5, 3))
    # actions = {Action(f"sleep_{i}", "sleep", "TestApp", {"sleep_time": 1}, i % 5 + 1, Point(i, 4)) for i in range(n)}
    # branches = {Branch(src=src, dst=dst) for action in actions for src, dst in [(a, action), (action, z)]}

    workflow = Workflow("TestWorkflow", start=a, actions=actions, branches=branches)

    if sys.argv[-1] == "--local":
        import multiprocessing
        from apps.TestApp import app
        import networkx as nx
        import matplotlib.pyplot as plt

        # Display our workflow
        nx.draw_networkx(workflow, pos={action: (action.pos.x, action.pos.y) for action in workflow.nodes})
        plt.show()

        # Launch instances of  TestApp in other processes to simulate containerized instances
        num_app_instances = 4
        app_procs = []
        for i in range(num_app_instances):
            p = multiprocessing.Process(target=app.main, args=[i])
            p.start()
            app_procs.append(p)

        # Launch the worker event loop
        asyncio.run(run_worker(workflow))

        # Politely ask the app to die
        logger.info("Terminating app process")
        for p in app_procs:
            p.terminate()
            p.join()
        logger.info('Shutdown complete.')

    else:
        # Launch the worker event loop
        asyncio.run(run_worker(workflow))
