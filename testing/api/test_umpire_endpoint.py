import json
import logging

import yaml
from starlette.testclient import TestClient

from testing.api.helpers import assert_crud_resource

logger = logging.getLogger(__name__)

base_umpire_url = "/walkoff/api/umpire"


def test_list_all_files(api: TestClient, auth_header: dict):
    list_url = base_umpire_url + f"/files/basics/1.0.0"
    print(list_url)
    p = api.get(list_url, headers=auth_header)
    assert p.status_code == 200

