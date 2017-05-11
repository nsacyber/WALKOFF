from tests.util.servertestcase import ServerTestCase
from server import flaskserver as server
from tests import config
import server.metrics as metrics
from server.endpoints.metrics import _convert_action_time_averages, _convert_workflow_time_averages
import json
from datetime import timedelta


class MetricsServerTest(ServerTestCase):
    def setUp(self):
        metrics.app_metrics = {}

    def test_convert_action_time_average(self):
        '''
        ret = deepcopy(metrics.app_metrics)
        for app in ret:
            for action in app['actions']:
                ret[app]['actions'][action]['avg_time'] = str(action['avg_time'])
        return ret
        '''

        test1 = {'app1': {'actions': {'action1': {'success': {'count': 0,
                                                              'avg_time': timedelta(100, 0, 1)}},
                                      'action2': {'error': {'count': 2,
                                                            'avg_time': timedelta(0, 0, 1000)}}},
                          'count': 2},
                 'app2': {'actions': {'action1': {'success': {'count': 0,
                                                              'avg_time': timedelta(0, 100, 1)},
                                                  'error': {'count': 100,
                                                            'avg_time': timedelta(1, 100, 500)}}},
                          'count': 100}}
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

        metrics.app_metrics = test1
        self.assertDictEqual(_convert_action_time_averages(), expected_json)

    def test_convert_workflow_time_average(self):
        test1 = {'worfklow1': {'count': 0,
                               'avg_time': timedelta(100, 0, 1)},
                 'worfklow2': {'count': 2,
                               'avg_time': timedelta(0, 0, 1000)},
                 'worfklow3': {'count': 0,
                               'avg_time': timedelta(0, 100, 1)},
                 'worfklow4': {'count': 100,
                               'avg_time': timedelta(1, 100, 500)}}
        expected_json = {'workflows': [{'count': 100,
                                        'avg_time': '1 day, 0:01:40.000500',
                                        'name': 'worfklow4'},
                                       {'count': 2,
                                        'avg_time': '0:00:00.001000',
                                        'name': 'worfklow2'},
                                       {'count': 0,
                                        'avg_time': '0:01:40.000001',
                                        'name': 'worfklow3'},
                                       {'count': 0,
                                        'avg_time': '100 days, 0:00:00.000001',
                                        'name': 'worfklow1'}]}
        metrics.workflow_metrics = test1
        self.assertDictEqual(_convert_workflow_time_averages(), expected_json)

    def test_action_metrics(self):
        server.running_context.controller.load_workflows_from_file(path=config.test_workflows_path +
                                                                        'multistepError.workflow')

        server.running_context.controller.execute_workflow('multistepError', 'multiactionErrorWorkflow')

        response = self.app.get('/metrics/apps', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, _convert_action_time_averages())

    def test_workflow_metrics(self):
        server.running_context.controller.load_workflows_from_file(path=config.test_workflows_path +
                                                                        'multistepError.workflow')
        server.running_context.controller.load_workflows_from_file(path=config.test_workflows_path +
                                                                        'tieredWorkflow.workflow')
        server.running_context.controller.load_workflows_from_file(path=config.test_workflows_path +
                                                                        'multiactionWorkflowTest.workflow')
        server.running_context.controller.execute_workflow('multistepError', 'multiactionErrorWorkflow')
        server.running_context.controller.execute_workflow('tieredWorkflow', 'parentWorkflow')
        server.running_context.controller.execute_workflow('multistepError', 'multiactionErrorWorkflow')
        server.running_context.controller.execute_workflow('tieredWorkflow', 'parentWorkflow')
        server.running_context.controller.execute_workflow('multiactionWorkflowTest', 'multiactionWorkflow')
        response = self.app.get('/metrics/workflows', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.get_data(as_text=True))
        self.assertDictEqual(response, _convert_workflow_time_averages())
