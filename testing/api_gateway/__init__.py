import json
from copy import deepcopy
from http import HTTPStatus
import yaml


def strip_known_extra_values(o):
    """Recursively removes values the backend is known to add"""
    for key in list(o):
        if o[key] in (None, {}, []):
            o.pop(key)
        elif isinstance(o[key], str):
            if key == "id_":
                o.pop("id_")
            elif key == "errors":
                o.pop("errors")
        elif isinstance(o[key], dict):
            strip_known_extra_values(o[key])
        elif isinstance(o[key], list):
            for ele in o[key]:
                if isinstance(ele, dict):
                    strip_known_extra_values(ele)


def assert_request_equals_response(request, response):
    """Verify that once known extra values are stripped from the resposne, that it matches what we sent"""

    r = deepcopy(response)
    strip_known_extra_values(r)
    assert request == r


def test_crd_resource(api_gateway, auth_header, path, resource_key, inputs, loader_func, valid=True, delete=False):
    """Generic test routine, attempt to create a resource, assert that the relevant artifacts were (or not) created"""

    for test_resource in inputs:
        dict_resource = loader_func(test_resource)
        resource_name = dict_resource.get(resource_key)
        p = api_gateway.post(f"{path}", headers=auth_header, data=json.dumps(dict_resource))
        if valid:
            assert p.status_code == HTTPStatus.CREATED
            assert_request_equals_response(dict_resource, p.get_json())
        else:
            assert p.status_code == HTTPStatus.BAD_REQUEST
            # ToDo: assert that the response is a problem - move problems to common

        g = api_gateway.get(f"{path}/{resource_name}", headers=auth_header)
        if valid:
            assert g.status_code == HTTPStatus.OK
            assert_request_equals_response(dict_resource, g.get_json())
        else:
            assert g.status_code == HTTPStatus.NOT_FOUND
            # ToDo: assert that the response is a problem - move problems to common

        if delete:
            d = api_gateway.delete(f"{path}/{resource_name}", headers=auth_header)
            assert d.status_code == HTTPStatus.NO_CONTENT
