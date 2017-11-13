import json

import core.case.database as case_database
from core.case.callbacks import (WorkflowShutdown, WorkflowExecutionStart, StepExecutionError, StepExecutionSuccess,
                                 TriggerStepTaken, TriggerStepAwaitingData, WorkflowPaused, WorkflowResumed)
from core.case.workflowresults import WorkflowResult, StepResult


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


def __append_step_result(workflow_result, data, step_type):
    step_result = StepResult(data['name'], json.dumps(data['result']), json.dumps(data['arguments']), step_type, data['app'], data['action'])
    workflow_result.results.append(step_result)
    case_database.case_db.session.commit()


@StepExecutionSuccess.connect
def __step_execution_success_callback(sender, **kwargs):
    workflow_result = case_database.case_db.session.query(WorkflowResult).filter(
        WorkflowResult.uid == sender.workflow_execution_uid).first()
    if workflow_result is not None:
        __append_step_result(workflow_result, kwargs['data'], 'success')


@StepExecutionError.connect
def __step_execution_error_callback(sender, **kwargs):
    workflow_result = case_database.case_db.session.query(WorkflowResult).filter(
        WorkflowResult.uid == sender.workflow_execution_uid).first()
    if workflow_result is not None:
        __append_step_result(workflow_result, kwargs['data'], 'error')


@TriggerStepAwaitingData.connect
def __step_execution_awaiting_data_callback(sender, **kwargs):
    workflow_result = case_database.case_db.session.query(WorkflowResult).filter(
        WorkflowResult.uid == sender.workflow_execution_uid).first()
    if workflow_result is not None:
        workflow_result.trigger_step_awaiting_data()
        case_database.case_db.session.commit()


@TriggerStepTaken.connect
def __step_execution_awaiting_data_callback(sender, **kwargs):
    workflow_result = case_database.case_db.session.query(WorkflowResult).filter(
        WorkflowResult.uid == sender.workflow_execution_uid).first()
    if workflow_result is not None:
        workflow_result.trigger_step_executing()
        case_database.case_db.session.commit()


@WorkflowPaused.connect
def __step_execution_awaiting_data_callback(sender, **kwargs):
    workflow_result = case_database.case_db.session.query(WorkflowResult).filter(
        WorkflowResult.uid == sender.workflow_execution_uid).first()
    if workflow_result is not None:
        workflow_result.paused()
        case_database.case_db.session.commit()


@WorkflowResumed.connect
def __step_execution_awaiting_data_callback(sender, **kwargs):
    workflow_result = case_database.case_db.session.query(WorkflowResult).filter(
        WorkflowResult.uid == sender.workflow_execution_uid).first()
    if workflow_result is not None:
        workflow_result.resumed()
        case_database.case_db.session.commit()
