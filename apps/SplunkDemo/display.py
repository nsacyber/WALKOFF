from flask import Blueprint
from apps import AppBlueprint
import os.path
import json
import core.case.database as case_database
from core.case.workflowresults import WorkflowResult

blueprint = AppBlueprint(blueprint=Blueprint('SplunkDemoPage', __name__))


def load(*args, **kwargs):
    """
           Entry point for server side interface code
    """
    return {}

default_data_file = os.path.join('.', 'apps', 'SplunkDemo', 'data', 'data.json')


@blueprint.blueprint.route('/data', methods=['GET'])
def get_data():
    if not os.path.exists(default_data_file):
        return {'error': 'data not found'}, 404
    with open(default_data_file, 'r') as file_in:
        data_in = json.loads(file_in.read())

    workflow_result = case_database.case_db.session.query(WorkflowResult).filter(WorkflowResult.uid == 'INSERT UID HERE').first()
    unrolled_steps = []
    for step_result in workflow_result.results:
        if step_result.app != 'Walkoff' or step_result.action != 'wait for workflow completion':
            step_as_json = step_result.as_json()
            step_as_json['location'] = 'local'
            unrolled_steps.append(step_as_json)
        else:
            remote_workflowresults = step_result.results # this will itself be a workflowResults object
            remote_steps_results = remote_workflowresults['results']
            for step in remote_steps_results:
                step['location'] = 'remote'
                unrolled_steps.append(step)

    data_in.update({'workflow_results': unrolled_steps})
    # update with pcap and bin
    return data_in






