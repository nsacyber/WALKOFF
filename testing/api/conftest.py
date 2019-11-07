import json
import pytest
import pathlib
import shutil
from starlette.testclient import TestClient
from distutils.dir_util import copy_tree

import api.server.app as app
from common.minio_helper import push_all_apps_to_minio, remove_all_apps_from_minio

path = pathlib.Path("./apps")
temp_path = pathlib.Path("./temp_apps")


def write_temp_to_apps():
    shutil.rmtree(path)
    for directory in temp_path.iterdir():
        if directory.is_dir():
            hold = directory.parts[1]
            shutil.copytree(str(directory), f"./apps/{hold}")


def write_app_to_temp():
    for directory in path.iterdir():
        if directory.is_dir():
            hold = directory.parts[1]
            copy_tree(directory, f"./temp_apps/{hold}")


@pytest.fixture
def api():
    app.mongo.erase_db()
    app.mongo.init_db()
    write_app_to_temp()
    push_all_apps_to_minio()
    yield TestClient(app.app)
    remove_all_apps_from_minio()
    write_temp_to_apps()
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
