import json
import logging

import yaml
from starlette.testclient import TestClient

from testing.api.helpers import assert_crud_resource

logger = logging.getLogger(__name__)

base_dashboards_url = "/walkoff/api/dashboards/"


def test_sanity_check(api: TestClient, auth_header: dict):
    p = api.get(base_dashboards_url, headers=auth_header)
    assert p.status_code == 200
    assert p.json() == []


def test_create_dashboard(api: TestClient, auth_header: dict):
    assert True


def test_unauth_create_dashboard(api: TestClient, unauthorized_header: dict):
    assert True


def test_create_read_delete_dashboard(api: TestClient, auth_header: dict):
    assert True


def test_unauth_create_read_delete_dashboard(api: TestClient, unauthorized_header: dict):
    assert True
