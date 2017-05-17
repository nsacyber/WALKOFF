import json

from tests.util.servertestcase import ServerTestCase
from server import flaskserver as server
from server.triggers import Triggers
from server.return_codes import *

from core.case.callbacks import FunctionExecutionSuccess


class TestTriggers(ServerTestCase):
    def setUp(self):
        self.test_trigger_name = "testTrigger"
        self.test_trigger_workflow = "helloWorldWorkflow"

    def tearDown(self):
        with server.running_context.flask_app.app_context():
            Triggers.query.filter_by(name=self.test_trigger_name).delete()
            Triggers.query.filter_by(name="{0}rename".format(self.test_trigger_name)).delete()
            server.database.db.session.commit()

    def test_add_and_display_and_remove_trigger(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditional": json.dumps([condition])}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   "success", headers=self.headers, data=data, status_code=OBJECT_CREATED)
        triggers = [trigger.as_json() for trigger in Triggers.query.all()]
        self.assertEqual(len(triggers), 1)

        expected_json = {'name': self.test_trigger_name,
                         'playbook': 'test',
                         'workflow': self.test_trigger_workflow,
                         'conditions': [condition]}
        self.assertEqual(triggers[0]['name'], expected_json['name'])
        self.assertEqual(triggers[0]['workflow'], expected_json['workflow'])
        self.assertEqual(triggers[0]['playbook'], expected_json['playbook'])
        self.assertDictEqual(triggers[0]['conditions'][0], expected_json['conditions'][0])

        response = self.get_with_status_check('/execution/listener/triggers', "success", headers=self.headers)
        self.assertIn('triggers', response)
        self.assertEqual(len(response['triggers']), 1)
        self.assertEqual(response['triggers'][0]['name'], expected_json['name'])
        self.assertEqual(response['triggers'][0]['workflow'], expected_json['workflow'])
        self.assertEqual(response['triggers'][0]['playbook'], expected_json['playbook'])
        self.assertDictEqual(response['triggers'][0]['conditions'][0], expected_json['conditions'][0])

        response = self.get_with_status_check(
            '/execution/listener/triggers/{0}'.format(self.test_trigger_name),
            "success", headers=self.headers)
        self.assertIn('trigger', response)
        self.assertEqual(response['trigger']['name'], expected_json['name'])
        self.assertEqual(response['trigger']['workflow'], expected_json['workflow'])
        self.assertEqual(response['trigger']['playbook'], expected_json['playbook'])
        self.assertDictEqual(response['trigger']['conditions'][0], expected_json['conditions'][0])

        self.delete_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                      "success", headers=self.headers)

        triggers = [trigger.as_json() for trigger in Triggers.query.all()]
        self.assertEqual(len(triggers), 0)

        self.get_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   "Trigger does not exist.", headers=self.headers, status_code=OBJECT_DNE_ERROR)

    def test_add_trigger_invalid_form(self):
        data = {"playbrook": "test",
                "workbro": self.test_trigger_workflow,
                "conditional-0": ""}
        response = self.app.put('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                headers=self.headers,
                                data=data)
        self.assertEqual(response._status_code, 400)

    def test_add_trigger_add_duplicate(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditional": json.dumps(condition)}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   "success", headers=self.headers, data=data, status_code=OBJECT_CREATED)
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   "Trigger already exists.", headers=self.headers, data=data,
                                   status_code=OBJECT_EXISTS_ERROR)

    def test_remove_trigger_does_not_exist(self):
        self.delete_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                      "Trigger does not exist.", headers=self.headers, status_code=OBJECT_DNE_ERROR)

    def test_edit_trigger(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditional": json.dumps(condition)}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   "success", headers=self.headers, data=data, status_code=OBJECT_CREATED)
        edited_data = {"name": "{0}rename".format(self.test_trigger_name),
                       "playbook": "testrename",
                       "workflow": '{0}rename'.format(self.test_trigger_workflow),
                       "conditional": json.dumps(condition)}
        self.post_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                    "success", headers=self.headers, data=edited_data)

    def test_trigger_execute(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditional": json.dumps([condition])}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   "success", headers=self.headers, data=data, status_code=OBJECT_CREATED)

        self.post_with_status_check('/execution/listener/execute'.format(self.test_trigger_name),
                                    "success", headers=self.headers, data={"data": "hellohellohello"})

    def test_trigger_execute_invalid_name(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": "invalid_workflow_name",
                "conditional": json.dumps([condition])}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   "success", headers=self.headers, data=data, status_code=OBJECT_CREATED)

        self.post_with_status_check('/execution/listener/execute'.format(self.test_trigger_name),
                                    "error: workflow could not be found",
                                    headers=self.headers, data={"data": "hellohellohello"})

    def test_trigger_execute_no_matching_trigger(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": 'aaa'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditional": json.dumps([condition])}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   "success", headers=self.headers, data=data, status_code=OBJECT_CREATED)

        self.post_with_status_check('/execution/listener/execute'.format(self.test_trigger_name),
                                    "warning: no trigger found valid for data in", headers=self.headers,
                                    data={"data": "bbb"})

    def test_trigger_execute_change_input(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditional": json.dumps([condition])}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   "success", headers=self.headers, data=data, status_code=OBJECT_CREATED)

        result = {'value': None}

        def step_finished_listener(sender, **kwargs):
            result['value'] = kwargs['data']

        FunctionExecutionSuccess.connect(step_finished_listener)

        data = {"data": "hellohellohello",
                "input": json.dumps([{"key": "call", "value": "CHANGE INPUT"}])}

        self.post_with_status_check('/execution/listener/execute'.format(self.test_trigger_name),
                                    "success", headers=self.headers, data=data)
