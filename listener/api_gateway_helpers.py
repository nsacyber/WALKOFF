import requests, json

from common.config import config

from os import environ
from os.path import join, sep

def get_walkoff_auth_header(session, token=None, timeout=5*60):
    url = config.API_GATEWAY_URI.rstrip('/') + '/walkoff/api'
    if token is None:
        resp = session.post(url + "/auth", json={"username": config.WALKOFF_USERNAME, "password": config.get_from_file(config.INTERNAL_KEY_PATH)}, timeout=timeout, verify=False)
        resp_json = resp.json()
        token = resp_json["refresh_token"]

    headers = {"Authorization": f"Bearer {token}"}
    resp = session.post(url + "/auth/refresh", headers=headers, timeout=timeout, verify=False)
    resp_json = resp.json()
    access_token = resp_json["access_token"]

    return {"Authorization": f"Bearer {access_token}"}, token

def get_workflow(s, workflow_id):
    url = f"{config.API_GATEWAY_URI}/walkoff/api/workflows/{workflow_id}"
    headers, token = get_walkoff_auth_header(s)
    headers["content-type"] = "application/json"

    r = s.get(url + "/workflows/" + workflow_id, headers=headers, verify=False)
    return r

def get_buckets(s):
    url = f"{config.API_GATEWAY_URI}/walkoff/api/buckets"
    headers, token = get_walkoff_auth_header(s)
    headers["content-type"] = "application/json"

    r = s.get(url, headers=headers, verify=False)
    return r

def execute_workflow(s, id):
    url = f"{config.API_GATEWAY_URI}/walkoff/api"
    headers, token = get_walkoff_auth_header(s)
    headers["content-type"] = "application/json"
    params = {"workflow_id": id}
    r = s.post(url + "/workflowqueue", data=json.dumps(params), headers=headers, verify=False)
    return r
