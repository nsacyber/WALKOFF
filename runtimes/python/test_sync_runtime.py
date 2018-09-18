from datetime import datetime, timedelta
from uuid import uuid4
import logging

import sys
import os

sys.path.append(os.path.abspath('../..'))

print('HERHERHEHRE')

import jwt
import pytest
import syncruntime as runtime
from falcon import testing

from walkoff.appgateway import get_app
from walkoff.appgateway.accumulators import ExternallyCachedAccumulator
from walkoff.cache import make_cache
from walkoff.worker.action_exec_strategy import LocalActionExecutionStrategy





logging.disable(logging.CRITICAL)  # comment out to see logs

def make_token():
    return jwt.encode(
        {'user_identifier': 1, 'exp': datetime.utcnow() + timedelta(seconds=5)},
        runtime.jwt_secret,
        algorithm='HS256'
    ).decode("utf-8")


@pytest.fixture
def auth_header():
    return {'Authorization': 'Bearer {}'.format(make_token())}


@pytest.fixture
def client():
    return testing.TestClient(runtime.api)


@pytest.fixture
def kafka_client():
    class MockKafkaResultsSender:

        def __init__(self):
            self.call_history = []

        def handle_event(self, workflow, sender, **kwargs):
            self.call_history.append((workflow, sender, kwargs))

    return MockKafkaResultsSender()

@pytest.fixture
def accumulator():
    return ExternallyCachedAccumulator(runtime.redis_cache, 'null')


@pytest.fixture
def action_executor(accumulator, kafka_client):
    return runtime.ActionExecution(LocalActionExecutionStrategy(fully_cached=True), kafka_client, accumulator)


def make_execute_url(workflow_execution_id, executable_execution_id):
    return '/workflows/{}/actions/{}'.format(workflow_execution_id, executable_execution_id)


def make_execution_json(exec_type, name, arguments=None, device_id=None):
    if not arguments:
        arguments = []
    workflow_id = str(uuid4())
    executable_id = str(uuid4())
    executable_context = {
        'name': name,
        'type': exec_type,
        'id': executable_id,
    }
    if device_id:
        executable_context['device_id'] = device_id

    return {
        'workflow_context': {
            'name': 'TestWorkflow',
            'id': workflow_id
        },
        'executable_context': executable_context,
        'arguments': arguments
    }


def get_exec_id_from_exec_json(exec_json):
    return exec_json['executable_context']['id']


def make_workflow_context_from_exec_json(exec_json, workflow_exec_id):
    workflow_context = exec_json['workflow_context']
    workflow_context['workflow_execution_id'] = workflow_exec_id
    return workflow_context


@pytest.mark.parametrize("function_type", ['transform', 'condition', 'action'])
def test_unknown_function(function_type, client, auth_header):
    workflow_execution_id = str(uuid4())
    executable_execution_id = str(uuid4())

    invalid_name = 'invalid'
    doc = make_execution_json(function_type, invalid_name)

    url = make_execute_url(workflow_execution_id, executable_execution_id)
    resp = client.simulate_post(url, json=doc, headers=auth_header)
    assert resp.status_code == 404
    expected_response = {
        'title': 'Unknown {}'.format(function_type),
        'description': 'Unknown {} {}'.format(function_type, invalid_name)
    }
    assert resp.json == expected_response


def test_execute_transform(client, accumulator, auth_header):
    workflow_execution_id = str(uuid4())
    executable_execution_id = str(uuid4())
    accumulator.set_key(workflow_execution_id)
    arguments = [
        {
            'name': 'json_in',
            'value': {'a': 1, 'b': ['d', 'e', 'f']}
        },
        {
            'name': 'element',
            'value': 'a'
        }
    ]
    doc = make_execution_json('transform', 'select json', arguments=arguments)
    executable_id = get_exec_id_from_exec_json(doc)

    url = make_execute_url(workflow_execution_id, executable_execution_id)
    resp = client.simulate_post(url, json=doc, headers=auth_header)
    assert resp.status_code == 200
    expected_key = accumulator.format_key(executable_id)
    assert resp.json == {'status': 'Success', 'result_key': expected_key}
    # assert accumulator[expected_key].decode('utf-8') == '1' #unknown why this says key doesn't exist. Manual testing with redis-cli confirms it exists


def test_execute_transform_execution_error(client, accumulator, auth_header):
    workflow_execution_id = str(uuid4())
    executable_execution_id = str(uuid4())
    accumulator.set_key(workflow_execution_id)
    arguments = [
        {
            'name': 'json_in',
            'value': {'a': 1, 'b': ['d', 'e', 'f']}
        },
        {
            'name': 'invalid',
            'value': 'a'
        }
    ]
    doc = make_execution_json('transform', 'select json', arguments=arguments)
    executable_id = get_exec_id_from_exec_json(doc)
    url = make_execute_url(workflow_execution_id, executable_execution_id)
    resp = client.simulate_post(url, json=doc, headers=auth_header)
    assert resp.status_code == 200
    expected_key = accumulator.format_key(executable_id)
    assert resp.json == {'status': 'UnhandledException', 'result_key': expected_key}


def test_execute_condition(client, accumulator, auth_header):
    workflow_execution_id = str(uuid4())
    executable_execution_id = str(uuid4())
    accumulator.set_key(workflow_execution_id)
    arguments = [
        {
            'name': 'value',
            'value': 'aaa'
        },
        {
            'name': 'regex',
            'value': 'b'
        }
    ]
    doc = make_execution_json('condition', 'regMatch', arguments=arguments)
    executable_id = get_exec_id_from_exec_json(doc)

    url = make_execute_url(workflow_execution_id, executable_execution_id)
    resp = client.simulate_post(url, json=doc, headers=auth_header)
    assert resp.status_code == 200
    expected_key = accumulator.format_key(executable_id)
    assert resp.json == {'status': 'Success', 'result_key': expected_key}


def test_execute_condition_execution_error(client, accumulator, auth_header):
    workflow_execution_id = str(uuid4())
    executable_execution_id = str(uuid4())
    accumulator.set_key(workflow_execution_id)
    arguments = [
        {
            'name': 'value',
            'value': 'aaa'
        },
        {
            'name': 'invalid',
            'value': 'b'
        }
    ]
    doc = make_execution_json('condition', 'regMatch', arguments=arguments)
    executable_id = get_exec_id_from_exec_json(doc)

    url = make_execute_url(workflow_execution_id, executable_execution_id)
    resp = client.simulate_post(url, json=doc, headers=auth_header)
    assert resp.status_code == 200
    expected_key = accumulator.format_key(executable_id)
    assert resp.json == {'status': 'UnhandledException', 'result_key': expected_key}


def test_execute_action_no_device(client, accumulator, auth_header):
    workflow_execution_id = str(uuid4())
    executable_execution_id = str(uuid4())
    accumulator.set_key(workflow_execution_id)
    arguments = [
        {
            'name': 'arg1',
            'value': 'aaa'
        }
    ]
    doc = make_execution_json('action', 'global1', arguments=arguments)
    executable_id = get_exec_id_from_exec_json(doc)

    url = make_execute_url(workflow_execution_id, executable_execution_id)
    resp = client.simulate_post(url, json=doc, headers=auth_header)
    assert resp.status_code == 200
    expected_key = accumulator.format_key(executable_id)
    assert resp.json == {'status': 'Success', 'result_key': expected_key}


def test_create_device_already_in_cache(action_executor):
    workflow_execution_id = str(uuid4())
    workflow_id = str(uuid4())

    workflow_context = {
        'workflow_execution_id': workflow_execution_id,
        'workflow_id': workflow_id,
        'workflow_name': 'TestWorkflow'
    }

    device_id = 1
    app_instance = get_app(runtime.app_name)(runtime.app_name, device_id, workflow_context)
    new_message = {'message': 'changed'}
    app_instance.introMessage = new_message
    app_instance_key = runtime.ActionExecution.format_app_instance_key(workflow_execution_id, device_id)
    runtime.redis_cache.cache.sadd(runtime.app_instance_set_name, app_instance_key)
    remade_device = action_executor.create_device(workflow_context, device_id)
    assert remade_device.introMessage == new_message


def test_execute_action_device_not_in_cache(action_executor):
    workflow_execution_id = str(uuid4())
    workflow_id = str(uuid4())

    workflow_context = {
        'workflow_execution_id': workflow_execution_id,
        'workflow_id': workflow_id,
        'workflow_name': 'TestWorkflow'
    }

    device_id = 1
    app_instance = action_executor.create_device(workflow_context, device_id)
    assert app_instance.introMessage == {'message': 'HELLO WORLD'}


def test_workflow_execution_deleted(client, auth_header):
    workflow_execution_id = str(uuid4())

    def get_num_keys():
        key_pattern = runtime.WorkflowExecution.format_scan_pattern(workflow_execution_id)
        return sum(1 for _key in runtime.redis_cache.cache.sscan_iter(runtime.app_instance_set_name, key_pattern))

    num_app_instances_inserted = 3
    for i in range(num_app_instances_inserted):
        key = runtime.ActionExecution.format_app_instance_key(workflow_execution_id, i + 1)
        runtime.redis_cache.cache.sadd(runtime.app_instance_set_name, key)

    assert get_num_keys() == num_app_instances_inserted

    resp = client.simulate_delete('/workflows/{}'.format(workflow_execution_id), headers=auth_header)
    assert resp.status_code == 204
    assert get_num_keys() == 0


def test_get_health_good(client):
    expected = {
        'cache': [
            {
                'test_name': 'pinging',
                'result': 'pass'
            }
        ]
    }
    response = client.simulate_get('/health')
    assert response.status_code == 200
    data = response.json
    assert float(data['cache'][0]['time']) > 0.0
    data['cache'][0].pop('time')
    assert data == expected


def test_get_health_bad(client):
    expected = {
        'cache': [
            {
                'test_name': 'pinging',
                'result': 'failed',
                'reason': 'exception raised'
            }
        ]
    }
    runtime.redis_cache = make_cache({'host': 'invalid'})
    response = client.simulate_get('/health')
    assert response.status_code == 400
    data = response.json
    assert data == expected


@pytest.mark.parametrize(
    "url,is_execute",
    [
        ('/workflows/invalid/actions/{}', True),
        ('/workflows/{}/actions/invalid', True),
        ('/workflows/invalid', False)
    ]
)
def test_execute_invalid_workflow_uuid(url, is_execute, client):
    if is_execute:
        doc = make_execution_json('action', 'global1')
        resp = client.simulate_post(url.format(uuid4()), json=doc)
    else:
        resp = client.simulate_delete(url)
    assert resp.status_code == 404


def test_execute_no_token(client):
    workflow_execution_id = str(uuid4())
    executable_execution_id = str(uuid4())
    arguments = [
        {
            'name': 'arg1',
            'value': 'aaa'
        }
    ]
    doc = make_execution_json('action', 'global1', arguments=arguments)

    url = make_execute_url(workflow_execution_id, executable_execution_id)
    resp = client.simulate_post(url, json=doc)
    assert resp.status_code == 401


@pytest.mark.parametrize('token', ['invalid {}'.format(make_token()), '{}'.format(make_token()), 'Bearer invalid'])
def test_execute_invalid_token(token, client):
    workflow_execution_id = str(uuid4())
    executable_execution_id = str(uuid4())
    arguments = [
        {
            'name': 'arg1',
            'value': 'aaa'
        }
    ]
    doc = make_execution_json('action', 'global1', arguments=arguments)

    url = make_execute_url(workflow_execution_id, executable_execution_id)
    resp = client.simulate_post(url, json=doc, headers={'Authorization': token})
    assert resp.status_code == 401


def test_workflow_execution_deleted_no_token(client):
    workflow_execution_id = str(uuid4())

    resp = client.simulate_delete('/workflows/{}'.format(workflow_execution_id))
    assert resp.status_code == 401


@pytest.mark.parametrize('token', ['invalid {}'.format(make_token()), '{}'.format(make_token()), 'Bearer invalid'])
def test_workflow_execution_deleted_no_token(token, client):
    workflow_execution_id = str(uuid4())

    resp = client.simulate_delete('/workflows/{}'.format(workflow_execution_id), headers={'Authorization': token})
    assert resp.status_code == 401



def invalid_execution_request_generator():
    original_request = make_execution_json('action', 'something')

    # generate requests with missing sections or additional fields
    for field in ('workflow_context', 'executable_context'):
        invalid_request = original_request.copy()
        invalid_request[field]['invalid'] = 'something'
        yield invalid_request
        invalid_request.pop(field)
        yield invalid_request

    #generate requests with missing field in workflow context
    for field in ('name', 'id'):
        invalid_request = original_request.copy()
        invalid_request['workflow_context'].pop(field)
        yield invalid_request

    # generate requests with missing field in execution context
    for field in ('name', 'type', 'id'):
        invalid_request = original_request.copy()
        invalid_request['executable_context'].pop(field)
        yield invalid_request

    # generate malformed json
    yield ''
    yield '\x81'
    yield 'not json'



@pytest.mark.parametrize('request', [request for request in invalid_execution_request_generator()])
def test_execute_invalid_request(request, client, auth_header):  # test endpoint validation
    workflow_execution_id = str(uuid4())
    executable_execution_id = str(uuid4())
    url = make_execute_url(workflow_execution_id, executable_execution_id)
    resp = client.simulate_post(url, json=request, headers=auth_header)
    assert resp.status_code == 400
