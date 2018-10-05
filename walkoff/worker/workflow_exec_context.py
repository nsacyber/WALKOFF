import logging
from walkoff.events import WalkoffEvent
from walkoff.appgateway.accumulators import make_accumulator

logger = logging.getLogger(__name__)


class WorkflowExecutionContext(object):
    __slots__ = ['workflow', 'name', 'id', 'workflow_start', 'execution_id', 'accumulator', 'app_instance_repo',
                 'executing_action', 'is_paused', 'is_aborted', 'has_branches', 'last_status', 'user']

    def __init__(self, workflow, app_instance_repo, execution_id, resumed=False, user=None):
        self.workflow = workflow
        self.accumulator = None
        self.app_instance_repo = app_instance_repo
        self.execution_id = execution_id
        self.name = workflow.name
        self.id = workflow.id
        self.workflow_start = workflow.start
        self.executing_action = None
        self.is_paused = False
        self.is_aborted = False
        self.has_branches = bool(self.workflow.branches)
        self.last_status = None
        self.init_accumulator(resumed)
        self.user = user

    def pause(self):
        self.is_paused = True

    def abort(self):
        self.is_aborted = True

    def send_event(self, event, data=None):
        if data is None:
            WalkoffEvent.CommonWorkflowSignal.send(self.workflow, event=event)
        else:
            WalkoffEvent.CommonWorkflowSignal.send(self.workflow, event=event, data=data)

    def get_app_instance(self, device_id):
        return self.app_instance_repo.get_app_instance(device_id)()

    def get_action_by_id(self, action_id):
        return next((action for action in self.workflow.actions if action.id == action_id), None)

    def get_executing_action_id(self):
        return self.executing_action.id

    def get_executing_action(self):
        return self.executing_action

    def get_branches_by_action_id(self, action_id):
        return sorted(self.workflow.get_branches_by_action_id(action_id), key=lambda branch_: branch_.priority)

    def set_execution_id(self, execution_id):
        self.workflow.set_execution_id(execution_id)

    def update_accumulator(self, key, result):
        self.accumulator[key] = result

    def update_multiple_accumulator(self, updated_keys):
        self.accumulator.update(updated_keys)

    def update_status(self, status):
        self.last_status = status

    def init_accumulator(self, from_resumed=False):
        self.accumulator = make_accumulator(self.execution_id)
        if self.workflow.environment_variables:
            self.accumulator.update({env_var.id: env_var.value for env_var in self.workflow.environment_variables})
        if not from_resumed:
            self.accumulator.update({branch.id: 0 for branch in self.workflow.branches})

    def shutdown(self):
        # Upon finishing shut down instances
        self.app_instance_repo.shutdown_instances()
        accumulator = {str(key): value for key, value in self.accumulator.items()}
        self.send_event(WalkoffEvent.WorkflowShutdown, data=accumulator)
        logger.info('Workflow {0} completed. Result: {1}'.format(self.workflow.name, self.accumulator))
        self.accumulator.clear()

    @property
    def restricted_context(self):
        return RestrictedWorkflowContext.from_workflow_context(self)


class RestrictedWorkflowContext(object):

    def __init__(self, execution_id, id, name):
        self.execution_id = execution_id
        self.id = id
        self.name = name

    def as_json(self):
        return {
            'workflow_execution_id': self.execution_id,
            'workflow_id': self.id,
            'workflow_name': self.name
        }

    @classmethod
    def from_workflow(cls, workflow, execution_id):
        return cls(execution_id, workflow.id, workflow.name)

    @classmethod
    def from_workflow_context(cls, context):
        return cls(context.execution_id, context.id, context.name)