import json
import logging
from http import HTTPStatus

import yaml
from starlette.testclient import TestClient


logger = logging.getLogger(__name__)

base_settings_url = "/walkoff/api/settings/"


def test_get_settings(api: TestClient, auth_header: dict):
    p = api.get(base_settings_url, headers=auth_header)
    assert p.status_code == 200


def test_update_settings(api: TestClient, auth_header: dict):
    p = api.get(base_settings_url, headers=auth_header)
    settings_id = p.json()["id_"]

    data = {
      "id_": settings_id,
      "access_token_life_mins": 20,
      "refresh_token_life_days": 30
    }

    p = api.put(base_settings_url, headers=auth_header, data=json.dumps(data))
    assert p.status_code == 200

    p = api.get(base_settings_url, headers=auth_header)
    assert p.json()["access_token_life_mins"] == 20
    assert p.json()["refresh_token_life_days"] == 30


def test_update_invalid_settings(api: TestClient, auth_header: dict):
    api.get(base_settings_url, headers=auth_header)

    data = {
      "access_token_life_mins": 15,
      "refresh_token_life_days": 15
    }

    p = api.put(base_settings_url, headers=auth_header, data=json.dumps(data))
    assert p.status_code == 422


def test_get_invalid_permission(api: TestClient, unauthorized_header: dict):
    p = api.get(base_settings_url, headers=unauthorized_header)
    assert p.status_code == 403


def test_update_invalid_permission(api: TestClient, auth_header: dict, unauthorized_header: dict):
    p = api.get(base_settings_url, headers=auth_header)
    settings_id = p.json()["id_"]

    data = {
      "id_": settings_id,
      "access_token_life_mins": 15,
      "refresh_token_life_days": 15
    }

    p = api.put(base_settings_url, headers=unauthorized_header, data=json.dumps(data))
    assert p.status_code == 403