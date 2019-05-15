import asyncio
import logging
import sys
import os
import signal
from collections import deque
from inspect import getcoroutinelocals

import aiohttp
import aioredis

from common.message_types import message_dumps, message_loads, NodeStatusMessage, WorkflowStatusMessage, StatusEnum
from common.config import config
from common.helpers import get_walkoff_auth_header, send_status_update
from common.redis_helpers import connect_to_redis_pool, xdel, deref_stream_message
from common.workflow_types import Node, Action, Condition, Transform, Trigger, ParameterVariant, Workflow, \
    workflow_dumps, workflow_loads, ConditionException

logging.basicConfig(level=logging.INFO, format="{asctime} - {name} - {levelname}:{message}", style='{')
logger = logging.getLogger("WORKER")
# logging.getLogger("asyncio").setLevel(logging.DEBUG)
# logger.setLevel(logging.DEBUG)

CONTAINER_ID = os.getenv("HOSTNAME")


class Worker:
    def __init__(self, workflow: Workflow = None, start_action: str = None, redis: aioredis.Redis = None,
                 session: aiohttp.ClientSession = None):
        self.workflow = workflow
        self.start_action = start_action if start_action is not None else self.workflow.start
        self.accumulator = {}
        self.in_process = {}
        self.redis = redis
        self.streams = set()
        self.workflow_tasks = set()
        self.execution_task = None
        self.session = session
        self.token = None

    @staticmethod
    async def get_workflow(redis: aioredis.Redis):
        """
            Continuously monitors the workflow queue for new work
        """
        while True:
            logger.info("Waiting for workflows...")
            if CONTAINER_ID is None:
                logger.exception("Environment variable 'HOSTNAME' does not exist in worker container.")
                sys.exit(-1)

            try:
                message = await redis.xread_group(config.REDIS_WORKFLOW_GROUP, CONTAINER_ID,
                                                  streams=[config.REDIS_WORKFLOW_QUEUE], latest_ids=['>'],
                                                  timeout=config.get_int("WORKER_TIMEOUT", 30) * 1000, count=1)
            except aioredis.ReplyError:
                logger.error("Error reading from workflow queue.")
                sys.exit(-1)

            if len(message) < 1:  # We've timed out with no work. Guess we'll die now...
                sys.exit(1)

            execution_id_workflow, stream, id_ = deref_stream_message(message)
            execution_id, workflow = execution_id_workflow
            try:
                if not (await redis.sismember(config.REDIS_ABORTING_WORKFLOWS, execution_id)):
                    await redis.sadd(config.REDIS_EXECUTING_WORKFLOWS, execution_id)
                    yield workflow_loads(workflow)

            finally:  # Clean up workflow-queue
                await redis.xack(stream=stream, group_name=config.REDIS_WORKFLOW_GROUP, id=id_)
                await xdel(redis, stream=stream, id_=id_)

    @staticmethod
    async def run():
        async with connect_to_redis_pool(config.REDIS_URI) as redis,\
                aiohttp.ClientSession(json_serialize=message_dumps) as session:

            # Attach our signal handlers to cleanly close services we've created
            loop = asyncio.get_running_loop()
            loop.add_signal_handler(signal.SIGINT, lambda: asyncio.ensure_future(Worker.shutdown()))
            loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.ensure_future(Worker.shutdown()))

            async for workflow in Worker.get_workflow(redis):

                # Setup worker and results stream
                worker = Worker(workflow, redis=redis, session=session)

                # Attach our abort signal handler to a specific instance of the worker
                loop.add_signal_handler(signal.SIGQUIT, lambda: asyncio.ensure_future(worker.abort()))

                results_stream = f"{workflow.execution_id}:results"
                await redis.xgroup_create(results_stream, config.REDIS_ACTION_RESULTS_GROUP, mkstream=True)
                logger.info(f"Starting execution of workflow: {workflow.name}")
                status = WorkflowStatusMessage.execution_started(worker.workflow.execution_id,  worker.workflow.id_,
                                                                 worker.workflow.name)

                await send_status_update(session, workflow.execution_id, status)

                try:
                    worker.execution_task = asyncio.create_task(worker.execute_workflow())
                    await asyncio.gather(worker.execution_task)
                except asyncio.CancelledError:
                    logger.info(f"Aborted execution of workflow: {workflow.name}")
                    status = WorkflowStatusMessage.execution_aborted(worker.workflow.execution_id,
                                                                     worker.workflow.id_,
                                                                     worker.workflow.name)
                except Exception:
                    logger.exception(f"Failed execution of workflow: {workflow.name}")
                    status = WorkflowStatusMessage.execution_completed(worker.workflow.execution_id,
                                                                       worker.workflow.id_,
                                                                       worker.workflow.name)
                else:
                    logger.info(f"Completed execution of workflow: {workflow.name}")
                    status = WorkflowStatusMessage.execution_completed(worker.workflow.execution_id,
                                                                       worker.workflow.id_,
                                                                       worker.workflow.name)
                finally:
                    await send_status_update(session, workflow.execution_id, status)

            await Worker.shutdown()

    @staticmethod
    async def shutdown():
        logger.info("Shutting down Worker...")
        # Clean up any unfinished tasks (shouldn't really be any though)
        tasks = [t for t in asyncio.all_tasks() if t is not
                 asyncio.current_task()]
        [task.cancel() for task in tasks]
        logger.info("Canceling outstanding tasks")
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("Successfully shutdown Worker")

    async def abort(self):
        logger.info("Aborting workflow...")
        [task.cancel() for task in self.workflow_tasks]
        self.execution_task.cancel()

        # Try to cancel any outstanding actions
        msgs = [NodeStatusMessage.aborted_from_node(action, action.execution_id) for action in self.in_process.values()]
        message_tasks = [send_status_update(self.session, self.workflow.execution_id, msg) for msg in msgs]
        await asyncio.gather(*message_tasks, return_exceptions=True)

        logger.info("Canceling outstanding tasks...")
        await asyncio.gather(*self.workflow_tasks, *message_tasks, self.execution_task, return_exceptions=True)
        logger.info("Successfully aborted workflow!")

    async def cancel_subgraph(self, node):
        """
            Cancels the task related to the current node as well as the tasks related to every child of that node.
            Also removes them from the worker's internal in_process queue.
        """
        dependents = self.workflow.get_dependents(node)
        cancelled_tasks = set()

        for task in asyncio.all_tasks():
            if getattr(self, task._coro.__name__, None) == self.schedule_node:  # filter only node scheduling coroutines
                for _, arg in getcoroutinelocals(task._coro).items():
                    if isinstance(arg, Node):
                        if arg in dependents:
                            self.in_process.pop(arg.id_)
                            task.cancel()
                            cancelled_tasks.add(task)

        await asyncio.gather(*cancelled_tasks, return_exceptions=True)

    async def execute_workflow(self):
        """
            Do a simple BFS to visit and schedule each node in the workflow. We assume every node will run and thus
            preemptively schedule them all. We will clean up any nodes that will not run due to conditions or triggers
        """
        visited = {self.start_action}
        queue = deque([self.start_action])
        self.workflow_tasks = set()
        while queue:
            node = queue.pop()
            parents = {n.id_: n for n in self.workflow.predecessors(node)} if node is not self.start_action else {}
            children = {n.id_: n for n in self.workflow.successors(node)}
            self.in_process[node.id_] = node

            if isinstance(node, Action):
                node.execution_id = self.workflow.execution_id  # the app needs this as a key for the redis queue

            elif isinstance(node, Trigger):
                raise NotImplementedError

            self.workflow_tasks.add(asyncio.create_task(self.schedule_node(node, parents, children)))

            for child in sorted(children.values(), reverse=True):
                if child not in visited:
                    queue.appendleft(child)
                    visited.add(child)

        # TODO: Figure out a clean way of handling the exceptions here. Cancelling subgraphs throws CancelledErrors.
        # Launch the results accumulation task and wait for all the results to come in
        self.workflow_tasks.add(asyncio.create_task(self.get_action_results()))
        exceptions = await asyncio.gather(*self.workflow_tasks, return_exceptions=True)
        for e in exceptions:
            if isinstance(e, Exception) and not isinstance(e, asyncio.CancelledError):
                try:
                    raise e
                except:
                    logger.exception(f"Exception while executing Workflow:{self.workflow}")

    async def evaluate_condition(self, condition, parents, children):
        """
            TODO: This will change when we implement a better UI element for it. For now, if an action is given a user
            defined name like "Hello World", it would be referenced by the variable name "Hello_World" in the
            conditional script. All whitespace in the action name is replaced by '_'. This is clearly problematic
            if a user has an action named "Hello World" as well as "Hello_World". In this case, we cannot be sure
            which is being referenced in the conditional and must raise an exception.
        """
        logger.debug(f"Attempting evaluation of: {condition.label}-{self.workflow.execution_id}")
        try:
            child_id = condition(parents, children, self.accumulator)
            selected_node = children.pop(child_id)
            await send_status_update(self.session, self.workflow.execution_id,
                                     NodeStatusMessage.success_from_node(condition, self.workflow.execution_id,
                                                                         selected_node.name))
            logger.info(f"Condition selected node: {selected_node.label}-{self.workflow.execution_id}")

            # We preemptively schedule all branches of execution so we must cancel all "false" branches here
            [await self.cancel_subgraph(child) for child in children.values()]

            self.in_process.pop(condition.id_)
            self.accumulator[condition.id_] = selected_node

        except ConditionException as e:
            logger.exception(f"Worker received error for {condition.name}-{self.workflow.execution_id}")
            await send_status_update(self.session, self.workflow.execution_id,
                                     NodeStatusMessage.failure_from_node(condition, self.workflow.execution_id,
                                                                         result=repr(e)))

        except Exception:
            logger.exception("Something happened in Condition evaluation")

    async def execute_transform(self, transform, parent):
        """ Execute an transform and ship its result """
        logger.debug(f"Attempting evaluation of: {transform.label}-{self.workflow.execution_id}")
        try:
            result = transform(self.accumulator[parent.id_])  # run transform on parent's result
            await send_status_update(self.session, self.workflow.execution_id,
                                     NodeStatusMessage.success_from_node(transform, self.workflow.execution_id, result))
            logger.info(f"Transform {transform.label}-succeeded with result: {result}")

            self.accumulator[transform.id_] = result
            self.in_process.pop(transform.id_)

        # TODO: figure out exactly what can be raised by the possible transforms
        except Exception as e:
            logger.exception(f"Worker received error for {transform.name}-{self.workflow.execution_id}")
            await send_status_update(self.session, self.workflow.execution_id,
                                     NodeStatusMessage.failure_from_node(transform, self.workflow.execution_id,
                                                                         result=repr(e)))

    async def get_globals(self):
        url = config.API_GATEWAY_URI.rstrip('/') + '/api'
        headers, self.token = await get_walkoff_auth_header(self.session, self.token)
        async with self.session.get(url + "/globals", headers=headers) as resp:
            globals_ = await resp.json(loads=workflow_loads)
            logger.debug(f"Got globals: {globals_}")
            return {g.id_: g for g in globals_}

    async def dereference_params(self, action: Action):
        global_vars = await self.get_globals()
        for param in action.parameters:
            if param.variant == ParameterVariant.STATIC_VALUE:
                continue

            elif param.variant == ParameterVariant.ACTION_RESULT:
                if param.value in self.accumulator:
                    param.value = self.accumulator[param.value]

            elif param.variant == ParameterVariant.WORKFLOW_VARIABLE:
                if param.value in self.workflow.workflow_variables:
                    param.value = self.workflow.workflow_variables[param.value].value

            elif param.variant == ParameterVariant.GLOBAL:
                if param.value in global_vars:
                    param.value = global_vars[param.value].value

            else:
                logger.error(f"Unable to defeference parameter:{param} for action:{action}")
                break

            #param.variant = ParameterVariant.STATIC_VALUE

    async def schedule_node(self, node, parents, children):
        """ Waits until all dependencies of an action are met and then schedules the action """
        logger.info("Scheduling node...")

        while not all(parent.id_ in self.accumulator for parent in parents.values()):
            await asyncio.sleep(0)

        logger.info("Node ready to execute!")

        if isinstance(node, Action):
            group = f"{node.app_name}:{node.app_version}"
            stream = f"{node.execution_id}:{group}"
            try:
                # The stream doesn't exist so lets create that and the app group
                if len(await self.redis.keys(stream)) < 1:
                    await self.redis.xgroup_create(stream, group, mkstream=True)

                # The stream exists but the group does not so lets just make the app group
                if len(await self.redis.xinfo_groups(stream)) < 1:
                    await self.redis.xgroup_create(stream, group)

                # Keep track of these for clean up later
                self.streams.add(stream)

            except aioredis.ReplyError as e:
                logger.debug(f"Issue creating redis stream {e!r}")

            await self.dereference_params(node)
            await send_status_update(self.session, self.workflow.execution_id,
                                     NodeStatusMessage.executing_from_node(node, self.workflow.execution_id))
            await self.redis.xadd(stream, {node.execution_id: workflow_dumps(node)})

        elif isinstance(node, Condition):
            await send_status_update(self.session, self.workflow.execution_id,
                                     NodeStatusMessage.executing_from_node(node, self.workflow.execution_id))
            await self.evaluate_condition(node, parents, children)

        elif isinstance(node, Transform):
            if len(parents) > 1:
                logger.error(f"Error scheduling {node.name}: Transforms cannot have more than 1 incoming connection.")
            await send_status_update(self.session, self.workflow.execution_id,
                                     NodeStatusMessage.executing_from_node(node, self.workflow.execution_id))
            await self.execute_transform(node, parents.popitem()[1])

        elif isinstance(node, Trigger):
            raise NotImplementedError

        # TODO: decide if we want pending action messages and uncomment this line
        # await send_status_update(self.session, self.workflow.execution_id,
        # NodeStatus.pending_from_node(node, workflow.execution_id))
        logger.info(f"Scheduled {node}")

    async def get_action_results(self):
        """ Continuously monitors the results queue until all scheduled actions have been completed """
        results_stream = f"{self.workflow.execution_id}:results"

        while len(self.in_process) > 0:
            try:
                with await self.redis as redis:
                    msg = await redis.xread_group(config.REDIS_ACTION_RESULTS_GROUP, CONTAINER_ID,
                                                  streams=[results_stream], count=1, latest_ids=['>'])
            except aioredis.errors.ReplyError:
                logger.debug(f"Stream {self.workflow.execution_id} doesn't exist. Attempting to create it...")
                await self.redis.xgroup_create(results_stream, config.REDIS_ACTION_RESULTS_GROUP,
                                               mkstream=True)
                logger.debug(f"Created stream {results_stream}.")
                continue

            # Dereference the redis stream message and load the status message
            execution_id_node_message, stream, id_ = deref_stream_message(msg)
            execution_id, node_message = execution_id_node_message
            node_message = message_loads(node_message)

            # Ensure that the received NodeStatusMessage is for an action we launched
            if node_message.execution_id == self.workflow.execution_id and node_message.node_id in self.in_process:
                if node_message.status == StatusEnum.EXECUTING:
                    logger.info(f"App started execution of: {node_message.label}-{node_message.execution_id}")

                elif node_message.status == StatusEnum.SUCCESS:
                    self.accumulator[node_message.node_id] = node_message.result
                    logger.info(f"Worker received result for: {node_message.label}-{node_message.execution_id}")

                elif node_message.status == StatusEnum.FAILURE:
                    self.accumulator[node_message.node_id] = node_message.result
                    await self.cancel_subgraph(self.workflow.nodes[node_message.node_id])  # kill the children!
                    logger.info(f"Worker recieved error \"{node_message.result}\" for: {node_message.label}-"
                                f"{node_message.execution_id}")

                else:
                    logger.error(f"Unknown message status received: {node_message}")
                    node_message = None

                await send_status_update(self.session, self.workflow.execution_id, node_message)

            else:
                logger.error(f"Message received for unknown execution: {node_message}")

            # Clean up the redis stream and our in process queue
            if node_message.status != StatusEnum.EXECUTING:
                self.in_process.pop(node_message.node_id, None)
            await self.redis.xack(stream=stream, group_name=config.REDIS_ACTION_RESULTS_GROUP, id=id_)
            await xdel(self.redis, stream=stream, id_=id_)

        # Remove the finished results stream and group
        await self.redis.delete(results_stream)
        pipe: aioredis.commands.Pipeline = self.redis.pipeline()
        futs = [pipe.delete(stream) for stream in self.streams]
        results = await pipe.execute()
        self.streams = set()


if __name__ == "__main__":
    import argparse

    LOG_LEVELS = ("debug", "info", "error", "warn", "fatal", "DEBUG", "INFO", "ERROR", "WARN", "FATAL")
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-level", dest="log_level", choices=LOG_LEVELS, default="INFO")
    parser.add_argument("--debug", "-d", dest="debug", action="store_true",
                        help="Enables debug level logging for the umpire as well as asyncio debug mode.")
    args = parser.parse_args()

    logger.setLevel(args.log_level.upper())

    # Launch the worker event loop
    asyncio.run(Worker.run(), debug=args.debug)
