from contextlib import asynccontextmanager
import socketio


@asynccontextmanager
async def connect_to_socketio(socketio_uri, namespaces) -> socketio.AsyncClient:
    sio = socketio.AsyncClient()
    try:
        await sio.connect(socketio_uri, namespaces=namespaces)
        yield sio
    finally:
        await sio.disconnect()
