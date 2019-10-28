import json
import logging

import yaml
from starlette.testclient import TestClient

from testing.api.helpers import assert_crud_resource

logger = logging.getLogger(__name__)

base_umpire_url = "/walkoff/api/umpire"


def test_list_all_files(api: TestClient, auth_header: dict):
    list_url = base_umpire_url + f"/files/basics/1.0.0"
    p = api.get(list_url, headers=auth_header)
    assert p.status_code == 200


def test_list_file_missing(api: TestClient, auth_header: dict):
    list_url = base_umpire_url + f"/files/not_a_real_app/1.0.0"
    p = api.get(list_url, headers=auth_header)
    assert p.status_code == 200
    assert p.content == b'[]'


def test_get_file_contents(api: TestClient, auth_header: dict):
    list_url = base_umpire_url + f"/file/basics/1.0.0?file_path=src/app.py"
    p = api.get(list_url, headers=auth_header)
    assert p.status_code == 200


def test_get_file_contents_fail(api: TestClient, auth_header: dict):
    list_url = base_umpire_url + f"/file/not_a_real_app/1.0.0?file_path=src/notpython.py"
    p = api.get(list_url, headers=auth_header)
    print(p)
    assert p.status_code == 200
    assert p.content == b'"No Such Key"'
    # assert p.content == "Couldn't get file contents from specified application/version number."


def test_build_image(api: TestClient, auth_header: dict):
    list_url = base_umpire_url + f"/build/basics/1.0.0"
    p = api.post(list_url, headers=auth_header)
    assert p.status_code == 200


def test_save_file(api: TestClient, auth_header: dict):
    list_url = base_umpire_url + f"/save/basics/1.0.0"
    p = api.post(list_url, headers=auth_header)
    assert p.status_code == 200
    assert p.content == b'"Successful Update to Local Repo"'


def test_save_file_failed(api: TestClient, auth_header: dict):
    list_url = base_umpire_url + f"/save/not_a_real_app/1.0.0"
    p = api.post(list_url, headers=auth_header)
    assert p.status_code == 200
    assert p.content == b'"Failed"'
