import json
import logging
from http import HTTPStatus

import yaml
from starlette.testclient import TestClient
from datetime import datetime
from testing.api.helpers import assert_crud_resource

logger = logging.getLogger(__name__)

base_scheduler_url = "/walkoff/api/scheduler/"


def workflow_creation_helper(api: TestClient, auth_header: dict):
    with open('testing/util/workflow.json') as fp:
        wf_json = json.load(fp)
    p = api.post("walkoff/api/workflows/", headers=auth_header, data=json.dumps(wf_json))
    assert p.status_code == 201
    return p.json()


def test_sanity_check(api: TestClient, auth_header: dict):
    """ Scheduler should be off, no scheduled tasks """
    p = api.get(base_scheduler_url, headers=auth_header)
    assert p.status_code == 200
    p_response = p.json()
    assert p_response["status"] == 0

    p2 = api.get(base_scheduler_url + "tasks/", headers=auth_header)
    assert p2.status_code == 200
    assert p2.json() == []


def test_invalid_update_scheduler_status(api: TestClient, auth_header: dict):
    x1 = api.put(base_scheduler_url, params={"new_state": "stop"}, headers=auth_header)
    assert x1.status_code == HTTPStatus.BAD_REQUEST

    x2 = api.put(base_scheduler_url, params={"new_state": "start"}, headers=auth_header)
    assert x2.status_code == 200
    x2_response = x2.json()
    assert x2_response["status"] == 1

    x3 = api.put(base_scheduler_url, params={"new_state": "start"}, headers=auth_header)
    assert x3.status_code == HTTPStatus.BAD_REQUEST

    x4 = api.put(base_scheduler_url, params={"new_state": "stop"}, headers=auth_header)
    assert x4.status_code == 200
    x4_response = x4.json()
    assert x4_response["status"] == 0


def test_update_scheduler_status(api: TestClient, auth_header: dict):
    """ Update and check scheduler status """
    x = api.get(base_scheduler_url, headers=auth_header)
    assert x.status_code == 200
    x_response = x.json()
    assert x_response["status"] == 0

    x2 = api.put(base_scheduler_url, params={"new_state": "start"}, headers=auth_header)
    assert x2.status_code == 200
    x2_response = x2.json()
    assert x2_response["status"] == 1

    x4 = api.put(base_scheduler_url, params={"new_state": "pause"}, headers=auth_header)
    assert x4.status_code == 200
    x4_response = x4.json()
    assert x4_response["status"] == 2

    x6 = api.put(base_scheduler_url, params={"new_state": "resume"}, headers=auth_header)
    assert x6.status_code == 200
    x6_response = x6.json()
    assert x6_response["status"] == 1

    x7 = api.put(base_scheduler_url, params={"new_state": "stop"}, headers=auth_header)
    assert x7.status_code == 200
    x7_response = x7.json()
    assert x7_response["status"] == 0

    x8 = api.put(base_scheduler_url, params={"new_state": "start"}, headers=auth_header)
    assert x8.status_code == 200
    x8_response = x8.json()
    assert x8_response["status"] == 1


def test_create_scheduler_task(api: TestClient, auth_header: dict):
    """ Create scheduler task """
    p = workflow_creation_helper(api, auth_header)
    workflow_id = p["id_"]
    data = {
            "name": "test_task",
            "trigger_type": "date",
            "trigger_args": {"run_date": datetime.now().isoformat()},
            "description": "string",
            "workflows": [workflow_id]
        }

    x = api.post(base_scheduler_url + "tasks/", headers=auth_header, data=json.dumps(data))
    assert x.status_code == 200

    p2 = api.get(base_scheduler_url + "tasks/", headers=auth_header)
    assert p2.status_code == 200
    assert p2.json() == []