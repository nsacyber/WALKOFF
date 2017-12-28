import logging
from enum import unique, Enum
from collections import deque
from blinker import NamedSignal


logger = logging.getLogger(__name__)


@unique
class MessageAction(Enum):
    read = 1
    unread = 2
    delete = 3
    respond = 4

    @classmethod
    def get_all_action_names(cls):
        return [action.name for action in cls]

    @classmethod
    def convert_string(cls, name):
        return next((action for action in cls if action.name == name), None)


@unique
class MessageActionEvent(Enum):
    created = NamedSignal('message created')
    read = NamedSignal('message read')
    responded = NamedSignal('message responded')

    def send(self, message, **data):
        self.value.send(message, **data)

    def connect(self, func):
        self.value.connect(func)
        return func


class WorkflowAuthorizedUserSet(object):
    __slots__ = ['users', 'roles']

    def __init__(self, users=None, roles=None):
        self.users = set(users) if users is not None else set()
        self.roles = set(roles) if roles is not None else set()

    def is_authorized(self, user, role):
        return user is not None and role is not None and (user in self.users or role in self.roles)

    def add(self, users=None, roles=None):
        if users is not None:
            self.users |= set(users)
        if roles is not None:
            self.roles |= set(roles)


class WorkflowAuthorization(object):
    __slots__ = ['authorized_users', 'user_queue']

    def __init__(self, authorized_users, authorized_roles):
        self.authorized_users = WorkflowAuthorizedUserSet(users=authorized_users, roles=authorized_roles)
        self.user_queue = deque()

    def add_authorizations(self, users, roles):
        self.authorized_users.add(users=users, roles=roles)

    def is_authorized(self, user, role):
        return self.authorized_users.is_authorized(user, role)

    def append_user(self, user):
        self.user_queue.append(user)

    def pop_user(self):
        return self.user_queue.pop()

    def peek_user(self):
        try:
            return self.user_queue[-1]
        except IndexError:
            return None


class WorkflowAuthorizationCache(object):

    def __init__(self):
        self._cache = {}

    def add_authorized_users(self, workflow_execution_uid, users=None, roles=None):
        if workflow_execution_uid not in self._cache:
            self._cache[workflow_execution_uid] = WorkflowAuthorization(users, roles)
        else:
            self._cache[workflow_execution_uid].add_authorizations(users, roles)

    def is_authorized(self, workflow_execution_uid, user, role):
        if workflow_execution_uid in self._cache:
            return self._cache[workflow_execution_uid].is_authorized(user, role)
        return False

    def remove_authorizations(self, workflow_execution_uid):
        self._cache.pop(workflow_execution_uid, None)

    def workflow_requires_authorization(self, workflow_execution_uid):
        return workflow_execution_uid in self._cache

    def add_user_in_progress(self, workflow_execution_uid, user_id):
        if workflow_execution_uid in self._cache:
            self._cache[workflow_execution_uid].append_user(user_id)

    def pop_last_user_in_progress(self, workflow_execution_uid):
        if workflow_execution_uid in self._cache:
            try:
                return self._cache[workflow_execution_uid].pop_user()
            except IndexError:
                return None

    def peek_user_in_progress(self, workflow_execution_uid):
        if workflow_execution_uid in self._cache:
            return self._cache[workflow_execution_uid].peek_user()
        else:
            return None


workflow_authorization_cache = WorkflowAuthorizationCache()


