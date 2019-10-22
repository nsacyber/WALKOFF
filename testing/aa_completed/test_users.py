import json
import logging
from http import HTTPStatus

import yaml
from starlette.testclient import TestClient

from api.server.db.user_init import DefaultUserUUID, DefaultRoleUUID
from testing.api.helpers import assert_crud_resource
from testing.aa_temp.test_auth import test_super_admin_login

logger = logging.getLogger(__name__)

base_users_url = "/walkoff/api/users/"
base_auth_url = "/walkoff/api/auth/"


def test_read_all_users(api: TestClient, auth_header: dict):
    """ Assert that there are only two default users: Admin and Super_Admin"""
    p = api.get(base_users_url, headers=auth_header)
    p_response = p.json()
    assert p.status_code == 200
    assert len(p_response) == 2
    assert p_response[0]["username"] == "admin"
    assert p_response[1]["username"] == "super_admin"

    return p_response


def test_read_user_admin(api: TestClient, auth_header: dict):
    """ Assert the accuracy of reading admin value """
    p = api.get(base_users_url + "admin", headers=auth_header)
    p_response = p.json()
    assert p.status_code == 200
    assert p_response["username"] == "admin"
    assert p_response["id_"] == str(DefaultUserUUID.ADMIN.value)
    assert p_response["roles"][0] == str(DefaultRoleUUID.ADMIN.value)


def test_read_user_super_admin(api: TestClient, auth_header: dict):
    """ Assert the accuracy of reading super_admin value """
    p = api.get(base_users_url + "super_admin", headers=auth_header)
    p_response = p.json()
    assert p.status_code == 200
    assert p_response["username"] == "super_admin"
    assert p_response["id_"] == str(DefaultUserUUID.SUPER_ADMIN.value)
    assert p_response["roles"][0] == str(DefaultRoleUUID.SUPER_ADMIN.value)


def test_read_user_internal_user(api: TestClient, auth_header: dict):
    """ Assert that one cannot read the WALKOFF internal user"""
    p = api.get(base_users_url + "internal_user", headers=auth_header)
    assert p.status_code == 403


def test_read_nonexistent_user(api: TestClient, auth_header: dict):
    """ Assert that one cannot read the WALKOFF internal user"""
    p = api.get(base_users_url + "doesnotexist", headers=auth_header)
    assert p.status_code == HTTPStatus.NOT_FOUND


def test_delete_self(api: TestClient, auth_header: dict):
    """ Assert that one cannot delete the currently logged-in user """
    p = api.delete(base_users_url + "admin", headers=auth_header)
    assert p.status_code == 403


def test_delete_admin(api: TestClient):
    """ Assert that super_admin can delete admin """
    tokens = test_super_admin_login(api)
    access_token = tokens["access_token"]
    headers = {"Authorization": "Bearer " + access_token}
    p = api.delete(base_users_url + "admin", headers=headers)
    assert p.status_code == 200
    assert p.json() is True


def test_delete_super_admin(api: TestClient, auth_header: dict):
    """ Assert that super_admin cannot be deleted """
    p = api.delete(base_users_url + "super_admin", headers=auth_header)
    assert p.status_code == 403


def test_delete_internal_user(api: TestClient):
    """ Assert that internal_user cannot be deleted """
    tokens = test_super_admin_login(api)
    access_token = tokens["access_token"]
    headers = {"Authorization": "Bearer " + access_token}
    p = api.delete(base_users_url + "internal_user", headers=headers)
    assert p.status_code == 403


def test_create_new_admin(api: TestClient, auth_header: dict):
    """ Assert that a new admin can be created """
    inputs = [
        {
            "create": f"""
            username: new_admin
            password: new_admin
            active: {True}
            roles: [
                {str(DefaultRoleUUID.ADMIN.value)}
            ]
            """
        }
    ]
    assert_crud_resource(api, auth_header, base_users_url, inputs, yaml.full_load)
    p = api.get(base_users_url, headers=auth_header)
    p_response = p.json()
    assert p.status_code == 200
    assert len(p_response) == 3


def test_create_workflow_developer(api: TestClient, auth_header: dict):
    """ Assert that a workflow_developer user can be created """
    inputs = [
        {
            "create": f"""
            username: workflow_dev
            password: workflow_dev
            roles: [
                {str(DefaultRoleUUID.WF_DEV.value)}
            ]
            active: {True}
            """
        }
    ]
    assert_crud_resource(api, auth_header, base_users_url, inputs, yaml.full_load)


def test_create_workflow_operator(api: TestClient, auth_header: dict):
    """ Assert that a workflow_operator user can be created """
    inputs = [
        {
            "create": f"""
            username: workflow_op
            password: workflow_op
            roles: [
                {str(DefaultRoleUUID.WF_OP.value)}
            ]
            active: {True}
            """
        }
    ]
    assert_crud_resource(api, auth_header, base_users_url, inputs, yaml.full_load)


def test_create_app_developer(api: TestClient, auth_header: dict):
    """ Assert that a app_developer user can be created """
    inputs = [
        {
            "create": f"""
            username: app_dev
            password: app_dev
            roles: [
                {str(DefaultRoleUUID.APP_DEV.value)}
            ]
            active: {True}
            """
        }
    ]
    assert_crud_resource(api, auth_header, base_users_url, inputs, yaml.full_load)


def test_create_super_admin(api: TestClient, auth_header: dict):
    """ Assert that a new super_admin user CANNOT be created """
    inputs = [
        {
            "create": f"""
            username: super_admin2
            password: super_admin2
            roles: [
                {str(DefaultRoleUUID.SUPER_ADMIN.value)}
            ]
            active: {True}
            """
        }
    ]
    assert_crud_resource(api, auth_header, base_users_url, inputs, yaml.full_load, valid=False)


def test_create_internal_user(api: TestClient, auth_header: dict):
    """ Assert that a new internal user CANNOT be created """
    inputs = [
        {
            "create": f"""
            username: internal_user2
            password: internal_user2
            roles: [
                {str(DefaultRoleUUID.INTERNAL_USER.value)}
            ]
            active: {True}
            """
        }
    ]
    assert_crud_resource(api, auth_header, base_users_url, inputs, yaml.full_load, valid=False)


def test_update_admin(api: TestClient):
    """ Change admin password and login with new password """
    tokens = test_super_admin_login(api)
    access_token = tokens["access_token"]
    headers = {"Authorization": "Bearer " + access_token}

    data = {
        # "id_": str(DefaultUserUUID.ADMIN.value),
        "username": "admin",
        "new_username": "new_admin",
        "old_password": "admin",
        "new_password": "new_password",
        "active": True,
        "roles": [str(DefaultRoleUUID.ADMIN.value)]
        }
    p = api.put(base_users_url + "admin", headers=headers, data=json.dumps(data))
    assert p.status_code == 200


def test_invalid_update_admin(api: TestClient):
    """ Change admin password and login with new password """
    tokens = test_super_admin_login(api)
    access_token = tokens["access_token"]
    headers = {"Authorization": "Bearer " + access_token}

    data = {
        # "id_": str(DefaultUserUUID.ADMIN.value),
        "username": "invalid_name",
        "new_username": "new_admin",
        "old_password": "invalid_password",
        "new_password": "new_password",
        "active": True,
        "roles": [str(DefaultRoleUUID.ADMIN.value)]
        }
    p = api.put(base_users_url + "admin", headers=headers, data=json.dumps(data))
    assert p.status_code == 403


def test_update_super_admin_password_and_username(api: TestClient):
    """ Change admin password and login with new password """
    tokens = test_super_admin_login(api)
    access_token = tokens["access_token"]
    headers = {"Authorization": "Bearer " + access_token}

    data = {
        # "id_": str(DefaultUserUUID.ADMIN.value),
        "username": "super_admin",
        "new_username": "new_super_admin",
        "old_password": "super_admin",
        "new_password": "new_super_password",
        "active": True,
        "roles": [str(DefaultRoleUUID.ADMIN.value)]
        }
    p = api.put(base_users_url + "super_admin", headers=headers, data=json.dumps(data))
    assert p.status_code == 200


def test_invalid_update_super_admin_password_and_username(api: TestClient):
    """ Change admin password and login with new password """
    tokens = test_super_admin_login(api)
    access_token = tokens["access_token"]
    headers = {"Authorization": "Bearer " + access_token}

    data = {
        # "id_": str(DefaultUserUUID.ADMIN.value),
        "username": "invalid_username",
        "new_username": "new_super_admin",
        "old_password": "invalid_password",
        "new_password": "new_super_password",
        "active": True,
        "roles": [str(DefaultRoleUUID.ADMIN.value)]
        }
    p = api.put(base_users_url + "super_admin", headers=headers, data=json.dumps(data))
    assert p.status_code == 403


def test_invalid_update_super_admin_password_and_username2(api: TestClient, auth_header: dict):
    """ Assert unable to change super_admin data when logged in as admin """
    data = {
        # "id_": str(DefaultUserUUID.ADMIN.value),
        "username": "super_admin",
        "new_username": "new_super_admin",
        "old_password": "super_admin",
        "new_password": "new_super_password",
        "active": True,
        "roles": [str(DefaultRoleUUID.ADMIN.value)]
        }
    p = api.put(base_users_url + "super_admin", headers=auth_header, data=json.dumps(data))
    assert p.status_code == 403
