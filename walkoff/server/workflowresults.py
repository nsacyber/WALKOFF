import json

import walkoff.case.database as case_database
from walkoff.case.workflowresults import WorkflowResult, ActionResult
from walkoff.events import WalkoffEvent


@WalkoffEvent.WorkflowShutdown.connect
def __workflow_ended_callback(sender, **kwargs):
    workflow_result = case_database.case_db.session.query(WorkflowResult).filter(
        WorkflowResult.uid == sender['workflow_execution_uid']).first()
    if workflow_result is not None:
        workflow_result.complete()
        case_database.case_db.session.commit()


@WalkoffEvent.WorkflowExecutionStart.connect
def __workflow_started_callback(sender, **kwargs):
    workflow_result = WorkflowResult(sender['workflow_execution_uid'], sender['name'])
    case_database.case_db.session.add(workflow_result)
    case_database.case_db.session.commit()


def __append_action_result(workflow_result, data, action_type):
    action_result = ActionResult(data['name'], json.dumps(data['result']), json.dumps(data['arguments']), action_type,
                                 data['app_name'], data['action_name'])
    workflow_result.results.append(action_result)
    case_database.case_db.session.commit()


@WalkoffEvent.ActionExecutionSuccess.connect
def __action_execution_success_callback(sender, **kwargs):
    workflow_result = case_database.case_db.session.query(WorkflowResult).filter(
        WorkflowResult.uid == sender['workflow_execution_uid']).first()
    if workflow_result is not None:
        data = {'name': sender['name'],
                'app_name': sender['app_name'],
                'action_name': sender['action_name'],
                'arguments': sender['arguments'] if 'arguments' in sender else [],
                'result': kwargs['data']}
        __append_action_result(workflow_result, data, 'success')


@WalkoffEvent.ActionExecutionError.connect
def __action_execution_error_callback(sender, **kwargs):
    workflow_result = case_database.case_db.session.query(WorkflowResult).filter(
        WorkflowResult.uid == sender['workflow_execution_uid']).first()
    if workflow_result is not None:
        data = {'name': sender['name'],
                'app_name': sender['app_name'],
                'action_name': sender['action_name'],
                'arguments': sender['arguments'] if 'arguments' in sender else [],
                'result': kwargs['data']}
        __append_action_result(workflow_result, data, 'error')


@WalkoffEvent.TriggerActionAwaitingData.connect
def __action_execution_awaiting_data_callback(sender, **kwargs):
    workflow_result = case_database.case_db.session.query(WorkflowResult).filter(
        WorkflowResult.uid == sender['workflow_execution_uid']).first()
    if workflow_result is not None:
        workflow_result.trigger_action_awaiting_data()
        case_database.case_db.session.commit()


@WalkoffEvent.TriggerActionTaken.connect
def __action_trigger_taken_callback(sender, **kwargs):
    workflow_result = case_database.case_db.session.query(WorkflowResult).filter(
        WorkflowResult.uid == kwargs['data']['workflow_execution_id']).first()
    if workflow_result is not None:
        workflow_result.trigger_action_executing()
        case_database.case_db.session.commit()


@WalkoffEvent.WorkflowPaused.connect
def __workflow_paused_callback(sender, **kwargs):
    workflow_result = case_database.case_db.session.query(WorkflowResult).filter(
        WorkflowResult.uid == sender['workflow_execution_uid']).first()
    if workflow_result is not None:
        workflow_result.paused()
        case_database.case_db.session.commit()


@WalkoffEvent.WorkflowResumed.connect
def __workflow_resumed_callback(sender, **kwargs):
    workflow_result = case_database.case_db.session.query(WorkflowResult).filter(
        WorkflowResult.uid == sender['workflow_execution_uid']).first()
    if workflow_result is not None:
        workflow_result.resumed()
        case_database.case_db.session.commit()
