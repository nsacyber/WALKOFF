from walkoff.appgateway import get_app_action, get_condition, get_transform
from walkoff.appgateway.apiutil import get_app_action_api, get_condition_api, get_transform_api
from collections import namedtuple
from walkoff.helpers import ExecutionError


_ActionLookupKey = namedtuple('_ActionLookupKey', ['get_run_key', 'get_executable'])


class ExecutableContext(object):

    __slots__ = ['type', 'app_name', 'executable_name', 'id']

    def __init__(self, executable_type, app_name, executable_name, executable_id):
        self.type = executable_type
        self.app_name = app_name
        self.executable_name = executable_name
        self.id = executable_id

    def is_action(self):
        return self.type == 'action'

    @classmethod
    def from_executable(cls, executable):
        return cls(
            executable.__class__.__name__.lower(),
            executable.app_name,
            executable.action_name,
            executable.id
        )

    def __str__(self):
        return str({
            'type': self.type,
            'app_name': self.app_name,
            'executable_name': self.executable_name,
            'id': self.executable_name
        })

class LocalActionExecutionStrategy(object):
    _executable_lookup = {
        'action': _ActionLookupKey(get_app_action_api, get_app_action),
        'condition': _ActionLookupKey(get_condition_api, get_condition),
        'transform': _ActionLookupKey(get_transform_api, get_transform)
    }

    def __init__(self, fully_cached=False):
        self.fully_cached = fully_cached

    def _get_execution_func(self, context):
        key = self._executable_lookup[context.type]
        run_key = key.get_run_key(context.app_name, context.executable_name)

        if context.is_action():
            run_key = run_key[0]
        else:
            run_key = run_key[1]
        return key.get_executable(context.app_name, run_key)

    def execute(self, executable, accumulator, arguments, instance=None):
        context = ExecutableContext.from_executable(executable)
        return self._do_execute(
            context,
            accumulator,
            arguments,
            instance=instance
        )

    def execute_from_context(self, context, accumulator, arguments, instance=None):
        return self._do_execute(
            context,
            accumulator,
            arguments,
            instance=instance
        )

    def _do_execute(self, context, accumulator, arguments, instance=None):
        executable_func = self._get_execution_func(context)
        try:
            if instance:
                result = executable_func(instance, **arguments)
            else:
                result = executable_func(**arguments)
        except Exception as e:
            raise ExecutionError(e)
        if context.is_action():
            accumulator[context.id] = result.result
        elif self.fully_cached:
            accumulator[context.id] = result
        return result


def make_local_execution_strategy(config, **kwargs):
    return LocalActionExecutionStrategy(fully_cached=kwargs.get('fully_cached', False))


execution_strategy_lookup = {
    'local': make_local_execution_strategy,
}


def make_execution_strategy(config, execution_strategy_map=execution_strategy_lookup, **kwargs):
    strategy = config.ACTION_EXECUTION_STRATEGY
    try:
        return execution_strategy_map[strategy](config, **kwargs)
    except KeyError:
        raise ValueError('Unknown action execution strategy {}'.format(strategy))
