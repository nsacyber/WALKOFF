import json
import uuid
from datetime import timedelta

from tests.util import execution_db_help
from walkoff import executiondb
from walkoff.executiondb.metrics import AppMetric, ActionMetric, ActionStatusMetric, WorkflowMetric
from tests.util.assertwrappers import orderless_list_compare
from tests.util.servertestcase import ServerTestCase
from walkoff.server import flaskserver as server
from walkoff.server.endpoints.metrics import _convert_action_time_averages, _convert_workflow_time_averages


class MetricsServerTest(ServerTestCase):
    def tearDown(self):
        execution_db_help.cleanup_execution_db()

    def test_convert_action_time_average(self):
        expected_json = {'apps': [{'count': 100,
                                   'name': 'app2',
                                   'actions': [{'error_metrics': {'count': 100,
                                                                  'avg_time': '1 day, 0:01:40.000500'},
                                                'success_metrics': {'count': 0,
                                                                    'avg_time': '0:01:40.000001'},
                                                'name': 'action1'}]},
                                  {'count': 2,
                                   'name': 'app1',
                                   'actions': [{'success_metrics': {'count': 0,
                                                                    'avg_time': '100 days, 0:00:00.000001'},
                                                'name': 'action1'},
                                               {'error_metrics': {'count': 2,
                                                                  'avg_time': '0:00:00.001000'},
                                                'name': 'action2'}]}]}

        action_status_one = ActionStatusMetric("success", timedelta(100, 0, 1).total_seconds())
        action_status_one.count = 0
        action_status_two = ActionStatusMetric("error", timedelta(0, 0, 1000).total_seconds())
        action_status_two.count = 2
        app_one = AppMetric("app1", actions=[
            ActionMetric(uuid.uuid4(), "action1", [action_status_one]),
            ActionMetric(uuid.uuid4(), "action2", [action_status_two])])
        app_one.count = 2

        action_status_one = ActionStatusMetric("success", timedelta(0, 100, 1).total_seconds())
        action_status_one.count = 0
        action_status_two = ActionStatusMetric("error", timedelta(1, 100, 500).total_seconds())
        action_status_two.count = 100
        app_two = AppMetric("app2", actions=[
            ActionMetric(uuid.uuid4(), "action1", [action_status_one, action_status_two])])
        app_two.count = 100

        executiondb.execution_db.session.add(app_one)
        executiondb.execution_db.session.add(app_two)
        executiondb.execution_db.session.commit()

        converted = _convert_action_time_averages()
        print(converted)
        orderless_list_compare(self, converted.keys(), ['apps'])
        self.assertEqual(len(converted['apps']), len(expected_json['apps']))
        orderless_list_compare(self, [x['name'] for x in converted['apps']], ['app1', 'app2'])

        app1_metrics = [x for x in converted['apps'] if x['name'] == 'app1'][0]
        expected_app1_metrics = [x for x in expected_json['apps'] if x['name'] == 'app1'][0]
        orderless_list_compare(self, app1_metrics.keys(), ['count', 'name', 'actions'])
        self.assertEqual(app1_metrics['count'], expected_app1_metrics['count'])
        self.assertTrue(len(app1_metrics['actions']), len(expected_app1_metrics['actions']))
        for action_metric in expected_app1_metrics['actions']:
            self.assertIn(action_metric, app1_metrics['actions'])

        app2_metrics = [x for x in converted['apps'] if x['name'] == 'app2'][0]
        expected_app2_metrics = [x for x in expected_json['apps'] if x['name'] == 'app2'][0]
        orderless_list_compare(self, app2_metrics.keys(), ['count', 'name', 'actions'])
        self.assertEqual(app2_metrics['count'], expected_app2_metrics['count'])
        self.assertTrue(len(app2_metrics['actions']), len(expected_app2_metrics['actions']))
        for action_metric in expected_app2_metrics['actions']:
            self.assertIn(action_metric, app2_metrics['actions'])

    # def test_convert_workflow_time_average(self):
    #     test1 = {'workflow1': {'count': 0,
    #                            'avg_time': timedelta(100, 0, 1)},
    #              'workflow2': {'count': 2,
    #                            'avg_time': timedelta(0, 0, 1000)},
    #              'workflow3': {'count': 0,
    #                            'avg_time': timedelta(0, 100, 1)},
    #              'workflow4': {'count': 100,
    #                            'avg_time': timedelta(1, 100, 500)}}
    #     expected_json = {'workflows': [{'count': 100,
    #                                     'avg_time': '1 day, 0:01:40.000500',
    #                                     'name': 'workflow4'},
    #                                    {'count': 2,
    #                                     'avg_time': '0:00:00.001000',
    #                                     'name': 'workflow2'},
    #                                    {'count': 0,
    #                                     'avg_time': '0:01:40.000001',
    #                                     'name': 'workflow3'},
    #                                    {'count': 0,
    #                                     'avg_time': '100 days, 0:00:00.000001',
    #                                     'name': 'workflow1'}]}
    #     metrics.workflow_metrics = test1
    #     converted = _convert_workflow_time_averages()
    #     orderless_list_compare(self, converted.keys(), ['workflows'])
    #     self.assertEqual(len(converted['workflows']), len(expected_json['workflows']))
    #     for workflow in expected_json['workflows']:
    #         self.assertIn(workflow, converted['workflows'])
    #
    # def test_action_metrics(self):
    #
    #     workflow = execution_db_help.load_workflow('multiactionError', 'multiactionErrorWorkflow')
    #
    #     server.running_context.executor.execute_workflow(workflow.id)
    #     server.running_context.executor.wait_and_reset(1)
    #
    #     response = self.app.get('/api/metrics/apps', headers=self.headers)
    #     self.assertEqual(response.status_code, 200)
    #     response = json.loads(response.get_data(as_text=True))
    #     self.assertDictEqual(response, _convert_action_time_averages())
    #
    # def test_workflow_metrics(self):
    #     error_id = execution_db_help.load_workflow('multiactionError', 'multiactionErrorWorkflow').id
    #     test_id = execution_db_help.load_workflow('multiactionWorkflowTest', 'multiactionWorkflow').id
    #
    #     server.running_context.executor.execute_workflow(error_id)
    #     server.running_context.executor.execute_workflow(error_id)
    #     server.running_context.executor.execute_workflow(test_id)
    #     server.running_context.executor.wait_and_reset(3)
    #
    #     response = self.app.get('/api/metrics/workflows', headers=self.headers)
    #     self.assertEqual(response.status_code, 200)
    #     response = json.loads(response.get_data(as_text=True))
    #     self.assertDictEqual(response, _convert_workflow_time_averages())
