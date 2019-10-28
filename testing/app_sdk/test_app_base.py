import importlib.util
from pathlib import Path
import pytest

from app_sdk.walkoff_app_sdk.app_base import AppBase
from common.workflow_types import workflow_load, Parameter, Node, Action, Point, Condition, Transform, Trigger, \
    ParameterVariant, Workflow, workflow_dumps, workflow_loads, workflow_dump, ConditionException
from common.message_types import message_dumps, message_loads, NodeStatusMessage

from common.async_logger import AsyncLogger, AsyncHandler
# from apps.hello_world.1.0.0.src.app import HelloWorld
import logging
import os
import json


@pytest.fixture
def app(redis):
    spec = importlib.util.spec_from_file_location("app.py", Path("apps") / "hello_world" / "1.0.0" / "src")

    app = HelloWorld(redis=redis, logger=None)
    yield app


@pytest.fixture
def action(redis, scope='function'):
    with open("testing/util/action.json") as fp:
        action = workflow_load(fp)
    action.execution_id = "bd8c031a-b87e-4530-bf19-e0a08414f46f"
    yield action


# TESTS #
def test_init(app, redis):
    assert isinstance(app.action_queue_keys, tuple)
    assert app.action_queue_keys == tuple(f"{app.__class__.__name__}-{app.__version__}-{i}" for i in range(5, 0, -1))
    assert app.redis == redis
    assert app.logger == logging.getLogger("AppBaseLogger")
    assert app.current_execution_id is None


def test_init_action(action):
    assert action.name == "pause"
    assert action.app_name == "HelloWorld-v1.0"
    assert action.id_ == "55876340-50b1-d9a4-7f22-150a6f4be4c6"
    assert action.priority == 1
    assert action.execution_id == "bd8c031a-b87e-4530-bf19-e0a08414f46f"
    # assert Parameter(name= "seconds", value= 3, variant= "STATIC_VALUE") in action.parameters
    assert action.position == Point(x=400, y=190)


@pytest.mark.asyncio
async def test_get_actions(app, redis):
    with open("testing/util/action.json") as fp:
        action_json = json.load(fp)
        action_string = json.dumps(action_json)

    await redis.lpush(app.action_queue_keys[4], action_string)
    assert await redis.lpop(ACTIONS_IN_PROCESS) is None
    try:
        await app.get_actions()
        assert await redis.lpop(app.action_queue_keys[0]) is None
        assert await redis.lpop(ACTIONS_IN_PROCESS) == action_string
    except SystemExit:
        assert True
    except:
        assert False


@pytest.mark.asyncio
async def test_execute_action(app, action, redis):
    assert await redis.lpop(action.execution_id) is None
    await app.execute_action(action)

    returned = (await redis.lpop(action.execution_id)).decode("utf-8")
    returned = json.loads(returned)

    result = 3

    action_result = NodeStatusMessage.success_from_node(action, action.execution_id, result)
    to_compare = message_dumps(action_result)
    to_compare = json.loads(to_compare)

    for key in returned.keys():
        if key != "completed_at":
            assert returned[key] == to_compare[key]
