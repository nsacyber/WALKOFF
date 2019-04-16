import pytest

import api_gateway.server.endpoints.workflows
from api_gateway.executiondb.workflow import Workflow, WorkflowSchema
from api_gateway.executiondb.workflowresults import WorkflowStatus, WorkflowStatusSchema, WorkflowStatusSummarySchema

import json
import logging
from flask import request, current_app, send_file
# def test_abort_workflow(api_gateway, workflow, execdb):
@pytest.fixture
def data():
	with open("testing/util/workflow.json") as fp:
		wf_json = json.load(fp)
		data = json.dumps(wf_json)

	yield data

@pytest.fixture
def header(token):
	yield {'Authorization': 'Bearer {}'.format(token['access_token'])}


def test_workflow_post_and_get(api_gateway, execdb, header, data):
	response1 = api_gateway.post('/api/workflows', data=data, headers=header, content_type="application/json")
	assert response1.status_code == 201

	response2 = api_gateway.get('/api/workflows', data={"workflow_id": "e8c7840a-bd3e-4cfd-b9be-e07269b10c89"}, headers=header, content_type="application/json")
	key = json.loads(response2.get_data(as_text=True))
	data_json = json.loads(data)
	assert key[0]["id_"] == data_json["id_"]
	assert key[0]["name"] == data_json["name"]

	check = execdb.session.query(Workflow).filter_by(name=data_json["name"]).first()
	assert not (check == None)
	#response3 = api_gateway.delete('/api/workflows', data={"workflow_id": "e8c7840a-bd3e-4cfd-b9be-e07269b10c89"}, headers=header)
	#assert response3.status_code == 204

def test_workflow_delete(api_gateway, execdb, header, data):
	response = api_gateway.post('/api/workflows', data=data, headers=header, content_type="application/json")
	
	check = execdb.session.query(Workflow).filter_by(name="ConditionTest").first()
	assert not (check == None)
	response2 = api_gateway.delete('/api/workflows', data={"workflow_id": "e8c7840a-bd3e-4cfd-b9be-e07269b10c89"}, headers=header)
	assert response2.status_code == "hi"

def test_workflow_delete_invalid(api_gateway, execdb, header, data):
	response = api_gateway.delete('/api/workflows', data={"workflow_id": "e8c7840a-bd3e-4cfd-b9be-e07269b10c90"}, headers=header)
	assert response.status_code == 404


# def test_get_workflow_invalid(api_gateway, execdb, header, data):
# 	response = api_gateway.get('api_workflows', data={"workflow_id": "invalid"}, headers=header,content_type="application/json")
# 	key = json.loads(response.get_data(as_text=True))

# 	assert key == "Hi"
