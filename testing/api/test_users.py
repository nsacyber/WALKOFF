import json
import logging
from http import HTTPStatus

import yaml
from starlette.testclient import TestClient

from api.server.db.user_init import DefaultUserUUID
from testing.api.helpers import assert_crud_resource

logger = logging.getLogger(__name__)

base_auth_url = "/walkoff/api/users/"


def test_read_all_users(api: TestClient, auth_header: dict):
    p = api.get(base_auth_url, headers=auth_header)
    p_response = p.json()
    assert p.status_code == 200
    assert len(p_response) == 2
    assert p_response[0]["username"] == "admin"
    assert p_response[1]["username"] == "super_admin"

    return p_response


def test_read_user_admin(api: TestClient, auth_header: dict):
    p = api.get(base_auth_url + "admin", headers=auth_header)
    p_response = p.json()
    assert p.status_code == 200
    assert p_response["username"] == "admin"
    assert p_response["id_"] == DefaultUserUUID.ADMIN.value


def test_read_user_super_admin(api: TestClient, auth_header: dict):
    p = api.get(base_auth_url + "super_admin", headers=auth_header)
    p_response = p.json()
    assert p.status_code == 200
    assert p_response["username"] == "super_admin"
    assert p_response["id_"] == DefaultUserUUID.SUPER_ADMIN.value


def test_read_user_internal_user(api: TestClient, auth_header: dict):
    p = api.get(base_auth_url + "internal_user", headers=auth_header)
    assert p.status_code == 403


def test_delete_admin(api: TestClient, auth_header: dict):
    p = api.delete(base_auth_url + "admin", headers=auth_header)