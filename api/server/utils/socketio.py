import logging
from uuid import UUID

import socketio
from pydantic import BaseModel

logging.getLogger('socketio.client').setLevel(logging.WARNING)
logging.getLogger('engineio.client').setLevel(logging.WARNING)


sio = socketio.AsyncClient()


class SIOMessage(BaseModel):
    execution_id: UUID
    workflow_id: UUID
    message: str
