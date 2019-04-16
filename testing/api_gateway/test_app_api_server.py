import pytest

import api_gateway.config

from api_gateway.server.endpoints.appapi import *
from api_gateway.server.app import app

import json



def test_read_all_apps(api_gateway, token):
  # key = json.loads(response.get_data(as_text=True))
  header = {'Authorization': 'Bearer {}'.format(token['access_token'])}

  SUCCESS = 200
  expected_apps = ['HelloWorld']
  response = api_gateway.post('/api/apps', data="HelloWorld", headers=header)
  response = api_gateway.get('/api/apps' ,headers=header)

  assert response.status_code == SUCCESS
  # response = json.loads(response.get_data(as_text=True))
  # assert len(response) == len(expected_apps)
  # assert set(response) == set(expected_apps)

def test_extract_schema():
    test_json = {'name': 'a', 'example': 42, 'description': 'something', 'type': 'number', 'minimum': 1}
    expected = {'name': 'a', 'example': 42, 'description': 'something', 'schema': {'type': 'number', 'minimum': 1}}
    assert extract_schema(test_json) == expected

def test_extract_schema_unformatted_fields_specified():
    test_json = {'name': 'a', 'example': 42, 'description': 'something', 'type': 'number', 'minimum': 1}
    expected = {'name': 'a', 'example': 42,
                'schema': {'description': 'something', 'type': 'number', 'minimum': 1}}
    assert (extract_schema(test_json, unformatted_fields=('name', 'example')) == expected)

def test_extract_schema_with_object():
    test_json = {'name': 'a', 'description': 'something', 'type': 'object',
                 'schema': {'required': ['a', 'b'],
                            'properties': {'a': {'type': 'string'},
                                           'b': {'type': 'number'}}}}
    expected = {'name': 'a', 'description': 'something',
                'schema': {'type': 'object',
                           'required': ['a', 'b'],
                           'properties': {'a': {'type': 'string'},
                                          'b': {'type': 'number'}}}}
    assert extract_schema(test_json) == expected

def test_format_returns():
    returns = {'Success': {'description': 'something 1'}, 'Return2': {'schema': {'type': 'number', 'minimum': 10}}}
    expected = [{'status': 'Success', 'description': 'something 1'},
                {'status': 'Return2', 'schema': {'type': 'number', 'minimum': 10}},
                {'status': 'UnhandledException', 'failure': True, 'description': 'Exception occurred in action'},
                {'status': 'InvalidInput', 'failure': True, 'description': 'Input into the action was invalid'}]
    formatted = format_returns(returns)
    assert len(formatted) == len(expected)
    for return_ in formatted:
        assert return_ in expected

def test_format_returns_with_event():
    returns = {'Success': {'description': 'something 1'},
               'Return2': {'schema': {'type': 'number', 'minimum': 10}}}
    expected = [{'status': 'Success', 'description': 'something 1'},
                {'status': 'Return2', 'schema': {'type': 'number', 'minimum': 10}},
                {'status': 'UnhandledException', 'failure': True, 'description': 'Exception occurred in action'},
                {'status': 'InvalidInput', 'failure': True, 'description': 'Input into the action was invalid'},
                {'status': 'EventTimedOut', 'failure': True,
                 'description': 'Action timed out out waiting for event'}]
    formatted = format_returns(returns, with_event=True)
    assert len(formatted) == len(expected)
    for return_ in formatted:
        assert return_ in expected

# def test_format_app_action_api():
#     action_api = walkoff.config.app_apis['HelloWorldBounded']['actions']['pause']
#     expected = {
#         'returns': [{'status': 'Success', 'description': 'successfully paused', 'schema': {'type': 'number'}},
#                     {'status': 'UnhandledException', 'failure': True,
#                      'description': 'Exception occurred in action'},
#                     {'status': 'InvalidInput', 'failure': True,
#                      'description': 'Input into the action was invalid'}],
#         'run': 'main.Main.pause',
#         'description': 'Pauses execution',
#         'parameters': [
#             {'schema': {'type': 'number'}, 'name': 'seconds', 'description': 'Seconds to pause', 'required': True}]}
#     formatted = format_app_action_api(action_api, "HelloWorldBounded", "actions")
#     assert set(formatted.keys()) == set(expected.keys())
#     assert formatted['run'] == expected['run']
#     assert formatted['description'] == expected['description']
#     assert len(formatted['returns']) == len(expected['returns'])
#     for return_ in formatted['returns']:
#         assert return_ in expected['returns']
#     assert len(formatted['parameters']) == len(expected['parameters'])
#     for parameter in formatted['parameters']:
#         assert parameter in expected['parameters']

def test_format_device_api():
    device_api = {'description': 'Something',
                  'fields': [
                      {'name': 'username', 'placeholder': 'user', 'type': 'string', 'required': True,
                       'description': 'something'},
                      {'name': 'password', 'placeholder': 'pass', 'type': 'string', 'required': True, 'encrypted':
                          True, 'minimumLength': 6}]}
    formatted = format_device_api_full(device_api, 'TestDev')
    expected = {'description': 'Something',
                'name': 'TestDev',
                'fields': [
                    {'name': 'username', 'placeholder': 'user', 'required': True, 'schema': {'type': 'string'},
                     'description': 'something'},
                    {'name': 'password', 'placeholder': 'pass', 'encrypted': True, 'required': True,
                     'schema': {'type': 'string', 'minimumLength': 6}}]}
    assert set(formatted.keys()) == set(expected.keys())
    assert formatted['name'] == expected['name']
    assert formatted['description'] == expected['description']
    for field in formatted['fields']:
        assert field in expected['fields']


# def test_read_all_app_apis(api_gateway, token):
# 	header = {'Authorization': 'Bearer {}'.format(token['access_token'])}

# 	apps =  ['HelloWorldBounded', 'DailyQuote', 'HelloWorld']
# 	SUCCESS = 200
# 	response = api_gateway.get('/api/apps/apis', headers=header)
	
	
# 	assert json.loads(response.get_data(as_text=True)) == "hi"
# 	# assert len([app['name'] for app in response]) == len(apps)

# def test_read_all_app_apis_with_field(self):
#     response = self.test_client.get('/api/apps/apis?field_name=action_apis', headers=self.headers)
#     self.assertEqual(response.status_code, SUCCESS)
#     response = json.loads(response.get_data(as_text=True))
#     orderless_list_compare(self, [app['name'] for app in response],
#                            ['HelloWorldBounded', 'DailyQuote', 'HelloWorld'])
#     for app in response:
#         self.assertSetEqual(set(app.keys()), {'name', 'action_apis'})

def test_read_app_api_app_dne(api_gateway, token):
	header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
	try:
		response = api_gateway.get('/api/apps/apis/Invalid', headers=header)
		return False
	except:
		return True

def test_read_app_api_field_app_dne(api_gateway, token):
	header = {'Authorization': 'Bearer {}'.format(token['access_token'])}
	try:
		response = api_gateway.get('/api/apps/apis/Invalid/info', headers=header)
		return False
	except:
		return True