import json
import unittest

from server import flaskServer as server
from server.database import db
from server.triggers import Triggers


class TestTriggers(unittest.TestCase):
    def setUp(self):
        self.app = server.app.test_client(self)
        self.app.testing = True
        response = self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)
        response = self.app.post('/key', data=dict(email='admin', password='admin'), follow_redirects=True).get_data(
            as_text=True)

        self.key = json.loads(response)["auth_token"]
        self.headers = {"Authentication-Token": self.key}
        self.testTriggerName = "testTrigger"
        self.testTriggerPlay = "HelloWorldWorkflow"

    def tearDown(self):
        Triggers.query.filter_by(name=self.testTriggerName).delete()
        db.session.commit()

    def test_display_triggers(self):
        response = self.app.post('/execution/listener/triggers', headers=self.headers).get_data(as_text=True)

    def test_add_and_remove_trigger(self):
        data = {"name": self.testTriggerName,
                "play": self.testTriggerPlay,
                "conditional-0": "{'flag':'regMatch', 'args':{'regex': '(.*)' }, 'filters':[]}"}
        response = json.loads(
            self.app.post('/execution/listener/triggers/add', data=data, headers=self.headers).get_data(as_text=True))

        self.assertEqual(response["status"], "trigger successfully added")

        response = json.loads(self.app.post('/execution/listener/triggers/' + self.testTriggerName + '/remove',
                                            headers=self.headers).get_data(as_text=True))
        self.assertEqual(response["status"], "removed trigger")

    def test_trigger_execute(self):
        data = {"name": self.testTriggerName,
                "play": "basicWorkflow.workflow",
                "conditional-0": "{'flag':'regMatch', 'args':[{'type': 'str', 'value': '(.*)', 'key': 'regex'}], 'filters':[]}"
                }
        response = json.loads(
            self.app.post('/execution/listener/triggers/add', data=data, headers=self.headers).get_data(as_text=True))
        self.assertEqual(response["status"], "trigger successfully added")

        response = self.app.post('/execution/listener',
                                            data={"data": "hellohellohello"}, headers=self.headers).get_data(as_text=True)
        response = json.loads(response)
        #self.assertEqual(response[self.testTriggerName][0]['output'], 'REPEATING: Hello World')
