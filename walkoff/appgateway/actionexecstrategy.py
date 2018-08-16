from walkoff.appgateway import get_app_action, get_condition, get_transform
from walkoff.appgateway.apiutil import get_app_action_api, get_condition_api, get_transform_api
from walkoff.executiondb.action import Action
from walkoff.executiondb.condition import Condition
from walkoff.executiondb.transform import Transform
from collections import namedtuple


_ActionLookupKey = namedtuple('_ActionLookupKey', ['get_run_key', 'get_executable'])


class LocalActionExecutionStrategy(object):
    _executable_lookup = {
        Action: _ActionLookupKey(get_app_action_api, get_app_action),
        Condition: _ActionLookupKey(get_condition_api, get_condition),
        Transform: _ActionLookupKey(get_transform_api, get_transform)
    }

    def _get_execution_func(self, executable):
        key = self._executable_lookup[executable.__class__]
        run_key = key.get_run_key(executable.app_name, executable.action_name)
        if executable.__class__ is Action:
            run_key = run_key[0]
        else:
            run_key = run_key[1]
        return key.get_executable(executable.app_name, run_key)

    def execute(self, executable, arguments, instance=None):
        executable = self._get_execution_func(executable)
        if instance:
            return executable(instance, **arguments)
        else:
            return executable(**arguments)


def make_local_execution_strategy(config, **kwargs):
    return LocalActionExecutionStrategy()


execution_strategy_lookup = {
    'local': make_local_execution_strategy,
}


def make_execution_strategy(config, execution_strategy_map=execution_strategy_lookup, **kwargs):
    strategy = config.ACTION_EXECUTION_STRATEGY
    try:
        return execution_strategy_map[strategy](config, **kwargs)
    except KeyError:
        raise ValueError('Unknown action execution strategy {}'.format(strategy))