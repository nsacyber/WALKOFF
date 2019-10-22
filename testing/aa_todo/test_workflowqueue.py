import json
import logging

import yaml
from starlette.testclient import TestClient

from testing.api.helpers import assert_crud_resource

logger = logging.getLogger(__name__)

base_workflowqueue_url = "/walkoff/api/workflowqueue/"
