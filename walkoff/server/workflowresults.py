import json

from walkoff import executiondb
from walkoff.events import WalkoffEvent
from walkoff.executiondb import WorkflowStatusEnum, ActionStatusEnum
from walkoff.executiondb.saved_workflow import SavedWorkflow
from walkoff.executiondb.workflowresults import WorkflowStatus, ActionStatus
from walkoff.executiondb.metrics import AppMetric, ActionMetric, ActionStatusMetric, WorkflowMetric


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

    # Update metrics
    execution_time = (workflow_status.completed_at - workflow_status.started_at).total_seconds()

    workflow_metric = executiondb.execution_db.session.query(WorkflowMetric).filter_by(workflow_id=sender['id']).first()
    if workflow_metric is None:
        workflow_metric = WorkflowMetric(sender['id'], sender['name'], execution_time)
        executiondb.execution_db.session.add(workflow_metric)
    else:
        workflow_metric.update(execution_time)

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
        workflow_status.add_action_status(action_status)
        executiondb.execution_db.session.add(action_status)

    executiondb.execution_db.session.commit()


@WalkoffEvent.ActionExecutionSuccess.connect
def __action_execution_success_callback(sender, **kwargs):
    executiondb.execution_db.session.expire_all()
    action_status = executiondb.execution_db.session.query(ActionStatus).filter_by(
        execution_id=sender['execution_id']).first()
    action_status.completed_success(kwargs['data']['data'])

    # Update metrics
    __update_success_action_tracker(action_status)

    executiondb.execution_db.session.commit()


@WalkoffEvent.ActionExecutionError.connect
def __action_execution_error_callback(sender, **kwargs):
    executiondb.execution_db.session.expire_all()
    action_status = executiondb.execution_db.session.query(ActionStatus).filter_by(
        execution_id=sender['execution_id']).first()

    action_status.completed_failure(kwargs['data']['data'])

    # Update metrics
    __update_error_action_tracker(action_status)
    executiondb.execution_db.session.commit()


@WalkoffEvent.ActionArgumentsInvalid.connect
def __action_args_invalid_callback(sender, **kwargs):
    executiondb.execution_db.session.expire_all()
    action_status = executiondb.execution_db.session.query(ActionStatus).filter_by(
        execution_id=sender['execution_id']).first()

    action_status.completed_failure(kwargs['data']['data'])

    # Update metrics
    __update_error_action_tracker(action_status)
    executiondb.execution_db.session.commit()


def __update_success_action_tracker(action_status):
    __update_action_tracker('success', action_status)


def __update_error_action_tracker(action_status):
    __update_action_tracker('error', action_status)


def __update_action_tracker(status, action_status):
    app_metric = executiondb.execution_db.session.query(AppMetric).filter_by(app=action_status.app_name).first()
    if app_metric is None:
        app_metric = AppMetric(action_status.app_name)
        executiondb.execution_db.session.add(app_metric)

    app_metric.count += 1

    execution_time = (action_status.completed_at - action_status.started_at).total_seconds()
    action_metric = app_metric.get_action_by_id(action_status.action_id)
    if action_metric is None:
        action_status_metric = ActionStatusMetric(status, execution_time)
        action_metric = ActionMetric(action_status.action_id, action_status.action_name, [action_status_metric])
        app_metric.actions.append(action_metric)
    else:
        action_status_metric = action_metric.get_action_status(status)
        if action_status is None:
            action_status_metric = ActionStatusMetric(status, execution_time)
            action_metric.action_statuses.append(action_status_metric)
        else:
            action_status_metric.update(execution_time)

    executiondb.execution_db.session.commit()
