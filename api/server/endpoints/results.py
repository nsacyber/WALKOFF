import json
import logging
import re
import traceback

import jsonpatch
from fastapi import APIRouter

from api.server.db.mongo import mongo
from api.server.db.workflowresults import WorkflowStatus, UpdateMessage
from api.server.utils.socketio import sio
from common import async_mongo_helpers as mongo_helpers
from common.config import config, static
from common.redis_helpers import connect_to_aioredis_pool

logger = logging.getLogger("API")
router = APIRouter()

WORKFLOW_STREAM_GLOB = "workflow_stream"
ACTION_STREAM_GLOB = "action_stream"


async def update_workflow_status():
    async with connect_to_aioredis_pool(config.REDIS_URI) as redis:
        wfq_col = mongo.async_client.walkoff_db.workflowqueue
        node_id_regex = r"/node_statuses/([0-9a-f]{8}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{12})"
        while True:
            try:
                logger.debug("Waiting for results...")
                message = (await redis.brpop(static.REDIS_RESULTS_QUEUE))[1]
                message = UpdateMessage(**json.loads(message.decode()))

                old_workflow_status = await mongo_helpers.get_item(wfq_col, WorkflowStatus, message.execution_id,
                                                                   id_key="execution_id")
                patch = jsonpatch.JsonPatch.from_string(message.message)
                new_workflow_status = WorkflowStatus(**patch.apply(old_workflow_status.dict()))
                update_wfs: WorkflowStatus = await mongo_helpers.update_item(wfq_col, WorkflowStatus,
                                                                             message.execution_id,
                                                                             new_workflow_status,
                                                                             id_key="execution_id")

                if message.type == "workflow":
                    update_wfs.to_response()
                    await sio.emit(static.SIO_EVENT_LOG, json.loads(update_wfs.json()),
                                   namespace=static.SIO_NS_WORKFLOW)
                else:
                    for patch in json.loads(message.message):
                        node_id = re.search(node_id_regex, patch["path"], re.IGNORECASE).group(1)
                        await sio.emit(static.SIO_EVENT_LOG, json.loads(update_wfs.node_statuses[node_id].json()),
                                       namespace=static.SIO_NS_NODE)
            except Exception as e:
                traceback.print_exc()
