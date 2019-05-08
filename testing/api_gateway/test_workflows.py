import json
import logging

import pytest
import yaml

from testing.api_gateway.helpers import assert_crud_resource

logger = logging.getLogger(__name__)
workflows_url = "/api/workflows"

# @pytest.fixture
# def hello_world_api(api_gateway, auth_header, execdb):
#     with open("apps/hello_world/1.0.0/api.yaml") as f:
#         r = f.read()
#     return r


def test_workflow_post_and_get(api_gateway, auth_header, execdb):
    with open("apps/hello_world/1.0.0/api.yaml") as f:
        r = {"create": f.read()}
    assert_crud_resource(api_gateway, auth_header, "/api/apps/apis", [r], yaml.full_load)

    inputs = [
        {
            "create": """
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
                        }
                    }
                ],
                "description": "A minimal hello world workflow",
                "name": "Test",
                "start": "703dc24c-5d83-9001-5e54-aabfbe401e64"
            }
            """,
        },
    ]
    assert_crud_resource(api_gateway, auth_header, workflows_url, inputs, json.loads, delete=True)
