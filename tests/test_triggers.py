import json

from tests.util.servertestcase import ServerTestCase
from server import flaskserver as server
from server.triggers import Triggers
from server.return_codes import *
from core.helpers import import_all_apps, import_all_filters, import_all_flags
from tests.apps import App
from tests import config
import core.config.config

from core.case.callbacks import FunctionExecutionSuccess


class TestTriggers(ServerTestCase):
    def setUp(self):
        App.registry = {}
        import_all_apps(path=config.test_apps_path, reload=True)
        core.config.config.load_app_apis(apps_path=config.test_apps_path)
        core.config.config.flags = import_all_flags('tests.util.flagsfilters')
        core.config.config.filters = import_all_filters('tests.util.flagsfilters')
        core.config.config.load_flagfilter_apis(path=config.function_api_path)
        self.test_trigger_name = "testTrigger"
        self.test_trigger_workflow = "helloWorldWorkflow"

    def tearDown(self):
        with server.running_context.flask_app.app_context():
            Triggers.query.filter_by(name=self.test_trigger_name).delete()
            Triggers.query.filter_by(name="execute_me").delete()
            Triggers.query.filter_by(name="execute_one").delete()
            Triggers.query.filter_by(name="execute_two").delete()
            Triggers.query.filter_by(name="execute_three").delete()
            Triggers.query.filter_by(name="execute_four").delete()
            Triggers.query.filter_by(name="{0}rename".format(self.test_trigger_name)).delete()
            server.database.db.session.commit()
            server.running_context.controller.workflows = {}

    def test_add_and_display_and_remove_trigger(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditional": json.dumps([condition])}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=data, status_code=OBJECT_CREATED)
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

        response = self.get_with_status_check('/execution/listener/triggers', headers=self.headers)
        self.assertIn('triggers', response)
        self.assertEqual(len(response['triggers']), 1)
        self.assertEqual(response['triggers'][0]['name'], expected_json['name'])
        self.assertEqual(response['triggers'][0]['workflow'], expected_json['workflow'])
        self.assertEqual(response['triggers'][0]['playbook'], expected_json['playbook'])
        self.assertDictEqual(response['triggers'][0]['conditions'][0], expected_json['conditions'][0])

        response = self.get_with_status_check(
            '/execution/listener/triggers/{0}'.format(self.test_trigger_name),
            headers=self.headers)
        self.assertIn('trigger', response)
        self.assertEqual(response['trigger']['name'], expected_json['name'])
        self.assertEqual(response['trigger']['workflow'], expected_json['workflow'])
        self.assertEqual(response['trigger']['playbook'], expected_json['playbook'])
        self.assertDictEqual(response['trigger']['conditions'][0], expected_json['conditions'][0])

        self.delete_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                      headers=self.headers)

        triggers = [trigger.as_json() for trigger in Triggers.query.all()]
        self.assertEqual(len(triggers), 0)

        self.get_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   error="Trigger does not exist.", headers=self.headers, status_code=OBJECT_DNE_ERROR)

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
                                   headers=self.headers, data=data, status_code=OBJECT_CREATED)
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   error="Trigger already exists.", headers=self.headers, data=data,
                                   status_code=OBJECT_EXISTS_ERROR)

    def test_remove_trigger_does_not_exist(self):
        self.delete_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                      error="Trigger does not exist.", headers=self.headers,
                                      status_code=OBJECT_DNE_ERROR)

    def test_edit_trigger(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditional": json.dumps(condition)}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=data, status_code=OBJECT_CREATED)
        edited_data = {"name": "{0}rename".format(self.test_trigger_name),
                       "playbook": "testrename",
                       "workflow": '{0}rename'.format(self.test_trigger_workflow),
                       "conditional": json.dumps(condition)}
        self.post_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                    headers=self.headers, data=edited_data)

    def test_trigger_execute(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditional": json.dumps([condition])}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=data, status_code=OBJECT_CREATED)

        response = self.post_with_status_check('/execution/listener/execute',
                                               headers=self.headers, data={"data": "hellohellohello"})
        self.assertSetEqual(set(response.keys()), {'errors', 'executed'})
        self.assertListEqual(response['executed'], ['testTrigger'])
        self.assertListEqual(response['errors'], [])

    def test_trigger_execute_invalid_name(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": "invalid_workflow_name",
                "conditional": json.dumps([condition])}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=data, status_code=OBJECT_CREATED)

        response = self.app.post('/execution/listener/execute', headers=self.headers, data={"data": "hellohellohello"})
        error = {self.test_trigger_name: "Workflow could not be found."}
        self.assertEqual(INVALID_INPUT_ERROR, response._status_code)
        response = json.loads(response.get_data(as_text=True))
        self.assertIn("errors", response)
        self.assertIn(error, response["errors"])

    def test_trigger_execute_no_matching_trigger(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": 'aaa'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditional": json.dumps([condition])}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=data, status_code=OBJECT_CREATED)

        self.post_with_status_check('/execution/listener/execute',
                                    headers=self.headers, data={"data": "bbb"}, status_code=SUCCESS_WITH_WARNING)

    def test_trigger_execute_change_input(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditional": json.dumps([condition])}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=data, status_code=OBJECT_CREATED)

        result = {'value': None}

        def step_finished_listener(sender, **kwargs):
            result['value'] = kwargs['data']

        FunctionExecutionSuccess.connect(step_finished_listener)

        data = {"data": "hellohellohello",
                "input": json.dumps([{"key": "call", "value": "CHANGE INPUT"}])}

        response = self.post_with_status_check('/execution/listener/execute',
                                               headers=self.headers, data=data)
        self.assertSetEqual(set(response.keys()), {'errors', 'executed'})
        self.assertListEqual(response['executed'], ['testTrigger'])
        self.assertListEqual(response['errors'], [])
        step_input = {'result': 'REPEATING: CHANGE INPUT'}
        self.assertDictEqual(json.loads(result['value']), step_input)

    def test_trigger_with_change_input_invalid_input(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditional": json.dumps([condition])}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=data, status_code=OBJECT_CREATED)

        data = {"data": "hellohellohello",
                "input": json.dumps([{"key": "invalid", "value": "CHANGE INPUT"}])}

        response = self.post_with_status_check('/execution/listener/execute',
                                               headers=self.headers, data=data, status_code=INVALID_INPUT_ERROR)
        self.assertSetEqual(set(response.keys()), {'errors', 'executed'})
        self.assertListEqual(response['executed'], [])
        self.assertEqual(len(response['errors']), 1)
        self.assertIn(self.test_trigger_name, response['errors'][0])

    def test_trigger_execute_one(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditional": json.dumps([condition])}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=data, status_code=OBJECT_CREATED)

        self.put_with_status_check('/execution/listener/triggers/{0}'.format("execute_me"),
                                   headers=self.headers, data=data, status_code=OBJECT_CREATED)

        result = {'value': 0}

        def step_finished_listener(sender, **kwargs):
            result['value'] += 1

        FunctionExecutionSuccess.connect(step_finished_listener)

        data = {"data": "hellohellohello"}

        response = self.post_with_status_check('/execution/listener/execute?name=execute_me',
                                               headers=self.headers, data=data)
        self.assertEqual(1, result['value'])
        self.assertIn("execute_me", response["executed"])
        self.assertEqual(1, len(response["executed"]))
        self.assertEqual(0, len(response["errors"]))

    def test_trigger_execute_one_invalid_name(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditional": json.dumps([condition])}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=data, status_code=OBJECT_CREATED)

        response = self.post_with_status_check('/execution/listener/execute?name=badname',
                                               headers=self.headers, data={"data": "hellohellohello"},
                                               status_code=SUCCESS_WITH_WARNING)
        self.assertEqual(0, len(response["executed"]))
        self.assertEqual(0, len(response["errors"]))

    def test_trigger_execute_tag(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditional": json.dumps([condition]),
                "tag": "wrong_tag"}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=data, status_code=OBJECT_CREATED)

        data["tag"] = "execute_tag"

        self.put_with_status_check('/execution/listener/triggers/{0}'.format("execute_one"),
                                   headers=self.headers, data=data, status_code=OBJECT_CREATED)
        self.put_with_status_check('/execution/listener/triggers/{0}'.format("execute_two"),
                                   headers=self.headers, data=data, status_code=OBJECT_CREATED)

        result = {'value': 0}

        def step_finished_listener(sender, **kwargs):
            result['value'] += 1

        FunctionExecutionSuccess.connect(step_finished_listener)

        data = {"data": "hellohellohello"}

        response = self.post_with_status_check('/execution/listener/execute?tags=execute_tag',
                                               headers=self.headers, data=data)
        self.assertEqual(2, result['value'])
        self.assertIn("execute_one", response["executed"])
        self.assertIn("execute_two", response["executed"])
        self.assertEqual(2, len(response["executed"]))
        self.assertEqual(0, len(response["errors"]))

    def test_trigger_execute_multiple_tags(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditional": json.dumps([condition]),
                "tag": "wrong_tag"}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=data, status_code=OBJECT_CREATED)

        data["tag"] = "execute_tag"

        self.put_with_status_check('/execution/listener/triggers/{0}'.format("execute_one"),
                                   headers=self.headers, data=data, status_code=OBJECT_CREATED)

        data["tag"] = "execute_tag_two"
        self.put_with_status_check('/execution/listener/triggers/{0}'.format("execute_two"),
                                   headers=self.headers, data=data, status_code=OBJECT_CREATED)

        result = {'value': 0}

        def step_finished_listener(sender, **kwargs):
            result['value'] += 1

        FunctionExecutionSuccess.connect(step_finished_listener)

        data = {"data": "hellohellohello"}

        response = self.post_with_status_check('/execution/listener/execute?tags=execute_tag&tags=execute_tag_two',
                                               headers=self.headers, data=data)
        self.assertEqual(2, result['value'])
        self.assertIn("execute_one", response["executed"])
        self.assertIn("execute_two", response["executed"])
        self.assertEqual(2, len(response["executed"]))
        self.assertEqual(0, len(response["errors"]))

    def test_trigger_execute_multiple_tags_with_name(self):
        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditional": json.dumps([condition]),
                "tag": "wrong_tag"}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=data, status_code=OBJECT_CREATED)

        data["tag"] = "execute_tag"

        self.put_with_status_check('/execution/listener/triggers/{0}'.format("execute_one"),
                                   headers=self.headers, data=data, status_code=OBJECT_CREATED)
        self.put_with_status_check('/execution/listener/triggers/{0}'.format("execute_two"),
                                   headers=self.headers, data=data, status_code=OBJECT_CREATED)

        data["tag"] = "execute_tag_two"
        self.put_with_status_check('/execution/listener/triggers/{0}'.format("execute_three"),
                                   headers=self.headers, data=data, status_code=OBJECT_CREATED)
        self.put_with_status_check('/execution/listener/triggers/{0}'.format("execute_four"),
                                   headers=self.headers, data=data, status_code=OBJECT_CREATED)

        data = {"data": "hellohellohello"}

        response = self.post_with_status_check(
            '/execution/listener/execute?tags=execute_tag&tags=execute_tag_two&name=testTrigger',
            headers=self.headers, data=data)
        self.assertIn("execute_one", response["executed"])
        self.assertIn("execute_two", response["executed"])
        self.assertIn("execute_three", response["executed"])
        self.assertIn("execute_four", response["executed"])
        self.assertIn("testTrigger", response["executed"])
        self.assertEqual(5, len(response["executed"]))
        self.assertEqual(0, len(response["errors"]))

    def test_triggers_change_playbook_name(self):
        self.put_with_status_check('/playbooks/test_playbook', headers=self.headers,
                                   status_code=OBJECT_CREATED)
        self.put_with_status_check('/playbooks/test_playbook/workflows/test_workflow',
                                   headers=self.headers, status_code=OBJECT_CREATED)

        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": '(.*)'}], "filters": []}
        data = {"playbook": "test_playbook",
                "workflow": "test_workflow",
                "conditional": json.dumps([condition])}
        self.put_with_status_check('/execution/listener/triggers/' + self.test_trigger_name,
                                   headers=self.headers, data=data, status_code=OBJECT_CREATED)

        data = {'new_name': 'test_playbook_new'}
        self.post_with_status_check('/playbooks/test_playbook',
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type='application/json')

        trigger = Triggers.query.filter_by(name=self.test_trigger_name).first()
        self.assertEqual('test_playbook_new', trigger.playbook)

    def test_triggers_change_workflow_name(self):
        self.put_with_status_check('/playbooks/test_playbook', headers=self.headers,
                                   status_code=OBJECT_CREATED)
        self.put_with_status_check('/playbooks/test_playbook/workflows/test_workflow',
                                   headers=self.headers, status_code=OBJECT_CREATED)

        condition = {"flag": 'regMatch', "args": [{"key": "regex", "value": '(.*)'}], "filters": []}
        data = {"playbook": "test_playbook",
                "workflow": "test_workflow",
                "conditional": json.dumps([condition])}
        self.put_with_status_check('/execution/listener/triggers/' + self.test_trigger_name,
                                   headers=self.headers, data=data, status_code=OBJECT_CREATED)

        data = {'new_name': 'test_workflow_new'}
        self.post_with_status_check('/playbooks/test_playbook/workflows/test_workflow',
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type='application/json')

        trigger = Triggers.query.filter_by(name=self.test_trigger_name).first()
        self.assertEqual('test_workflow_new', trigger.workflow)
