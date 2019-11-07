import logging
from contextlib import asynccontextmanager, contextmanager
from typing import List

import socketio

from common.config import config, static

logging.getLogger('socketio.client').setLevel(logging.WARNING)
logging.getLogger('engineio.client').setLevel(logging.WARNING)


@asynccontextmanager
async def connect_to_socketio_async(socketio_uri: str, namespaces: List[str]) -> socketio.AsyncClient:

    sio = socketio.AsyncClient()
    try:
        await sio.connect(socketio_uri, socketio_path=static.SOCKETIO_PATH, namespaces=namespaces)
        yield sio
    finally:
        await sio.disconnect()


@contextmanager
def connect_to_socketio(socketio_uri: str, namespaces: List[str]) -> socketio.Client:
    sio = socketio.Client()
    try:
        sio.connect(socketio_uri, socketio_path=static.SOCKETIO_PATH, namespaces=namespaces)
        yield sio
    finally:
        sio.disconnect()
