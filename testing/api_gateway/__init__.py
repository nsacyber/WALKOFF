import logging
import json
from copy import deepcopy
from http import HTTPStatus
from functools import partial

import jsonpatch
from flask.testing import FlaskClient

logger = logging.getLogger(__name__)


def strip_known_extra_values(o):
    """
    Recursively removes values the backend is known to add for the purpose of testing sameness.
    This should only be used in testing with known inputs, as parameter or return values that
    contain these 'reserved' words will be discarded
    """
    for key in list(o):
        if o[key] in (None, {}, [], ""):
            o.pop(key)
        elif isinstance(o[key], int) and key == "priority":
            o.pop("priority")
        elif isinstance(o[key], str) and key == "id_":
            o.pop("id_")
        elif isinstance(o[key], bool) and key == "is_valid":
            o.pop("is_valid")
        elif isinstance(o[key], dict):
            strip_known_extra_values(o[key])
        elif isinstance(o[key], list):
            if key == "errors":
                o.pop("errors")
            else:
                for ele in o[key]:
                    if isinstance(ele, dict):
                        strip_known_extra_values(ele)


def assert_request_equals_response(request, response):
    """Verify that once known extra values are stripped from the resposne, that it matches what we sent"""

    request_copy = deepcopy(request)
    response_copy = deepcopy(response)
    strip_known_extra_values(request_copy)
    strip_known_extra_values(response_copy)
    assert request_copy == response_copy


def assert_crud_resource(api_gateway: FlaskClient, auth_header, path, inputs, loader_func, valid=True, delete=False):
    """
    Generic test routine, attempt to create a resource, assert that the relevant artifacts were (or not) created
    """

    for test_resource in inputs:
        resource_to_create = loader_func(test_resource["create"])
        p = api_gateway.post(f"{path}", headers=auth_header, data=json.dumps(resource_to_create))
        if valid:
            assert p.status_code == HTTPStatus.CREATED
            assert_request_equals_response(resource_to_create, p.get_json())
        else:
            assert p.status_code == HTTPStatus.BAD_REQUEST
            # ToDo: assert that the response is a problem - move problems to common

        resource_id = p.get_json()["id_"]
        g = api_gateway.get(f"{path}/{resource_id}", headers=auth_header)
        if valid:
            assert g.status_code == HTTPStatus.OK
            assert_request_equals_response(resource_to_create, g.get_json())
        else:
            assert g.status_code == HTTPStatus.NOT_FOUND
            # ToDo: assert that the response is a problem - move problems to common

        update = test_resource.get("update")
        if update:
            resource_to_update = loader_func(update)
            if update["type"] == "put":
                u = api_gateway.put(f"{path}/{resource_id}", headers=auth_header, data=json.dumps(resource_to_update))
                assert_request_equals_response(resource_to_update, u.get_json())
            elif update["type"] == "patch":
                u = api_gateway.patch(f"{path}/{resource_id}", headers=auth_header, data=json.dumps(resource_to_update))
                patch = jsonpatch.JsonPatch.from_string(resource_to_update)
                baseline = patch.apply(resource_to_create)
                assert_request_equals_response(baseline, u.get_json())

        if delete:
            d = api_gateway.delete(f"{path}/{resource_id}", headers=auth_header)
            assert d.status_code == HTTPStatus.NO_CONTENT
