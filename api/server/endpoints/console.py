import asyncio
import json
import logging
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel
from starlette.websockets import WebSocket

from common.config import config
from common.redis_helpers import connect_to_aioredis_pool

# console_stream = Blueprint('console_stream', __name__)
console_stream_subs = set()
USERS = []

logger = logging.getLogger("API")
router = APIRouter()

CONSOLE_STREAM_GLOB = "console_stream"


class ConsoleBody(BaseModel):
    message: str
    close: str = None


# async def push_to_console_stream_queue(console_message, execution_id):
#     sse_event_text = sse_format(data=console_message, event='log', event_id=execution_id)
#     if execution_id in console_stream_subs:
#         console_stream_subs[execution_id].put(sse_event_text)
#     if 'all' in console_stream_subs:
#         console_stream_subs['all'].put(sse_event_text)


@router.post("/logger/")
async def create_console_message(body: ConsoleBody, wf_exec_id: UUID = None):
    logger.info(f"App console log: {body.message}")
    if wf_exec_id in console_stream_subs:
        redis_stream = CONSOLE_STREAM_GLOB + "." + str(wf_exec_id)
    elif 'all' in console_stream_subs:
        redis_stream = CONSOLE_STREAM_GLOB + ".all"
    else:
        # return body.message
        redis_stream = CONSOLE_STREAM_GLOB + "." + str(wf_exec_id)
    async with connect_to_aioredis_pool(config.REDIS_URI) as conn:
        key = f"{redis_stream}"
        value = body.json()
        await conn.lpush(key, value)

    return str(body.message)


@router.websocket("/log")
async def read_console_message(websocket: WebSocket, exec_id: UUID):
    await websocket.accept()
    USERS.append(websocket)
    redis_stream = CONSOLE_STREAM_GLOB + "." + str(exec_id)
    if exec_id not in console_stream_subs:
        console_stream_subs.add(exec_id)
    logger.info(f"console log subscription for {exec_id}")
    # if execution_id != 'all':
    #     try:
    #         UUID(execution_id)
    #     except ValueError:
    #         return invalid_id_problem('console log', 'read', execution_id)

    async def console_log_generator():
        async with connect_to_aioredis_pool(config.REDIS_URI) as conn:
            try:
                while True:
                    await asyncio.sleep(1)
                    event = await conn.rpop(redis_stream)
                    if event is not None:
                        event_object = json.loads(event.decode("ascii"))
                        message = event_object["message"]
                        for user in USERS:
                            await user.send_text(message)
                        logger.info(f"Sending console message for {exec_id}: {message}")
                        if event_object["close"] == "Done":
                            await conn.delete(redis_stream)
                            console_stream_subs.remove(exec_id)
                            for user in USERS:
                                await user.close(code=1000)
            except Exception as e:
                await conn.delete(redis_stream)
                console_stream_subs.remove(exec_id)
                USERS.remove(websocket)
                # Websocket closed so no one else can access.
                await websocket.close(code=1000)
                logger.info(f"Error: {e}")

    return await console_log_generator()

    # Response(console_log_generator(), mimetype="text/event-stream")


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
