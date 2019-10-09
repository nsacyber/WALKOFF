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
