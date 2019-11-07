import json
from typing import Callable, Union

from copy import deepcopy
from http import HTTPStatus

import jsonpatch
from starlette.testclient import TestClient


def assert_json_subset(subset, superset):
    subset.pop("password", None)
    superset.pop("password", None)
    patches = jsonpatch.JsonPatch.from_diff(subset, superset)
    for patch in list(patches):
        assert patch['op'] == 'add'


def assert_crud_resource(api: TestClient, auth_header: dict, path: str, inputs: list, loader_func: Callable, *,
                         valid=True, delete=False):
    """
    Generic test routine, attempt to create a resource, assert that the relevant artifacts were (or not) created
    """

    for test_resource in inputs:
        resource_to_create = loader_func(test_resource["create"])
        p = api.post(f"{path}", headers=auth_header, data=json.dumps(resource_to_create))
        p_response = p.json()
        if valid:
            assert p.status_code in (HTTPStatus.CREATED, HTTPStatus.OK)
            assert_json_subset(resource_to_create, p_response)
        else:
            assert p.status_code in (HTTPStatus.BAD_REQUEST, HTTPStatus.UNPROCESSABLE_ENTITY, HTTPStatus.FORBIDDEN, HTTPStatus.NOT_FOUND)
            # ToDo: assert that the response is a problem - move problems to common

        resource_id = p_response.get("id_")
        g = api.get(f"{path}{resource_id}", headers=auth_header)
        g_response = g.json()
        if valid:
            assert g.status_code == HTTPStatus.OK
            assert_json_subset(resource_to_create, g_response)
        else:
            assert g.status_code == HTTPStatus.NOT_FOUND
            # ToDo: assert that the response is a problem - move problems to common

        update = test_resource.get("update")
        if update:
            resource_to_update = loader_func(update)
            if update["type"] == "put":
                u = api.put(f"{path}{resource_id}", headers=auth_header, data=json.dumps(resource_to_update))
                u_response = u.json()
                assert_json_subset(resource_to_update, u_response)
            elif update["type"] == "patch":
                u = api.patch(f"{path}{resource_id}", headers=auth_header, data=json.dumps(resource_to_update))
                u_response = u.json()
                patch = jsonpatch.JsonPatch.from_string(resource_to_update)
                baseline = patch.apply(resource_to_create)
                assert_json_subset(baseline, u_response)

        if delete:
            d = api.delete(f"{path}{resource_id}", headers=auth_header)
            assert d.status_code == HTTPStatus.OK
