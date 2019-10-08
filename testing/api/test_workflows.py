import json
import logging
from http import HTTPStatus

import yaml
from starlette.testclient import TestClient

from common.workflow_types import workflow_load
from testing.api.helpers import assert_crud_resource

logger = logging.getLogger(__name__)

base_workflows_url = "/walkoff/api/workflows/"


def test_workflow_creation(api: TestClient, auth_header: dict):
    with open('testing/util/workflow.json') as fp:
        wf_json = json.load(fp)
    p = api.post(base_workflows_url, headers=auth_header, data=json.dumps(wf_json))
    assert p.status_code == 201