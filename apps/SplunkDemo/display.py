from flask import Blueprint
from apps import AppBlueprint
import os.path
import json
import os
import core.case.database as case_database
from core.case.workflowresults import WorkflowResult
import pprint
blueprint = AppBlueprint(blueprint=Blueprint('SplunkDemoPage', __name__))


def load(*args, **kwargs):
    """
           Entry point for server side interface code
    """
    return {}

default_data_file = os.path.join('.', 'apps', 'SplunkDemo', 'data', 'data.json')

@blueprint.blueprint.route('/data', methods=['GET'])
def get_data():
   
    workflow_result = case_database.case_db.session.query(WorkflowResult).all()[0]
    unrolled_steps = []
    for step_result in workflow_result.results:
        if step_result.app != 'Walkoff' or step_result.action != 'wait for workflow completion':
            step_as_json = step_result.as_json()
            step_as_json['location'] = 'local'
            unrolled_steps.append(step_as_json)
        else:
            remote_workflowresults = step_result.result # this will itself be a workflowResults object
            remote_workflowresults = json.loads(remote_workflowresults)['result']
            for step in remote_workflowresults['results']:
                step['location'] = 'remote'
                unrolled_steps.append(step)
    workflow_results = unrolled_steps
    echo_step = next((step for step in unrolled_steps if step['action'] == 'echo object'), None)
    data = echo_step['input']['data']
    print(data)
    response = {'workflow_results': unrolled_steps, 
                'pcap_name': 'capture.pcap',
                'exe_name': 'quanrantined_malware.bin'}
    response.update(data)
    # update with pcap and bin
    return response

@blueprint.blueprint.route('/view_pcap', methods=['GET'])
def view_in_wireshark():
    os.system('wireshark -r /home/ubunutu/WALKOFF/SplunkDemo/data/capture.pcap &')




