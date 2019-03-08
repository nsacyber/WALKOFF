from collections import deque
import asyncio
import logging
import json
import sys
import uuid
from typing import Union

import aiohttp
import aioredis
from asteval import Interpreter, make_symbol_table

from common.message_types import message_dumps, message_loads, message_dump, ActionStatusMessage, WorkflowStatusMessage, StatusEnum, \
    JSONPatch, JSONPatchOps
from common.config import config
from common.helpers import connect_to_redis_pool
from common.workflow_types import Node, Action, Condition, Transform, Trigger, ParameterVariant, Workflow, \
    workflow_dumps, workflow_loads

logging.basicConfig(level=logging.INFO, format="{asctime} - {name} - {levelname}:{message}", style='{')
logger = logging.getLogger("WORKER")

class Worker:
    class ConditionException(Exception): pass

    def __init__(self, workflow: Workflow = None, start_action: str = None, redis: aioredis.Redis = None,
                 session:aiohttp.ClientSession = None):
        self.workflow = workflow
        self.start_action = start_action if start_action is not None else self.workflow.start
        self.accumulator = {}
        self.in_process = {}
        self.redis = redis
        self.session = session

    @staticmethod
    async def get_workflow(redis: aioredis.Redis):
        """
            Continuously monitors the workflow queue for new work
        """
        while True:
            logger.info("Waiting for workflows...")
            # TODO: Remove the test code
            # Push test workflow in for now
            with open("../data/not_workflows/hello.json") as fp:
                wf = json.load(fp)
                await redis.lpush(config["REDIS"]["workflow_q"], json.dumps(wf))

            workflow = await redis.brpoplpush(sourcekey=config["REDIS"]["workflow_q"],
                                              destkey=config["REDIS"]["workflows_in_process"],
                                              timeout=config.getint("WORKER", "timeout"))

            if workflow is None:  # We've timed out with no work. Guess we'll die now...
                sys.exit(1)

            yield workflow_loads(workflow)

    @staticmethod
    async def run():
        async with connect_to_redis_pool(config["REDIS"]["redis_uri"]) as redis, aiohttp.ClientSession() as session:
            async for workflow in Worker.get_workflow(redis):

                # Setup worker launch the event loop
                worker = Worker(workflow, redis=redis, session=session)
                logger.info(f"Starting execution of workflow: {workflow.name}")

                try:
                    await worker.execute_workflow()

                except Exception:
                    logger.info(f"Failed execution of workflow: {workflow.name}")

                else:
                    logger.info(f"Completed execution of workflow: {workflow.name}")
        await Worker.shutdown()

    @staticmethod
    async def shutdown():
        # Clean up any unfinished tasks (shouldn't really be any though)
        tasks = [t for t in asyncio.all_tasks() if t is not
                 asyncio.current_task()]

        [task.cancel() for task in tasks]

        logger.info('Canceling outstanding tasks')
        await asyncio.gather(*tasks, return_exceptions=True)

    async def cancel_subgraph(self, node):
        """
            Cancels the task related to the current node as well as the tasks related to every child of that node.
            Also removes them from the worker's internal in_process queue.
        """
        dependents = self.workflow.get_dependents(node)
        cancelled_tasks = set()

        for task in asyncio.all_tasks():
            for _, arg in task._coro.cr_frame.f_locals.items():  # Where the args of a coro are stored...trust me
                if isinstance(arg, Node):
                    if arg in dependents:
                        self.in_process.pop(arg.id_)
                        task.cancel()
                        cancelled_tasks.add(task)

        exceptions = await asyncio.gather(*cancelled_tasks, return_exceptions=True)

    async def execute_workflow(self):
        """
            Do a simple BFS to visit and schedule each node in the workflow. We assume every node will run and thus
            preemptively schedule them all. We will clean up any nodes that will not run due to conditions or triggers
        """
        visited = {self.start_action}
        queue = deque([self.start_action])
        tasks = set()

        while queue:
            node = queue.pop()
            parents = set(self.workflow.predecessors(node)) if node is not self.start_action else set()
            children = set(self.workflow.successors(node))
            node.execution_id = str(uuid.uuid4())
            node.workflow_execution_id = self.workflow.execution_id
            self.in_process[node.id_] = node

            if isinstance(node, Action):
                tasks.add(asyncio.create_task(self.schedule_action(parents, node)))

            elif isinstance(node, Condition):
                self.evaluate_condition(parents=parents, children=children, condition=node.conditional)

            elif isinstance(node, Transform):
                pass

            elif isinstance(node, Trigger):
                raise NotImplementedError

            for child in sorted(children, reverse=True):
                if child not in visited:
                    queue.appendleft(child)
                    visited.add(child)

        # Launch the results accumulation task and wait for all the results to come in
        results_task = asyncio.create_task(self.get_action_results())

        done, pending = await asyncio.wait([asyncio.gather(*tasks), results_task], return_when=asyncio.FIRST_EXCEPTION)
        try:
            for task in done:
                await task

        except Exception as e:
            # We timed out or were unsubbed. Clean up any scheduled actions and such that we didn't make it to
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            logger.info("Cleaned up remaining actions.")
            raise e

    def evaluate_condition(self, condition, parents, children):
        """
            TODO: This will change when we implement a better UI element for it. For now, if an action is given a user
            defined name like "Hello World", it would be referenced by the variable name "Hello_World" in the
            conditional script. All whitespace in the action name is replaced by '_'. This is clearly problematic
            if a user has an action named "Hello World" as well as "Hello_World". In this case, we cannot be sure
            which is being referenced in the conditional and must raise an exception.
        """
        def format_node_names(nodes):
            # We need to format space delimited names into underscore delimited names
            names_to_modify = {node.name for node in nodes if node.name.count(' ') > 0}
            formatted_nodes = {}
            for node in nodes:
                formatted_name = node.name.strip().replace(' ', '_')

                if formatted_name in names_to_modify:  # we have to check for a name conflict as described above
                    logger.error(f"Error processing condition. {node.name} or {formatted_name} must be renamed.")
                    raise self.ConditionException

                formatted_nodes[formatted_name] = node
            return formatted_nodes

        parent_symbols = format_node_names(parents)
        children_symbols = format_node_names(children)
        syms = make_symbol_table(**parent_symbols, **children_symbols)
        aeval = Interpreter(usersyms=syms, no_for=True, no_while=True, no_try=True, no_functiondef=True, no_ifexp=True,
                            no_listcomp=True, no_augassign=True, no_assert=True, no_delete=True, no_raise=True,
                            no_print=True, builtins_readonly=True)

        return aeval(condition) if len(aeval.error) is 0 else aeval.error

    # async def execute_transform(self, action):
    #     """ Execute an transform and ship its result """
    #     self.logger.debug(f"Attempting execution of: {self.name}-{self.id}")
    #     if hasattr(self, self.transform):
    #         start_action_msg = ActionResult(action=action, result=None, status=WorkflowEvent.TransformStarted)
    #         await self.redis.publish_json(ACTION_RESULT_CH, start_action_msg.to_json())
    #         try:
    #             if action.get("params", None) is None:
    #                 result = getattr(self, action["action_name"])()
    #             else:
    #                 result = getattr(self, action["action_name"])(**action["params"])
    #             action_result = ActionResult(action=action, result=result, status=WorkflowEvent.TransformSuccess)
    #             self.logger.debug(f"Executed {action['name']}-{action['id']} with result: {result}")
    #
    #         except Exception as e:
    #             action_result = ActionResult(action=action, result=None, error=repr(e), status=WorkflowEvent.TransformError)
    #             self.logger.exception(f"Failed to execute {action['name']}-{action['id']}")
    #
    #         await self.redis.publish_json(ACTION_RESULT_CH, action_result.to_json())
    #
    #     else:
    #         self.logger.error(f"App {self.__class__.__name__} has no method {action['action_name']}")
    #         action_result = ActionResult(action, error="Action does not exist")
    #         await self.redis.publish_json(ACTION_RESULT_CH, action_result.to_json())

    async def dereference_params(self, action: Action):
        global_vars = set(await self.redis.hkeys(config["REDIS"]["globals_key"]))

        for param in action.parameters:
            if param.variant == ParameterVariant.STATIC_VALUE:
                continue

            elif param.variant == ParameterVariant.ACTION_RESULT:
                if param.reference in self.accumulator:
                    param.value = self.accumulator[param.reference]

            elif param.variant == ParameterVariant.WORKFLOW_VARIABLE:
                if param.reference in self.workflow.workflow_variables:
                    param.value = self.workflow.workflow_variables[param.reference]

            elif param.variant == ParameterVariant.GLOBAL:
                if param.reference in global_vars:
                    param.value = self.accumulator[param.reference]

            else:
                logger.error(f"Unable to defeference parameter:{param} for action:{action}")
                break

            param.reference = None
            param.variant = ParameterVariant.STATIC_VALUE

    async def schedule_action(self, parents: {Action}, action: Action):
        """ Waits until all dependencies of an action are met and then schedules the action """
        while not all(parent.id_ in self.accumulator for parent in parents):
            await asyncio.sleep(0)

        await self.dereference_params(action)

        # TODO: decide if we want pending action messages and uncomment this line
        # await self.send_message(ActionStatusMessage.pending_from_action(action))

        await self.redis.lpush(f"{action.app_name}-{action.priority}", workflow_dumps(action))
        logger.info(f"Scheduled {action}")

    async def get_action_results(self):
        """ Continuously monitors the results queue until all scheduled actions have been completed """
        read_messages_queue = f"{self.workflow.execution_id}::read"
        while len(self.in_process) > 0:
            msg = await self.redis.brpoplpush(self.workflow.execution_id, read_messages_queue, timeout=5)

            if msg is None:
                continue

            msg = message_loads(msg)
            # Ensure that the recieved ActionResult is for an action we launched
            if msg.workflow_execution_id == self.workflow.execution_id and msg.action_id in self.in_process:
                # if msg["error"] is None and msg["result"] is not None:

                if msg.status == StatusEnum.EXECUTING:
                    logger.info(f"App started exectuion of: {msg.name}-{msg.workflow_execution_id}")

                elif msg.status == StatusEnum.SUCCESS:
                    self.accumulator[msg.action_id] = msg.result
                    logger.info(f"Worker recieved result for: {msg.name}-{msg.workflow_execution_id}")

                    # Remove the action from our local in_process queue as well as the one in redis
                    action = self.in_process.pop(msg.action_id)
                    await self.redis.lrem(config["REDIS"]["actions_in_process"], 0, workflow_dumps(action))

                elif msg.status == StatusEnum.FAILURE:
                    self.accumulator[msg.action_id] = msg.error
                    logger.info(f"Worker recieved error \"{msg.error}\" for: {msg.name}-{msg.workflow_execution_id}")

                else:
                    logger.error(f"Unknown message recieved: {msg}")

        # Clean up our redis mess
        await self.redis.delete(read_messages_queue)

    async def send_message(self, message: Union[ActionStatusMessage, WorkflowStatusMessage]):
        execution_id = None
        patches = None
        if isinstance(message, ActionStatusMessage):
            execution_id = message.workflow_execution_id
            root = f"/action_statuses/{message.action_id}"

            if message.status == StatusEnum.EXECUTING:
                black_list = {"result", "completed_at"}
                fields = {'/'.join((root, k)): v for k, v in message_dump(message).items() if k not in black_list}
                patches = [JSONPatch(JSONPatchOps.ADD, path=path, value=value) for path, value in fields]

            elif message.status == StatusEnum.SUCCESS:
                white_list = {"status", "result", "completed_at"}
                fields = {'/'.join((root, k)): v for k, v in message_dump(message).items() if k in white_list}
                patches = [JSONPatch(JSONPatchOps.REMOVE, path=path, value=value) for path, value in fields]

            elif message.status == StatusEnum.FAILURE:
                white_list = {"status", "error", "completed_at"}
                fields = {'/'.join((root, k)): v for k, v in message_dump(message).items() if k in white_list}
                patches = [JSONPatch(JSONPatchOps.REMOVE, path=path, value=value) for path, value in fields]

        elif isinstance(message, WorkflowStatusMessage):
            execution_id = message.execution_id
            root = f"#/"

            if message.status == StatusEnum.EXECUTING:
                black_list = {"status", "started_at"}
                fields = {'/'.join((root, k)): v for k, v in message_dump(message).items() if k not in black_list}
                patches = [JSONPatch(JSONPatchOps.ADD, path=path, value=value) for path, value in fields]

            elif message.status == StatusEnum.COMPLETED:
                white_list = {"status", "completed_at"}
                fields = {'/'.join((root, k)): v for k, v in message_dump(message).items() if k in white_list}
                patches = [JSONPatch(JSONPatchOps.REMOVE, path=path, value=value) for path, value in fields]

            elif message.status == StatusEnum.ABORTED:
                white_list = {"status", "completed_at"}
                fields = {'/'.join((root, k)): v for k, v in message_dump(message).items() if k in white_list}
                patches = [JSONPatch(JSONPatchOps.REMOVE, path=path, value=value) for path, value in fields]

        if execution_id is None:
            raise ValueError(f"Attempting to send improper message type: {type(message)}")

        data = message_dumps(patches)
        params = {"event": message.status.value}
        url = f"/iapi/workflowstatus/{execution_id}"
        async with self.session.patch(url, data=data, params=params) as resp:
            return resp.json(loads=message_loads)

if __name__ == "__main__":
    # Launch the worker event loop
    asyncio.run(Worker.run())
