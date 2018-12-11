import logging
from collections import namedtuple
from uuid import uuid4

import requests

from walkoff.appgateway import get_app_action, get_condition, get_transform
from walkoff.appgateway.actionresult import ActionResult
from walkoff.appgateway.apiutil import get_app_action_api, get_condition_api, get_transform_api
from walkoff.helpers import ExecutionError

logger = logging.getLogger(__name__)

_ActionLookupKey = namedtuple('_ActionLookupKey', ['get_run_key', 'get_executable'])


class ExecutableContext(object):
    __slots__ = ['type', 'app_name', 'executable_name', 'id', 'execution_id']

    def __init__(self, executable_type, app_name, executable_name, executable_id, execution_id=None):
        self.type = executable_type
        self.app_name = app_name
        self.executable_name = executable_name
        self.id = executable_id
        self.execution_id = execution_id or uuid4()

    @classmethod
    def from_executable(cls, executable):
        execution_id = getattr(cls, '_execution_id', None)
        return cls(
            executable.__class__.__name__.lower(),
            executable.app_name,
            executable.action_name,
            executable.id,
            execution_id=execution_id
        )

    def is_action(self):
        return self.type == 'action'

    def __str__(self):
        return str(self.as_json())

    def as_json(self):
        return {
            'type': self.type,
            'app_name': self.app_name,
            'executable_name': self.executable_name,
            'id': str(self.id),
            'execution_id': str(self.execution_id)
        }


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


class RemoteActionExecutionStrategy(object):

    def __init__(self, workflow_context):
        self.workflow_context = workflow_context

    @staticmethod
    def format_url(app_name, worfklow_exec_id, executable_exec_id):
        return 'https://{}-svc/workflows/{}/executables/{}'.format(app_name, worfklow_exec_id, executable_exec_id)

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
        workflow_context = {'id': self.workflow_context.id, 'name': self.workflow_context.name}
        execution_context = context.as_json()
        execution_id = execution_context.pop('execution_id')
        app_name = execution_context.pop('app_name')
        arguments = [{'name': key, 'value': value} for key, value in arguments.items()]
        request_json = {
            'workflow_context': workflow_context,
            'executable_context': execution_context,
            'arguments': arguments
        }
        url = RemoteActionExecutionStrategy.format_url(app_name, self.workflow_context.execution_id, execution_id)
        response = requests.post(url, json=request_json)
        data = response.json()
        if response.status_code == 200:
            if context.is_action():
                result = ActionResult(None, data['status'])
            else:
                result = accumulator[str(context.id)]
            if data['status'] == 'UnhandledException' and not context.is_action():
                raise ExecutionError(message=result)
            return result
        else:
            message = 'Error executing {} {} (id={}) remotely: {{status: {}, data: {}}}'.format(
                context.type,
                context.executable_name,
                context.id,
                response.status_code,
                data
            )

            logger.error(message)
            if context.is_action():
                return ActionResult(None, 'UnhandledException')
            else:
                raise ExecutionError(message=message)


def make_local_execution_strategy(config, workflow_context, **kwargs):
    return LocalActionExecutionStrategy(fully_cached=kwargs.get('fully_cached', False))


def make_remote_execution_strategy(config, workflow_context, **kwargs):
    return RemoteActionExecutionStrategy(workflow_context)


execution_strategy_lookup = {
    'local': make_local_execution_strategy,
    'remote': make_remote_execution_strategy,
}


def make_execution_strategy(
        config,
        workflow_context,
        execution_strategy_map=execution_strategy_lookup,
        **kwargs
):
    strategy = config.ACTION_EXECUTION_STRATEGY
    try:
        return execution_strategy_map[strategy](config, workflow_context, **kwargs)
    except KeyError:
        raise ValueError('Unknown action execution strategy {}'.format(strategy))
