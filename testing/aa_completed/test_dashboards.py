import json
import logging

from starlette.testclient import TestClient

logger = logging.getLogger(__name__)

base_dashboards_url = "/walkoff/api/dashboards/"


def create_and_execute_workflow(api: TestClient, auth_header: dict):
    with open('testing/util/dashboard_workflow.json') as fp:
        wf_json = json.load(fp)
    p = api.post("/walkoff/api/workflows/", headers=auth_header, data=json.dumps(wf_json))

    # todo: check execute workflow
    with open('testing/util/dashboard_workflowqueue.json') as fp:
        wfqueue_json = json.load(fp)
        api.post("/walkoff/api/workflows/", headers=auth_header, data=json.dumps(wfqueue_json))

    return p.json()


def test_sanity_check(api: TestClient, auth_header: dict):
    p = api.get(base_dashboards_url, headers=auth_header)
    assert p.status_code == 200
    assert p.json() == []


def test_get_nonexistent_dashboard(api: TestClient, auth_header: dict):
    p = api.get(base_dashboards_url + "404", headers=auth_header)
    assert p.status_code == 404


def test_unauth_get_nonexistent_dashboard(api: TestClient, unauthorized_header: dict):
    p = api.get(base_dashboards_url + "404", headers=unauthorized_header)
    assert p.status_code == 403


def test_create_and_get_dashboard(api: TestClient, auth_header: dict):
    create_and_execute_workflow(api, auth_header)

    with open('testing/util/dashboard.json') as fp:
        dashboard_json = json.load(fp)
    p = api.post(base_dashboards_url, headers=auth_header, data=json.dumps(dashboard_json))
    assert p.status_code == 201
    dashboard_id = p.json()["id_"]

    p = api.get(base_dashboards_url, headers=auth_header)
    assert p.status_code == 200
    assert len(p.json()) == 1

    p = api.get(base_dashboards_url + dashboard_id, headers=auth_header)
    assert p.status_code == 200


def test_unauth_create_dashboard(api: TestClient, unauthorized_header: dict):
    with open('testing/util/dashboard.json') as fp:
        dashboard_json = json.load(fp)
    p = api.post(base_dashboards_url, headers=unauthorized_header, data=json.dumps(dashboard_json))
    assert p.status_code == 403


def test_delete_nonexistent_dashboard(api: TestClient, auth_header: dict):
    p = api.delete(base_dashboards_url + "404", headers=auth_header)
    assert p.status_code == 404


def test_unauth_delete_nonexistent_dashboard(api: TestClient, unauthorized_header: dict):
    p = api.delete(base_dashboards_url + "404", headers=unauthorized_header)
    assert p.status_code == 403


def test_delete_dashboard(api: TestClient, auth_header: dict):
    create_and_execute_workflow(api, auth_header)
    with open('testing/util/dashboard.json') as fp:
        dashboard_json = json.load(fp)
    p = api.post(base_dashboards_url, headers=auth_header, data=json.dumps(dashboard_json))
    assert p.status_code == 201
    dashboard_id = p.json()["id_"]

    p = api.get(base_dashboards_url, headers=auth_header)
    assert len(p.json()) == 1

    p = api.delete(base_dashboards_url + dashboard_id, headers=auth_header)
    assert p.status_code == 200
    assert p.json()

    p = api.get(base_dashboards_url, headers=auth_header)
    assert p.json() == []


def test_unauth_delete_dashboard(api: TestClient, auth_header: dict, unauthorized_header: dict):
    create_and_execute_workflow(api, auth_header)
    with open('testing/util/dashboard.json') as fp:
        dashboard_json = json.load(fp)
    p = api.post(base_dashboards_url, headers=auth_header, data=json.dumps(dashboard_json))
    assert p.status_code == 201
    dashboard_id = p.json()["id_"]

    p = api.delete(base_dashboards_url + dashboard_id, headers=unauthorized_header)
    assert p.status_code == 403


def test_update_nonexistent_dashboard(api: TestClient, auth_header: dict):
    with open('testing/util/dashboard.json') as fp:
        dashboard_json = json.load(fp)
    p = api.put(base_dashboards_url + "404", headers=auth_header, data=json.dumps(dashboard_json))
    assert p.status_code == 404


def test_unauth_update_nonexistent_dashboard(api: TestClient, unauthorized_header: dict):
    p = api.put(base_dashboards_url + "404", headers=unauthorized_header)
    assert p.status_code == 403


def test_update_dashboard(api: TestClient, auth_header: dict):
    create_and_execute_workflow(api, auth_header)

    with open('testing/util/dashboard.json') as fp:
        dashboard_json = json.load(fp)
    p = api.post(base_dashboards_url, headers=auth_header, data=json.dumps(dashboard_json))
    assert p.status_code == 201
    dashboard_id = p.json()["id_"]

    dashboard_json.update({"name": "updated_dashboard_name"})
    p = api.put(base_dashboards_url + dashboard_id, headers=auth_header, data=json.dumps(dashboard_json))
    assert p.status_code == 200

    p = api.get(base_dashboards_url + dashboard_id, headers=auth_header)
    assert p.status_code == 200
    assert p.json()["name"] == "updated_dashboard_name"


def test_unauth_update_dashboard(api: TestClient, auth_header: dict, unauthorized_header: dict):
    create_and_execute_workflow(api, auth_header)

    with open('testing/util/dashboard.json') as fp:
        dashboard_json = json.load(fp)
    p = api.post(base_dashboards_url, headers=auth_header, data=json.dumps(dashboard_json))
    assert p.status_code == 201
    dashboard_id = p.json()["id_"]

    updated_dashboard_json = dashboard_json.update({"name": "updated_dashboard_name"})
    p = api.put(base_dashboards_url + dashboard_id, headers=unauthorized_header, data=json.dumps(updated_dashboard_json))
    assert p.status_code == 403
