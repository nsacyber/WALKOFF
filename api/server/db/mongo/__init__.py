import motor.motor_asyncio
import pymongo
from starlette.requests import Request

from common.config import config
from common.helpers import preset_uuid


class MongoManager(object):
    def __init__(self):
        self.async_client = motor.motor_asyncio.AsyncIOMotorClient(username=config.DB_USERNAME,
                                                                   password=config.get_from_file(config.MONGO_KEY_PATH),
                                                                   host=config.MONGO_HOST,
                                                                   port=config.get_int("MONGO_PORT", 27016))

        self.reg_client = pymongo.MongoClient(username=config.DB_USERNAME,
                                              password=config.get_from_file(config.MONGO_KEY_PATH),
                                              host=config.MONGO_HOST,
                                              port=config.get_int("MONGO_PORT", 27016))

        self.init_db()

    def init_db(self):
        from api.server.db.user_init import default_users, default_roles

        id_index = pymongo.IndexModel([("id_", pymongo.ASCENDING)], unique=True)
        name_index = pymongo.IndexModel([("name", pymongo.ASCENDING)], unique=True)
        username_index = pymongo.IndexModel([("username", pymongo.ASCENDING)], unique=True)
        execution_index = pymongo.IndexModel([("execution_id", pymongo.ASCENDING)], unique=True)

        self.reg_client.walkoff_db.apps.create_indexes([id_index, name_index])

        self.reg_client.walkoff_db.workflows.create_indexes([id_index, name_index])

        self.reg_client.walkoff_db.globals.create_indexes([id_index, name_index])

        self.reg_client.walkoff_db.roles.create_indexes([id_index, name_index])

        self.reg_client.walkoff_db.users.create_indexes([id_index, username_index])

        self.reg_client.walkoff_db.dashboards.create_indexes([id_index, name_index])

        self.reg_client.walkoff_db.scheduler.create_indexes([id_index, name_index])

        self.reg_client.walkoff_db.workflowqueue.create_indexes([execution_index])

        if "settings" not in self.reg_client.walkoff_db.list_collection_names():
            self.reg_client.walkoff_db.settings.insert_one({
                "id_": preset_uuid("settings"),
                "access_token_life_mins": 15,
                "refresh_token_life_days": 90
            })

        roles_col = self.reg_client.walkoff_db.roles
        users_col = self.reg_client.walkoff_db.users

        for role_name, role in default_roles.items():
            role_d = roles_col.find_one({"id_": role["id_"]})
            if not role_d:
                roles_col.insert_one(role)

        for user_name, user in default_users.items():
            user_d = users_col.find_one({"id_": user["id_"]})
            if not user_d:
                users_col.insert_one(user)

    def erase_db(self):
        self.reg_client.drop_database("walkoff_db")

    def collection_from_url(self, path: str):
        parts = path.split("/")
        if len(parts) >= 4:
            resource = parts[3]
            return self.async_client.walkoff_db[resource]
        else:
            return None


def get_mongo_c(request: Request):
    return request.state.mongo_c


def get_mongo_d(request: Request):
    return request.state.mongo_d


mongo = MongoManager()
