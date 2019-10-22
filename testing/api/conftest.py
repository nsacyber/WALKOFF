import json
import pytest
from starlette.testclient import TestClient

import api.server.app as app


@pytest.fixture
def api():
    app.mongo.erase_db()
    app.mongo.init_db()
    yield TestClient(app.app)
    app.mongo.erase_db()
    app.mongo.init_db()
    # connect_to_redis_pool(config.REDIS_URI).flushall()


@pytest.fixture
def auth_header(api: TestClient):
    response = api.post("http://localhost/walkoff/api/auth/login",
                        data=json.dumps({"username": "admin", "password": "admin"}),
                        headers={'content-type': "application/json"})
    tokens = response.json()
    header = {"Authorization": f"Bearer {tokens['access_token']}",
              "content-type": "application/json"}
    return header


@pytest.fixture
def super_auth_header(api: TestClient):
    response = api.post("http://localhost/walkoff/api/auth/login",
                        data=json.dumps({"username": "super_admin", "password": "super_admin"}),
                        headers={'content-type': "application/json"})
    tokens = response.json()
    header = {"Authorization": f"Bearer {tokens['access_token']}",
              "content-type": "application/json"}
    return header


@pytest.fixture
def unauthorized_header(api: TestClient):
    response = api.post("http://localhost/walkoff/api/auth/login",
                        data=json.dumps({"username": "super_admin", "password": "super_admin"}),
                        headers={'content-type': "application/json"})
    tokens = response.json()
    auth_header = {"Authorization": f"Bearer {tokens['access_token']}",
              "content-type": "application/json"}

    with open('testing/util/limited_role.json') as fp:
        role_json = json.load(fp)
        api.post("http://localhost/walkoff/api/roles/", headers=auth_header, data=json.dumps(role_json))

    data2 = {
        "username": "unauth_user",
        "password": "123",
        "active": True,
        "roles": ["00000000-0000-9766-5f6f-705f726f6c65"]
    }
    api.post("http://localhost/walkoff/api/users/", headers=auth_header, data=json.dumps(data2))

    response = api.post("http://localhost/walkoff/api/auth/login",
                        data=json.dumps({"username": data2["username"], "password": data2["password"]}),
                        headers={'content-type': "application/json"})
    tokens = response.json()
    header = {"Authorization": f"Bearer {tokens['access_token']}",
              "content-type": "application/json"}
    return header
