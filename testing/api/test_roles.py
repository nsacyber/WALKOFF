import json
import logging
from http import HTTPStatus

import yaml
from starlette.testclient import TestClient


logger = logging.getLogger(__name__)

base_roles_url = "/walkoff/api/roles/"


def test_read_all_roles(api: TestClient, auth_header: dict):
    """ Assert that there are only two default users: Admin and Super_Admin"""
    p = api.get(base_roles_url, headers=auth_header)
    p_response = p.json()
    assert p.status_code == 200
    assert len(p_response) == 5
    assert p_response[0]["name"] == "admin"
    assert p_response[1]["name"] == "workflow_operator"
    assert p_response[2]["name"] == "super_admin"
    assert p_response[3]["name"] == "workflow_developer"
    assert p_response[4]["name"] == "app_developer"

    return p_response


def test_read_role_internal_user(api: TestClient, auth_header: dict):
    """ Assert the accuracy of reading admin value """
    p = api.get(base_roles_url + "internal_user", headers=auth_header)
    assert p.status_code == 403


def test_read_default_roles(api: TestClient, auth_header: dict):
    """ Assert the accuracy of reading admin value """
    elems = ["super_admin", "admin", "workflow_developer", "workflow_operator", "app_developer"]

    for elem in elems:
        p = api.get(base_roles_url + elem, headers=auth_header)
        p_response = p.json()
        assert p.status_code == 200
        assert p_response["name"] == elem


def test_delete_default_roles(api: TestClient, auth_header: dict):
    elems = ["internal_user", "super_admin", "admin", "workflow_developer", "workflow_operator", "app_developer"]

    for elem in elems:
        p = api.delete(base_roles_url + elem, headers=auth_header)
        assert p.status_code == 403


def test_update_default_roles(api: TestClient, auth_header: dict):
    elems = ["internal_user", "super_admin", "admin", "workflow_developer", "workflow_operator", "app_developer"]

    with open('testing/util/role.json') as fp:
        role_json = json.load(fp)

    for elem in elems:
        p = api.put(base_roles_url + elem, headers=auth_header, data=json.dumps(role_json))
        assert p.status_code == 403


def test_crud_new_role(api: TestClient, auth_header: dict):
    with open('testing/util/role.json') as fp:
        role_json = json.load(fp)
        role_id = role_json["id_"]

    p = api.post(base_roles_url, headers=auth_header, data=json.dumps(role_json))
    assert p.status_code == 201

    p = api.get(base_roles_url + "test_role", headers=auth_header, data=json.dumps(role_json))
    assert p.status_code == 200
    assert p.json()["id_"] == role_id

    role_json["name"] = "updated_name"
    p = api.put(base_roles_url + "test_role", headers=auth_header, data=json.dumps(role_json))
    assert p.status_code == 200
    assert p.json()["name"] == "updated_name"

    p = api.delete(base_roles_url + "updated_name", headers=auth_header)
    assert p.status_code == 200


def test_cred_role_dne(api: TestClient, auth_header: dict):
    with open('testing/util/role.json') as fp:
        role_json = json.load(fp)

    p = api.get(base_roles_url + "404", headers=auth_header, data=json.dumps(role_json))
    assert p.status_code == 404

    p = api.put(base_roles_url + "404", headers=auth_header, data=json.dumps(role_json))
    assert p.status_code == 404

    p = api.delete(base_roles_url + "404", headers=auth_header)
    assert p.status_code == 404


def test_unauth_cred_role_dne(api: TestClient, unauthorized_header: dict):
    with open('testing/util/role.json') as fp:
        role_json = json.load(fp)

    p = api.get(base_roles_url + "404", headers=unauthorized_header, data=json.dumps(role_json))
    assert p.status_code == 403

    p = api.put(base_roles_url + "404", headers=unauthorized_header, data=json.dumps(role_json))
    assert p.status_code == 403

    p = api.delete(base_roles_url + "404", headers=unauthorized_header)
    assert p.status_code == 403