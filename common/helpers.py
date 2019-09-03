import logging
import json

from tenacity import retry, stop_after_attempt, wait_exponential

from common.config import config
from common.message_types import(message_dumps, NodeStatusMessage, WorkflowStatusMessage,
                                 StatusEnum, JSONPatch, JSONPatchOps)

logger = logging.getLogger("WALKOFF")

HEX_CHARS = 'abcdefABCDEF0123456789'
UUID_GLOB = "-".join((f"[{HEX_CHARS}]" * i for i in (8, 4, 4, 4, 12)))
UUID_REGEX = "[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}"


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

@retry(stop=stop_after_attempt(5), wait=wait_exponential(min=1, max=10))
async def get_walkoff_auth_header(session, token=None, timeout=5*60):
    url = config.API_GATEWAY_URI.rstrip('/') + '/walkoff/api'

    # TODO: make this secure and don't use default admin user
    if token is None:
        async with session.post(url + "/auth", json={"username": config.WALKOFF_USERNAME,
                                                     "password": config.WALKOFF_PASSWORD}, timeout=timeout) as resp:
            resp_json = await resp.json()
            token = resp_json["refresh_token"]
            logger.debug("Successfully logged into WALKOFF")

    headers = {"Authorization": f"Bearer {token}"}
    async with session.post(url + "/auth/refresh", headers=headers, timeout=timeout) as resp:
        resp_json = await resp.json()
        access_token = resp_json["access_token"]
        logger.debug("Successfully refreshed WALKOFF JWT")

    return {"Authorization": f"Bearer {access_token}"}, token


def make_patch(message, root, op, value_only=False, white_list=None, black_list=None):
    if white_list is None and black_list is None:
        raise ValueError("Either white_list or black_list must be provided")

    if white_list is not None and black_list is not None:
        raise ValueError("Either white_list or black_list must be provided, not both")

    # convert blacklist to whitelist and grab those attrs from the message
    white_list = set(message.__slots__).difference(black_list) if black_list is not None else white_list

    if value_only and len(white_list) != 1:
        raise ValueError("value_only can only be set if a single key is in white_list")

    if value_only:
        (key,) = white_list
        values = getattr(message, key)
    else:
        values = {k: getattr(message, k) for k in message.__slots__ if k in white_list}

    return JSONPatch(op, path=root, value=values)


def get_patches(message):
    patches = []
    if isinstance(message, NodeStatusMessage):
        root = f"/node_statuses/{message.node_id}"
        if message.status == StatusEnum.EXECUTING:
            patches.append(make_patch(message, root, JSONPatchOps.ADD, black_list={"result", "completed_at"}))

        else:
            patches.append(make_patch(message, root, JSONPatchOps.REPLACE, black_list={}))

    elif isinstance(message, WorkflowStatusMessage):
        if message.status == StatusEnum.EXECUTING:
            for key in [attr for attr in message.__slots__ if getattr(message, attr)]:
                patches.append(make_patch(message, f"/{key}", JSONPatchOps.REPLACE, value_only=True,
                                          white_list={f"{key}"}))

        elif message.status == StatusEnum.COMPLETED or message.status == StatusEnum.ABORTED:
            patches.append(make_patch(message, f"/status", JSONPatchOps.REPLACE, value_only=True,
                                      white_list={"status"}))
            patches.append(make_patch(message, f"/completed_at", JSONPatchOps.REPLACE, value_only=True,
                                      white_list={"completed_at"}))

    return patches


async def send_status_update(session, execution_id, message, headers=None):
    import aiohttp
    """ Forms and sends a JSONPatch message to the api_gateway to update the status of an action or workflow """

    if message is None:
        return None

    patches = get_patches(message)

    if len(patches) < 1:
        raise ValueError(f"Attempting to send improper message type: {type(message)}")

    params = {"event": message.status.value}
    url = f"{config.API_GATEWAY_URI}/walkoff/api/internal/workflowstatus/{execution_id}"
    headers, token = await get_walkoff_auth_header(session)
    headers["content-type"] = "application/json"

    try:
        async with session.patch(url, data=message_dumps(patches), params=params, headers=headers, timeout=5) as resp:
            if resp.content_type == "application/json":
                results = await resp.json()
                logger.debug(f"API-Gateway status update response: {results}")
                return results
    except aiohttp.ClientConnectionError as e:
        logger.error(f"Could not send status message to {url}: {e!r}")
    except Exception as e:
        logger.error(f"Unknown error while sending message to {url}: {e!r}")


def fernet_encrypt(key, string):
    from cryptography.fernet import Fernet

    if type(string) is not str:
        to_enc = json.dumps(string)
    else:
        to_enc = string

    return Fernet(key).encrypt(to_enc.encode()).decode()


def fernet_decrypt(key, string):
    from cryptography.fernet import Fernet

    try:
        to_dec = json.loads(string)
    except (TypeError, json.decoder.JSONDecodeError):
        to_dec = string

    return Fernet(key).decrypt(to_dec.encode()).decode()
