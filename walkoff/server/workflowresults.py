import json

from walkoff import executiondb
from walkoff.events import WalkoffEvent
from walkoff.executiondb import WorkflowStatusEnum, ActionStatusEnum
from walkoff.executiondb.saved_workflow import SavedWorkflow
from walkoff.executiondb.workflowresults import WorkflowStatus, ActionStatus


@WalkoffEvent.WorkflowExecutionPending.connect
def __workflow_pending(sender, **kwargs):
    executiondb.execution_db.session.expire_all()
    workflow_status = executiondb.execution_db.session.query(WorkflowStatus).filter_by(
        execution_id=sender['execution_id']).first()
    if workflow_status:
        workflow_status.status = WorkflowStatusEnum.pending
    else:
        workflow_status = WorkflowStatus(sender['execution_id'], sender['id'], sender['name'])
        executiondb.execution_db.session.add(workflow_status)
    executiondb.execution_db.session.commit()


@WalkoffEvent.WorkflowExecutionStart.connect
def __workflow_started_callback(sender, **kwargs):
    executiondb.execution_db.session.expire_all()
    workflow_status = executiondb.execution_db.session.query(WorkflowStatus).filter_by(
        execution_id=sender['execution_id']).first()
    workflow_status.running()
    executiondb.execution_db.session.commit()


@WalkoffEvent.WorkflowPaused.connect
def __workflow_paused_callback(sender, **kwargs):
    executiondb.execution_db.session.expire_all()
    workflow_status = executiondb.execution_db.session.query(WorkflowStatus).filter_by(
        execution_id=sender['execution_id']).first()
    workflow_status.paused()
    executiondb.execution_db.session.commit()


@WalkoffEvent.TriggerActionAwaitingData.connect
def __workflow_awaiting_data_callback(sender, **kwargs):
    workflow_execution_id = kwargs['data']['workflow']['execution_id']
    executiondb.execution_db.session.expire_all()
    workflow_status = executiondb.execution_db.session.query(WorkflowStatus).filter_by(
        execution_id=workflow_execution_id).first()
    workflow_status.awaiting_data()
    executiondb.execution_db.session.commit()


@WalkoffEvent.WorkflowShutdown.connect
def __workflow_ended_callback(sender, **kwargs):
    executiondb.execution_db.session.expire_all()
    workflow_status = executiondb.execution_db.session.query(WorkflowStatus).filter_by(
        execution_id=sender['execution_id']).first()
    workflow_status.completed()
    executiondb.execution_db.session.commit()

    saved_state = executiondb.execution_db.session.query(SavedWorkflow).filter_by(
        workflow_execution_id=sender['execution_id']).first()
    if saved_state:
        executiondb.execution_db.session.delete(saved_state)

    executiondb.execution_db.session.commit()


@WalkoffEvent.WorkflowAborted.connect
def __workflow_aborted(sender, **kwargs):
    executiondb.execution_db.session.expire_all()
    workflow_status = executiondb.execution_db.session.query(WorkflowStatus).filter_by(
        execution_id=sender['execution_id']).first()
    workflow_status.aborted()

    saved_state = executiondb.execution_db.session.query(SavedWorkflow).filter_by(
        workflow_execution_id=sender['execution_id']).first()
    if saved_state:
        executiondb.execution_db.session.delete(saved_state)

    executiondb.execution_db.session.commit()


@WalkoffEvent.ActionStarted.connect
def __action_start_callback(sender, **kwargs):
    workflow_execution_id = kwargs['data']['workflow']['execution_id']
    executiondb.execution_db.session.expire_all()
    action_status = executiondb.execution_db.session.query(ActionStatus).filter_by(
        execution_id=sender['execution_id']).first()
    if action_status:
        action_status.status = ActionStatusEnum.executing
    else:
        workflow_status = executiondb.execution_db.session.query(WorkflowStatus).filter_by(
            execution_id=workflow_execution_id).first()
        arguments = sender['arguments'] if 'arguments' in sender else []
        action_status = ActionStatus(sender['execution_id'], sender['id'], sender['name'], sender['app_name'],
                                     sender['action_name'], json.dumps(arguments))
        workflow_status._action_statuses.append(action_status)
        executiondb.execution_db.session.add(action_status)

    executiondb.execution_db.session.commit()


@WalkoffEvent.ActionExecutionSuccess.connect
def __action_execution_success_callback(sender, **kwargs):
    executiondb.execution_db.session.expire_all()
    action_status = executiondb.execution_db.session.query(ActionStatus).filter_by(
        execution_id=sender['execution_id']).first()
    action_status.completed_success(kwargs['data']['data'])
    executiondb.execution_db.session.commit()


@WalkoffEvent.ActionExecutionError.connect
def __action_execution_error_callback(sender, **kwargs):
    handle_action_error(sender, kwargs)


@WalkoffEvent.ActionArgumentsInvalid.connect
def __action_args_invalid_callback(sender, **kwargs):
    handle_action_error(sender, kwargs)


def handle_action_error(sender, kwargs):
    executiondb.execution_db.session.expire_all()
    action_status = executiondb.execution_db.session.query(ActionStatus).filter_by(
        execution_id=sender['execution_id']).first()
    action_status.completed_failure(kwargs['data']['data'])
    executiondb.execution_db.session.commit()
