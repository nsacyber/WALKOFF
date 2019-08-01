from os import environ
import pytest

from api_gateway.flask_config import Config
from api_gateway.helpers import format_db_path

environ["REDIS_OPTIONS"] = "{\"host\": \"redis\", \"port\": 6479}"
environ["IP"] = "0.0.0.0"
environ["PORT"] = "8080"
environ["WALKOFF_DB_TYPE"] = "postgresql"
environ["EXECUTION_DB_TYPE"] = "postgresql"
environ["DB_PATH"] = "walkoff"
environ["EXECUTION_DB_PATH"] = "execution"
environ["WALKOFF_DB_HOST"] = "localhost"
environ["EXECUTION_DB_HOST"] = "localhost"
environ["EXECUTION_DB_USERNAME"] = "walkoff"
environ["EXECUTION_DB_PASSWORD"] = "walkoff"
environ["WALKOFF_DB_USERNAME"] = "walkoff"
environ["WALKOFF_DB_PASSWORD"] = "walkoff"
Config.load_env_vars()

from api_gateway.extensions import db
from api_gateway.server.app import app
from api_gateway.server.blueprints.root import create_user

import json
import birdisle.aioredis
from common.config import config
from common.workflow_types import workflow_load


@pytest.fixture
async def server():
    server = birdisle.Server()
    yield server
    server.close()


@pytest.fixture
def workflow():
    with open("testing/util/workflow.json") as fp:
        workflow = workflow_load(fp)
    yield workflow


@pytest.fixture
async def redis(server):
    redis = await birdisle.aioredis.create_redis(server)
    with open("testing/util/workflow.json") as fp:
        wf_json = json.load(fp)
        await redis.lpush(config["REDIS"]["workflow_q"], json.dumps(wf_json))
    yield redis
    redis.close()
    await redis.wait_closed()


@pytest.fixture
def auth_header(api_gateway):
    header = {'content-type': "application/json"}
    response = api_gateway.post('/api/auth',
                                data=json.dumps(dict(username='admin', password='admin')), headers=header)
    token = json.loads(response.get_data(as_text=True))
    header = {'Authorization': 'Bearer {}'.format(token['access_token']), 'content-type': 'application/json'}
    return header


@pytest.fixture(scope='function')
def api_gateway():
    with app.app_context():
        create_user()
        app.testing = True
        api_gateway = app.test_client()
        yield api_gateway


@pytest.fixture
def serverdb():
    yield db
    db.drop_all()


@pytest.fixture
def workflow(api_gateway, token):
    header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
    with open("testing/util/workflow.json") as fp:
        wf_json = json.load(fp)
        data = json.dumps(wf_json)
    response1 = api_gateway.post('/api/workflows', data=data, headers=header, content_type="application/json")
    wf = json.loads(response1.get_data(as_text=True))
    yield wf


@pytest.fixture
def execdb():

    from api_gateway.executiondb import ExecutionDatabase
    from api_gateway.executiondb.action import Action
    from api_gateway.executiondb.appapi import AppApi
    from api_gateway.executiondb.branch import Branch
    from api_gateway.executiondb.condition import Condition
    from api_gateway.executiondb.dashboard import Dashboard
    from api_gateway.executiondb.global_variable import GlobalVariable
    from api_gateway.executiondb.parameter import Parameter
    from api_gateway.executiondb.returns import ReturnApi
    from api_gateway.executiondb.transform import Transform
    from api_gateway.executiondb.workflow import Workflow
    from api_gateway.executiondb.workflow_variable import WorkflowVariable
    from api_gateway.executiondb.workflowresults import WorkflowStatus

    yield app.running_context.execution_db
    execution_db = ExecutionDatabase.instance
    execution_db.session.rollback()
    classes = [Workflow, Action, AppApi, Branch, GlobalVariable, Dashboard,
               Condition, Transform, WorkflowStatus, WorkflowStatus, Parameter, ReturnApi,
               WorkflowVariable]
    for ee in classes:
        execution_db.session.query(ee).delete()
    execution_db.session.commit()
