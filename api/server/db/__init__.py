from starlette.requests import Request

import motor.motor_asyncio
import pymongo

from common.config import config, static
from common.helpers import preset_uuid


class MongoManager(object):
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(username=config.DB_USERNAME,
                                                             password=config.get_from_file(config.MONGO_KEY_PATH),
                                                             host=config.MONGO_HOST)

    async def init_db(self):

        id_index = pymongo.IndexModel([("id_", pymongo.ASCENDING)], unique=True)
        name_index = pymongo.IndexModel([("name", pymongo.ASCENDING)], unique=True)
        username_index = pymongo.IndexModel([("username", pymongo.ASCENDING)], unique=True)

        await self.client.walkoff_db.apps.create_indexes([id_index, name_index])

        await self.client.walkoff_db.workflows.create_indexes([id_index, name_index])

        await self.client.walkoff_db.globals.create_indexes([id_index, name_index])

        await self.client.walkoff_db.roles.create_indexes([id_index, name_index])

        await self.client.walkoff_db.users.create_indexes([id_index, username_index])

        await self.client.walkoff_db.dashboards.create_indexes([id_index, name_index])

        await self.client.walkoff_db.scheduler.create_indexes([id_index, name_index])

        if "settings" not in await self.client.walkoff_db.list_collection_names():
            await self.client.walkoff_db.settings.insert_one({
                "id_": preset_uuid("settings"),
                "access_token_life_mins": 15,
                "refresh_token_life_days": 90
            })

    def collection_from_url(self, path: str):
        parts = path.split("/")
        if len(parts) >= 4:
            resource = parts[3]
            return self.client.walkoff_db[resource]
        else:
            return None


def get_mongo_c(request: Request):
    return request.state.mongo_c


def get_mongo_d(request: Request):
    return request.state.mongo_d


mongo = MongoManager()
