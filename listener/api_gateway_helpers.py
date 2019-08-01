import requests, json

from common import helpers
from common.config import config

url = "https://127.0.0.1:8080/api"
def get_walkoff_auth_header(session, token=None, timeout=5*60):
    # url = config.API_GATEWAY_URI.rstrip('/') + '/api'
    if token is None:
        resp = session.post(url + "/auth", json={"username": config.WALKOFF_USERNAME,"password": config.WALKOFF_PASSWORD}, timeout=timeout, verify=False)
        resp_json = resp.json()
        token = resp_json["refresh_token"]

    headers = {"Authorization": f"Bearer {token}"}
    resp = session.post(url + "/auth/refresh", headers=headers, timeout=timeout, verify=False)
    resp_json = resp.json()
    access_token = resp_json["access_token"]

    return {"Authorization": f"Bearer {access_token}"}, token

def get_workflow(s, workflow_id):
    # url = f"{config.API_GATEWAY_URI}/api/workflows/{workflow_id}"
    headers, token = get_walkoff_auth_header(s)
    headers["content-type"] = "application/json"

    r = s.get(url + "/workflows/" + workflow_id, headers=headers, verify=False)
    return r

def get_buckets(s):
    # url = f"{config.API_GATEWAY_URI}/api/buckets"
    headers, token = get_walkoff_auth_header(s)
    headers["content-type"] = "application/json"

    r = s.get(url + "/buckets", headers=headers, verify=False)
    return r

def execute_workflow(s, id):
    headers, token = get_walkoff_auth_header(s)
    headers["content-type"] = "application/json"
    params = {"workflow_id": id}
    r = s.post(url + "/workflowqueue", data=json.dumps(params), headers=headers, verify=False)
    return r