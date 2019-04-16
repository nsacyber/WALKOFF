import pytest
from api_gateway.extensions import db
from api_gateway.server.app import app
from api_gateway.server.blueprints.root import create_user
from api_gateway.executiondb import ExecutionDatabase
from api_gateway.executiondb.action import Action
from api_gateway.executiondb.appapi import AppApi
from api_gateway.executiondb.branch import Branch
from api_gateway.executiondb.condition import Condition
from api_gateway.executiondb.dashboard import Dashboard
from api_gateway.executiondb.global_variable import GlobalVariable
from api_gateway.executiondb.parameter import Parameter
from api_gateway.executiondb.position import Position
from api_gateway.executiondb.returns import ReturnApi
from api_gateway.executiondb.transform import Transform
from api_gateway.executiondb.trigger import Trigger
from api_gateway.executiondb.workflow import Workflow
from api_gateway.executiondb.workflow_variable import WorkflowVariable
from api_gateway.executiondb.workflowresults import WorkflowStatus
import json
from async_generator import yield_, async_generator
import birdisle.aioredis
from common.config import config
from common.workflow_types import workflow_load

@pytest.fixture
@async_generator
async def server(scope='function'):
    server = birdisle.Server()
    await yield_(server)
    server.close()


@pytest.fixture
def workflow():
    with open("testing/util/workflow.json") as fp:
        workflow = workflow_load(fp)
    yield workflow


@pytest.fixture
@async_generator
async def redis(server, scope='function'):
    redis = await birdisle.aioredis.create_redis(server)
    with open("testing/util/workflow.json") as fp:
        wf_json = json.load(fp)
        await redis.lpush(config["REDIS"]["workflow_q"], json.dumps(wf_json))
    await yield_(redis)
    redis.close()
    await redis.wait_closed()


@pytest.fixture(scope='function')
def token(api_gateway):
    header = {'content-type': "application/json"}
    response = api_gateway.post('/api/auth',
                                data=json.dumps(dict(username='admin', password='admin')), headers=header)
    token = json.loads(response.get_data(as_text=True))
    yield token


@pytest.fixture(scope='function')
def api_gateway():
    with app.app_context():
        create_user()
        app.testing = True
        api_gateway = app.test_client()
        yield api_gateway


@pytest.fixture(scope='function')
def serverdb():
    yield db
    db.drop_all()
