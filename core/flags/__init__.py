from six import with_metaclass
from core.helpers import SubclassRegistry

__all__ = ['count', 'regMatch']


class FlagExecutionNotImplementedError(NotImplementedError):
    pass


class FlagNotImplementedError(Exception):
    pass


class FlagType(with_metaclass(SubclassRegistry, object)):
    @staticmethod
    def execute(args, value):
        raise FlagExecutionNotImplementedError


def execute_flag(action, args=None, value=None):
    if action in FlagType.registry:
        return FlagType.registry[action].execute(args, value)
    else:
        raise FlagNotImplementedError
