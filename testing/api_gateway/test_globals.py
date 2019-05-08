import logging
import json

from flask.testing import FlaskClient

from testing.api_gateway.helpers import assert_crud_resource

logger = logging.getLogger(__name__)
globals_url = "/api/globals"


def test_sanity_check(api_gateway: FlaskClient, auth_header, execdb):
    """Assert that Execution Database is empty"""

    p = api_gateway.get(globals_url, headers=auth_header)
    assert p.get_json() == []


def test_create_global_no_template(api_gateway: FlaskClient, auth_header, execdb):
    """Assert that creating a global without a template is accepted"""
    inputs = [
        {
            "create": """
            {
                "name": "string",
                "value": "bar",
                "description": "string global variable"
            }
            """,
        },
        {
            "create": """
            {
                "name": "number",
                "value": 1234,
                "description": "number global variable"
            }
            """,
        },
        {
            "create": """
            {
                "name": "number2",
                "value": 1234.5678,
                "description": "float global variable"
            }
            """,
        },
        {
            "create": """
            {
                "name": "object", 
                "value": {
                    "string": "bar",
                    "number": 1234,
                    "number2": 1234.567,
                    "object": {
                        "string": "bar",
                        "number": 1234,
                        "number2": 1234.567,
                        "object": {
                            "string": "bar",
                            "number": 1234,
                            "number2": 1234.567
                        },
                        "array": [
                            "bar",
                            1234,
                            1234.567
                        ],
                        "boolean": true,
                        "boolean2": false
                    },
                    "array": [
                        "bar",
                        1234,
                        1234.567
                    ],
                    "boolean": true,
                    "boolean2": false
                },
                "description": "Nested JSON global"
            }
            """,
        },
        {
            "create": """
            {
                "name": "array",
                "value": [
                    "bar",
                    "1234",
                    "1234.567"
                ],
                "description": "array global variable"
            }
            """,
        },
        {
            "create": """
            {
                "name": "boolean",
                "value": true,
                "description": "boolean global variable"
            }
            """,
        },
        {
            "create": """
            {
                "name": "boolean2",
                "value": false,
                "description": "boolean global variable"
            }
            """,
        }
    ]
    assert_crud_resource(api_gateway, auth_header, globals_url, inputs, json.loads)


# def test_read_all_globals_in_db(api_gateway, token, serverdb, execdb):
#     header = {'Authorization': 'Bearer {}'.format(token['access_token']), 'content-type': 'application/json'}
#     response = api_gateway.get("/api/globals", headers=header)
#     key = json.loads(response.get_data(as_text=True))
#     assert response.status_code == 200
#     assert key == []
#
#
# def test_read_all_globals(api_gateway, token, serverdb, execdb):
#     header = {'Authorization': 'Bearer {}'.format(token['access_token']), 'content-type': 'application/json'}
#     global1 = {'description': 'test1', 'name': 'test1', 'value': 'test1'}
#     global2 = {'description': 'test2', 'name': 'test2', 'value': 'test2'}
#
#     add_global1 = api_gateway.post('/api/globals',
#                                    data=json.dumps(global1), headers=header)
#     add_global2 = api_gateway.post('/api/globals',
#                                    data=json.dumps(global2), headers=header)
#     key1 = json.loads(add_global1.get_data(as_text=True))
#     key2 = json.loads(add_global2.get_data(as_text=True))
#     id_1 = key1['id_']
#     id_2 = key2['id_']
#     assert key1['name'] == 'test1'
#     assert key2['name'] == 'test2'
#
#     get_global1 = api_gateway.get(f'/api/globals/{id_1}', headers=header)
#     get_global2 = api_gateway.get(f'/api/globals/{id_2}', headers=header)
#
#     name1 = json.loads(get_global1.get_data(as_text=True))
#     name2 = json.loads(get_global2.get_data(as_text=True))
#
#     assert name1['name'] == 'test1'
#     assert name2['name'] == 'test2'
#
#
# def test_read_global_does_not_exist(api_gateway, token, serverdb, execdb):
#     header = {'Authorization': 'Bearer {}'.format(token['access_token']), 'content-type': 'application/json'}
#     fake_id = "8254ba1a-3f6a-40c6-b0c7-d00acd40650d"
#     response = api_gateway.get(f'/api/globals/{fake_id}', headers=header)
#     assert response.status_code == 404
#
#
# def test_update_global_exists(api_gateway, token, serverdb, execdb):
#     header = {'Authorization': 'Bearer {}'.format(token['access_token']), 'content-type': 'application/json'}
#     global1 = {'description': 'test1', 'name': 'foo', 'value': '12345'}
#     add_global1 = api_gateway.post('/api/globals',
#                                    data=json.dumps(global1), headers=header)
#     key1 = json.loads(add_global1.get_data(as_text=True))
#
#     assert key1['description'] == 'test1'
#     assert key1['name'] == 'foo'
#     assert key1['value'] == '12345'
#
#     global_id = key1['id_']
#     data = {'description': 'updated test1', 'name': 'foo2', 'value': '12345'}
#     response = api_gateway.put(f'/api/globals/{global_id}', headers=header, data=json.dumps(data))
#
#     assert response.status_code == 200
#
#     response = api_gateway.get(f'/api/globals/{global_id}', headers=header)
#     check = json.loads(response.get_data(as_text=True))
#
#     assert check['description'] == 'updated test1'
#     assert check['name'] == 'foo2'
#     assert check['value'] == '12345'
#
#
