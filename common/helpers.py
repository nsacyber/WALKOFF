import logging
from common.config import config
logger = logging.getLogger("WALKOFF")


def sint(value, default):
    if not isinstance(default, int):
        raise TypeError("Default value must be of integer type")
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def sfloat(value, default):
    if not isinstance(default, int):
        raise TypeError("Default value must be of float type")
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


async def get_walkoff_auth_header(session, token=None):
    url = config.API_GATEWAY_URI.rstrip('/') + '/api'

    # TODO: make this secure and don't use default admin user
    if token is None:
        async with session.post(url + "/auth", json={"username": config.WALKOFF_USERNAME,
                                                     "password": config.WALKOFF_PASSWORD}, timeout=.5) as resp:
            resp_json = await resp.json()
            token = resp_json["refresh_token"]
            logger.debug("Successfully logged into WALKOFF")

    headers = {"Authorization": f"Bearer {token}"}
    async with session.post(url + "/auth/refresh", headers=headers, timeout=.5) as resp:
        resp_json = await resp.json()
        access_token = resp_json["access_token"]
        logger.debug("Successfully refreshed WALKOFF JWT")

    return {"Authorization": f"Bearer {access_token}"}, token

