import json
import logging
from http import HTTPStatus

import yaml
from starlette.testclient import TestClient

from common.workflow_types import workflow_load
from testing.api.helpers import assert_crud_resource

logger = logging.getLogger(__name__)

base_globals_url = "/walkoff/api/globals/"


def unauth_user_creation(api: TestClient, auth_header: dict):
    with open('testing/util/role.json') as fp:
        role_json = json.load(fp)
        api.post("/walkoff/api/roles/", headers=auth_header, data=json.dumps(role_json))

    with open('testing/util/user.json') as fp:
        user_json = json.load(fp)
        api.post("/walkoff/api/users/", headers=auth_header, data=json.dumps(user_json))

    data = {
        "username": "test",
        "password": "123"
    }
    p = api.post("/walkoff/api/auth/login", data=json.dumps(data))
    response = p.json()
    access_token = response["access_token"]
    headers = {"Authorization": "Bearer " + access_token}
    return headers


def test_globals_get_all(api: TestClient, auth_header: dict):
    p = api.get(base_globals_url, headers=auth_header)
    assert p.status_code == 200
    assert p.json() == []


def test_global_invalid(api: TestClient, auth_header: dict):
    """ Assert global without permissions is invalid """
    with open('testing/util/global.json') as fp:
        gv_json = json.load(fp)
    gv_json.pop("permissions")
    p = api.post(base_globals_url, headers=auth_header, data=json.dumps(gv_json))
    assert p.status_code == 422


def test_globals_create_read_delete(api: TestClient, auth_header: dict):
    with open('testing/util/global.json') as fp:
        gv_json = json.load(fp)
    p = api.post(base_globals_url, headers=auth_header, data=json.dumps(gv_json))
    assert p.status_code == 201

    # gv_name = gv_json["name"]
    # gv_id = gv_json["id_"]
    #
    # p2 = api.get(base_globals_url, headers=auth_header)
    # assert p2.status_code == 200
    # assert len(p2.json()) == 1
    #
    # p3 = api.get(base_globals_url + gv_name, headers=auth_header)
    # p4 = api.get(base_globals_url + gv_id, headers=auth_header)
    # assert p3.status_code == p4.status_code == 200
    # assert p3.json()["id_"] == gv_id
    # assert p4.json()["name"] == gv_name
    #
    # p5 = api.delete(base_globals_url + gv_name, headers=auth_header)
    # assert p5.status_code == 204
    # assert p5.json()
    #
    # p6 = api.get(base_globals_url, headers=auth_header)
    # assert p6.status_code == 200
    # assert len(p6.json()) == 0