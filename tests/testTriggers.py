import unittest, json
from server import flaskServer as server

class TestTriggers(unittest.TestCase):
    def setUp(self):
        self.app = server.app.test_client(self)
        self.app.testing = True
        response = self.app.post('/login', data=dict(email='admin', password='admin'), follow_redirects=True)
        response = self.app.post('/key', data=dict(email='admin', password='admin'), follow_redirects=True).get_data(as_text=True)

        self.key = json.loads(response)["auth_token"]
        self.headers = {"Authentication-Token" : self.key}
        self.testTriggerName = "testTrigger"
        self.testTriggerPlay = "HelloWorldWorkflow"

    def test_display_triggers(self):
        response = self.app.post('/execution/listener/triggers', headers=self.headers).get_data(as_text=True)

    def test_add_and_remove_trigger(self):
        data = {"name":self.testTriggerName, "play":self.testTriggerName, "conditional-0":"{'flag':'regMatch', 'args':{'regex': '(.*)' }, 'filters':[]}"}
        response = json.loads(self.app.post('/execution/listener/triggers/add', data=data, headers=self.headers).get_data(as_text=True))
        self.assertTrue(response["status"] == "trigger successfully added")

        response = json.loads(self.app.post('/execution/listener/triggers/' + self.testTriggerName + '/remove', headers=self.headers).get_data(as_text=True))
        self.assertTrue(response["status"] == "removed trigger")



