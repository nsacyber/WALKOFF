import json
import unittest

from server import flaskServer as server
from server.triggers import Triggers
from tests.util.assertwrappers import assert_post_status, assert_get_status


class TestTriggers(unittest.TestCase):
    def setUp(self):
        self.app = server.app.test_client(self)
        self.app.testing = True
        self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)
        response = self.app.post('/key', data=dict(email='admin', password='admin'), follow_redirects=True).get_data(
            as_text=True)

        self.key = json.loads(response)["auth_token"]
        self.headers = {"Authentication-Token": self.key}
        self.test_trigger_name = "testTrigger"
        self.test_trigger_workflow = "helloWorldWorkflow"

    def tearDown(self):
        with server.running_context.flask_app.app_context():
            Triggers.query.filter_by(name=self.test_trigger_name).delete()
            Triggers.query.filter_by(name="{0}rename".format(self.test_trigger_name)).delete()
            server.database.db.session.commit()

    # def test_display_triggers(self):
    #    response = self.app.post('/execution/listener/triggers', headers=self.headers).get_data(as_text=True)

    def test_add_and_display_and_remove_trigger(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditional-0": json.dumps(condition)}
        assert_post_status(self, self.app, '/execution/listener/triggers/{0}/add'.format(self.test_trigger_name),
                           self.headers, "success", data=data)
        triggers = [trigger.as_json() for trigger in Triggers.query.all()]
        self.assertEqual(len(triggers), 1)

        expected_json = {'name': self.test_trigger_name,
                         'playbook': 'test',
                         'workflow': self.test_trigger_workflow,
                         'conditions': [condition]}
        self.assertEqual(triggers[0]['name'], expected_json['name'])
        self.assertEqual(triggers[0]['workflow'], expected_json['workflow'])
        self.assertEqual(triggers[0]['playbook'], expected_json['playbook'])
        self.assertDictEqual(json.loads(triggers[0]['conditions'][0]), expected_json['conditions'][0])

        response = assert_get_status(self, self.app, '/execution/listener/triggers', self.headers, "success")
        self.assertIn('triggers', response)
        self.assertEqual(len(response['triggers']), 1)
        self.assertEqual(response['triggers'][0]['name'], expected_json['name'])
        self.assertEqual(response['triggers'][0]['workflow'], expected_json['workflow'])
        self.assertEqual(response['triggers'][0]['playbook'], expected_json['playbook'])
        self.assertDictEqual(json.loads(response['triggers'][0]['conditions'][0]), expected_json['conditions'][0])

        response = assert_post_status(self, self.app,
                                      '/execution/listener/triggers/{0}/display'.format(self.test_trigger_name),
                                      self.headers, "success")
        self.assertIn('trigger', response)
        self.assertEqual(response['trigger']['name'], expected_json['name'])
        self.assertEqual(response['trigger']['workflow'], expected_json['workflow'])
        self.assertEqual(response['trigger']['playbook'], expected_json['playbook'])
        self.assertDictEqual(json.loads(response['trigger']['conditions'][0]), expected_json['conditions'][0])

        assert_post_status(self, self.app,
                           '/execution/listener/triggers/{0}/remove'.format(self.test_trigger_name),
                           self.headers, "success")

        triggers = [trigger.as_json() for trigger in Triggers.query.all()]
        self.assertEqual(len(triggers), 0)

        assert_post_status(self, self.app,
                           '/execution/listener/triggers/{0}/display'.format(self.test_trigger_name),
                           self.headers, "error: trigger not found")

    def test_add_trigger_invalid_form(self):
        data = {"playbrook": "test",
                "workbro": self.test_trigger_workflow,
                "conditional-0": ""}
        assert_post_status(self, self.app, '/execution/listener/triggers/{0}/add'.format(self.test_trigger_name),
                           self.headers, "error: form not valid", data=data)

    def test_add_trigger_add_duplicate(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditional-0": json.dumps(condition)}
        assert_post_status(self, self.app, '/execution/listener/triggers/{0}/add'.format(self.test_trigger_name),
                           self.headers, "success", data=data)
        assert_post_status(self, self.app, '/execution/listener/triggers/{0}/add'.format(self.test_trigger_name),
                           self.headers, "warning: trigger with that name already exists", data=data)

    def test_remove_trigger_does_not_exist(self):
        assert_post_status(self, self.app,
                           '/execution/listener/triggers/{0}/remove'.format(self.test_trigger_name),
                           self.headers, "error: trigger does not exist")

    def test_edit_trigger(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditional-0": json.dumps(condition)}
        assert_post_status(self, self.app, '/execution/listener/triggers/{0}/add'.format(self.test_trigger_name),
                           self.headers, "success", data=data)
        edited_data = {"name": "{0}rename".format(self.test_trigger_name),
                       "playbook": "testrename",
                       "workflow": '{0}rename'.format(self.test_trigger_workflow),
                       "conditional-0": json.dumps(condition)}
        assert_post_status(self, self.app,
                           '/execution/listener/triggers/{0}/edit'.format(self.test_trigger_name),
                           self.headers, "success", data=edited_data)

    def test_trigger_execute(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditional-0": json.dumps(condition)}
        assert_post_status(self, self.app, '/execution/listener/triggers/{0}/add'.format(self.test_trigger_name),
                           self.headers, "success", data=data)

        assert_post_status(self, self.app, '/execution/listener'.format(self.test_trigger_name),
                           self.headers, "success", data={"data": "hellohellohello"})

    def test_trigger_execute_invalid_name(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": "invalid_workflow_name",
                "conditional-0": json.dumps(condition)}
        assert_post_status(self, self.app, '/execution/listener/triggers/{0}/add'.format(self.test_trigger_name),
                           self.headers, "success", data=data)

        assert_post_status(self, self.app, '/execution/listener'.format(self.test_trigger_name),
                           self.headers, "error: workflow could not be found", data={"data": "hellohellohello"})

    def test_trigger_execute_no_matching_trigger(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": 'aaa'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditional-0": json.dumps(condition)}
        assert_post_status(self, self.app, '/execution/listener/triggers/{0}/add'.format(self.test_trigger_name),
                           self.headers, "success", data=data)

        assert_post_status(self, self.app, '/execution/listener'.format(self.test_trigger_name),
                           self.headers, "warning: no trigger found valid for data in", data={"data": "bbb"})