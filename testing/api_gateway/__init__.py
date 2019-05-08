import logging
import pytest

logger = logging.getLogger(__name__)
pytest.register_assert_rewrite("testing.api_gateway.helpers")
