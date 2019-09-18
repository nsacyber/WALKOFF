from api.security import get_jwt_identity
import logging
logger = logging.getLogger(__name__)


def auth_check(curr_user_id, resource_id, permission, resource_name, walkoff_db, updated_roles=None):
    user_col = walkoff_db.getCollection("users")
    resource_col = walkoff_db.getCollection(resource_name)
    curr_user = user_col.find_one({"id": curr_user_id}, projection={'_id': False})


