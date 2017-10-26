from tests.util.servertestcase import ServerTestCase
from server import flaskserver as server
from server.triggers import Triggers
from server.returncodes import *
from core.helpers import import_all_filters, import_all_flags
from tests import config
import core.config.config
from core.case import callbacks
import json
import apps

class TestTriggers(ServerTestCase):

    def setUp(self):
        apps.cache_apps(config.test_apps_path)
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
            # server.running_context.controller.shutdown_pool(0)

    def test_trigger_execute(self):
        server.running_context.controller.initialize_threading()

        response=self.post_with_status_check('/api/playbooks/triggerStepWorkflow/workflows/triggerStepWorkflow/execute',
                                             headers=self.headers, status_code=SUCCESS_ASYNC)

        data = {"execution_uids": [response['id']],
                "data_in": {"data": "1"}}

        result = {"result": False}

        @callbacks.TriggerStepAwaitingData.connect
        def send_data(sender, **kwargs):
            self.post_with_status_check('/api/triggers/send_data', headers=self.headers, data=json.dumps(data),
                                        status_code=SUCCESS, content_type='application/json')

        @callbacks.TriggerStepTaken.connect
        def trigger_taken(sender, **kwargs):
            result['result'] = True

        server.running_context.controller.shutdown_pool(1)
        self.assertTrue(result['result'])

    def test_trigger_execute_multiple_data(self):
        server.running_context.controller.initialize_threading()

        response = self.post_with_status_check(
            '/api/playbooks/triggerStepWorkflow/workflows/triggerStepWorkflow/execute',
            headers=self.headers, status_code=SUCCESS_ASYNC)

        data = {"execution_uids": [response['id']],
                "data_in": {"data": "aaa"}}

        result = {"result": 0}

        @callbacks.TriggerStepAwaitingData.connect
        def send_data(sender, **kwargs):
            self.post_with_status_check('/api/triggers/send_data', headers=self.headers, data=json.dumps(data),
                                        status_code=SUCCESS, content_type='application/json')
            data_correct = {"execution_uids": [response['id']],
                            "data_in": {"data": "1"}}
            self.post_with_status_check('/api/triggers/send_data', headers=self.headers, data=json.dumps(data_correct),
                                        status_code=SUCCESS, content_type='application/json')

        @callbacks.TriggerStepTaken.connect
        def trigger_taken(sender, **kwargs):
            result['result'] += 1

        server.running_context.controller.shutdown_pool(1)
        self.assertEqual(result['result'], 1)

    def test_trigger_execute_change_input(self):
        server.running_context.controller.initialize_threading()

        response = self.post_with_status_check(
            '/api/playbooks/triggerStepWorkflow/workflows/triggerStepWorkflow/execute',
            headers=self.headers, status_code=SUCCESS_ASYNC)

        data = {"execution_uids": [response['id']],
                "data_in": {"data": "1"},
                "inputs": {"call": "CHANGE INPUT"}}

        result = {"value": None}

        @callbacks.FunctionExecutionSuccess.connect
        def step_finished_listener(sender, **kwargs):
            result['value'] = kwargs['data']

        @callbacks.TriggerStepAwaitingData.connect
        def send_data(sender, **kwargs):
            self.post_with_status_check('/api/triggers/send_data', headers=self.headers, data=json.dumps(data),
                                        status_code=SUCCESS, content_type='application/json')

        server.running_context.controller.shutdown_pool(1)

        self.assertDictEqual(result['value'],
                             {'result': {'result': 'REPEATING: CHANGE INPUT', 'status': 'Success'}})

    # def test_trigger_execute_with_change_input_invalid_input(self):
    #     server.running_context.controller.initialize_threading()
    #
    #     response = self.post_with_status_check(
    #         '/api/playbooks/triggerStepWorkflow/workflows/triggerStepWorkflow/execute',
    #         headers=self.headers, status_code=SUCCESS_ASYNC)
    #
    #     data = {"execution_uids": [response['id']],
    #             "data_in": {"data": "1"},
    #             "inputs": {"invalid": "CHANGE INPUT"}}
    #
    #     result = {"result": False}
    #
    #     @callbacks.StepInputInvalid.connect
    #     def step_input_invalids(sender, **kwargs):
    #         result['result'] = True
    #
    #     @callbacks.TriggerStepAwaitingData.connect
    #     def send_data(sender, **kwargs):
    #         self.post_with_status_check('/api/triggers/send_data', headers=self.headers, data=json.dumps(data),
    #                                     status_code=SUCCESS, content_type='application/json')
    #
    #     server.running_context.controller.shutdown_pool(1)
    #     self.assertTrue(result['result'])

    # Old Trigger tests

    @classmethod
    def tearDownClass(cls):
        apps.clear_cache()

    def test_add_and_display_and_remove_trigger(self):
        condition = {"action": 'regMatch', "args": [{'name': 'regex', 'value': '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditions": [condition]}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=json.dumps(data), status_code=OBJECT_CREATED,
                                   content_type='application/json')
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
                "conditions-0": ""}
        response = self.app.put('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                headers=self.headers,
                                data=data, content_type='application/json')
        self.assertEqual(response._status_code, 400)

    def test_add_trigger_add_duplicate(self):
        condition = {"action": 'regMatch', "args": [{'name': 'regex', 'value': '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditions": [condition]}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=json.dumps(data), status_code=OBJECT_CREATED, content_type='application/json')
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   error="Trigger already exists.", headers=self.headers, data=json.dumps(data),
                                   status_code=OBJECT_EXISTS_ERROR, content_type='application/json')

    def test_remove_trigger_does_not_exist(self):
        self.delete_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                      error="Trigger does not exist.", headers=self.headers,
                                      status_code=OBJECT_DNE_ERROR)

    def test_edit_trigger(self):
        condition = {"action": 'regMatch', "args": [{'name': 'regex', 'value': '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditions": [condition]}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=json.dumps(data), status_code=OBJECT_CREATED, content_type='application/json')
        edited_data = {"name": "{0}rename".format(self.test_trigger_name),
                       "playbook": "testrename",
                       "workflow": '{0}rename'.format(self.test_trigger_workflow),
                       "conditions": [condition]}
        self.post_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name,),
                                    headers=self.headers, data=json.dumps(edited_data), content_type='application/json')

    def test_trigger_execute_old(self):
        server.running_context.controller.initialize_threading()
        condition = {"action": 'regMatch', "args": [{'name': 'regex', 'value': '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditions": [condition]}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=json.dumps(data), status_code=OBJECT_CREATED, content_type='application/json')

        response = self.post_with_status_check('/api/triggers/execute',
                                               headers=self.headers,
                                               data=json.dumps({"data": "hellohellohello"}),
                                               status_code=SUCCESS_ASYNC, content_type='application/json')

        server.running_context.controller.shutdown_pool(1)

        self.assertSetEqual(set(response.keys()), {'errors', 'executed'})
        self.assertEqual(len(response['executed']), 1)
        self.assertIn('id', response['executed'][0])
        self.assertEqual(response['executed'][0]['name'], 'testTrigger')
        self.assertListEqual(response['errors'], [])

    def test_trigger_execute_invalid_name(self):
        condition = {"action": 'regMatch', "args": [{'name': 'regex', 'value': '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": "invalid_workflow_name",
                "conditions": [condition]}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=json.dumps(data), status_code=OBJECT_CREATED, content_type='application/json')

        response = self.app.post('/api/triggers/execute', headers=self.headers, data=json.dumps({"data": "hellohellohello"}), content_type='application/json')
        error = {self.test_trigger_name: "Workflow could not be found."}
        self.assertEqual(INVALID_INPUT_ERROR, response._status_code)
        response = json.loads(response.get_data(as_text=True))
        self.assertIn("errors", response)
        self.assertIn(error, response["errors"])

    def test_trigger_execute_no_matching_trigger(self):
        condition = {"action": 'regMatch', "args": [{'name': 'regex', 'value': 'aaaa'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditions": [condition]}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=json.dumps(data), status_code=OBJECT_CREATED, content_type='application/json')

        self.post_with_status_check('/api/triggers/execute',
                                    headers=self.headers, data=json.dumps({"data": "bbb"}), status_code=SUCCESS_WITH_WARNING, content_type='application/json')

    def test_trigger_execute_change_input_old(self):
        server.running_context.controller.initialize_threading()
        condition = {"action": 'regMatch', "args": [{'name': 'regex', 'value': '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditions": [condition]}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=json.dumps(data), status_code=OBJECT_CREATED, content_type='application/json')

        result = {'value': None}

        def step_finished_listener(sender, **kwargs):
            result['value'] = kwargs['data']

        callbacks.FunctionExecutionSuccess.connect(step_finished_listener)

        data = {"data": "hellohellohello",
                "inputs": {"call": "CHANGE INPUT"}}

        response = self.post_with_status_check('/api/triggers/execute',
                                               headers=self.headers, data=json.dumps(data), status_code=SUCCESS_ASYNC,
                                               content_type='application/json')

        server.running_context.controller.shutdown_pool(1)

        self.assertSetEqual(set(response.keys()), {'errors', 'executed'})
        self.assertEqual(len(response['executed']), 1)
        self.assertIn('id', response['executed'][0])
        self.assertEqual(response['executed'][0]['name'], 'testTrigger')
        self.assertListEqual(response['errors'], [])
        self.assertDictEqual(result['value'],
                     {'result': {'result': 'REPEATING: CHANGE INPUT', 'status': 'Success'}})

    def test_trigger_with_change_input_invalid_input(self):
        server.running_context.controller.initialize_threading()
        condition = {"action": 'regMatch', "args": [{'name': 'regex', 'value': '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditions": [condition]}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=json.dumps(data), status_code=OBJECT_CREATED, content_type='application/json')

        data = {"data": "hellohellohello",
                "inputs": {"invalid": "CHANGE INPUT"}}

        response = self.post_with_status_check('/api/triggers/execute',
                                               headers=self.headers, data=json.dumps(data), status_code=SUCCESS_ASYNC, content_type='application/json')

        server.running_context.controller.shutdown_pool(1)

        self.assertSetEqual(set(response.keys()), {'errors', 'executed'})
        self.assertEqual(len(response['executed']), 1)
        self.assertEqual(response['executed'][0]['name'], 'testTrigger')
        self.assertListEqual(response['errors'], [])

    def test_trigger_execute_one(self):
        server.running_context.controller.initialize_threading()
        condition = {"action": 'regMatch', "args": [{'name': 'regex', 'value': '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditions": [condition]}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=json.dumps(data), status_code=OBJECT_CREATED, content_type='application/json')

        self.put_with_status_check('/execution/listener/triggers/{0}'.format("execute_me"),
                                   headers=self.headers, data=json.dumps(data), status_code=OBJECT_CREATED, content_type='application/json')

        result = {'value': 0}

        def step_finished_listener(sender, **kwargs):
            result['value'] += 1

        callbacks.FunctionExecutionSuccess.connect(step_finished_listener)

        data = {"data": "hellohellohello",
                "triggers": ['execute_me']}

        response = self.post_with_status_check('/api/triggers/execute?name=execute_me',
                                               headers=self.headers, data=json.dumps(data), status_code=SUCCESS_ASYNC, content_type='application/json')

        server.running_context.controller.shutdown_pool(1)

        self.assertEqual(1, result['value'])
        self.assertEqual(len(response['executed']), 1)
        self.assertIn('id', response['executed'][0])
        self.assertEqual(response['executed'][0]['name'], 'execute_me')
        self.assertEqual(0, len(response["errors"]))

    def test_trigger_execute_one_invalid_name(self):
        condition = {"action": 'regMatch', "args": [{'name': 'regex', 'value': '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditions": [condition]}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=json.dumps(data), status_code=OBJECT_CREATED, content_type='application/json')

        response = self.post_with_status_check('/api/triggers/execute',
                                               headers=self.headers, data=json.dumps({"data": "hellohellohello", "triggers": ['badname']}),
                                               status_code=SUCCESS_WITH_WARNING, content_type='application/json')
        self.assertEqual(0, len(response["executed"]))
        self.assertEqual(0, len(response["errors"]))

    def test_trigger_execute_tag(self):
        server.running_context.controller.initialize_threading()
        condition = {"action": 'regMatch', "args": [{'name': 'regex', 'value': '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditions": [condition],
                "tag": "wrong_tag"}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=json.dumps(data), status_code=OBJECT_CREATED, content_type='application/json')

        data["tag"] = "execute_tag"

        self.put_with_status_check('/execution/listener/triggers/{0}'.format("execute_one"),
                                   headers=self.headers, data=json.dumps(data), status_code=OBJECT_CREATED, content_type='application/json')
        self.put_with_status_check('/execution/listener/triggers/{0}'.format("execute_two"),
                                   headers=self.headers, data=json.dumps(data), status_code=OBJECT_CREATED, content_type='application/json')

        result = {'value': 0}

        def step_finished_listener(sender, **kwargs):
            result['value'] += 1

        callbacks.FunctionExecutionSuccess.connect(step_finished_listener)

        data = {"data": "hellohellohello", "tags": ['execute_tag']}

        response = self.post_with_status_check('/api/triggers/execute',
                                               headers=self.headers, data=json.dumps(data), status_code=SUCCESS_ASYNC, content_type='application/json')

        server.running_context.controller.shutdown_pool(2)

        self.assertEqual(2, result['value'])
        self.assertEqual(len(response['executed']), 2)
        executed_names = {executed['name'] for executed in response['executed']}
        self.assertSetEqual(executed_names, {'execute_one', 'execute_two'})
        self.assertEqual(0, len(response["errors"]))

    def test_trigger_execute_multiple_tags(self):
        server.running_context.controller.initialize_threading()
        condition = {"action": 'regMatch', "args": [{'name': 'regex', 'value': '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditions": [condition],
                "tag": "wrong_tag"}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=json.dumps(data), status_code=OBJECT_CREATED, content_type='application/json')

        data["tag"] = "execute_tag"

        self.put_with_status_check('/execution/listener/triggers/{0}'.format("execute_one"),
                                   headers=self.headers, data=json.dumps(data), status_code=OBJECT_CREATED, content_type='application/json')

        data["tag"] = "execute_tag_two"
        self.put_with_status_check('/execution/listener/triggers/{0}'.format("execute_two"),
                                   headers=self.headers, data=json.dumps(data), status_code=OBJECT_CREATED, content_type='application/json')

        result = {'value': 0}

        def step_finished_listener(sender, **kwargs):
            result['value'] += 1

        callbacks.FunctionExecutionSuccess.connect(step_finished_listener)

        data = {"data": "hellohellohello", "tags": ['execute_tag', 'execute_tag_two']}

        response = self.post_with_status_check('/api/triggers/execute',
                                               headers=self.headers, data=json.dumps(data), status_code=SUCCESS_ASYNC, content_type='application/json')

        server.running_context.controller.shutdown_pool(2)

        self.assertEqual(2, result['value'])
        executed_names = {executed['name'] for executed in response['executed']}
        self.assertSetEqual(executed_names, {'execute_one', 'execute_two'})
        self.assertEqual(2, len(response["executed"]))
        self.assertEqual(0, len(response["errors"]))

    def test_trigger_execute_multiple_tags_with_name(self):
        server.running_context.controller.initialize_threading()
        condition = {"action": 'regMatch', "args": [{'name': 'regex', 'value': '(.*)'}], "filters": []}
        data = {"playbook": "test",
                "workflow": self.test_trigger_workflow,
                "conditions": [condition],
                "tag": "wrong_tag"}
        self.put_with_status_check('/execution/listener/triggers/{0}'.format(self.test_trigger_name),
                                   headers=self.headers, data=json.dumps(data), status_code=OBJECT_CREATED, content_type='application/json')

        data["tag"] = "execute_tag"

        self.put_with_status_check('/execution/listener/triggers/{0}'.format("execute_one"),
                                   headers=self.headers, data=json.dumps(data), status_code=OBJECT_CREATED, content_type='application/json')
        self.put_with_status_check('/execution/listener/triggers/{0}'.format("execute_two"),
                                   headers=self.headers, data=json.dumps(data), status_code=OBJECT_CREATED, content_type='application/json')

        data["tag"] = "execute_tag_two"
        self.put_with_status_check('/execution/listener/triggers/{0}'.format("execute_three"),
                                   headers=self.headers, data=json.dumps(data), status_code=OBJECT_CREATED, content_type='application/json')
        self.put_with_status_check('/execution/listener/triggers/{0}'.format("execute_four"),
                                   headers=self.headers, data=json.dumps(data), status_code=OBJECT_CREATED, content_type='application/json')

        data = {"data": "hellohellohello", "tags": ['execute_tag', 'execute_tag_two'], 'triggers': ['testTrigger']}

        response = self.post_with_status_check(
            '/api/triggers/execute',
            headers=self.headers, data=json.dumps(data), status_code=SUCCESS_ASYNC, content_type='application/json')

        server.running_context.controller.shutdown_pool(5)

        executed_names = {executed['name'] for executed in response['executed']}
        self.assertSetEqual(executed_names, {'execute_one', 'execute_two', 'execute_three', 'execute_four', 'testTrigger'})
        self.assertEqual(5, len(response["executed"]))
        self.assertEqual(0, len(response["errors"]))

    def test_triggers_change_playbook_name(self):
        data = {"name": "test_playbook"}
        self.put_with_status_check('/api/playbooks', headers=self.headers,
                                   status_code=OBJECT_CREATED, data=json.dumps(data), content_type="application/json")
        data = {"name": "test_workflow"}
        self.put_with_status_check('/api/playbooks/test_playbook/workflows',
                                   headers=self.headers, status_code=OBJECT_CREATED, content_type='application/json',
                                   data=json.dumps(data))

        condition = {"action": 'regMatch', "args": [{'name': 'regex', 'value': '(.*)'}], "filters": []}
        data = {"playbook": "test_playbook",
                "workflow": "test_workflow",
                "conditions": [condition]}
        self.put_with_status_check('/execution/listener/triggers/' + self.test_trigger_name,
                                   headers=self.headers, data=json.dumps(data), status_code=OBJECT_CREATED, content_type='application/json')

        data = {'name': 'test_playbook', 'new_name': 'test_playbook_new'}
        self.post_with_status_check('/api/playbooks',
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type='application/json')

        trigger = Triggers.query.filter_by(name=self.test_trigger_name).first()
        self.assertEqual('test_playbook_new', trigger.playbook)

    def test_triggers_change_workflow_name(self):
        data = {'name': "test_playbook"}
        self.put_with_status_check('/api/playbooks', headers=self.headers,
                                   status_code=OBJECT_CREATED, data=json.dumps(data), content_type="application/json")
        data = {"name": "test_workflow"}
        self.put_with_status_check('/api/playbooks/test_playbook/workflows',
                                   headers=self.headers, status_code=OBJECT_CREATED, content_type='application/json',
                                   data=json.dumps(data))

        condition = {"action": 'regMatch', "args": [{'name': 'regex', 'value': '(.*)'}], "filters": []}
        data = {"playbook": "test_playbook",
                "workflow": "test_workflow",
                "conditions": [condition]}
        self.put_with_status_check('/execution/listener/triggers/' + self.test_trigger_name,
                                   headers=self.headers, data=json.dumps(data), status_code=OBJECT_CREATED, content_type='application/json')

        data = {'new_name': 'test_workflow_new', 'name': 'test_workflow'}
        self.post_with_status_check('/api/playbooks/test_playbook/workflows',
                                    data=json.dumps(data),
                                    headers=self.headers,
                                    content_type='application/json')

        trigger = Triggers.query.filter_by(name=self.test_trigger_name).first()
        self.assertEqual('test_workflow_new', trigger.workflow)
