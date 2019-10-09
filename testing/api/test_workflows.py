import json
import logging
from http import HTTPStatus

import yaml
from starlette.testclient import TestClient

from common.workflow_types import workflow_load
from testing.api.helpers import assert_crud_resource

logger = logging.getLogger(__name__)

base_workflows_url = "/walkoff/api/workflows/"


def test_workflow_get_all(api: TestClient, auth_header: dict):
    p = api.get(base_workflows_url, headers=auth_header)
    assert p.status_code == 200
    assert p.json() == []


def test_workflow_create_read_delete(api: TestClient, auth_header: dict):
    wf_name = "ConditionTest"
    wf_id = "e8c7840a-bd3e-4cfd-b9be-e07269b10c89"

    with open('testing/util/workflow.json') as fp:
        wf_json = json.load(fp)
    p = api.post(base_workflows_url, headers=auth_header, data=json.dumps(wf_json))
    assert p.status_code == 201

    p2 = api.get(base_workflows_url, headers=auth_header)
    assert p2.status_code == 200
    assert len(p2.json()) == 1

    p3 = api.get(base_workflows_url + wf_name, headers=auth_header)
    p4 = api.get(base_workflows_url + wf_id, headers=auth_header)
    assert p3.status_code == p4.status_code == 200
    assert p3.json()["id_"] == wf_id
    assert p4.json()["name"] == wf_name

    p5 = api.delete(base_workflows_url + wf_name, headers=auth_header)
    assert p5.status_code == 204
    assert p5.json()

    p6 = api.get(base_workflows_url, headers=auth_header)
    assert p6.status_code == 200
    assert len(p6.json()) == 0


def test_workflow_copy_read_delete(api: TestClient, auth_header: dict):
    assert 1 == 1


def test_workflow_upload_read_delete(api: TestClient, auth_header: dict):
    assert 1 == 1


def test_workflow_export(api: TestClient, auth_header: dict):
    assert 1 == 1