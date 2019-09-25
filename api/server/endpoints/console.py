import logging
from uuid import UUID
from http import HTTPStatus

import gevent
from fastapi import APIRouter, Depends
from gevent.lock import RLock
from gevent.queue import Queue
from pydantic import BaseModel
from starlette.websockets import WebSocket

from api.server.utils.helpers import sse_format
from api_gateway.server.problem import invalid_id_problem

console_stream = Blueprint('console_stream', __name__)
console_stream_subs = {}

logger = logging.getLogger(__name__)
router = APIRouter()


class ConsoleBody(BaseModel):
    message: str


async def push_to_console_stream_queue(console_message, execution_id):
    sse_event_text = sse_format(data=console_message, event='log', event_id=execution_id)
    if execution_id in console_stream_subs:
        console_stream_subs[execution_id].put(sse_event_text)
    if 'all' in console_stream_subs:
        console_stream_subs['all'].put(sse_event_text)


@router.post("/logger")
async def create_console_message(body: ConsoleBody, wf_exec_id: UUID = None):
    workflow_execution_id = wf_exec_id
    logger.info(f"App console log: {body.message}")
    gevent.spawn(push_to_console_stream_queue, body.message, workflow_execution_id)

    return body.message


@router.websocket_route("/log")
async def read_console_message(websocket: WebSocket, exec_id: UUID = None):
    await websocket.accept()
    execution_id = exec_id
    logger.info(f"console log subscription for {execution_id}")
    if execution_id != 'all':
        try:
            UUID(execution_id)
        except ValueError:
            return invalid_id_problem('console log', 'read', execution_id)

    async def console_log_generator():
        console_stream_subs[execution_id] = events = console_stream_subs.get(execution_id, Queue())
        try:
            while True:
                event = events.get().encode()
                logger.info(f"Sending console message for {execution_id}: {event}")
                await websocket.send_text(event)
        except GeneratorExit:
            console_stream_subs.pop(execution_id)
            await websocket.close(code=1000)
            logger.info(f"console log unsubscription for {execution_id}")

    return Response(console_log_generator(), mimetype="text/event-stream")


#
# def format_console_data(sender, data):
#     try:
#         level = int(data['level'])
#     except ValueError:
#         level = data['level']
#     return {
#         'workflow': sender['name'],
#         'app_name': data['app_name'],
#         'name': data['name'],
#         'level': logging.getLevelName(level),
#         'message': data['message']
#     }
#
