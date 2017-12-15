import logging
from enum import unique, Enum
logger = logging.getLogger(__name__)


@unique
class MessageAction(Enum):
    read = 1
    unread = 2
    delete = 3
    act = 4

    @classmethod
    def get_all_action_names(cls):
        return [action.name for action in cls]

    @classmethod
    def convert_string(cls, name):
        return next((action for action in cls if action.name == name), None)


class WorkflowAuthorization(object):
    def __init__(self, users=None, roles=None):
        self.users = set(users) if users is not None else set()
        self.roles = set(roles) if roles is not None else set()

    def is_authorized(self, user, role):
        return user in self.users or role in self.roles

    def __add__(self, other):
        users = self.users | other.users
        roles = self.roles | other.roles
        return WorkflowAuthorization(users, roles)


class WorkflowAuthorizationCache(object):

    def __init__(self):
        self._cache = {}

    def add_authorized_users(self, workflow_execution_uid, users=None, roles=None):
        if workflow_execution_uid not in self._cache:
            self._cache[workflow_execution_uid] = WorkflowAuthorization(users=users, roles=roles)
        else:
            self._cache[workflow_execution_uid] += WorkflowAuthorization(users=users, roles=roles)

    def is_authorized(self, workflow_execution_uid, user, role):
        if workflow_execution_uid in self._cache:
            return self._cache[workflow_execution_uid].is_authorized(user, role)
        return False

    def remove_authorizations(self, workflow_execution_uid):
        self._cache.pop(workflow_execution_uid, None)

    def workflow_requires_authorization(self, workflow_execution_uid):
        return workflow_execution_uid in self._cache


workflow_authorization_cache = WorkflowAuthorizationCache()


