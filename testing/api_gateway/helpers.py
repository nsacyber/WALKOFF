import json

from copy import deepcopy
from http import HTTPStatus

import jsonpatch
from flask.testing import FlaskClient


def assert_json_subset(subset, superset):
    patches = jsonpatch.JsonPatch.from_diff(subset, superset)
    for patch in list(patches):
        assert patch['op'] == 'add'


def assert_crud_resource(api_gateway: FlaskClient, auth_header, path, inputs, loader_func, valid=True, delete=False):
    """
    Generic test routine, attempt to create a resource, assert that the relevant artifacts were (or not) created
    """

    for test_resource in inputs:
        resource_to_create = loader_func(test_resource["create"])
        p = api_gateway.post(f"{path}", headers=auth_header, data=json.dumps(resource_to_create))
        if valid:
            assert p.status_code == HTTPStatus.CREATED
            assert_json_subset(resource_to_create, p.get_json())
        else:
            assert p.status_code == HTTPStatus.BAD_REQUEST
            # ToDo: assert that the response is a problem - move problems to common

        resource_id = p.get_json().get("id_")
        g = api_gateway.get(f"{path}/{resource_id}", headers=auth_header)
        if valid:
            assert g.status_code == HTTPStatus.OK
            assert_json_subset(resource_to_create, g.get_json())
        else:
            assert g.status_code == HTTPStatus.NOT_FOUND
            # ToDo: assert that the response is a problem - move problems to common

        update = test_resource.get("update")
        if update:
            resource_to_update = loader_func(update)
            if update["type"] == "put":
                u = api_gateway.put(f"{path}/{resource_id}", headers=auth_header, data=json.dumps(resource_to_update))
                assert_json_subset(resource_to_update, u.get_json())
            elif update["type"] == "patch":
                u = api_gateway.patch(f"{path}/{resource_id}", headers=auth_header, data=json.dumps(resource_to_update))
                patch = jsonpatch.JsonPatch.from_string(resource_to_update)
                baseline = patch.apply(resource_to_create)
                assert_json_subset(baseline, u.get_json())

        if delete:
            d = api_gateway.delete(f"{path}/{resource_id}", headers=auth_header)
            assert d.status_code == HTTPStatus.NO_CONTENT
