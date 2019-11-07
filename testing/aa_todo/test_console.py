import json
import logging

import yaml
from starlette.testclient import TestClient

from testing.api.helpers import assert_crud_resource

logger = logging.getLogger(__name__)

base_console_url = "/walkoff/api/streams/console/logger/"


def test_create_console_message(api: TestClient, auth_header: dict):
    wf_exec_id = "1234"
    data = {
        "message": "This is a test",
        "close": "Done"
    }
    p = api.post(base_console_url, headers=auth_header, params={"wf_exec_id": wf_exec_id}, data=json.loads(data))
    assert p.status_code == 200
    assert p.json() == data["message"]

