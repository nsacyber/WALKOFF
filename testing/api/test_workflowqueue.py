import json
import logging

import yaml
from starlette.testclient import TestClient

from testing.api.helpers import assert_crud_resource

logger = logging.getLogger(__name__)

base_workflowqueue_url = "/walkoff/api/workflowqueue/"
base_workflows_url = "/walkoff/api/workflows/"


def test_sanity_check(api: TestClient, auth_header: dict):
    p = api.get(base_workflowqueue_url, headers=auth_header)
    assert p.status_code == 200
    assert p.json() == []


def test_execute_workflow(api: TestClient, auth_header: dict):
    with open('testing/util/workflow.json') as fp:
        wf_json = json.load(fp)
    p = api.post(base_workflows_url, headers=auth_header, data=json.dumps(wf_json))
    assert p.status_code == 201

    with open('testing/util/workflowqueue.json') as fp:
        wf_queue_json = json.load(fp)
    p = api.post(base_workflowqueue_url, headers=auth_header, data=json.dumps(wf_queue_json))
    assert p.status_code == 202

    p = api.get(base_workflowqueue_url, headers=auth_header)
    assert p.status_code == 200
    assert len(p.json()) == 1

    p = api.get(base_workflowqueue_url + wf_queue_json["execution_id"], headers=auth_header)
    assert p.status_code == 200
    assert p.json()["status"] == "PENDING"


def test_invalid_get(api: TestClient, auth_header: dict):
    with open('testing/util/workflowqueue.json') as fp:
        wf_queue_json = json.load(fp)
    p = api.post(base_workflowqueue_url, headers=auth_header, data=json.dumps(wf_queue_json))
    assert p.status_code == 404


def test_cleardb(api: TestClient, auth_header: dict):
    assert False


def test_control_workflow_abort_trigger(api: TestClient, auth_header: dict):
    assert False


def test_control_workflow_abort(api: TestClient, auth_header: dict):
    with open('testing/util/workflow.json') as fp:
        wf_json = json.load(fp)
    p = api.post(base_workflows_url, headers=auth_header, data=json.dumps(wf_json))
    assert p.status_code == 201

    with open('testing/util/workflowqueue.json') as fp:
        wf_queue_json = json.load(fp)
    p = api.post(base_workflowqueue_url, headers=auth_header, data=json.dumps(wf_queue_json))
    assert p.status_code == 202

    data = {
        "status": "abort"
    }
    p = api.patch(base_workflowqueue_url + wf_queue_json["execution_id"],
                 headers=auth_header, data=json.dumps(data))
    assert p.status_code == 204

    p = api.get(base_workflowqueue_url + wf_queue_json["execution_id"], headers=auth_header)
    assert p.status_code == 200
    assert p.json()["status"] == "ABORTED"
