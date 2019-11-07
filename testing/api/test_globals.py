import json
import logging

from starlette.testclient import TestClient

logger = logging.getLogger(__name__)

base_globals_url = "/walkoff/api/globals/"


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

    gv_id = gv_json["id_"]

    p2 = api.get(base_globals_url, headers=auth_header)
    assert p2.status_code == 200
    assert len(p2.json()) == 1

    p4 = api.get(base_globals_url + gv_id, headers=auth_header)
    assert p4.status_code == 200

    p5 = api.delete(base_globals_url + gv_id, headers=auth_header)
    assert p5.status_code == 200
    assert p5.json()

    p6 = api.get(base_globals_url, headers=auth_header)
    assert p6.status_code == 200
    assert len(p6.json()) == 0


def test_globals_nonexistent(api: TestClient, auth_header: dict):
    with open('testing/util/global.json') as fp:
        gv_json = json.load(fp)

    nonexistent_global_uuid = "00000000-0073-6164-6d69-6e5f726f6c65"
    p = api.get(base_globals_url + nonexistent_global_uuid, headers=auth_header)
    assert p.status_code == 404

    p = api.delete(base_globals_url + nonexistent_global_uuid, headers=auth_header)
    assert p.status_code == 404

    p = api.put(base_globals_url + nonexistent_global_uuid, headers=auth_header, data=json.dumps(gv_json))
    assert p.status_code == 404


def test_global_unauth(api: TestClient, unauthorized_header: dict, auth_header: dict):
    with open('testing/util/global.json') as fp:
        gv_json = json.load(fp)
    p = api.post(base_globals_url, headers=unauthorized_header, data=json.dumps(gv_json))

    with open('testing/util/global.json') as fp:
        gv_json2 = json.load(fp)
        # authorized post
        api.post(base_globals_url, headers=auth_header, data=json.dumps(gv_json2))

    p2 = api.get(base_globals_url + gv_json["id_"], headers=unauthorized_header)
    p3 = api.delete(base_globals_url + gv_json["id_"], headers=unauthorized_header)
    p4 = api.put(base_globals_url + gv_json["id_"], headers=unauthorized_header, data=json.dumps(gv_json))

    assert p.status_code == p2.status_code == p3.status_code == p4.status_code == 403