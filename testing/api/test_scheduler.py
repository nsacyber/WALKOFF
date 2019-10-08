import json
import logging
from http import HTTPStatus

import yaml
from starlette.testclient import TestClient

from testing.api.helpers import assert_crud_resource

logger = logging.getLogger(__name__)

base_auth_url = "/walkoff/api/scheduler/"