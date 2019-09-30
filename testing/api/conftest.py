import json
import pytest
import aioredis
# from starlette.testclient import TestClient
# from async_asgi_testclient import TestClient
from testing.api import StarletteTestClient

from common.config import config

import api.server.app as app
from common.redis_helpers import connect_to_redis_pool


@pytest.fixture
def api():
    return StarletteTestClient(app.app, base_url="/walkoff/api")
    # await app._mongo_manager.init_db()
    # yield TestClient(app.app)

    # async with TestClient(app) as client:
    #     yield client

    # await _mongo_manager.client.drop_database("walkoff_db")
    # async with connect_to_redis_pool(config.REDIS_URI) as conn:  # type: aioredis.Redis
    #     await conn.flushall()


# @pytest.fixture
# async def auth_header(api: TestClient):
#     async with TestClient(api) as client:
#         response = await client.post("/walkoff/api/auth/login",
#                                      data=json.dumps({"username": "admin", "password": "admin"}),
#                                      headers={'content-type': "application/json"})
#         tokens = response.json()
#         header = {"Authorization": f"Bearer {tokens['access_token']}",
#                   "content-type": "application/json"}
#         return header


@pytest.fixture
async def auth_header(api: StarletteTestClient):
    response = await api.post("http://localhost/walkoff/api/auth/login",
                              data=json.dumps({"username": "admin", "password": "admin"}),
                              headers={'content-type': "application/json"})
    tokens = response.json()
    header = {"Authorization": f"Bearer {tokens['access_token']}",
              "content-type": "application/json"}
    return header
