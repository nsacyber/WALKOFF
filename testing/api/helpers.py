import json
from typing import Callable

from copy import deepcopy
from http import HTTPStatus

import jsonpatch
from starlette.testclient import TestClient


def assert_json_subset(subset, superset):
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
        if valid:
            assert p.status_code == HTTPStatus.CREATED
            assert_json_subset(resource_to_create, p.json())
        else:
            assert p.status_code == HTTPStatus.BAD_REQUEST
            # ToDo: assert that the response is a problem - move problems to common

        resource_id = p.json().get("id_")
        g = api.get(f"{path}/{resource_id}", headers=auth_header)
        if valid:
            assert g.status_code == HTTPStatus.OK
            assert_json_subset(resource_to_create, g.json())
        else:
            assert g.status_code == HTTPStatus.NOT_FOUND
            # ToDo: assert that the response is a problem - move problems to common

        update = test_resource.get("update")
        if update:
            resource_to_update = loader_func(update)
            if update["type"] == "put":
                u = api.put(f"{path}/{resource_id}", headers=auth_header, data=json.dumps(resource_to_update))
                assert_json_subset(resource_to_update, u.json())
            elif update["type"] == "patch":
                u = api.patch(f"{path}/{resource_id}", headers=auth_header, data=json.dumps(resource_to_update))
                patch = jsonpatch.JsonPatch.from_string(resource_to_update)
                baseline = patch.apply(resource_to_create)
                assert_json_subset(baseline, u.json())

        if delete:
            d = api.delete(f"{path}/{resource_id}", headers=auth_header)
            assert d.status_code == HTTPStatus.NO_CONTENT
