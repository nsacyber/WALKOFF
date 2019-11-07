import json
import logging
from http import HTTPStatus

import yaml
from starlette.datastructures import UploadFile, FormData

from starlette.testclient import TestClient

from common.workflow_types import workflow_load
from testing.api.helpers import assert_crud_resource

logger = logging.getLogger(__name__)

base_workflows_url = "/walkoff/api/workflows/"


def test_workflow_get_all(api: TestClient, auth_header: dict):
    p = api.get(base_workflows_url, headers=auth_header)
    assert p.status_code == 200
    assert p.json() == []


def test_workflow_invalid(api: TestClient, auth_header: dict):
    """ Assert workflow without actions is invalid """
    with open('testing/util/workflow.json') as fp:
        wf_json = json.load(fp)
    wf_json.pop("actions")
    p = api.post(base_workflows_url, headers=auth_header, data=json.dumps(wf_json))
    assert p.status_code == 422


def test_workflow_create_read_delete(api: TestClient, auth_header: dict):
    with open('testing/util/workflow.json') as fp:
        wf_json = json.load(fp)
    p = api.post(base_workflows_url, headers=auth_header, data=json.dumps(wf_json))
    assert p.status_code == 201

    wf_name = wf_json["name"]
    wf_id = wf_json["id_"]

    p2 = api.get(base_workflows_url, headers=auth_header)
    assert p2.status_code == 200
    assert len(p2.json()) == 1

    p3 = api.get(base_workflows_url + wf_name, headers=auth_header)
    p4 = api.get(base_workflows_url + wf_id, headers=auth_header)
    assert p3.status_code == p4.status_code == 200
    assert p3.json()["id_"] == wf_id
    assert p4.json()["name"] == wf_name

    p5 = api.delete(base_workflows_url + wf_name, headers=auth_header)
    assert p5.status_code == 200
    assert p5.json()

    p6 = api.get(base_workflows_url, headers=auth_header)
    assert p6.status_code == 200
    assert len(p6.json()) == 0


def test_workflow_unauth(api: TestClient, unauthorized_header: dict, auth_header: dict):
    with open('testing/util/workflow.json') as fp:
        wf_json = json.load(fp)
    p = api.post(base_workflows_url, headers=unauthorized_header, data=json.dumps(wf_json))

    with open('testing/util/workflow.json') as fp:
        wf_json = json.load(fp)
        # authorized post
        api.post(base_workflows_url, headers=auth_header, data=json.dumps(wf_json))

    p2 = api.get(base_workflows_url + wf_json["name"], headers=unauthorized_header)
    p3 = api.delete(base_workflows_url + wf_json["name"], headers=unauthorized_header)
    p4 = api.put(base_workflows_url + wf_json["name"], headers=unauthorized_header, data=json.dumps(wf_json))

    assert p.status_code == p2.status_code == p3.status_code == p4.status_code == 403


def test_workflow_copy_get(api: TestClient, auth_header: dict):
    with open('testing/util/workflow.json') as fp:
        wf_json = json.load(fp)
    p = api.post(base_workflows_url, headers=auth_header, data=json.dumps(wf_json))
    assert p.status_code == 201

    wf_id = wf_json["id_"]

    data = {"name": "copied_wf"}
    p2 = api.post(base_workflows_url + "copy", params={"source": wf_id}, headers=auth_header, data=json.dumps(data))
    assert p2.status_code == 201
    assert p2.json()["id_"] != p.json()["id_"]
    assert p2.json()["name"] != p.json()["name"]
    assert p2.json()["name"] == "copied_wf"

    p3 = api.get(base_workflows_url + p2.json()["name"], headers=auth_header)
    p4 = api.get(base_workflows_url + p.json()["name"], headers=auth_header)
    assert p3.status_code == p4.status_code == 200


def test_workflow_export(api: TestClient, auth_header: dict):
    with open('testing/util/workflow.json') as fp:
        wf_json = json.load(fp)
    p = api.post(base_workflows_url, headers=auth_header, data=json.dumps(wf_json))
    assert p.status_code == 201

    wf_name = wf_json["name"]

    p2 = api.get(base_workflows_url + wf_name, headers=auth_header, params={"mode": "export"})
    assert p2.status_code == 200


def test_workflow_upload_read(api: TestClient, auth_header: dict):
    auth_header.pop("content-type")
    x = open('testing/util/workflow.json', 'rb')
    files = {"file": x}
    p = api.post(base_workflows_url + "upload", headers=auth_header, files=files)

    assert p.status_code == 201
    x.close()


def test_rud_workflow_dne(api: TestClient, auth_header: dict):
    with open('testing/util/workflow.json') as fp:
        workflow_json = json.load(fp)

    p = api.get(base_workflows_url + "404", headers=auth_header, data=json.dumps(workflow_json))
    assert p.status_code == 404

    p = api.put(base_workflows_url + "404", headers=auth_header, data=json.dumps(workflow_json))
    assert p.status_code == 404

    p = api.delete(base_workflows_url + "404", headers=auth_header)
    assert p.status_code == 404
