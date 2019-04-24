import json
import logging

import pytest

from testing.api_gateway import test_crd_resource


# @pytest.fixture
# def valid_workflow_1():
#     with open("testing/util/workflow.json") as fp:
#         r = fp.read()
#     return r


def test_workflow_post_and_get(api_gateway, auth_header, execdb, valid_workflow_1):
    inputs = [
        """
        {
            "actions": [
                {
                    "app_name": "hello_world:1.0.0",
                    "app_version": "1.0.0",
                    "id_": "703dc24c-5d83-9001-5e54-aabfbe401e64",
                    "label": "hello_world",
                    "name": "hello_world",
                    "position": {
                        "x": 0,
                        "y": 0
                    },
                }
            ],
            "description": "A minimal hello world workflow",
            "id_": "85e0d665-6490-841c-0e3d-d70c4db740b8",
            "name": "Test",
            "start": "703dc24c-5d83-9001-5e54-aabfbe401e64",
        }
        """
    ]
    test_crd_resource(api_gateway, auth_header, "/api/apps/apis", "name", [valid_workflow_1], json.loads, valid=False,
                      delete=True)
