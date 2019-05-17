import logging
import os
import re
import json
import copy
import base64
import tarfile
from io import BytesIO
from pathlib import Path
from contextlib import contextmanager, asynccontextmanager

import aiodocker
from aiodocker.utils import clean_map
from aiodocker.exceptions import DockerError

logger = logging.getLogger("UMPIRE")


async def get_secret(client: aiodocker.Docker, secret_id):
    resp = await client._query(f"secrets/{secret_id}")
    return await resp.json()


@asynccontextmanager
async def connect_to_aiodocker():
    client = aiodocker.Docker()
    try:

        if (await client._query("_ping")).status == 200:
            resp = await client._query("version")
            version = (await resp.json())["Version"]
            logger.debug(f"Connected to Docker Engine: v{version}")
            yield client
    finally:
        await client.close()
        logger.info("Docker connection closed.")