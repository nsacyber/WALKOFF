import json

from flask import current_app

from common.message_types import StatusEnum
from api_gateway.events import WalkoffEvent
from api_gateway.executiondb.workflowresults import WorkflowStatus, ActionStatus


@WalkoffEvent.WorkflowExecutionPending.connect
def __workflow_pending(sender, **kwargs):
    current_app.running_context.execution_db.session.expire_all()
    workflow_status = current_app.running_context.execution_db.session.query(WorkflowStatus).filter_by(
        execution_id=str(sender['execution_id'])).first()
    if workflow_status:
        workflow_status.status = StatusEnum.PENDING
    else:
        user = kwargs['data']['user'] if ('data' in kwargs and 'user' in kwargs['data']) else None
        workflow_status = WorkflowStatus(str(sender['execution_id']), sender['id'], sender['name'], user=user)
        current_app.running_context.execution_db.session.add(workflow_status)
    current_app.running_context.execution_db.session.commit()


@WalkoffEvent.WorkflowExecutionStart.connect
def __workflow_started_callback(sender, **kwargs):
    current_app.running_context.execution_db.session.expire_all()
    workflow_status = current_app.running_context.execution_db.session.query(WorkflowStatus).filter_by(
        execution_id=sender['execution_id']).first()
    workflow_status.running()
    current_app.running_context.execution_db.session.commit()


@WalkoffEvent.WorkflowPaused.connect
def __workflow_paused_callback(sender, **kwargs):
    current_app.running_context.execution_db.session.expire_all()
    workflow_status = current_app.running_context.execution_db.session.query(WorkflowStatus).filter_by(
        execution_id=sender['execution_id']).first()
    workflow_status.paused()
    current_app.running_context.execution_db.session.commit()


@WalkoffEvent.TriggerActionAwaitingData.connect
def __workflow_awaiting_data_callback(sender, **kwargs):
    workflow_execution_id = kwargs['data']['workflow']['execution_id']
    current_app.running_context.execution_db.session.expire_all()
    workflow_status = current_app.running_context.execution_db.session.query(WorkflowStatus).filter_by(
        execution_id=workflow_execution_id).first()
    workflow_status.awaiting_data()
    current_app.running_context.execution_db.session.commit()


@WalkoffEvent.WorkflowShutdown.connect
def __workflow_ended_callback(sender, **kwargs):
    current_app.running_context.execution_db.session.expire_all()
    workflow_status = current_app.running_context.execution_db.session.query(WorkflowStatus).filter_by(
        execution_id=sender['execution_id']).first()
    workflow_status.completed()
    current_app.running_context.execution_db.session.commit()


@WalkoffEvent.WorkflowAborted.connect
def __workflow_aborted(sender, **kwargs):
    current_app.running_context.execution_db.session.expire_all()
    workflow_status = current_app.running_context.execution_db.session.query(WorkflowStatus).filter_by(
        execution_id=sender['execution_id']).first()
    workflow_status.aborted()

    current_app.running_context.execution_db.session.commit()


@WalkoffEvent.ActionStarted.connect
def __action_start_callback(sender, **kwargs):
    workflow_execution_id = kwargs['data']['workflow']['execution_id']
    current_app.running_context.execution_db.session.expire_all()
    action_status = current_app.running_context.execution_db.session.query(ActionStatus).filter_by(
        execution_id=sender['execution_id']).first()
    if action_status:
        action_status.status = StatusEnum.EXECUTING
    else:
        workflow_status = current_app.running_context.execution_db.session.query(WorkflowStatus).filter_by(
            execution_id=workflow_execution_id).first()
        arguments = sender['arguments'] if 'arguments' in sender else []
        action_status = ActionStatus(sender['execution_id'], sender['id'], sender['name'], sender['app_name'],
                                     sender['action_name'], json.dumps(arguments))
        workflow_status.add_action_status(action_status)
        current_app.running_context.execution_db.session.add(action_status)

    current_app.running_context.execution_db.session.commit()


@WalkoffEvent.ActionExecutionSuccess.connect
def __action_execution_success_callback(sender, **kwargs):
    current_app.running_context.execution_db.session.expire_all()
    action_status = current_app.running_context.execution_db.session.query(ActionStatus).filter_by(
        execution_id=sender['execution_id']).first()
    action_status.completed_success(kwargs['data']['data'])
    current_app.running_context.execution_db.session.commit()


@WalkoffEvent.ActionExecutionError.connect
def __action_execution_error_callback(sender, **kwargs):
    current_app.running_context.execution_db.session.expire_all()
    action_status = current_app.running_context.execution_db.session.query(ActionStatus).filter_by(
        execution_id=sender['execution_id']).first()

    action_status.completed_failure(kwargs['data']['data'])
    current_app.running_context.execution_db.session.commit()


@WalkoffEvent.ActionArgumentsInvalid.connect
def __action_args_invalid_callback(sender, **kwargs):
    current_app.running_context.execution_db.session.expire_all()
    action_status = current_app.running_context.execution_db.session.query(ActionStatus).filter_by(
        execution_id=sender['execution_id']).first()

    action_status.completed_failure(kwargs['data']['data'])
    current_app.running_context.execution_db.session.commit()


