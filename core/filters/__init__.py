from six import with_metaclass
from core.helpers import SubclassRegistry

__all__ = ['length']


class FilterExecutionNotImplementedError(NotImplementedError):
    pass


class FilterNotImplementedError(Exception):
    pass


class FilterType(with_metaclass(SubclassRegistry, object)):
    @staticmethod
    def execute(args, value):
        raise FilterExecutionNotImplementedError


def execute_filter(action, args=None, value=None):
    if action in FilterType.registry:
        return FilterType.registry[action].execute(args, value)
    else:
        raise FilterNotImplementedError
