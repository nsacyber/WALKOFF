import logging
from uuid import UUID

import socketio
from pydantic import BaseModel

from common.config import config, static


logging.getLogger('socketio.client').setLevel(logging.WARNING)
logging.getLogger('engineio.client').setLevel(logging.WARNING)
logger = logging.getLogger("API")
sio = socketio.AsyncClient()


class SIOMessage(BaseModel):
    execution_id: UUID
    workflow_id: UUID
    message: str


async def init_sio():
    logger.info("Connecting to Socket.IO server.")
    await sio.connect(config.SOCKETIO_URI, socketio_path=static.SOCKETIO_PATH, namespaces=[static.SIO_NS_NODE,
                                                                                           static.SIO_NS_WORKFLOW,
                                                                                           static.SIO_NS_BUILD])
