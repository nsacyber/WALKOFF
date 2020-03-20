import logging
import json
from base64 import b64encode
from uuid import UUID

from tenacity import retry, stop_after_attempt, wait_exponential

from common.config import config, static
from common.message_types import (message_dumps, NodeStatusMessage, WorkflowStatusMessage,
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
async def get_walkoff_auth_header(session, token=None, timeout=5 * 60):
    url = config.API_URI.rstrip('/') + '/walkoff/api'
    logger.debug("Attempting to refresh WALKOFF JWT")
    if token is None:
        key = config.get_from_file(config.INTERNAL_KEY_PATH)
        async with session.post(url + "/auth/login", json={"username": config.WALKOFF_USERNAME,
                                                           "password": key}, timeout=timeout) as resp:
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


async def send_status_update(redis, execution_id, workflow_id, message):
    """ Forms and sends a JSONPatch message to the api_gateway to update the status of an action or workflow """

    if message is None:
        return None
    patches = {
        "execution_id": execution_id,
        "workflow_id": workflow_id,
        "message": message_dumps(get_patches(message)),
        "type": "workflow" if type(message) is WorkflowStatusMessage else "node"
    }
    # try:
    logger.info(f"Sending result {patches}")
    await redis.lpush(static.REDIS_RESULTS_QUEUE, json.dumps(patches))
    # except ConnectionError as e:
    #     logger.error(f"Could not send event to {config.SOCKETIO_URI}: {e!r}")
    # except TimeoutError as e:
    #     logger.error(f"Timed out sending event to {config.SOCKETIO_URI}: {e!r}")


def fernet_encrypt(key: bytes, string: str):
    from cryptography.fernet import Fernet

    if type(string) is not str:
        to_enc = json.dumps(string)
    else:
        to_enc = string

    return Fernet(b64encode(key)).encrypt(to_enc.encode()).decode()


def fernet_decrypt(key: bytes, string: str):
    from cryptography.fernet import Fernet
    s = Fernet(b64encode(key)).decrypt(string.encode()).decode()
    try:
        r = json.loads(s)
    except (TypeError, json.decoder.JSONDecodeError):
        r = s

    return r


def validate_uuid(id_, stringify=False):
    try:
        uuid_ = id_
        if not isinstance(uuid_, UUID):
            uuid_ = UUID(str(uuid_))
        return uuid_ if not stringify else id_
    except (ValueError, TypeError):
        return None


def preset_uuid(s: str):
    """Generates a UUID from string (deterministic)"""
    return UUID(bytes=s.encode().rjust(16, b'\0'))
