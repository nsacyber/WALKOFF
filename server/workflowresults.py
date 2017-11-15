import json

import core.case.database as case_database
from core.case.callbacks import (WorkflowShutdown, WorkflowExecutionStart, ActionExecutionError, ActionExecutionSuccess,
                                 TriggerActionTaken, TriggerActionAwaitingData, WorkflowPaused, WorkflowResumed)
from core.case.workflowresults import WorkflowResult, ActionResult


@WorkflowShutdown.connect
def __workflow_ended_callback(sender, **kwargs):
    workflow_result = case_database.case_db.session.query(WorkflowResult).filter(
        WorkflowResult.uid == sender.workflow_execution_uid).first()
    if workflow_result is not None:
        workflow_result.complete()
        case_database.case_db.session.commit()


@WorkflowExecutionStart.connect
def __workflow_started_callback(sender, **kwargs):
    workflow_result = WorkflowResult(sender.workflow_execution_uid, sender.name)
    case_database.case_db.session.add(workflow_result)
    case_database.case_db.session.commit()


def __append_action_result(workflow_result, data, action_type):
    action_result = ActionResult(data['name'], json.dumps(data['result']), json.dumps(data['arguments']), action_type, data['app_name'], data['action_name'])
    workflow_result.results.append(action_result)
    case_database.case_db.session.commit()


@ActionExecutionSuccess.connect
def __action_execution_success_callback(sender, **kwargs):
    workflow_result = case_database.case_db.session.query(WorkflowResult).filter(
        WorkflowResult.uid == sender.workflow_execution_uid).first()
    if workflow_result is not None:
        __append_action_result(workflow_result, kwargs['data'], 'success')


@ActionExecutionError.connect
def __action_execution_error_callback(sender, **kwargs):
    workflow_result = case_database.case_db.session.query(WorkflowResult).filter(
        WorkflowResult.uid == sender.workflow_execution_uid).first()
    if workflow_result is not None:
        __append_action_result(workflow_result, kwargs['data'], 'error')


@TriggerActionAwaitingData.connect
def __action_execution_awaiting_data_callback(sender, **kwargs):
    workflow_result = case_database.case_db.session.query(WorkflowResult).filter(
        WorkflowResult.uid == sender.workflow_execution_uid).first()
    if workflow_result is not None:
        workflow_result.trigger_action_awaiting_data()
        case_database.case_db.session.commit()


@TriggerActionTaken.connect
def __action_trigger_taken_callback(sender, **kwargs):
    workflow_result = case_database.case_db.session.query(WorkflowResult).filter(
        WorkflowResult.uid == sender.workflow_execution_uid).first()
    if workflow_result is not None:
        workflow_result.trigger_action_executing()
        case_database.case_db.session.commit()


@WorkflowPaused.connect
def __workflow_paused_callback(sender, **kwargs):
    workflow_result = case_database.case_db.session.query(WorkflowResult).filter(
        WorkflowResult.uid == sender.workflow_execution_uid).first()
    if workflow_result is not None:
        workflow_result.paused()
        case_database.case_db.session.commit()


@WorkflowResumed.connect
def __workflow_resumed_callback(sender, **kwargs):
    workflow_result = case_database.case_db.session.query(WorkflowResult).filter(
        WorkflowResult.uid == sender.workflow_execution_uid).first()
    if workflow_result is not None:
        workflow_result.resumed()
        case_database.case_db.session.commit()
